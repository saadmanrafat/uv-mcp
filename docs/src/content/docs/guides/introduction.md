---
title: Introduction
description: Overview of UV-MCP, MCP, and Gemini Extensions
---

# Introduction

**UV-MCP** is a Model Context Protocol (MCP) server designed to bridge the gap between AI assistants (like Gemini and Claude) and your Python development environment.

It leverages the speed and efficiency of **[uv](https://docs.astral.sh/uv/)**, the extremely fast Python package manager written in Rust.

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard that enables AI models to interact with external tools and data sources. Instead of hardcoding integrations into the AI model itself, MCP allows developers to build "servers" (like UV-MCP) that expose specific capabilities.

In this case, UV-MCP exposes tools to:
*   Read your project structure.
*   Run `uv` commands.
*   Analyze environment health.

Your AI client (like Claude Desktop or Gemini CLI) connects to this server, allowing the AI to "see" and "touch" your Python environment securely.

## What are Extensions?

In the context of the **Gemini CLI**, an "Extension" is a package that bundles an MCP server with configuration that makes it easy to install and use.

When you install the UV-MCP extension:
1.  The Gemini CLI downloads the UV-MCP package.
2.  It registers the MCP server in its configuration.
3.  It automatically manages the server's lifecycle (starting/stopping it when needed).

This seamless integration means you don't have to manually configure ports or connection strings. You just install it, and your AI assistant immediately gains new powers.

## Why UV-MCP?

Managing Python environments can be complex. Dependency conflicts, broken virtual environments, and configuration mismatches are common headaches. UV-MCP allows your AI assistant to:

*   **Diagnose** issues automatically.
*   **Repair** broken environments without manual intervention.
*   **Manage** dependencies using natural language.

## Core Capabilities

*   **Environment Health Checks**: Validates `pyproject.toml`, virtualenvs, and lockfiles.
*   **Automated Repairs**: Can initialize projects, create venvs, and sync dependencies.
*   **Dependency Management**: Add or remove packages, including dev dependencies and optional groups.