---
title: Architecture
description: Overview of the UV-MCP codebase and design.
---

# Architecture

This document provides a high-level overview of the UV-MCP codebase to help developers understand how it works and where to find things.

## Code Layout

The source code is located in `src/uv_mcp/`. Here is the structure:

```text
src/uv_mcp/
├── __init__.py
├── server.py         # Entry point and tool definitions
├── actions.py        # Implementation of tool logic
├── diagnostics.py    # Environment health check logic
├── project_tools.py  # Class-based tools (init, sync, export)
└── uv_utils.py       # Low-level wrappers for 'uv' CLI
```

## Component Summary

### 1. Server (`server.py`)
This is the heart of the application. It initializes the `FastMCP` server and defines the tools exposed to the AI.
-   **Responsibility**: Routing MCP requests to the appropriate internal functions.
-   **Key Libraries**: `fastmcp`.

### 2. Actions (`actions.py`)
Contains the core "business logic" for environment modifications.
-   **Functions**: `repair_environment_action`, `add_dependency_action`, etc.
-   **Responsibility**: Orchestrating checks and command executions to perform a user request.

### 3. Diagnostics (`diagnostics.py`)
Implements the read-only logic for analyzing the project state.
-   **Responsibility**: parsing `pyproject.toml`, checking `.venv`, verifying Python versions, and generating the JSON health report.

### 4. Utilities (`uv_utils.py`)
A wrapper around Python's `asyncio.subprocess`.
-   **Responsibility**: Executing `uv` shell commands safely, handling timeouts, and capturing stdout/stderr.

### 5. Project Tools (`project_tools.py`)
Encapsulates operations related to project lifecycle, like initialization and exporting.

## Data Flow

1.  **Request**: The generic MCP client sends a JSON-RPC request (e.g., `call_tool("add_dependency", {"package": "numpy"})`).
2.  **Server**: `server.py` receives the request and calls `add_dependency`.
3.  **Action**: `actions.py` validates the request (checks for `pyproject.toml`).
4.  **Execution**: `uv_utils.py` spawns a subprocess `uv add numpy`.
5.  **Response**: The subprocess output is captured, formatted as JSON, and returned to the client.

## Design Principles

-   **Safety**: We try to validate project paths before running commands.
-   **Transparency**: We prefer returning detailed JSON responses so the AI can interpret errors intelligently.
-   **Fallback**: Diagnostics try to handle missing files or partial setups gracefully.