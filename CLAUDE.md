# Working on uv-mcp

uv-mcp is an MCP server (PyPI: `uv-mcp-server`, import: `uv_mcp`) that exposes the uv CLI as typed tools.

## Commands

```bash
uv sync                          # install dev environment
uv run pytest -m "not network"   # fast suite (needs uv on PATH, no internet)
uv run pytest                    # full suite (downloads from PyPI)
uv run ruff check src tests && uv run ruff format --check src tests
uv run uv-mcp-server --list-tools
uv run python scripts/gen_tool_reference.py   # regenerate docs/src/content/docs/reference/tools.md
```

## Layout

- `src/uv_mcp/server.py`: FastMCP app factory (`create_server`), agent `INSTRUCTIONS`, CLI `main`.
- `src/uv_mcp/registry.py`: `@uv_tool(...)` decorator. Declares MCP annotations and the toolset.
- `src/uv_mcp/tools/*.py`: one module per uv area (project, workspace, python, pip, env, uvtools, build, cache, auth, meta, diagnostics).
- `src/uv_mcp/coverage.py`: every uv command mapped to its tool (or `uv_info`, `uv_command`, or blocked). `tests/test_coverage.py` fails when the installed uv has a command missing from it.
- `src/uv_mcp/runner.py`: the only place a subprocess is started. No shell, scrubbed env, timeouts, redaction.
- `src/uv_mcp/security.py`: argument validation, path confinement, secret redaction.
- `src/uv_mcp/diagnostics.py`: `uv_project_info` / `uv_diagnose` / `uv_repair` logic.

## Rules for new tools

1. Name it after the uv command (`uv pip tree` becomes `uv_pip_tree`) and set honest annotations in `@uv_tool`.
2. Build argv with `Args`; validate every user value (`opt`, `many`, `positional` already do). Never use a shell.
3. Resolve paths with `security.resolve_path` / `project_dir` so confinement applies.
4. Secrets go through `env=` or `stdin_data=` plus `secrets=[...]`, never argv.
5. Keep parameter descriptions short; rarely used flags belong in `extra_args`.
6. Map it in `coverage.py`, add a test, then regenerate the tool reference.
