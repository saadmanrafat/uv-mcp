---
title: Introduction
description: What uv-mcp is, why agents work better with it than with a shell, and how it is organised.
---

**uv-mcp** is a [Model Context Protocol](https://modelcontextprotocol.io/) server that gives AI coding
agents the whole of [uv](https://docs.astral.sh/uv/): projects and lockfiles, dependencies, Python
versions, virtual environments, `uvx` tools, building and publishing, the pip interface, the cache, and
uv's newer type-checking and vulnerability-audit commands. It works with Claude Code, Codex CLI, Gemini
CLI, Claude Desktop, Cursor, VS Code, OpenCode and any other MCP client.

## Why not just let the agent run `uv` in a shell?

Agents can run shell commands, but a dedicated server makes them faster and safer:

- **Typed tools with obvious names.** `uv_add(packages=["httpx"], dev=true)` mirrors `uv add --dev httpx`,
  so models that know uv know the tools. Parameters are validated before uv runs.
- **Structured results.** Every call returns `success`, `exit_code`, `stdout`, `stderr` and, on failure, a
  `hint` such as *"uv.lock is out of date with pyproject.toml. Run uv_lock."* Listing tools return parsed
  data (packages, Python installations, tools) instead of tables to scrape.
- **Diagnosis and repair.** `uv_diagnose` checks the interpreter, lockfile, `.venv` and installed packages
  and says what to call to fix each problem; `uv_repair` does it.
- **Safety the client can see.** Tools carry read-only/destructive annotations, so clients can ask before
  risky calls. There is a read-only mode, path confinement, secret redaction, and no shell anywhere. See
  [Security](/uv-mcp/guides/security/).
- **No surprises about where it runs.** Commands run in your project, never in the server's own
  environment, and `uv_info` tells the agent exactly which directory and uv version it is using.

## What is included

51 tools, grouped into toolsets that can be enabled individually:

| Area | Tools |
|---|---|
| Orientation | `uv_info`, `uv_project_info`, `uv_help` |
| Projects | `uv_init`, `uv_add`, `uv_remove`, `uv_sync`, `uv_lock`, `uv_run`, `uv_tree`, `uv_export`, `uv_version`, `uv_format`, `uv_check`, `uv_audit`, `uv_workspace_list`, `uv_workspace_dir`, `uv_workspace_metadata` |
| Python versions | `uv_python_list`, `uv_python_install`, `uv_python_upgrade`, `uv_python_uninstall`, `uv_python_find`, `uv_python_pin` |
| pip interface | `uv_pip_install`, `uv_pip_uninstall`, `uv_pip_list`, `uv_pip_show`, `uv_pip_freeze`, `uv_pip_tree`, `uv_pip_check`, `uv_pip_compile`, `uv_pip_sync` |
| Virtual environments | `uv_venv` |
| Tools (`uvx`) | `uv_tool_run`, `uv_tool_install`, `uv_tool_upgrade`, `uv_tool_uninstall`, `uv_tool_list`, `uv_tool_audit` |
| Packaging | `uv_build`, `uv_publish` |
| Cache, auth, uv itself | `uv_cache_clean`, `uv_cache_prune`, `uv_cache_size`, `uv_auth_login`, `uv_auth_logout`, `uv_self_update` |
| Health | `uv_diagnose`, `uv_repair` |
| Anything else | `uv_command` |

Every uv option is available too. Common options are tool parameters, and resolution and index options are
grouped in a `resolver` object. Every other option goes in `extra_args`, which is checked against the installed
uv before anything runs, with suggestions for typos. `uv_help` shows any command's options and how to pass each
one. The
[coverage table](/uv-mcp/reference/tools/#uv-command-coverage) maps every uv command to its tool, and a test
fails if a new uv release adds a command uv-mcp does not cover.

## Next steps

- [Installation](/uv-mcp/guides/installation/): one command per client.
- [Usage](/uv-mcp/guides/usage/): common workflows and what the agent calls.
- [Tool reference](/uv-mcp/reference/tools/): every tool and parameter.
