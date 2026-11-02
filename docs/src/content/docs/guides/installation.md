---
title: Installation
description: Install uv-mcp and connect it to Claude Code, Codex CLI, Gemini CLI, Claude Desktop, Cursor, VS Code, OpenCode or any MCP client.
---

uv-mcp is a local stdio MCP server. Your MCP client starts it on demand; there is nothing to keep running.

## Prerequisites

The only requirement is **uv** itself. uv-mcp runs with `uvx`, which downloads the server and a suitable
Python the first time, so you do not need to install Python or clone anything.

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Other methods (Homebrew, pipx, WinGet) are in the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).
Check it works with `uv --version`.

:::caution[Use the right package name]
The PyPI package is **`uv-mcp-server`**. The name `uv-mcp` on PyPI belongs to an unrelated project, so
`uvx uv-mcp` would run someone else's code.
:::

## The server command

Every client below runs the same command:

```bash
uvx uv-mcp-server@latest
```

`@latest` makes uvx check for a new release each time the client starts the server. To pin a version
for reproducibility, use `uv-mcp-server@2.0.0` instead.

You can run it in a terminal to confirm it starts. It waits silently for JSON-RPC on stdin; press `Ctrl+C`
to stop. To see what it exposes without starting it:

```bash
uvx uv-mcp-server@latest --list-tools
```

:::note[Which directory does it work in?]
Project tools default to the **workspace root**: `UV_MCP_WORKSPACE_ROOT` if set, otherwise
`CLAUDE_PROJECT_DIR` (Claude Code sets it), otherwise the directory the client launched the server in.
Terminal clients launch servers in your project, so this normally just works. Agents can always pass
`project_path` explicitly. See [Configuration](/uv-mcp/guides/configuration/).
:::

## Claude Code

Add it for all your projects:

```bash
claude mcp add --scope user --transport stdio uv -- uvx uv-mcp-server@latest
```

Or share it with your team by committing a `.mcp.json` at the project root
(`claude mcp add --scope project ...` writes the same file):

```json
{
  "mcpServers": {
    "uv": {
      "command": "uvx",
      "args": ["uv-mcp-server@latest"]
    }
  }
}
```

Run `claude mcp list` or `/mcp` inside Claude Code to check that it is connected. Tools appear as
`mcp__uv__uv_add`, `mcp__uv__uv_sync`, and so on, which you can use in permission rules.

## Codex CLI

```bash
codex mcp add uv -- uvx uv-mcp-server@latest
```

Then raise the per-call timeout so long installs are not cut off. Edit `~/.codex/config.toml`:

```toml
[mcp_servers.uv]
command = "uvx"
args = ["uv-mcp-server@latest"]
startup_timeout_sec = 60   # the first start downloads the server
tool_timeout_sec = 600     # syncs and Python installs can take minutes
```

The same table also works in a project-level `.codex/config.toml`, which Codex loads for trusted projects.

## Gemini CLI

Install the extension. It bundles the server config and a `GEMINI.md` context file that teaches Gemini
when to use each tool:

```bash
gemini extensions install https://github.com/saadmanrafat/uv-mcp
```

Update later with `gemini extensions update uv-mcp`. The extension runs the server from its checkout with
`uv run --project ${extensionPath}`, and points it at your workspace with `${workspacePath}`.

If you prefer a plain MCP server entry:

```bash
gemini mcp add --scope user uv uvx uv-mcp-server@latest
```

## Claude Desktop

Edit the config file, then restart Claude Desktop:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "uv": {
      "command": "/Users/you/.local/bin/uvx",
      "args": ["uv-mcp-server@latest"],
      "env": {
        "UV_MCP_WORKSPACE_ROOT": "/Users/you/code/my-project"
      }
    }
  }
}
```

Two things differ from terminal clients:

- Desktop apps do not inherit your shell's `PATH`, so use the **absolute path** to `uvx`. Find it with
  `which uvx` (macOS/Linux) or `where uvx` (Windows).
- Desktop apps have no notion of a current project, so set `UV_MCP_WORKSPACE_ROOT`, or ask Claude to pass
  `project_path` on each call.

## Cursor

Add to `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (one project):

```json
{
  "mcpServers": {
    "uv": {
      "command": "uvx",
      "args": ["uv-mcp-server@latest"]
    }
  }
}
```

## VS Code (GitHub Copilot)

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "uv": {
      "type": "stdio",
      "command": "uvx",
      "args": ["uv-mcp-server@latest"],
      "env": { "UV_MCP_WORKSPACE_ROOT": "${workspaceFolder}" }
    }
  }
}
```

## OpenCode

Add to `opencode.json` in your project, or to `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "uv": {
      "type": "local",
      "command": ["uvx", "uv-mcp-server@latest"],
      "enabled": true
    }
  }
}
```

## Any other MCP client

Configure a **stdio** server with command `uvx` and arguments `["uv-mcp-server@latest"]`. Set environment
variables from the [Configuration](/uv-mcp/guides/configuration/) page in the client's `env` block.

## Verify

Ask your agent:

> *"Call uv_info and tell me which uv version and workspace root you see."*

You should get the uv version, the workspace root, the enabled toolsets and uv's directories. If the
workspace root is wrong, see [Troubleshooting](/uv-mcp/guides/troubleshooting/).

## Running from source

For development, or to try unreleased changes:

```bash
git clone https://github.com/saadmanrafat/uv-mcp.git
cd uv-mcp
uv sync
```

Point a client at the checkout with `--project`, which, unlike `--directory`, does not change the working
directory and therefore does not change which project the server operates on:

```json
{
  "mcpServers": {
    "uv": {
      "command": "uv",
      "args": ["run", "--quiet", "--project", "/path/to/uv-mcp", "uv-mcp-server"]
    }
  }
}
```

You can also run the latest commit on GitHub without cloning:

```bash
uvx --from git+https://github.com/saadmanrafat/uv-mcp uv-mcp-server
```
