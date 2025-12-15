---
title: Introduction
description: Welcome to UV-MCP, the AI-powered interface for the uv package manager.
---

# Introduction

**UV-MCP** is a Model Context Protocol (MCP) server that empowers your AI assistants to manage Python environments using **uv**, the incredibly fast Python package manager written in Rust.

## What is UV-MCP?

UV-MCP acts as a bridge between Large Language Models (LLMs) like Claude or Gemini and your local Python development environment. Instead of manually typing terminal commands to install packages, fix virtual environments, or resolve dependency conflicts, you can simply ask your AI to do it for you.

## Why use UV-MCP?

Managing Python environments can be complex. `uv` simplifies this with speed and correctness, and UV-MCP takes it a step further by giving your AI agent direct access to these capabilities.

### Key Benefits

- **Lightning Fast**: Leverages `uv`'s performance for near-instant package installations and resolutions.
- **AI-Native**: Designed specifically for MCP-compliant agents, allowing for natural language interaction.
- **Self-Healing**: Includes diagnostic tools that can automatically identify and repair broken environments (missing venvs, desynced lockfiles, etc.).
- **Effortless Management**: Add, remove, and update dependencies without leaving your chat context.

## What can it do?

- **Diagnose Health**: instantly check if your project structure, virtual environment, and dependencies are healthy.
- **Repair Environments**: Automatically fix common issues like missing virtual environments or uninstalled dependencies.
- **Manage Dependencies**: Add or remove libraries with simple prompts like "Add pandas to this project".
- **Initialize Projects**: Bootstrap new Python projects with best practices in seconds.

## Next Steps

- **[Installation](/uv-mcp/guides/installation)**: Get UV-MCP running on your system.
- **[Usage Guide](/uv-mcp/guides/usage)**: Learn how to interact with the tools.
- **[Architecture](/uv-mcp/guides/architecture)**: Understand how it works under the hood.