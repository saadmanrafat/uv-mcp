---
title: Usage Guide
description: Operational workflows and command patterns for UV-MCP.
---

# Usage Guide

This document outlines the primary workflows for interacting with UV-MCP. The server translates natural language intent into precise `uv` commands.

## Environment Health & Setup

Tools to verify the system state and fix configuration issues.

### Diagnostics & Repair

**Intent**: Check project integrity or fix broken environments.

> "Diagnose the current environment."
> "Why is my build failing?"
> "Fix the missing virtual environment."

**System Actions**:
-   `diagnose_environment`: Checks for `pyproject.toml`, virtual environment status, and dependency synchronization.
-   `repair_environment`: Automatically creates `.venv`, installs Python, and syncs dependencies if broken.

### UV Installation

**Intent**: Verify or install the core `uv` tool.

> "Check if uv is installed."
> "How do I install uv?"

**System Actions**:
-   `check_uv_installation`: Verifies `uv` presence and version.
-   `install_uv`: Provides platform-specific installation instructions.

## Dependency Management

Manage your project's libraries and packages.

### Installation & Removal

**Intent**: Add or remove packages.

> "Install pandas and numpy."
> "Add pytest as a dev dependency."
> "Remove the requests library."

**System Actions**:
-   `add_dependency`: Adds packages to `pyproject.toml` and installs them. Supports `--dev` and optional groups.
-   `remove_dependency`: Removes packages from configuration and the environment.

### Synchronization

**Intent**: Ensure the environment matches the lockfile.

> "Sync the environment."
> "Upgrade all packages."

**System Action**:
-   `sync_environment`: Updates the virtual environment to match `uv.lock`. Can also upgrade locked versions.

### Maintenance

**Intent**: Check for updates or inspect specific packages.

> "Check for outdated packages."
> "Show details for the fastapi package."

**System Actions**:
-   `check_outdated_packages`: Lists packages that have newer versions available on PyPI.
-   `show_package_info`: Retrieves detailed metadata (version, location, dependencies) for a specific package.

## Project Inspection

Visualize and understand your dependency graph.

**Intent**: View installed packages.

> "List all installed dependencies."
> "Show me the dependency tree."

**System Actions**:
-   `list_dependencies`: Enumerates all installed packages. Supports a `tree` view.
-   `analyze_dependency_tree`: visualizes the hierarchical dependency structure and calculates depth.

## Runtime Management

Control the Python interpreters used by your project.

**Intent**: Manage Python versions.

> "List available Python versions."
> "Install Python 3.11."
> "Pin this project to Python 3.12."

**System Actions**:
-   `list_python_versions`: Shows Python versions managed by `uv`.
-   `install_python_version`: Downloads and installs a specific Python interpreter.
-   `pin_python_version`: Updates `.python-version` to lock the project to a specific runtime.

## Project Lifecycle

**Intent**: Start or export projects.

> "Initialize a new Python app named 'data-pipeline'."
> "Export dependencies to requirements.txt."

**System Actions**:
-   `init_project`: Scaffolds a new project with `pyproject.toml`.
-   `export_requirements`: Generates a standard `requirements.txt` file for compatibility.
