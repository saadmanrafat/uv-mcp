# UV-MCP Context & Integration Guide

## Project Overview
`uv-mcp` is a Model Context Protocol (MCP) server that bridges modern Python environments with AI CLI agents. It provides reproducible Python environment management, diagnosis, and self-healing capabilities through the `uv` package manager.

## Supported AI Agents
- OpenCode
- Codex
- Gemini
- Claude

## Core Capabilities
The server exposes tools for:
- **Project Management**: `init`, `sync`, `lock`, `build`, `add`, `remove`
- **Python Version Management**: `uv python` operations
- **Dependency Inspection**: `uv pip` tools and analysis
- **Environment Diagnostics**: Health checks and self-healing workflows

## Key Configuration
- **Workspace Root**: Set via `UV_MCP_WORKSPACE_ROOT` environment variable
- **Output Format**: ANSI color and terminal sequences stripped for compatibility
- **Terminal Mode**: Dumb terminal mode enforced for consistent subprocess handling

## MCP Server Details
- **Command**: `uv run` with isolated Python environment
- **Port**: Configurable via agent integration
- **Environment**: Inherits `PATH`, `HOME/.local/bin`, `HOME/.cargo/bin`

## Quick Start for Agents
1. Initialize workspace: Call `uv_init_project`
2. Resolve dependencies: Call `uv_sync_project` or `uv_lock_project`
3. Inspect environment: Use `uv_pip_list` or `uv_pip_show`
4. Execute workflows: Chain tool calls for complex operations

## Installation & Client Configuration
For detailed setup instructions specific to your AI agent, visit the [Client Configuration Guide](https://saadman.dev/uv-mcp/guides/installation/#client-configuration).
