"""uv-mcp server: wiring, agent instructions and the ``uv-mcp-server`` CLI."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import replace
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.tools import Tool

from . import __version__
from .config import ALL_TOOLSETS, Settings, get_settings, parse_paths, parse_toolsets, set_settings
from .registry import REGISTRY, ToolSpec

# Importing the modules registers their tools.
from .tools import auth, build, cache, diagnostics, env, meta, pip, project, python, uvtools  # noqa: F401

logger = logging.getLogger("uv_mcp")

INSTRUCTIONS = """\
uv-mcp gives you uv, the Python package, project and interpreter manager, as typed tools. Tool names mirror the
uv CLI (`uv add` -> uv_add, `uv pip list` -> uv_pip_list, `uvx` -> uv_tool_run).

Where commands run
- Project tools take project_path (absolute, or relative to the workspace root). Omit it to use the workspace
  root; uv then searches upward for pyproject.toml. Call uv_info if unsure what the workspace root is.

Choosing tools
- Projects (pyproject.toml): change dependencies with uv_add / uv_remove (never edit uv.lock, never use pip),
  install with uv_sync, run code, tests and scripts with uv_run, inspect with uv_tree and uv_project_info.
- New project: uv_init. Interpreters: uv_python_install / uv_python_pin / uv_python_list.
- uv_pip_* tools are for plain virtual environments and requirements.txt workflows, not uv projects.
- One-off CLI tools (ruff, black, httpie, cookiecutter): uv_tool_run, the equivalent of uvx.
- Broken environment, ImportError/ModuleNotFoundError, or unsure of state: uv_diagnose, then uv_repair.
- Anything without a dedicated tool: uv_command with the raw uv arguments.

Results
- Every command returns success, exit_code, stdout, stderr and, on failure, a hint with the likely fix.
  uv writes progress and most errors to stderr. Read hint before retrying.

Safety
- uv_publish is a dry run unless you pass dry_run=false; only do that when the user explicitly asked to publish.
- Never put tokens or passwords in extra_args; use the dedicated token/password parameters.
"""


def enabled_specs(settings: Settings) -> list[ToolSpec]:
    """Tools allowed by the toolset selection and read-only mode, in a stable order."""
    specs = []
    for spec in REGISTRY.values():
        if spec.toolset is not None and spec.toolset not in settings.toolsets:
            continue
        if settings.read_only and not spec.read_only and spec.name != "uv_command":
            continue
        if spec.name == "uv_command" and not settings.allow_raw_command:
            continue
        specs.append(spec)
    order = {name: i for i, name in enumerate((None, "diagnostics", *ALL_TOOLSETS))}
    return sorted(specs, key=lambda s: order[s.toolset])  # stable: keeps declaration order within a toolset


def compact_schema(schema: dict) -> dict:
    """Shrink a tool's input schema without changing what it accepts in practice.

    Pydantic renders ``x: str | None = None`` as ``{"anyOf": [{"type": "string"}, {"type": "null"}],
    "default": null}``. The field is already optional (absent from ``required``), so the null branch
    and default only cost the agent context. Arguments are still validated by pydantic, which keeps
    accepting an explicit null.
    """
    for prop in schema.get("properties", {}).values():
        branches = prop.get("anyOf")
        if prop.get("default", 0) is None and isinstance(branches, list) and len(branches) == 2:
            non_null = [b for b in branches if b != {"type": "null"}]
            if len(non_null) == 1:
                del prop["anyOf"]
                prop.pop("default")
                prop.update(non_null[0])
    return schema


def create_server(settings: Settings | None = None) -> FastMCP:
    """Build a FastMCP server for ``settings`` (defaults to the environment)."""
    if settings is not None:
        set_settings(settings)
    settings = get_settings()
    mcp = FastMCP(
        "uv-mcp",
        instructions=INSTRUCTIONS,
        version=__version__,
        website_url="https://saadman.dev/uv-mcp/",
    )
    for spec in enabled_specs(settings):
        tool = Tool.from_function(
            spec.fn,
            name=spec.name,
            title=spec.title,
            annotations=spec.annotations,
            tags={spec.toolset or "core"},
        )
        compact_schema(tool.parameters)
        mcp.add_tool(tool)
    return mcp


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="uv-mcp-server",
        description="MCP server exposing the uv Python package manager to AI agents (stdio transport).",
        epilog="Every option can also be set with the UV_MCP_* environment variable named in its help.",
    )
    parser.add_argument("--version", action="version", version=f"uv-mcp-server {__version__}")
    parser.add_argument(
        "--workspace", metavar="DIR", help="Default project directory [UV_MCP_WORKSPACE_ROOT; default: cwd]"
    )
    parser.add_argument(
        "--allowed-roots",
        metavar="DIRS",
        help=f"Confine all paths to these directories, separated by '{os.pathsep}' [UV_MCP_ALLOWED_ROOTS]",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=None,
        help="Only expose tools that change nothing [UV_MCP_READ_ONLY]",
    )
    parser.add_argument(
        "--toolsets",
        metavar="LIST",
        help=f"Comma-separated toolsets to enable: {', '.join(ALL_TOOLSETS)}, all [UV_MCP_TOOLSETS]",
    )
    parser.add_argument(
        "--timeout", type=float, metavar="SECONDS", help="Default uv command timeout [UV_MCP_TIMEOUT; default: 600]"
    )
    parser.add_argument(
        "--no-raw-command",
        action="store_true",
        help="Disable the uv_command escape hatch [UV_MCP_ALLOW_RAW_COMMAND=false]",
    )
    parser.add_argument("--list-tools", action="store_true", help="Print the enabled tools and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for ``uv-mcp-server`` / ``uv-mcp``."""
    logging.basicConfig(
        level=os.environ.get("UV_MCP_LOG_LEVEL", "WARNING").upper(),
        stream=sys.stderr,  # stdout carries the JSON-RPC stream
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args(argv)
    try:
        settings = Settings.from_env()
        overrides: dict = {}
        if args.workspace:
            overrides["workspace_root"] = Path(args.workspace).expanduser().resolve()
        if args.allowed_roots:
            overrides["allowed_roots"] = parse_paths(args.allowed_roots)
        if args.read_only:
            overrides["read_only"] = True
        if args.toolsets:
            overrides["toolsets"] = parse_toolsets(args.toolsets)
        if args.timeout:
            overrides["timeout"] = args.timeout
        if args.no_raw_command:
            overrides["allow_raw_command"] = False
        settings = replace(settings, **overrides)
    except ValueError as exc:
        print(f"uv-mcp-server: configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    if not settings.workspace_root.is_dir():
        print(f"uv-mcp-server: workspace root {settings.workspace_root} is not a directory", file=sys.stderr)
        raise SystemExit(2)
    if settings.allowed_roots and not any(
        settings.workspace_root == r or r in settings.workspace_root.parents for r in settings.allowed_roots
    ):
        print("uv-mcp-server: the workspace root must be inside UV_MCP_ALLOWED_ROOTS", file=sys.stderr)
        raise SystemExit(2)

    set_settings(settings)
    if args.list_tools:
        for spec in enabled_specs(settings):
            kind = "read-only" if spec.read_only else ("destructive" if spec.destructive else "writes")
            print(f"{spec.name:<22} {spec.toolset or 'core':<12} {kind}")
        return
    if settings.resolve_uv() is None:
        logger.warning("uv was not found on PATH; tools will report how to install it")
    create_server(settings).run(show_banner=False)


if __name__ == "__main__":
    main()
