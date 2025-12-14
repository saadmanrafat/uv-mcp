---
title: Usage Guide
description: detailed usage instructions for different clients
---

# Usage Guide

Once UV-MCP is installed, you can interact with it through your AI assistant using natural language.

## Clients

### Gemini CLI

If you installed UV-MCP as a Gemini extension, no further configuration is needed.

**Start a session:**
```bash
gemini chat
```

**Verify tools:**
Ask the model:
> "What tools do you have available?"

It should list `diagnose_environment`, `repair_environment`, and others.

### Claude Desktop

Ensure you have added the configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "uv-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/uv-mcp",
        "run",
        "uv-mcp"
      ]
    }
  }
}
```

Restart Claude Desktop completely for changes to take effect. Look for the plug icon to verify the server is connected.

### Claude Code (CLI)

You can run UV-MCP temporarily or permanently with Claude Code.

**Per-session:**
```bash
claude mcp add uv-mcp --scope user -- uv --directory /path/to/uv-mcp run uv-mcp
```

## Common Workflows

### Diagnosing Your Environment

If you suspect something is wrong with your Python setup, simply ask:

> "Diagnose my Python environment."
> "Why isn't my project working?"

The AI will use the `diagnose_environment` tool to check:
*   Is `uv` installed?
*   Does `pyproject.toml` exist?
*   Is the virtual environment active and valid?
*   Are there dependency conflicts?

### Repairing Issues

If issues are found, you can ask the AI to fix them:

> "Fix the environment issues."
> "Repair my project setup."

The `repair_environment` tool can:
*   Create a missing `.venv`.
*   Initialize a new project structure.
*   Sync dependencies from `uv.lock`.
*   Install the correct Python interpreter version.

### Managing Dependencies

You can add or remove packages without remembering the exact CLI commands.

**Adding packages:**
> "Add requests and pandas to the project."
> "Install pytest as a dev dependency."

**Removing packages:**
> "Remove numpy from dependencies."
> "Uninstall black."

## Example Session

**User**: "I want to start a new data science project here."

**Model**: "I'll check the current directory status."
*(Calls `diagnose_environment` -> finds empty directory)*
"The directory is empty. Shall I set up a new Python project for you?"

**User**: "Yes, please."

**Model**: *(Calls `repair_environment`)*
"I've initialized a new project with `pyproject.toml` and created a virtual environment."

**User**: "Add pandas and matplotlib."

**Model**: *(Calls `add_dependency` for pandas and matplotlib)*
"Added `pandas` and `matplotlib` to your project dependencies."