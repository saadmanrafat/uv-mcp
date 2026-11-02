"""Input validation, path confinement and secret redaction.

uv-mcp never invokes a shell: every uv call is an ``argv`` list handed straight
to the OS. The remaining risks are *argument injection* (a value such as
``--index-url=https://evil`` smuggled in where a package name was expected),
*path escape* (touching directories outside the ones the operator allowed),
and *secret leakage* (tokens echoed back into the model's context or logs).
This module contains the guards for all three.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from pathlib import Path

from fastmcp.exceptions import ToolError

from .config import Settings

_MAX_VALUE_LENGTH = 4096
_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

#: Global uv flags that relocate where uv operates or which config it reads.
#: They are rejected in ``extra_args`` when path confinement is enabled because
#: they would let a caller step outside the allowed roots.
_RELOCATING_FLAGS = ("--directory", "--project", "--config-file", "--cache-dir")


class ValidationError(ToolError):
    """Raised when a tool argument is rejected before uv is ever invoked."""


def _check_text(value: str, what: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{what} must be a string")
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ValidationError(f"{what} must not contain NUL or newline characters")
    if len(value) > _MAX_VALUE_LENGTH:
        raise ValidationError(f"{what} is too long ({len(value)} > {_MAX_VALUE_LENGTH})")
    return value


def safe_value(value: str, what: str) -> str:
    """Validate a free-form value that is passed as the *argument* of a flag.

    Values that follow a flag (``--python 3.12``) cannot be reinterpreted as a
    flag by uv's parser only if they do not start with ``-``, so we reject that.
    """
    value = _check_text(value, what).strip()
    if not value:
        raise ValidationError(f"{what} must not be empty")
    if value.startswith("-"):
        raise ValidationError(f"{what} must not start with '-' (got {value!r})")
    return value


def safe_values(values: Iterable[str] | None, what: str) -> list[str]:
    """Validate a list of values with :func:`safe_value`."""
    return [safe_value(v, what) for v in (values or [])]


def require_values(values: Sequence[str] | None, what: str) -> list[str]:
    """Like :func:`safe_values` but at least one value is required."""
    cleaned = safe_values(values, what)
    if not cleaned:
        raise ValidationError(f"At least one {what} is required")
    return cleaned


def safe_extra_args(extra_args: Sequence[str] | None, settings: Settings) -> list[str]:
    """Validate pass-through uv flags supplied by the caller.

    These are deliberately allowed to start with ``-`` (that is their purpose),
    but they still go through the same NUL/newline/length checks, and flags that
    relocate uv are refused when path confinement is on.
    """
    cleaned: list[str] = []
    for arg in extra_args or []:
        arg = _check_text(arg, "extra_args entry")
        if settings.allowed_roots:
            for flag in _RELOCATING_FLAGS:
                if arg == flag or arg.startswith(flag + "="):
                    raise ValidationError(
                        f"{flag} is not allowed in extra_args while UV_MCP_ALLOWED_ROOTS is set; "
                        "use the tool's project_path parameter instead"
                    )
        cleaned.append(arg)
    return cleaned


def safe_env(env: dict[str, str] | None) -> dict[str, str]:
    """Validate user supplied environment variables for ``uv run``."""
    cleaned: dict[str, str] = {}
    for key, value in (env or {}).items():
        if not _ENV_KEY_RE.match(key):
            raise ValidationError(f"Invalid environment variable name: {key!r}")
        if "\x00" in value:
            raise ValidationError(f"Environment variable {key} contains a NUL byte")
        cleaned[key] = value
    return cleaned


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def ensure_allowed(path: Path, settings: Settings) -> Path:
    """Raise unless ``path`` is inside one of the configured allowed roots."""
    if settings.allowed_roots and not any(_is_within(path, r) for r in settings.allowed_roots):
        roots = ", ".join(str(r) for r in settings.allowed_roots)
        raise ValidationError(
            f"Path {path} is outside the allowed roots ({roots}). Adjust UV_MCP_ALLOWED_ROOTS to permit it."
        )
    return path


def resolve_path(
    raw: str | None,
    settings: Settings,
    *,
    base: Path | None = None,
    what: str = "path",
    must_exist: bool = False,
    must_be_dir: bool = False,
) -> Path:
    """Resolve a user supplied path to an absolute, symlink-free path.

    Relative paths are interpreted against ``base`` (defaults to the workspace
    root) rather than the server process' working directory, so behaviour does
    not depend on how the MCP client launched the server.
    """
    anchor = base or settings.workspace_root
    if raw is None or not str(raw).strip():
        path = anchor
    else:
        text = _check_text(str(raw), what).strip()
        candidate = Path(text).expanduser()
        path = candidate if candidate.is_absolute() else anchor / candidate
    path = path.resolve()
    ensure_allowed(path, settings)
    if must_exist and not path.exists():
        raise ValidationError(f"{what.capitalize()} does not exist: {path}")
    if must_be_dir and path.exists() and not path.is_dir():
        raise ValidationError(f"{what.capitalize()} is not a directory: {path}")
    return path


def resolve_project_dir(project_path: str | None, settings: Settings) -> Path:
    """Resolve the directory a project-scoped uv command should run in."""
    return resolve_path(project_path, settings, what="project directory", must_exist=True, must_be_dir=True)


# --------------------------------------------------------------------------- #
# Redaction
# --------------------------------------------------------------------------- #

_URL_CREDENTIALS_RE = re.compile(r"(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*://)[^/\s:@]+(?::[^/\s@]*)?@")
_PYPI_TOKEN_RE = re.compile(r"pypi-[A-Za-z0-9_\-]{16,}")
_GITHUB_TOKEN_RE = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
#: Flags whose *following* argument is a secret. Only unambiguous long forms are
#: listed: short flags such as ``-t`` mean different things in different uv
#: subcommands (``uv pip install -t`` is ``--target``). uv-mcp's own tools never
#: put secrets on the command line in the first place (they go through the
#: environment or stdin); this is a backstop for ``extra_args``/``uv_command``.
SECRET_FLAGS = frozenset({"--token", "--password"})
REDACTED = "***"


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """Remove credentials from free-form text (command output, error messages)."""
    if not text:
        return text
    for secret in secrets:
        if secret and len(secret) >= 4:
            text = text.replace(secret, REDACTED)
    text = _URL_CREDENTIALS_RE.sub(lambda m: f"{m.group('scheme')}{REDACTED}@", text)
    text = _PYPI_TOKEN_RE.sub(REDACTED, text)
    text = _GITHUB_TOKEN_RE.sub(REDACTED, text)
    return text


def redact_argv(argv: Sequence[str], secret_flags: Iterable[str] = SECRET_FLAGS) -> list[str]:
    """Redact the values of secret-bearing flags and any URL credentials in argv."""
    flags = set(secret_flags)
    out: list[str] = []
    hide_next = False
    for arg in argv:
        if hide_next:
            out.append(REDACTED)
            hide_next = False
            continue
        name, sep, _ = arg.partition("=")
        if name in flags:
            if sep:
                out.append(f"{name}={REDACTED}")
            else:
                out.append(arg)
                hide_next = True
            continue
        out.append(redact(arg))
    return out
