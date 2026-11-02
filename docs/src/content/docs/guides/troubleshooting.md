---
title: Troubleshooting
description: Fixes for the common problems when connecting and using uv-mcp.
---

Start with `uv_info`. It reports the uv version and path, the workspace root, the active settings and
notes about anything suspicious.

## The server does not start or shows as disconnected

- **`uvx` not found.** Desktop apps (Claude Desktop, some IDEs) do not inherit your shell's `PATH`. Use the
  absolute path to `uvx` as the command (`which uvx` / `where uvx`).
- **First start is slow.** The first launch downloads the server and possibly a Python. Raise the
  client's startup timeout (Codex: `startup_timeout_sec = 60`; Claude Code: `MCP_TIMEOUT=60000 claude`).
- **Run it by hand** to see errors: `uvx uv-mcp-server@latest --list-tools`.

## It installed something that is not uv-mcp

The PyPI package is `uv-mcp-server`. `uvx uv-mcp` runs an unrelated project that happens to own the
`uv-mcp` name.

## The tools are old or missing

`uvx` caches environments. `@latest` in the command makes it check for new releases; without it you may
keep running whatever version was cached first. Force a refresh with:

```bash
uvx --refresh uv-mcp-server@latest --version
```

## Commands run in the wrong directory

Check `workspace_root` in `uv_info`.

- If it is the uv-mcp source tree, your config uses `uv --directory /path/to/uv-mcp run ...`, which changes
  the working directory. Use `uvx uv-mcp-server@latest`, or `uv run --project /path/to/uv-mcp ...`.
- If it is `/` or your home directory, the client does not start servers in your project (typical of
  desktop apps). Set `UV_MCP_WORKSPACE_ROOT`, or have the agent pass `project_path`.

## uv is not found

`uv_info` returns `uv_installed: false` with install commands. Install uv, then restart the MCP server. If
uv lives somewhere unusual, set `UV_MCP_UV_PATH` to the executable.

## Certificate or network errors

Behind a corporate proxy or TLS-inspecting firewall, uv may need the system certificate store. MCP clients
usually start servers with a reduced environment, so set it in the server's `env` block even if it is in
your shell profile:

```json
"env": { "UV_SYSTEM_CERTS": "1", "HTTPS_PROXY": "http://proxy.example:3128" }
```

To work from the cache only, have the agent pass `extra_args: ["--offline"]`.

## Calls time out

Two limits apply: uv-mcp's (`UV_MCP_TIMEOUT`, default 600 s) and your client's per-call limit. Raise the
client's for long installs, for example `tool_timeout_sec = 600` in Codex. A result with `timed_out: true`
came from uv-mcp; a client-side error with no result came from the client.

## `uv_check` or `uv_audit` says the command is not recognised

Both use recent, experimental uv commands. Upgrade uv (`uv_self_update`, or your package manager) and check
the version in `uv_info`.

## Output is cut off

Each stream is limited to `UV_MCP_MAX_OUTPUT_CHARS` (default 30,000), keeping the beginning and the end;
`truncated: true` tells you this happened. Claude Code also caps tool output (`MAX_MCP_OUTPUT_TOKENS`).
Prefer narrower calls, such as `uv_tree` with `depth` or `packages`.

## `uv_pip_*` lists the wrong environment

Without `python`, uv targets the `.venv` in `project_path` or its parents. Pass `python` with the path of a
virtual environment or interpreter to target another one.
