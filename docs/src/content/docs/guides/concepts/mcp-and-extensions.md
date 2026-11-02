---
title: MCP and extensions
description: How MCP servers, clients and Gemini extensions fit together, and what that means for uv-mcp.
---

## The Model Context Protocol

The [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) is an open standard that lets AI
applications call tools provided by separate programs. A **client** (Claude Code, Codex, Gemini CLI, an
IDE) starts a **server** and talks to it over JSON-RPC. The server advertises **tools**, each with a name,
a description, a JSON Schema for its input and, optionally, its output, plus **annotations** such as
"read-only" or "destructive". The model decides which tool to call, the client sends the call, and the
server returns the result.

uv-mcp is a **stdio** server: the client launches `uvx uv-mcp-server` as a child process and exchanges
messages over its stdin and stdout. Nothing listens on the network, and the server lives exactly as long as
the client session.

When the session starts, uv-mcp also sends **instructions**: a short guide telling the model to prefer
project commands over pip, to diagnose before guessing, to read `hint` on failures and never to publish
without being asked. Clients add these to the model's context.

## A tool call, end to end

1. You ask: *"Add httpx to this project."*
2. The model chooses `uv_add` with `{"packages": ["httpx"]}`.
3. The client checks its permission rules. `uv_add` is not read-only, so it may ask you first.
4. uv-mcp validates the arguments, resolves the project directory, and runs `uv add httpx` without a shell.
5. It returns a structured result. The model reads `success` and `stderr` (where uv reports what it
   resolved and installed) and tells you what happened.

## Gemini CLI extensions

A Gemini **extension** packages MCP servers together with context files for Gemini CLI. uv-mcp's
repository is itself an extension: `gemini-extension.json` declares the server, and `GEMINI.md` is loaded
as context so Gemini knows when each tool is appropriate. `gemini extensions install
https://github.com/saadmanrafat/uv-mcp` clones the repository and registers both. The extension runs the
server from that clone with `uv run --project ${extensionPath}`, and passes `${workspacePath}` as the
workspace root.

Other clients have no extension format; you add the server to their MCP configuration as shown in
[Installation](/uv-mcp/guides/installation/).
