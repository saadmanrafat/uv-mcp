# Contributing to uv-mcp

Thanks for helping! The full guide, including how to add a tool, is at
https://saadman.dev/uv-mcp/guides/contributing/. The short version:

```bash
git clone https://github.com/saadmanrafat/uv-mcp
cd uv-mcp
uv sync

uv run pytest -m "not network"        # fast suite (needs uv on PATH)
uv run pytest                         # full suite (downloads from PyPI)
uv run ruff check src tests scripts
uv run ruff format src tests scripts
uv run python scripts/gen_tool_reference.py   # after changing any tool
```

To try the extension in Gemini CLI from your checkout: `gemini extensions link .`.
Claude Code, Codex and OpenCode pick up the server from `.mcp.json`, `.codex/config.toml` and
`opencode.json` when you open the repository.

Rules for tools:

- Name tools after the uv command (`uv pip tree` becomes `uv_pip_tree`) and set honest annotations in `@uv_tool`.
- Build argv with `Args` and resolve paths with `project_dir()` / `resolve_path()`. Never use a shell.
- Secrets go through `env=` or `stdin_data=` with `secrets=[...]`, never argv.
- Keep descriptions short; rarely used flags belong in `extra_args`.

Please report security issues privately through GitHub security advisories rather than public issues.
