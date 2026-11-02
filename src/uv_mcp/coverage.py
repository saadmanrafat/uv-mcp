"""How uv-mcp covers every uv command.

This table is the single source of truth for "uv-mcp can do everything uv can". Each uv command path maps to:

* the name of the dedicated tool that runs it, or
* ``"uv_info"`` for read-only facts that tool aggregates (directories, uv's version), or
* ``"uv_command"`` for commands that are only useful through the raw escape hatch, or
* a :class:`Blocked` entry for commands deliberately refused, with the reason.

``tests/test_coverage.py`` reads the installed uv's ``--help`` and fails if uv has a command missing from this table,
so new uv features are flagged as soon as CI runs against a newer uv.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Blocked:
    reason: str


Coverage = str | Blocked

COVERAGE: dict[tuple[str, ...], Coverage] = {
    # Projects
    ("init",): "uv_init",
    ("add",): "uv_add",
    ("remove",): "uv_remove",
    ("sync",): "uv_sync",
    ("lock",): "uv_lock",
    ("run",): "uv_run",
    ("tree",): "uv_tree",
    ("export",): "uv_export",
    ("version",): "uv_version",
    ("format",): "uv_format",
    ("check",): "uv_check",
    ("audit",): "uv_audit",
    ("workspace", "list"): "uv_workspace_list",
    ("workspace", "dir"): "uv_workspace_dir",
    ("workspace", "metadata"): "uv_workspace_metadata",
    # Python interpreters
    ("python", "list"): "uv_python_list",
    ("python", "install"): "uv_python_install",
    ("python", "upgrade"): "uv_python_upgrade",
    ("python", "uninstall"): "uv_python_uninstall",
    ("python", "find"): "uv_python_find",
    ("python", "pin"): "uv_python_pin",
    ("python", "dir"): "uv_info",
    ("python", "update-shell"): Blocked("edits the user's shell profile"),
    # pip interface
    ("pip", "install"): "uv_pip_install",
    ("pip", "uninstall"): "uv_pip_uninstall",
    ("pip", "list"): "uv_pip_list",
    ("pip", "show"): "uv_pip_show",
    ("pip", "freeze"): "uv_pip_freeze",
    ("pip", "tree"): "uv_pip_tree",
    ("pip", "check"): "uv_pip_check",
    ("pip", "compile"): "uv_pip_compile",
    ("pip", "sync"): "uv_pip_sync",
    # Environments
    ("venv",): "uv_venv",
    # Tools
    ("tool", "run"): "uv_tool_run",
    ("tool", "install"): "uv_tool_install",
    ("tool", "upgrade"): "uv_tool_upgrade",
    ("tool", "uninstall"): "uv_tool_uninstall",
    ("tool", "list"): "uv_tool_list",
    ("tool", "audit"): "uv_tool_audit",
    ("tool", "dir"): "uv_info",
    ("tool", "update-shell"): Blocked("edits the user's shell profile"),
    # Packaging
    ("build",): "uv_build",
    ("publish",): "uv_publish",
    # Cache
    ("cache", "clean"): "uv_cache_clean",
    ("cache", "prune"): "uv_cache_prune",
    ("cache", "size"): "uv_cache_size",
    ("cache", "dir"): "uv_info",
    # Authentication
    ("auth", "login"): "uv_auth_login",
    ("auth", "logout"): "uv_auth_logout",
    ("auth", "dir"): "uv_info",
    ("auth", "token"): Blocked("returns stored secrets into the conversation"),
    # uv itself
    ("self", "update"): "uv_self_update",
    ("self", "version"): "uv_info",
    ("help",): "uv_command",
}

BLOCKED: dict[tuple[str, ...], str] = {path: c.reason for path, c in COVERAGE.items() if isinstance(c, Blocked)}
