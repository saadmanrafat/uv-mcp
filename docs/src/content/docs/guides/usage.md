---
title: Usage Guide
description: Common workflows and usage examples
---

# Usage Guide

Once UV-MCP is installed, you can interact with it through your AI assistant using natural language.

## Diagnosing Your Environment

If you suspect something is wrong with your Python setup, simply ask:

> "Diagnose my Python environment."
> "Why isn't my project working?"

The AI will use the `diagnose_environment` tool to check:
*   Is `uv` installed?
*   Does `pyproject.toml` exist?
*   Is the virtual environment active and valid?
*   Are there dependency conflicts?

## Repairing Issues

If issues are found, you can ask the AI to fix them:

> "Fix the environment issues."
> "Repair my project setup."

The `repair_environment` tool can:
*   Create a missing `.venv`.
*   Initialize a new project structure.
*   Sync dependencies from `uv.lock`.
*   Install the correct Python interpreter version.

## Managing Dependencies

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
