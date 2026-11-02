---
title: Configuration
description: Environment variables and flags for workspace root, read-only mode, toolsets, path confinement, timeouts and output limits.
---

uv-mcp works with no configuration. Every setting is available both as an environment variable (set it in
your MCP client's `env` block) and as a command-line flag (append it to `args`). Flags take precedence.

| Environment variable | Flag | Default | Effect |
|---|---|---|---|
| `UV_MCP_WORKSPACE_ROOT` | `--workspace DIR` | see below | Default directory for project tools; relative `project_path` values are resolved against it. |
| `UV_MCP_READ_ONLY` | `--read-only` | `false` | Register only tools that change nothing. |
| `UV_MCP_TOOLSETS` | `--toolsets LIST` | `all` | Comma-separated toolsets to register. |
| `UV_MCP_ALLOWED_ROOTS` | `--allowed-roots DIRS` | unset | Refuse any path outside these directories (`:`-separated, `;` on Windows). |
| `UV_MCP_TIMEOUT` | `--timeout SECONDS` | `600` | Default limit for one uv command; the process tree is killed when it expires. |
| `UV_MCP_ALLOW_RAW_COMMAND` | `--no-raw-command` | `true` | Set to `false` to remove the `uv_command` escape hatch. |
| `UV_MCP_MAX_OUTPUT_CHARS` | | `30000` | Characters kept per output stream; the middle of longer output is elided. |
| `UV_MCP_UV_PATH` | | `uv` on `PATH` | Absolute path to the uv executable. |
| `UV_MCP_LOG_LEVEL` | | `WARNING` | Server log level. Logs go to stderr, never stdout. |

Run `uvx uv-mcp-server --help` for the same list.

uv's own environment variables (`UV_INDEX_URL`, `UV_PYTHON_PREFERENCE`, `UV_SYSTEM_CERTS`, `UV_CACHE_DIR`...)
and your `uv.toml` / `[tool.uv]` settings are honoured as usual, because the server runs the real uv.

## Workspace root

When a tool is called without `project_path`, it runs in the workspace root, and uv searches upward from
there for `pyproject.toml`, exactly as it does in a terminal. The root is chosen in this order:

1. `UV_MCP_WORKSPACE_ROOT` (or `--workspace`).
2. `CLAUDE_PROJECT_DIR`, which Claude Code sets for the MCP servers it starts.
3. The working directory the client started the server in.

Empty values, values that still contain an unexpanded `${...}` placeholder, and paths that do not exist
are skipped.

Agents can always override it per call with `project_path`, either absolute or relative to the root.
`uv_info` reports the root in effect.

## Read-only mode

```json
"args": ["uv-mcp-server@latest", "--read-only"]
```

Only tools annotated read-only are registered: `uv_info`, `uv_help`, `uv_project_info`, `uv_diagnose`, `uv_tree`,
`uv_export` (to stdout only), `uv_audit`, `uv_python_list`, `uv_python_find`, `uv_pip_list`, `uv_pip_show`,
`uv_pip_freeze`, `uv_pip_tree`, `uv_pip_check`, `uv_tool_list`, `uv_tool_audit`, `uv_workspace_list`,
`uv_workspace_dir`, `uv_workspace_metadata` and `uv_cache_size`. Commands that would
otherwise refresh `uv.lock` are run with `--frozen`, and `uv_command` only accepts inspection commands.

Use it for review or CI agents that should look at environments but never change them.

## Toolsets

Fewer tools means less context spent on tool definitions. Pick only what an agent needs:

| Toolset | Tools |
|---|---|
| `project` | `uv_init`, `uv_add`, `uv_remove`, `uv_sync`, `uv_lock`, `uv_run`, `uv_tree`, `uv_export`, `uv_version`, `uv_format`, `uv_check`, `uv_audit`, `uv_workspace_list`, `uv_workspace_dir`, `uv_workspace_metadata` |
| `python` | `uv_python_list`, `uv_python_install`, `uv_python_upgrade`, `uv_python_uninstall`, `uv_python_find`, `uv_python_pin` |
| `pip` | `uv_pip_install`, `uv_pip_uninstall`, `uv_pip_list`, `uv_pip_show`, `uv_pip_freeze`, `uv_pip_tree`, `uv_pip_check`, `uv_pip_compile`, `uv_pip_sync` |
| `venv` | `uv_venv` |
| `tool` | `uv_tool_run`, `uv_tool_install`, `uv_tool_upgrade`, `uv_tool_uninstall`, `uv_tool_list`, `uv_tool_audit` |
| `build` | `uv_build`, `uv_publish` |
| `cache` | `uv_cache_clean`, `uv_cache_prune`, `uv_cache_size` |
| `auth` | `uv_auth_login`, `uv_auth_logout` |
| `self` | `uv_self_update` |
| `diagnostics` | `uv_project_info`, `uv_diagnose`, `uv_repair` |

`uv_info`, `uv_help` and `uv_command` are always registered. For example, a coding agent that only works inside
projects:

```json
"env": { "UV_MCP_TOOLSETS": "project,python,diagnostics" }
```

## Confining paths

```json
"env": { "UV_MCP_ALLOWED_ROOTS": "/home/me/code" }
```

With allowed roots set, every `project_path`, output file, requirements file and virtual environment path
must resolve (after following symlinks) inside one of them, and the uv flags that relocate uv
(`--directory`, `--project`, `--config-file`, `--cache-dir`) are refused in `extra_args`. The workspace root
must itself be inside an allowed root or the server will not start.

Machine-wide operations such as installing Python versions or CLI tools are not path-scoped; disable their
toolsets if you want to forbid them.

## Timeouts

A uv command that runs longer than `UV_MCP_TIMEOUT` is killed together with any processes it started, and
the result reports `timed_out: true`. `uv_run`, `uv_tool_run` and `uv_command` also accept
`timeout_seconds` for one call.

Your client has its own limit per tool call, and whichever is shorter wins. Codex in particular needs
`tool_timeout_sec` raised for long installs; see [Installation](/uv-mcp/guides/installation/#codex-cli).
While a command runs, uv-mcp sends MCP progress notifications every few seconds to clients that request
them.
