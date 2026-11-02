"""Runtime configuration for uv-mcp.

Every setting can be supplied through an environment variable (so it can be set
from an MCP client's ``env`` block) or through a command-line flag on
``uv-mcp-server``. Command-line flags win over environment variables.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

#: Every toolset the server knows about. ``uv_info`` and ``uv_command`` are
#: always registered and are therefore not part of any toolset.
ALL_TOOLSETS: tuple[str, ...] = (
    "project",
    "python",
    "pip",
    "venv",
    "tool",
    "build",
    "cache",
    "auth",
    "self",
    "diagnostics",
)

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off", ""}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    raise ValueError(f"{name} must be a boolean (true/false), got {raw!r}")


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    value = float(raw)
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {raw!r}")
    return value


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {raw!r}")
    return value


def parse_toolsets(raw: str | None) -> frozenset[str]:
    """Parse a comma-separated toolset list. ``all`` (or empty) selects everything."""
    if raw is None or not raw.strip() or raw.strip().lower() == "all":
        return frozenset(ALL_TOOLSETS)
    selected = {part.strip().lower() for part in raw.split(",") if part.strip()}
    unknown = selected - set(ALL_TOOLSETS)
    if unknown:
        raise ValueError(
            f"Unknown toolset(s): {', '.join(sorted(unknown))}. Valid toolsets: {', '.join(ALL_TOOLSETS)}, all"
        )
    return frozenset(selected)


def parse_paths(raw: str | None) -> tuple[Path, ...]:
    """Parse an ``os.pathsep``-separated list of directories into resolved paths."""
    if not raw or not raw.strip():
        return ()
    return tuple(Path(part).expanduser().resolve() for part in raw.split(os.pathsep) if part.strip())


@dataclass(frozen=True)
class Settings:
    """Immutable server settings."""

    #: Default directory for project-scoped tools when no ``project_path`` is given.
    workspace_root: Path = field(default_factory=lambda: Path.cwd().resolve())
    #: When non-empty, every path the server touches must live under one of these.
    allowed_roots: tuple[Path, ...] = ()
    #: Only register tools that never modify anything.
    read_only: bool = False
    #: Toolsets to register.
    toolsets: frozenset[str] = frozenset(ALL_TOOLSETS)
    #: Default timeout for a uv invocation, in seconds.
    timeout: float = 600.0
    #: Maximum characters kept per output stream (stdout/stderr) in a tool result.
    max_output_chars: int = 30_000
    #: Explicit path to the uv executable (``None`` means look it up on PATH).
    uv_path: str | None = None
    #: Allow ``uv_command`` (the raw escape hatch).
    allow_raw_command: bool = True

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            workspace_root=default_workspace_root(),
            allowed_roots=parse_paths(os.environ.get("UV_MCP_ALLOWED_ROOTS")),
            read_only=_env_bool("UV_MCP_READ_ONLY", False),
            toolsets=parse_toolsets(os.environ.get("UV_MCP_TOOLSETS")),
            timeout=_env_float("UV_MCP_TIMEOUT", 600.0),
            max_output_chars=_env_int("UV_MCP_MAX_OUTPUT_CHARS", 30_000),
            uv_path=os.environ.get("UV_MCP_UV_PATH", "").strip() or None,
            allow_raw_command=_env_bool("UV_MCP_ALLOW_RAW_COMMAND", True),
        )

    def resolve_uv(self) -> str | None:
        """Return the absolute path of the uv executable, or ``None`` if not found."""
        if self.uv_path:
            candidate = Path(self.uv_path).expanduser()
            return str(candidate) if candidate.is_file() else None
        return shutil.which("uv")


def default_workspace_root() -> Path:
    """Pick the directory project tools default to.

    Order: ``UV_MCP_WORKSPACE_ROOT``; ``CLAUDE_PROJECT_DIR`` (set by Claude Code for MCP servers);
    the process working directory (stdio clients normally launch servers in the project).
    Values that are empty, still contain an unexpanded ``${...}`` placeholder, or do not
    point at an existing directory are skipped.
    """
    for var in ("UV_MCP_WORKSPACE_ROOT", "CLAUDE_PROJECT_DIR"):
        raw = os.environ.get(var, "").strip()
        if not raw or "${" in raw:
            continue
        candidate = Path(raw).expanduser()
        if candidate.is_dir():
            return candidate.resolve()
    return Path.cwd().resolve()


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the active settings (loading them from the environment on first use)."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def set_settings(settings: Settings) -> None:
    """Install ``settings`` as the active configuration."""
    global _settings
    _settings = settings
