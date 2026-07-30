---
title: Installation
description: Install and configure uv-mcp for Claude Code, OpenCode, Codex CLI, Gemini CLI, VS Code, and Cursor.
---

# Installation

## Prerequisites

- **uv** — [install guide](https://docs.astral.sh/uv/getting-started/installation/)
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Python 3.10+** (uv can manage this for you: `uv python install 3.12`)

---

## Get the server

**Option A — install as a global tool (recommended)**

```bash
uv tool install git+https://github.com/saadmanrafat/uv-mcp
```

**Option B — clone and run from source**

```bash
git clone https://github.com/saadmanrafat/uv-mcp.git
cd uv-mcp
uv sync
```

When running from source, replace every `uv run uv-mcp` below with:

```bash
uv --directory /path/to/uv-mcp run uv-mcp
```

---

## Client configuration

### Claude Code

Create `.mcp.json` at your project root:

```json
{
  "mcpServers": {
    "uv-mcp": {
      "command": "uv",
      "args": ["run", "uv-mcp"],
      "env": { "UV_COLOR": "never", "TERM": "dumb" }
    }
  }
}
```

Or add it globally with one command:

```bash
claude mcp add uv-mcp -- uv run uv-mcp
```

Claude Code reads `.mcp.json` automatically when you open the project.

---

### OpenCode

Create `opencode.json` at your project root:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "uv-mcp": {
      "type": "local",
      "command": ["uv", "run", "uv-mcp"],
      "enabled": true,
      "environment": { "UV_COLOR": "never", "TERM": "dumb" }
    }
  }
}
```

OpenCode merges this with your global `~/.config/opencode/opencode.json`, so this stays project-scoped without touching global settings.

---

### Codex CLI

Create `.codex/config.toml` at your project root:

```toml
[mcp_servers.uv-mcp]
command = "uv"
args    = ["run", "uv-mcp"]
enabled = true

[mcp_servers.uv-mcp.env]
UV_COLOR = "never"
TERM     = "dumb"
```

Then trust the project once so Codex loads the local config:

```bash
codex trust
```

Or register it globally:

```bash
codex mcp add uv-mcp -- uv run uv-mcp
```

---

### Gemini CLI

Install uv-mcp as a Gemini extension:

```bash
gemini extensions install https://github.com/saadmanrafat/uv-mcp
```

The bundled `gemini-extension.json` handles the rest. To update later:

```bash
gemini extensions update uv-mcp
```

---

### Claude Desktop

Edit the config file for your OS:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "uv-mcp": {
      "command": "uv",
      "args": ["run", "uv-mcp"],
      "env": { "UV_COLOR": "never", "TERM": "dumb" }
    }
  }
}
```

Restart Claude Desktop after saving.

---

### VS Code (GitHub Copilot)

**Step 1 — install `uv`** (skip if already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 2 — install uv-mcp as a global tool:**

```bash
uv tool install git+https://github.com/saadmanrafat/uv-mcp
```

**Step 3 — create `.vscode/mcp.json` in your project and open it:**

```bash
mkdir -p .vscode && echo '{"servers":{"uv-mcp":{"command":"uvx","args":["uv-mcp"],"env":{"UV_COLOR":"never","TERM":"dumb"}}}}' > .vscode/mcp.json && code .vscode/mcp.json
```

**Step 4 — start the server:**

1. Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Run **MCP: List Servers**
3. Click **Start** next to `uv-mcp`

VS Code picks up `.vscode/mcp.json` automatically whenever you open the folder. Steps 1 and 2 are one-time; only Step 3 is needed for each new project.

---

### Cursor

**Step 1 — install `uv`** (skip if already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 2 — install uv-mcp as a global tool:**

```bash
uv tool install git+https://github.com/saadmanrafat/uv-mcp
```

**Step 3 — create `.cursor/mcp.json` in your project and open it:**

```bash
mkdir -p .cursor && echo '{"mcpServers":{"uv-mcp":{"command":"uvx","args":["uv-mcp"],"env":{"UV_COLOR":"never","TERM":"dumb"}}}}' > .cursor/mcp.json && cursor .cursor/mcp.json
```

For a global install that applies to all projects:

```bash
mkdir -p ~/.cursor && echo '{"mcpServers":{"uv-mcp":{"command":"uvx","args":["uv-mcp"],"env":{"UV_COLOR":"never","TERM":"dumb"}}}}' > ~/.cursor/mcp.json && cursor ~/.cursor/mcp.json
```

**Step 4 — reload the window:**

`Cmd+Shift+P` / `Ctrl+Shift+P` → **Developer: Reload Window**

Cursor picks up the project-level file automatically after reload. Steps 1 and 2 are one-time; only Step 3 is needed for each new project.

---

In any connected client, send:

> *"Check if uv is installed."*

A response with the uv version confirms the server is running.

---

## Security configuration

Two optional environment variables scope what the server is allowed to do.

### `UV_MCP_WORKSPACE_ROOT`

Set this to the absolute path of your project root. When set, every `project_path`
argument is resolved and validated against this boundary — any path that resolves
outside the root is rejected before any subprocess is spawned.

```bash
export UV_MCP_WORKSPACE_ROOT="/home/user/projects/my-app"
```

Add it to the `env` block of your client config to make it permanent:

```json
"env": {
  "UV_COLOR": "never",
  "TERM": "dumb",
  "UV_MCP_WORKSPACE_ROOT": "/home/user/projects/my-app"
}
```

### `UV_MCP_ALLOWED_TOOLS`

Comma-separated list of PyPI package names that may be run or installed. When set,
`uv_run_ephemeral_tool`, `uv_tool_install`, and `uv_tool_upgrade` will reject any
package not in this list.

```bash
export UV_MCP_ALLOWED_TOOLS="ruff,black,mypy,pytest"
```

When not set, any valid PyPI package name is accepted (existing behaviour).
