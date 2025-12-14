---
title: Installation
description: How to install and configure UV-MCP
---

# Installation

## Prerequisites

1.  **Python 3.10** or higher.
2.  **`uv` package manager**.
    ```bash
    # Linux/macOS
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

## Installing the Extension

### Via Gemini CLI

The easiest way to use UV-MCP is with the Gemini CLI.

```bash
gemini extensions install https://github.com/saadmanrafat/uv-mcp
```

### Via Claude Code

If you use Claude Code, you can register the server globally:

```bash
claude mcp add uv-mcp --scope user -- uv --directory /path/to/uv-mcp run uv-mcp
```

*Replace `/path/to/uv-mcp` with the actual path to your cloned repository.*

### Manual Configuration (Claude Desktop)

Add the following to your `claude_desktop_config.json`:

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
