---
title: MCP and Extensions
description: Understanding the Model Context Protocol and how UV-MCP fits in.
---

# MCP and Extensions

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard that enables AI models to interact with external tools and data safely. Instead of hardcoding integrations, AI assistants (like Claude or Gemini) use MCP to "discover" available tools and call them when needed.

UV-MCP is an **MCP Server**. It sits on your local machine and exposes specific capabilities (tools) to the AI.

## What is uv?

**uv** is an extremely fast Python package and project manager, written in Rust. It is designed to be a drop-in replacement for `pip`, `pip-tools`, and `virtualenv`.

- **Speed**: It is 10-100x faster than pip.
- **Reliability**: Uses a universal lockfile (`uv.lock`) to ensure reproducible builds.
- **Convenience**: Manages Python versions, virtual environments, and dependencies in one tool.

## How they work together

UV-MCP wraps the `uv` command-line interface into a structured API that the AI can understand.

1.  **User Prompt**: "Add requests to my project."
2.  **AI Decision**: The AI sees the `add_dependency` tool and decides to call it.
3.  **MCP Request**: The AI sends a structured request to the UV-MCP server.
4.  **Execution**: UV-MCP runs `uv add requests` on your machine.
5.  **Response**: UV-MCP captures the output (success/failure) and sends it back to the AI.
6.  **User Response**: The AI confirms to you that the package was added.
