---
title: Introduction
description: An overview of UV-MCP, the AI-native interface for Python project management.
---

# Introduction

**UV-MCP** is a Model Context Protocol (MCP) server designed to bridge the gap between Large Language Models (LLMs) and the **uv** Python package manager. It enables AI assistants to autonomously manage Python environments, dependencies, and project lifecycles with the speed and reliability of Rust-based tooling.

## Value Proposition

Modern Python development involves complex environment management—virtual environments, lockfiles, and dependency resolution. UV-MCP abstracts this complexity, allowing developers to interact with their projects using natural language while ensuring rigorous adherence to best practices.

-   **Speed**: Leverages `uv` for near-instant package resolution and installation.
-   **Correctness**: Enforces reproducible environments via universal lockfiles (`uv.lock`).
-   **Autonomy**: Empowers agents to diagnose issues and perform self-healing operations without user intervention.

## Core Concepts

### Model Context Protocol (MCP)
The **Model Context Protocol** is the standard interface that allows AI models to execute code and retrieve context from local systems.
-   **Server**: UV-MCP runs locally, exposing discrete **Tools** (e.g., `add_dependency`, `repair_environment`) to the client.
-   **Client**: The AI interface (e.g., Gemini CLI, Claude Desktop) consumes these tools to fulfill user requests.

### The `uv` Engine
UV-MCP is built on top of **uv**, an extremely fast Python package installer and resolver. It does not reinvent package management; rather, it exposes `uv`'s capabilities to the AI context layer.

## Capabilities

UV-MCP provides a comprehensive suite of tools for the entire project lifecycle:

1.  **Environment Health**:
    -   **Diagnostics**: Comprehensive checks for project structure, interpreter validity, and dependency synchronization.
    -   **Repair**: Automated remediation of common issues (e.g., missing venvs, desynced lockfiles).

2.  **Dependency Management**:
    -   Add, remove, and update packages.
    -   Manage development and optional dependency groups.
    -   Export locked dependencies to standard formats.

3.  **Introspection**:
    -   Analyze dependency trees and hierarchies.
    -   Audit outdated packages and security implications.
    -   Retrieve detailed metadata for installed libraries.

4.  **Project Scaffolding**:
    -   Initialize new applications or libraries with industry-standard templates.
    -   Manage Python version pinning and installation.

## Next Steps

To begin using UV-MCP, proceed to the following guides:

-   **[Installation](/uv-mcp/guides/installation)**: Setup instructions for your operating system and AI client.
-   **[Usage](/uv-mcp/guides/usage)**: Common workflows and prompt engineering examples.
-   **[Tool Reference](/uv-mcp/reference/tools)**: Technical API documentation for all available tools.