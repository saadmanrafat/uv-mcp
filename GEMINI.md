# uv-mcp

MCP server exposing 45 typed tools for `uv` — the fast Python package manager.

## What it does

- Manages Python environments, dependencies, and project lifecycles via natural language
- Every `uv` command is a structured, type-safe MCP tool (Pydantic models, full return types)
- Self-healing: detects broken environments and auto-repairs them
- ANSI-free output — safe for JSON-RPC parsing

## Available tool categories

| Category | Tools |
|---|---|
| Project | `init`, `version`, `format`, `build`, `publish`, `lock` |
| Dependencies | `add`, `remove`, `sync`, `tree`, `list`, `show`, `outdated`, `freeze` |
| Python | `install`, `pin`, `find`, `upgrade`, `uninstall`, `dir` |
| Virtual Env | `create`, `seed`, `relocatable`, `system-site-packages` |
| Ephemeral | `run script`, `uvx proxy`, `temporary --with` |
| Diagnostics | `check`, `repair`, `self-heal`, `workspace manifest` |

## Usage

Call tools by name. Example prompts:
- *"Add requests and httpx to this project"*
- *"Check if the environment is broken and fix it"*
- *"Show the full dependency tree"*
- *"Build and publish to PyPI"*

## Security configuration

| Variable | Purpose |
|---|---|
| `UV_MCP_WORKSPACE_ROOT` | Absolute path of the allowed workspace. All `project_path` arguments are validated against this boundary; paths outside it are rejected. |
| `UV_MCP_ALLOWED_TOOLS` | Comma-separated list of permitted PyPI packages (e.g. `ruff,black,mypy`). When set, `uv_run_ephemeral_tool`, `uv_tool_install`, and `uv_tool_upgrade` reject unlisted packages. |

Both variables are optional. When unset, behaviour is unchanged.
