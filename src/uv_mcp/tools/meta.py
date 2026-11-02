"""Server/uv introspection, uv self update, and the guarded ``uv_command`` escape hatch."""

from __future__ import annotations

import asyncio
import inspect
import os
import platform
import re
from typing import Annotated

from pydantic import Field

from .. import __version__
from ..config import get_settings
from ..coverage import BLOCKED, COVERAGE
from ..flags import clear_cache, command_help
from ..models import CommandResult, HelpResult, OptionInfo, SelfUpdateResult, ServerInfo, UVDirectories
from ..parsing import last_line, load_json
from ..registry import uv_tool
from ..security import ValidationError, safe_extra_args, safe_value
from ._common import Args, TimeoutSeconds, extend, run

INSTALL_INSTRUCTIONS = {
    "macos_linux": "curl -LsSf https://astral.sh/uv/install.sh | sh",
    "windows": 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"',
    "homebrew": "brew install uv",
    "pipx": "pipx install uv",
    "docs": "https://docs.astral.sh/uv/getting-started/installation/",
}


async def _uv_version() -> str | None:
    result = await run(Args("self", "version", "--output-format", "json"))
    data = load_json(result.stdout) if result.success else None
    if isinstance(data, dict) and data.get("version"):
        return str(data["version"])
    fallback = await run(Args("--version"))
    if fallback.success and fallback.stdout.strip():
        return fallback.stdout.strip().split()[-1] if " " in fallback.stdout.strip() else fallback.stdout.strip()
    return None


async def _dir(*argv: str) -> str | None:
    result = await run(Args(*argv))
    return last_line(result.stdout) if result.success else None


@uv_tool(title="Describe uv and this server", toolset=None, read_only=True, idempotent=True)
async def uv_info() -> ServerInfo:
    """Report the uv version, workspace root, enabled toolsets, safety settings and uv's directories.

    Call this first if unsure which project the server operates on or whether uv is installed.
    """
    settings = get_settings()
    uv_path = settings.resolve_uv()
    notes: list[str] = []
    root = settings.workspace_root
    is_project = any((p / "pyproject.toml").is_file() for p in (root, *root.parents))

    if uv_path is None:
        return ServerInfo(
            server_version=__version__,
            uv_installed=False,
            platform=f"{platform.system()} {platform.machine()}",
            workspace_root=str(root),
            workspace_is_project=is_project,
            read_only=settings.read_only,
            toolsets=sorted(settings.toolsets),
            allowed_roots=[str(r) for r in settings.allowed_roots],
            install_instructions=INSTALL_INSTRUCTIONS,
            notes=[
                "uv was not found. Ask the user to install it with one of install_instructions, then restart the MCP server."
            ],
        )

    version, cache, py_dir, py_bin, tool_dir, tool_bin, creds = await asyncio.gather(
        _uv_version(),
        _dir("cache", "dir"),
        _dir("python", "dir"),
        _dir("python", "dir", "--bin"),
        _dir("tool", "dir"),
        _dir("tool", "dir", "--bin"),
        _dir("auth", "dir"),
    )
    if not is_project:
        notes.append(
            "The workspace root is not inside a uv project. Pass project_path to project tools, "
            "or create a project with uv_init."
        )
    if (root / "src" / "uv_mcp").is_dir() and not os.environ.get("UV_MCP_WORKSPACE_ROOT"):
        notes.append(
            "The workspace root is the uv-mcp source tree. That is expected when working on uv-mcp itself; if you "
            "meant another project, the client config likely uses `uv --directory`. Switch it to "
            "`uvx uv-mcp-server`, set UV_MCP_WORKSPACE_ROOT, or pass project_path."
        )
    if settings.read_only:
        notes.append("Read-only mode: tools that modify projects, environments or caches are disabled.")
    return ServerInfo(
        server_version=__version__,
        uv_installed=True,
        uv_version=version,
        uv_path=uv_path,
        platform=f"{platform.system()} {platform.machine()}",
        workspace_root=str(root),
        workspace_is_project=is_project,
        read_only=settings.read_only,
        toolsets=sorted(settings.toolsets),
        allowed_roots=[str(r) for r in settings.allowed_roots],
        directories=UVDirectories(
            cache=cache, python_installs=py_dir, python_bin=py_bin, tools=tool_dir, tool_bin=tool_bin, credentials=creds
        ),
        notes=notes,
    )


@uv_tool(title="Update uv itself (uv self update)", toolset="self", destructive=True, open_world=True)
async def uv_self_update(
    target_version: Annotated[
        str | None, Field(description="Specific uv version to install (default: latest).")
    ] = None,
    dry_run: bool = False,
) -> SelfUpdateResult:
    """Update the uv executable. Only works when uv was installed with the standalone installer."""
    before = await _uv_version()
    args = Args("self", "update").flag(dry_run, "--dry-run")
    if target_version:
        args.argv.append(safe_value(target_version, "target_version"))
    result = await run(args, mutating=True, lock_key="global:self")
    if result.success and not dry_run:
        clear_cache()  # options may have changed with the new uv
    after = await _uv_version() if result.success and not dry_run else before
    if not result.success and "installed via" in (result.stderr + result.stdout).lower():
        result.hint = "uv was installed by a package manager; update it with that package manager instead."
    return extend(result, SelfUpdateResult, previous_version=before, new_version=after)


# --------------------------------------------------------------------------- #
# Option discovery
# --------------------------------------------------------------------------- #

_FLAG_LITERAL_RE = re.compile(r'"(--[a-z0-9][a-z0-9-]*)"')
_RESOLVER_FLAGS = {
    "--resolution", "--prerelease", "--exclude-newer", "--index", "--default-index", "--python-platform",
    "--no-build", "--no-sources", "--offline",
}  # fmt: skip


def _tool_flags(tool: str) -> tuple[set[str], bool]:
    """Flags a tool sets from its own parameters, and whether it takes the shared `resolver` options."""
    from ..registry import REGISTRY

    spec = REGISTRY.get(tool)
    if spec is None:
        return set(), False
    try:
        source = inspect.getsource(spec.fn)
    except (OSError, TypeError):
        source = ""
    return set(_FLAG_LITERAL_RE.findall(source)), "resolver" in inspect.signature(spec.fn).parameters


@uv_tool(title="Look up uv command options (uv help)", toolset=None, read_only=True, idempotent=True)
async def uv_help(
    command: Annotated[
        str, Field(description="uv command, e.g. 'add', 'pip install', 'python'. Empty for the list of commands.")
    ] = "",
    search: Annotated[
        str | None, Field(description="Only options whose flag or description contains this text.")
    ] = None,
) -> HelpResult:
    """List every option the installed uv accepts for a command: value type, allowed choices, env var, and how to
    pass it with uv-mcp (a tool parameter, the `resolver` object, or extra_args). Use it before reaching for an
    uncommon uv feature."""
    words = command.split()
    if any(not _SUBCOMMAND_RE.match(w) for w in words):
        raise ValidationError(f"Not a uv command: {command!r}")
    path = tuple(words)
    help_ = command_help(path)
    if help_ is None:
        raise ValidationError(f"uv has no command `uv {command}` (or uv is not installed). Try command=''.")
    how = COVERAGE.get(path)
    tool = how if isinstance(how, str) else None
    dedicated, has_resolver = _tool_flags(tool) if tool else (set(), False)
    needle = (search or "").lower()
    options = []
    for opt in help_.options.values():
        if needle and needle not in opt.flag and needle not in opt.description.lower():
            continue
        if opt.flag in dedicated:
            via = "parameter"
        elif has_resolver and opt.flag in _RESOLVER_FLAGS:
            via = "resolver"
        else:
            via = "extra_args"
        options.append(
            OptionInfo(
                flag=opt.flag,
                short=opt.short,
                value=opt.value,
                choices=opt.choices,
                env=opt.env,
                scope=opt.scope,  # type: ignore[arg-type]
                description=opt.description,
                via=via,  # type: ignore[arg-type]
            )
        )
    return HelpResult(
        command=" ".join(("uv", *path)),
        summary=help_.summary,
        usage=help_.usage,
        tool=tool,
        subcommands=help_.subcommands,
        options=options,
        total_options=len(help_.options),
        uv_version=await _uv_version(),
    )


# --------------------------------------------------------------------------- #
# Escape hatch
# --------------------------------------------------------------------------- #

#: The first argument must be a subcommand (or --version/--help), never a global flag such as --directory.
#: Any subcommand shape is accepted so commands added in newer uv releases work immediately; uv rejects unknown ones.
_SUBCOMMAND_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_TOP_LEVEL_FLAGS = {"--version", "--help", "-V", "-h"}
#: Subcommand prefixes that are never allowed through uv_command (see uv_mcp.coverage).
_BLOCKED = BLOCKED
#: Subcommand prefixes permitted in read-only mode.
_READ_ONLY = {
    ("--version",),
    ("help",),
    ("tree",),
    ("audit",),
    ("python", "list"),
    ("python", "find"),
    ("python", "dir"),
    ("tool", "list"),
    ("tool", "dir"),
    ("tool", "audit"),
    ("pip", "list"),
    ("pip", "show"),
    ("pip", "freeze"),
    ("pip", "tree"),
    ("pip", "check"),
    ("cache", "dir"),
    ("cache", "size"),
    ("self", "version"),
    ("workspace", "list"),
    ("workspace", "dir"),
    ("workspace", "metadata"),
    ("auth", "dir"),
    ("lock", "--check"),
    ("sync", "--check"),
}


def _is_blocked(args: list[str], prefix: tuple[str, ...]) -> bool:
    """Loose match for the blocklist: uv accepts global flags between subcommands (``auth -q token``), so a
    blocked subcommand anywhere after its parent counts."""
    return args[0] == prefix[0] and all(part in args[1:] for part in prefix[1:])


def _matches(args: list[str], prefix: tuple[str, ...]) -> bool:
    if prefix[-1].startswith("-"):  # flag prefixes like ("lock", "--check") may appear anywhere
        return args[: len(prefix) - 1] == list(prefix[:-1]) and prefix[-1] in args
    return args[: len(prefix)] == list(prefix)


@uv_tool(title="Run any uv command (escape hatch)", toolset=None, destructive=True, open_world=True)
async def uv_command(
    args: Annotated[
        list[str],
        Field(
            description="Arguments after `uv`, subcommand first, e.g. ['workspace', 'list'] or ['pip', 'install', '--dry-run', 'x']. "
            "Global flags go after the subcommand.",
            min_length=1,
        ),
    ],
    project_path: Annotated[str | None, Field(description="Working directory (default: workspace root).")] = None,
    timeout_seconds: TimeoutSeconds = None,
) -> CommandResult:
    """Run an arbitrary uv command. Use only when no dedicated uv_* tool covers what you need.

    Not run through a shell. `uv auth token` and `update-shell` commands are refused. In read-only mode
    only inspection commands are allowed.
    """
    from ._common import project_dir

    settings = get_settings()
    argv = safe_extra_args(args, settings)
    if not (_SUBCOMMAND_RE.match(argv[0]) or argv[0] in _TOP_LEVEL_FLAGS):
        raise ValidationError(
            f"The first argument must be a uv subcommand such as 'sync' or 'pip', not {argv[0]!r}. "
            "Put global flags after the subcommand."
        )
    for prefix, reason in _BLOCKED.items():
        if _is_blocked(argv, prefix):
            raise ValidationError(f"`uv {' '.join(prefix)}` is not allowed through uv-mcp: it {reason}.")
    if settings.read_only and not any(_matches(argv, p) for p in _READ_ONLY):
        raise ValidationError("uv-mcp is in read-only mode; only inspection commands may run through uv_command.")
    implicitly_locks = argv[0] in ("tree", "audit") or argv[:2] == ["workspace", "metadata"]
    if settings.read_only and implicitly_locks and "--frozen" not in argv and "--locked" not in argv:
        argv.append("--frozen")
    cwd = project_dir(project_path)
    return await run(argv, cwd=cwd, timeout=timeout_seconds)
