---
title: Usage Guide
description: Learn how to interact with UV-MCP to manage your Python projects.
---

# Usage Guide

Once UV-MCP is installed and connected to your AI agent, you can interact with it using natural language. This guide covers common workflows and example prompts.

## Basic Diagnostics

The most powerful feature of UV-MCP is its ability to diagnose the current environment.

**Prompt:**
> "Diagnose my environment."
> "Why is my python setup broken?"

**What happens:**
The agent calls `diagnose_environment`. It checks:
- If `uv` is installed.
- If a `pyproject.toml` or `requirements.txt` exists.
- If a virtual environment (`.venv`) exists and is active.
- If dependencies are in sync with the lockfile.
- If the Python version matches project requirements.

## Auto-Repair

If diagnostics find issues, the agent can often fix them automatically.

**Prompt:**
> "Fix my environment."
> "Repair the project setup."

**What happens:**
The agent calls `repair_environment`. It attempts to:
1.  Initialize a project if missing.
2.  Create a virtual environment.
3.  Install a compatible Python version.
4.  Sync dependencies.

## Managing Dependencies

You can add or remove packages without remembering exact CLI flags.

### Adding Packages

**Prompt:**
> "Add pandas to this project."
> "Install pytest as a dev dependency."
> "Add fastapi and uvicorn."

**What happens:**
The agent uses `add_dependency`.
- `uv add pandas`
- `uv add --dev pytest`

### Removing Packages

**Prompt:**
> "Remove numpy."
> "Uninstall the requests library."

**What happens:**
The agent uses `remove_dependency`.

## Project Initialization

Starting a new project is easy.

**Prompt:**
> "Initialize a new Python app named 'my-bot'."
> "Create a new library project called 'utils'."

**What happens:**
The agent uses `init_project`.
- `uv init --app --name my-bot`

## Advanced Workflows

### Syncing and Locking

If you suspect your lockfile is out of date:

**Prompt:**
> "Sync the environment."
> "Ensure the lockfile is up to date."

### Exporting Requirements

If you need a `requirements.txt` for legacy systems:

**Prompt:**
> "Export the dependencies to requirements.txt."
