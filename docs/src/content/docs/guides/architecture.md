---
title: Architecture
description: How uv-mcp is put together, for contributors and the curious.
---

uv-mcp is a thin, careful layer between an MCP client and the real `uv` executable. It does not
reimplement any packaging logic: every operation is a uv invocation, so behaviour always matches the uv
the user has installed.

## Layout

```text
src/uv_mcp/
├── server.py        create_server(), agent INSTRUCTIONS, the uv-mcp-server CLI
├── config.py        Settings (env vars and flags), workspace-root resolution
├── registry.py      @uv_tool: declares a tool's toolset and MCP annotations
├── runner.py        run_uv(): the only place a subprocess is started
├── security.py      argument validation, path confinement, secret redaction
├── hints.py         uv error text to a one-line suggested fix
├── parsing.py       uv output (JSON and text) to typed models
├── models.py        Pydantic result models (the tools' output schemas)
├── diagnostics.py   project introspection, health checks, repair planning
└── tools/
    ├── project.py   init, add, remove, sync, lock, run, tree, export, version, format, check, audit
    ├── python.py    python list, install, upgrade, uninstall, find, pin
    ├── pip.py       pip install, uninstall, list, show, freeze, tree, check, compile, sync
    ├── env.py       venv
    ├── uvtools.py   tool run (uvx), install, upgrade, uninstall, list
    ├── build.py     build, publish
    ├── cache.py     cache clean, prune, size
    ├── auth.py      auth login, logout
    ├── meta.py      uv_info, self update, uv_command
    └── diagnostics.py  uv_project_info, uv_diagnose, uv_repair
```

## A request, step by step

1. **Registration.** At start-up `create_server()` takes every `@uv_tool` from the registry, drops those
   excluded by the toolset selection or read-only mode, builds the input schema from the function's type
   hints, compacts it, and registers it with [FastMCP](https://gofastmcp.com/).
2. **Validation.** FastMCP validates the JSON arguments against the schema. Each tool then resolves paths
   with `security.resolve_path` (relative to the workspace root, symlinks resolved, confinement checked) and
   builds argv with the `Args` helper, which rejects option-like values. Invalid input becomes an MCP tool
   error and uv never runs.
3. **Execution.** `runner.run_uv()` starts uv with no shell, a scrubbed environment (no inherited
   `VIRTUAL_ENV`, no colours or progress bars), closed stdin and its own process group. Mutating calls
   take a per-directory lock. A heartbeat sends MCP progress notifications while uv runs. On timeout the
   process group is killed.
4. **Result.** Output is decoded, redacted and truncated; a hint is attached on failure; parsers turn JSON
   or text output into typed fields. The tool returns a Pydantic model, which FastMCP sends as structured
   content that matches the advertised output schema.

## Design decisions

- **Mirror the CLI.** Tool and parameter names follow uv's, because models already know uv. Only commonly
  used flags get parameters; `extra_args` covers the rest, which keeps schemas small.
- **Results, not exceptions, for uv failures.** A failed `uv sync` is a normal outcome the agent must
  reason about, so it returns `success: false` with stderr and a hint. Exceptions (MCP tool errors) are
  reserved for invalid input and policy refusals.
- **Annotations are part of the contract.** `readOnlyHint` drives read-only mode, and clients use the
  annotations to decide when to ask the user. A test checks that every read-only-mode tool is annotated
  read-only.
- **The filesystem is the state.** The server keeps no state between calls apart from locks; restarting it
  loses nothing.
- **Generated reference.** `docs/.../reference/tools.md` is generated from the live schemas by
  `scripts/gen_tool_reference.py`, and CI fails if it is stale.
