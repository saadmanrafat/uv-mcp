# uv-mcp

You have the `uv` MCP server, which exposes uv (the Python package, project and interpreter manager) as typed
tools. Prefer these tools over running `pip`, `python -m venv` or `uv` in a shell.

Tool names mirror the uv CLI: `uv add` is `uv_add`, `uv pip list` is `uv_pip_list`, `uvx` is `uv_tool_run`.

## Picking a tool

| Task | Tool |
|---|---|
| Orient yourself (uv version, workspace root, safety mode) | `uv_info` |
| Summarise a project | `uv_project_info` |
| New project / script | `uv_init` |
| Add or remove dependencies | `uv_add`, `uv_remove` |
| Install everything from the lockfile | `uv_sync` |
| Run code, tests, scripts | `uv_run` |
| Why is X installed? | `uv_tree` with `packages=["X"]`, `invert=true` |
| Workspaces (monorepos) | `uv_workspace_list`, `uv_workspace_dir`, `uv_workspace_metadata` |
| Python versions | `uv_python_list`, `uv_python_install`, `uv_python_pin`, `uv_python_find` |
| Plain virtualenv / requirements.txt | `uv_venv`, `uv_pip_install`, `uv_pip_compile`, `uv_pip_sync` |
| One-off CLI tool (ruff, black, httpie) | `uv_tool_run` |
| Vulnerability audit | `uv_audit` (project), `uv_tool_audit` (installed tools) |
| Broken environment or ImportError | `uv_diagnose`, then `uv_repair` |
| Anything else uv can do | `uv_command` |

## Conventions

- `project_path` is absolute or relative to the workspace root. Omit it to use the workspace root.
- Every command result has `success`, `exit_code`, `stdout`, `stderr` and, on failure, a `hint`. Read the hint first.
- Never edit `uv.lock` by hand. Change dependencies with `uv_add` / `uv_remove`.
- `uv_publish` is a dry run unless `dry_run=false`; only publish when the user explicitly asks.
