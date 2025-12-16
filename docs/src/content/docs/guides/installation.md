---
title: Installation
description: Comprehensive guide for installing and configuring the UV-MCP server.
---

# Installation

This guide details the steps to install the UV-MCP server and configure it for use with MCP-compliant clients such as the Gemini CLI or Claude Desktop.

## Prerequisites

Ensure the following components are installed on your system:

1.  **uv Package Manager**:
    -   **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    -   **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
    -   Reference: [Official uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
2.  **Python Runtime**:
    -   Python 3.10 or higher is required.


## Client Configuration

To enable the server, you must register it in your client's configuration file.

### Gemini CLI

Locate your configuration file (typically `~/.gemini/settings.json`) and add the server definition:

```bash
gemini extensions install https://github.com/saadmanrafat/uv-mcp
```

```json
{
  "mcpServers": {
    "uv-mcp": {
      "command": "uv",
      "args": [
        "/path/to/tool",
        "run",
        "uv-mcp"
      ]
    }
  }
}
```

### Claude Desktop

Modify the configuration file located at:
-   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
-   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```bash
claude mcp add uv-mcp --scope user -- uv --directory /path/to/uv-mcp run uv-mcp
```

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

### Development Configuration

If running from source, point the command to your local directory:

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


## Server Installation

We recommend installing `uv-mcp` using `uv tool` to ensure it runs in an isolated environment while remaining globally accessible.

### Method 1: uv tool 

Execute the following command to install the server directly from the repository:

```bash
uv tool install git+https://github.com/saadmanrafat/uv-mcp
```

This command creates a managed environment for `uv-mcp` and exposes the binary.

### Method 2: pip / Local Development

If you are contributing to the project or prefer manual management:

```bash
git clone https://github.com/saadmanrafat/uv-mcp.git
cd uv-mcp
uv sync
```

## Verification

After configuration, restart your client. You can verify the connection by issuing a simple prompt:

> "Check if uv is installed."

A successful response containing the `uv` version indicates the server is active and communicating.
