---
title: Architecture
description: Overview of the UV-MCP codebase architecture
---

# Architecture

This document provides a high-level overview of the UV-MCP codebase to help contributors understand how the project is structured.

## Directory Structure

```
uv-mcp/
├── src/
│   └── uv_mcp/
│       ├── __init__.py
│       ├── server.py          # Entry point and tool definitions
│       ├── actions.py         # Implementation of tool logic
│       ├── diagnostics.py     # Logic for environment health checks
│       └── uv_utils.py        # Low-level wrappers for uv CLI commands
├── tests/                     # Pytest test suite
├── docs/                      # Astro Starlight documentation
├── gemini-extension.json      # Manifest for Gemini CLI extension
├── pyproject.toml             # Project metadata and dependencies
└── Dockerfile                 # Container definition
```

## Component Summary

### `server.py`
The main entry point for the application. It initializes the `FastMCP` server and defines the `@mcp.tool()` decorators. It handles the JSON serialization of responses but delegates the actual business logic to `actions.py`.

### `actions.py`
Contains the "business logic" for each tool. It orchestrates calls to `uv_utils.py` and formats the results into structured dictionaries. For example, `repair_environment_action` decides *which* repairs to run based on the current state.

### `diagnostics.py`
Dedicated to the `diagnose_environment` tool. It performs read-only analysis of the project directory. It checks file existence, parses `pyproject.toml`, and runs `uv pip check` to find dependency conflicts.

### `uv_utils.py`
The lowest layer of the stack. It uses `asyncio.create_subprocess_exec` to run the actual `uv` binary. It handles `stdout/stderr` capture, timeouts, and basic error handling. It has no knowledge of MCP; it just knows how to run CLI commands.

## Design Principles

1.  **Statelessness**: The server does not maintain persistent state between tool calls. Each call analyzes the directory fresh.
2.  **Safety**: Destructive actions (like `uv init` or `uv remove`) are always explicit user actions via tools.
3.  **Idempotency**: Repair actions attempt to be idempotent. Running `repair_environment` twice should not break a healthy environment.
4.  **Async/Await**: All I/O operations (file system, subprocesses) are asynchronous to ensure the server remains responsive.
