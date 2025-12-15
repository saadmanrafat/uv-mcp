---
title: Installation
description: How to install and configure UV-MCP.
---

# Installation

This guide will help you set up UV-MCP on your system and configure it for use with your MCP client (like Claude Desktop or Gemini CLI).

## Prerequisites

Before installing UV-MCP, ensure you have the following:

1.  **uv**: The `uv` package manager must be installed.
    -   macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    -   Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
    -   [Official Installation Docs](https://docs.astral.sh/uv/getting-started/installation/)
2.  **Python**: Python 3.10 or higher.

## Installing the Server

You can install `uv-mcp` directly from the repository or via `pip`. Since it's a tool intended to be run by an agent, we recommend installing it using `uv tool`.

### Option 1: Using `uv tool` (Recommended)

```bash
uv tool install git+https://github.com/saadmanrafat/uv-mcp
```

This installs `uv-mcp` in an isolated environment and makes the `uv-mcp` command available.

### Option 2: Using `pip`

```bash
pip install uv-mcp
```

*(Note: Adjust command if installing from a specific source or local path)*

## Configuration

To use UV-MCP with an AI client, you need to add it to your MCP configuration file.

### Finding your `mcp-config.json`

-   **Claude Desktop App**: usually located at `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows).
-   **Gemini CLI**: typically uses a configuration file passed via flags or located in `~/.gemini/config.json`.

### Configuration Snippet

Add the following to your `mcpServers` object:

```json
{
  "mcpServers": {
    "uv-mcp": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "uv-mcp"
      ]
    }
  }
}
```

If you are developing locally or running from source:

```json
{
  "mcpServers": {
    "uv-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/uv-mcp",
        "run",
        "uv-mcp"
      ]
    }
  }
}
```

## Verifying Installation

Once configured, restart your AI client. You should be able to ask the agent:

> "Check if uv is installed"

If the agent responds with the version of `uv`, the connection is successful.