---
title: Contributing
description: Set up a development environment, run the tests and add a new tool.
---

## Set up

```bash
git clone https://github.com/saadmanrafat/uv-mcp.git
cd uv-mcp
uv sync
```

The repository ships `.mcp.json`, `.codex/config.toml` and `opencode.json` that run the server from your
checkout, so opening the repo in Claude Code, Codex or OpenCode lets you try your changes immediately.

## Check your work

```bash
uv run pytest -m "not network"     # fast; needs uv on PATH but no internet
uv run pytest                      # everything, including tests that download from PyPI
uv run ruff check src tests scripts
uv run ruff format src tests scripts
uv run uv-mcp-server --list-tools
```

The integration tests drive the server through a real MCP client against the real uv, in temporary
directories.

## Adding or changing a tool

1. Put it in the matching module under `src/uv_mcp/tools/`, named after the uv command
   (`uv pip tree` becomes `uv_pip_tree`).
2. Decorate it with `@uv_tool(title=..., toolset=..., read_only=..., destructive=..., idempotent=..., open_world=...)`.
   Be honest: clients rely on these annotations to decide when to ask the user.
3. Build the command with `Args`, which validates values, and resolve every path with `project_dir()` or
   `security.resolve_path()`. Never use a shell.
4. Pass secrets with `env=`/`stdin_data=` plus `secrets=[...]`, never on argv.
5. Keep descriptions short (they cost every user context) and leave rare flags to `extra_args`.
6. Add tests, then regenerate the reference:

```bash
uv run python scripts/gen_tool_reference.py
```

## Documentation

The site is [Starlight](https://starlight.astro.build/) under `docs/`:

```bash
cd docs
npm ci
npm run dev
python3 ../scripts/check_docs.py   # internal links and style checks, run from the repo root
```

## Releasing

1. Bump the version in `pyproject.toml` and `gemini-extension.json` and add a changelog entry.
2. Tag `vX.Y.Z` and push the tag. CI tests everything, publishes `uv-mcp-server` to PyPI with trusted
   publishing, and creates a GitHub release.
