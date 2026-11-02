"""Shared parameter types and helpers for tool modules."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Annotated, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from ..config import get_settings
from ..coverage import COVERAGE
from ..flags import CommandHelp, command_help, suggest
from ..models import CommandResult
from ..runner import run_uv
from ..security import ValidationError, _check_text, resolve_project_dir, safe_extra_args, safe_value, safe_values

# --------------------------------------------------------------------------- #
# Reusable parameter annotations (keep descriptions short: they cost context).
# --------------------------------------------------------------------------- #

ProjectPath = Annotated[
    str | None,
    Field(description="Project directory, absolute or relative to the workspace root (default: workspace root)."),
]
ExtraArgs = Annotated[
    list[str] | None,
    Field(
        description="Any other option of this uv command, e.g. ['--compile-bytecode']. Checked against the "
        "installed uv; uv_help lists every option."
    ),
]
PythonRequest = Annotated[
    str | None,
    Field(description="Python to use: version ('3.12'), 'pypy@3.10' or a path."),
]
Member = Annotated[
    str | None,
    Field(description="Workspace member (--package)."),
]
Script = Annotated[
    str | None,
    Field(description="PEP 723 script to operate on instead of the project."),
]
Groups = Annotated[list[str] | None, Field(description="Dependency groups to include (--group).")]
Extras = Annotated[list[str] | None, Field(description="Optional-dependency extras to include (--extra).")]
Frozen = Annotated[bool, Field(description="Use uv.lock without updating it.")]
Locked = Annotated[bool, Field(description="Fail if uv.lock is out of date.")]
TimeoutSeconds = Annotated[
    float | None,
    Field(description="Timeout in seconds (default: server setting).", gt=0, le=86_400),
]

R = TypeVar("R", bound=CommandResult)


class ResolverOptions(BaseModel):
    """The resolver options agents need most. Every other uv option goes through extra_args (see uv_help)."""

    model_config = ConfigDict(extra="forbid")

    resolution: Literal["highest", "lowest", "lowest-direct"] | None = None
    prerelease: Literal["disallow", "allow", "if-necessary", "explicit", "if-necessary-or-explicit"] | None = None
    exclude_newer: str | None = Field(None, description="Ignore uploads after this date, e.g. '2025-01-31'.")
    index: list[str] | None = Field(None, description="Extra indexes, URL or name=URL, highest priority first.")
    default_index: str | None = Field(None, description="Use instead of PyPI.")
    python_platform: str | None = Field(None, description="Target platform, e.g. 'linux' (pip, sync, run, tool).")
    no_build: bool = Field(False, description="Wheels only; never build from source.")
    no_sources: bool = Field(False, description="Ignore [tool.uv.sources].")
    offline: bool = Field(False, description="Cache only, no network.")


Resolver = Annotated[
    ResolverOptions | None,
    Field(description="Resolution and index options."),
]


def _command_path(base: Sequence[str]) -> tuple[str, ...]:
    """The uv command an argv targets, e.g. ('pip', 'install') for ['pip', 'install', '--dry-run']."""
    words = []
    for token in base:
        if token.startswith("-"):
            break
        words.append(token)
    for n in range(len(words), 0, -1):
        if tuple(words[:n]) in COVERAGE:
            return tuple(words[:n])
    return tuple(words[:1])


def validate_options(path: tuple[str, ...], extra_args: Sequence[str], help_: CommandHelp | None) -> list[str]:
    """Check extra uv options against what the installed uv accepts for ``path``.

    Unknown flags, flags given a value they do not take, missing values and values outside a flag's allowed
    choices are rejected with a precise message, before uv runs. If uv's help is unavailable the arguments are
    passed through (uv will report problems itself).
    """
    args = list(extra_args)
    if help_ is None:
        return args
    cmd = "uv " + " ".join(path)
    out: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--":
            raise ValidationError("'--' is not allowed in extra_args")
        if not token.startswith("-") or token == "-":
            out.append(token)
            i += 1
            continue
        if token.startswith("--"):
            name, eq, value = token.partition("=")
            opt = help_.lookup(name)
            inline = bool(eq)
        else:  # short flag: -p3.12, -p 3.12, -U, -qq
            name, value = token[:2], token[2:]
            opt = help_.lookup(name)
            inline = bool(value)
            if opt is not None and not opt.takes_value and value:
                if any(help_.lookup("-" + c) is None or help_.lookup("-" + c).takes_value for c in value):
                    raise ValidationError(f"Unknown combined short flags {token!r} for `{cmd}`")
                inline = False
        if opt is None:
            hints = suggest(name, help_)
            did_you_mean = f" Did you mean {', '.join(hints)}?" if hints else ""
            raise ValidationError(
                f"`{cmd}` has no option {name}.{did_you_mean} Call uv_help with command='{' '.join(path)}' to list options."
            )
        if opt.takes_value:
            if not inline:
                if i + 1 >= len(args):
                    raise ValidationError(f"{name} needs a value <{opt.value}>")
                value = _check_text(args[i + 1], f"value for {name}")
                out += [token, value]
                i += 2
            else:
                out.append(token)
                i += 1
            if opt.choices and value.split("=", 1)[0] not in opt.choices:
                raise ValidationError(f"{name} must be one of: {', '.join(opt.choices)} (got {value!r})")
            continue
        if inline and token.startswith("--"):
            raise ValidationError(f"{name} does not take a value")
        out.append(token)
        i += 1
    return out


class Args:
    """Small argv builder that validates values as they are added."""

    def __init__(self, *base: str) -> None:
        self.argv: list[str] = list(base)
        self.path = _command_path(base)

    def flag(self, enabled: bool | None, name: str) -> Args:
        if enabled:
            self.argv.append(name)
        return self

    def opt(self, name: str, value: str | None, what: str | None = None) -> Args:
        if value is not None and str(value).strip():
            self.argv += [name, safe_value(str(value), what or name)]
        return self

    def path_opt(self, name: str, value: Path | None) -> Args:
        if value is not None:
            self.argv += [name, str(value)]
        return self

    def many(self, name: str, values: Iterable[str] | None, what: str | None = None) -> Args:
        for v in safe_values(values, what or name):
            self.argv += [name, v]
        return self

    def positional(self, values: Iterable[str] | None, what: str) -> Args:
        self.argv += safe_values(values, what)
        return self

    def extra(self, extra_args: Sequence[str] | None) -> Args:
        """Append caller-supplied uv options, validated against the installed uv's options for this command."""
        cleaned = safe_extra_args(extra_args, get_settings())
        if cleaned and self.path:
            cleaned = validate_options(self.path, cleaned, command_help(self.path))
        self.argv += cleaned
        return self

    def passthrough(self, args: Sequence[str] | None) -> Args:
        """Append arguments meant for another program (e.g. ruff), with only basic safety checks."""
        self.argv += safe_extra_args(args, get_settings())
        return self

    def resolver(self, options: ResolverOptions | None) -> Args:
        """Append resolver/index options, refusing any the installed uv does not support for this command."""
        if options is None:
            return self
        o = options
        wanted: list[tuple[str, list[str]]] = []
        for flag, value in (
            ("--resolution", o.resolution),
            ("--prerelease", o.prerelease),
            ("--exclude-newer", o.exclude_newer),
            ("--default-index", o.default_index),
            ("--python-platform", o.python_platform),
        ):
            if value:
                wanted.append((flag, [flag, safe_value(value, flag)]))
        for value in o.index or []:
            wanted.append(("--index", ["--index", safe_value(value, "--index")]))
        for flag, enabled in (("--no-build", o.no_build), ("--no-sources", o.no_sources), ("--offline", o.offline)):
            if enabled:
                wanted.append((flag, [flag]))
        help_ = command_help(self.path) if self.path else None
        for flag, argv in wanted:
            if help_ is not None and help_.lookup(flag) is None:
                raise ValidationError(f"`uv {' '.join(self.path)}` does not support {flag}")
            self.argv += argv
        return self

    def dependency_selection(
        self,
        *,
        extras: Sequence[str] | None = None,
        all_extras: bool = False,
        groups: Sequence[str] | None = None,
        all_groups: bool = False,
        no_dev: bool = False,
        only_dev: bool = False,
    ) -> Args:
        self.many("--extra", extras, "extra")
        self.flag(all_extras, "--all-extras")
        self.many("--group", groups, "group")
        self.flag(all_groups, "--all-groups")
        self.flag(no_dev, "--no-dev")
        self.flag(only_dev, "--only-dev")
        return self


def project_dir(project_path: str | None) -> Path:
    return resolve_project_dir(project_path, get_settings())


async def run(
    args: Args | Sequence[str],
    *,
    cwd: Path | None = None,
    mutating: bool = False,
    lock_key: str | None = None,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
    stdin_data: str | None = None,
    secrets: Sequence[str] = (),
) -> CommandResult:
    argv = args.argv if isinstance(args, Args) else list(args)
    return await run_uv(
        argv,
        cwd=cwd,
        mutating=mutating,
        lock_key=lock_key,
        timeout=timeout,
        env=env,
        stdin_data=stdin_data,
        secrets=secrets,
    )


def extend(result: CommandResult, cls: type[R], **fields: object) -> R:
    """Upgrade a base :class:`CommandResult` into a richer subclass."""
    return cls(**{**result.model_dump(), **fields})


def frozen_if_read_only(args: Args) -> Args:
    """In read-only mode, stop commands that implicitly lock from rewriting uv.lock."""
    if get_settings().read_only and "--frozen" not in args.argv and "--locked" not in args.argv:
        args.argv.append("--frozen")
    return args
