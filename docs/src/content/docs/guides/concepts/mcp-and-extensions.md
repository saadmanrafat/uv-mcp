---
title: MCP and Extensions
description: "Understanding the ecosystem: Model Context Protocol and Gemini Extensions."
---

# MCP and Extensions

This document explains the underlying standards that enable UV-MCP to function.

## The Model Context Protocol (MCP)

The **Model Context Protocol (MCP)** is an open standard designed to solve the connectivity problem between AI models and external systems.

### The Problem
Traditionally, AI models are isolated ("sandboxed"). They cannot read your files, run code, or check your system status without complex, custom-built integrations.

### The MCP Solution
MCP defines a universal language for:
1.  **Exposing Resources**: Allowing the AI to read data (logs, files).
2.  **Exposing Tools**: Allowing the AI to execute actions (commands, API calls).
3.  **Exposing Prompts**: Pre-defined templates for user interaction.

UV-MCP functions as an **MCP Server**. It translates the AI's intent into local `uv` commands.

## Gemini Extensions

While MCP is the *communication protocol*, a **Gemini Extension** is the *packaging format* used to distribute these capabilities to Gemini-powered interfaces.

### Integration
When you install UV-MCP as an extension, you are registering it as a trusted tool provider. The Gemini CLI uses the extension manifest to:
-   **Discover** the server.
-   **Launch** the server process in the background.
-   **Route** relevant user queries to the server.

### The Workflow

1.  **User Query**: "Install numpy."
2.  **Gemini Client**: Identifies that `install_dependency` (a tool provided by the UV-MCP extension) is relevant.
3.  **Protocol Handshake**: The client sends an MCP JSON-RPC request to the UV-MCP server.
4.  **Execution**: UV-MCP executes the `uv` command locally.
5.  **Response**: The result is sent back via MCP, and Gemini summarizes it for you.