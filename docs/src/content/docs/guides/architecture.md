---
title: Architecture
description: Technical deep dive into the UV-MCP system design and implementation.
---

# Architecture

This document provides a technical overview of the UV-MCP codebase, intended for developers who wish to understand the internal mechanisms or contribute to the project.

## Project Structure

The codebase follows a modular design within the `src/uv_mcp/` directory, separating protocol handling, business logic, and low-level system interactions.

```text
src/uv_mcp/
├── __init__.py
├── server.py         # MCP Protocol Server & Entry Point
├── actions.py        # Imperative Action Handlers (Write operations)
├── diagnostics.py    # State Analysis & Health Checks (Read operations)
├── tools.py          # Project Lifecycle & Utility Tools
└── utils.py          # Subprocess abstraction & uv CLI wrappers
```

## System Components

### 1. The MCP Server (`server.py`)
The server module acts as the interface layer. It utilizes the `fastmcp` library to define the capabilities exposed to the client.
-   **Role**: Router and Protocol Handler.
-   **Function**: Maps incoming JSON-RPC requests (e.g., "call_tool") to internal Python functions.

### 2. Action Orchestrator (`actions.py`)
This module contains the imperative logic for modifying the system state.
-   **Role**: Executor.
-   **Key Functions**: `repair_environment_action`, `add_dependency_action`.
-   **Responsibility**: Validates preconditions (e.g., existence of `pyproject.toml`) before invoking `uv` commands.

### 3. Diagnostic Engine (`diagnostics.py`)
A read-only subsystem responsible for analyzing project health.
-   **Role**: Analyst.
-   **Key Functions**: `diagnose_environment`.
-   **Responsibility**: Parses metadata, inspects the virtual environment, and aggregates health metrics into a structured JSON report.

### 4. Process Abstraction (`utils.py`)
A safety layer around `asyncio.subprocess`.
-   **Role**: HAL (Hardware/System Abstraction).
-   **Responsibility**: Executes shell commands, handles timeouts, captures standard output/error streams, and ensures proper error propagation.

## Request Lifecycle

The flow of a typical user request (e.g., "Add numpy") is as follows:

1.  **Ingest**: The AI client transmits a JSON-RPC request: `call_tool("add_dependency", {"package": "numpy"})`.
2.  **Routing**: `server.py` receives the payload and dispatches it to the registered handler in `actions.py`.
3.  **Validation**: The handler verifies that the current working directory is a valid Python project.
4.  **Execution**: `utils.py` spawns a subprocess: `uv add numpy`.
5.  **Output**: The subprocess's `stdout` and `stderr` are captured and parsed.
6.  **Response**: A JSON response indicating success or failure is returned to the client.

## Design Principles

-   **Statelessness**: The server maintains minimal state between requests, relying on the filesystem as the source of truth.
-   **Idempotency**: Where possible, tools are designed to be idempotent (e.g., diagnosing an already healthy environment is a no-op).
-   **Fail-Safe**: Subprocesses are isolated; a failure in `uv` execution is caught and returned as a structured error, preventing a server crash.
