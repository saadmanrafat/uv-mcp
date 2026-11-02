"""Turn uv error output into a short, actionable next step for the agent."""

from __future__ import annotations

import re

# Ordered: the first matching rule wins. Each entry is (pattern, hint).
_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"No `pyproject\.toml` found|No `project` table found|does not appear to be a Python project", re.I),
        "No uv project here. Pass project_path pointing at the directory that contains "
        "pyproject.toml, or create one with uv_init.",
    ),
    (
        re.compile(
            r"The lockfile at `uv\.lock` needs to be updated|lockfile .* needs to be updated|`--locked` was provided",
            re.I,
        ),
        "uv.lock is out of date with pyproject.toml. Run uv_lock (or uv_sync without locked=true).",
    ),
    (
        re.compile(r"Unable to find lockfile|`uv\.lock` does not exist|lockfile does not exist", re.I),
        "There is no uv.lock yet. Run uv_lock to create it.",
    ),
    (
        re.compile(r"No solution found when resolving|unsatisfiable", re.I),
        "Dependency resolution failed. Read the explanation in stderr, then relax the "
        "conflicting version constraints or pick compatible versions.",
    ),
    (
        re.compile(
            r"not found in the package registry|Package `?[^`\s]+`? was not found|No matching distribution", re.I
        ),
        "A package name may be misspelled or not exist on the configured index.",
    ),
    (
        re.compile(
            r"No interpreter found|No Python at|Python interpreter .* not found|No download found for request", re.I
        ),
        "The requested Python is not available. Install it with uv_python_install, "
        "or check available versions with uv_python_list.",
    ),
    (
        re.compile(r"requires-python|Requires-Python", re.I),
        "A requires-python constraint is not satisfied. Pin a compatible interpreter with "
        "uv_python_pin or adjust requires-python in pyproject.toml.",
    ),
    (
        re.compile(r"No virtual environment found", re.I),
        "No virtual environment is active or present. Create one with uv_venv or uv_sync, "
        "or pass the python parameter to target a specific interpreter.",
    ),
    (
        re.compile(r"externally[- ]managed", re.I),
        "The target interpreter is externally managed (PEP 668). Use a project (uv_add/uv_sync) "
        "or a virtual environment (uv_venv) instead of installing into the system Python.",
    ),
    (
        re.compile(r"A virtual environment already exists", re.I),
        "A virtual environment already exists there. Pass clear=true to replace it.",
    ),
    (
        re.compile(
            r"Failed to (?:fetch|download)|error sending request|dns error|Connection refused|timed out|tcp connect error|certificate",
            re.I,
        ),
        "A network request failed. Check connectivity or proxy settings; certificate errors can "
        "often be fixed with UV_SYSTEM_CERTS=1. Retry with extra_args=['--offline'] to use only cached data.",
    ),
    (
        re.compile(r"Permission denied|Access is denied", re.I),
        "uv was denied access to a file. Check ownership/permissions of the project, the virtual "
        "environment and the uv cache (see uv_info for directories).",
    ),
    (
        re.compile(r"unrecognized subcommand|unexpected argument|unrecognized argument", re.I),
        "The installed uv does not recognise this command or flag; it may be too old. Check the "
        "version with uv_info and upgrade with uv_self_update if needed.",
    ),
]

_TIMEOUT_HINT = (
    "uv did not finish before the timeout. Increase timeout_seconds (where available) or "
    "UV_MCP_TIMEOUT, or make the operation smaller."
)
_MISSING_UV_HINT = (
    "uv is not installed or not on PATH. Install it (see uv_info for the official commands) or "
    "set UV_MCP_UV_PATH to the uv executable."
)


def hint_for(stderr: str, *, timed_out: bool = False, uv_missing: bool = False) -> str | None:
    """Return a one-line remedy for a failed uv invocation, if one is known."""
    if uv_missing:
        return _MISSING_UV_HINT
    if timed_out:
        return _TIMEOUT_HINT
    for pattern, hint in _RULES:
        if pattern.search(stderr or ""):
            return hint
    return None
