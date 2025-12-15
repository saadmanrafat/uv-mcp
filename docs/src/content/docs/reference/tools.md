---
title: Tool Reference
description: Complete reference of all tools available in UV-MCP.
---

# Tool Reference

This section lists all the tools exposed by the UV-MCP server.

## Environment Management

### `check_uv_installation`
Checks if `uv` is installed on the system and returns version information.
-   **Parameters**: None
-   **Returns**: JSON object with `installed` (bool) and `version` (string).

### `install_uv`
Provides instructions on how to install `uv` for various platforms.
-   **Parameters**: None
-   **Returns**: JSON with installation command strings.

### `diagnose_environment`
Analyzes the health of the current Python project.
-   **Parameters**:
    -   `project_path` (optional, string): Path to project root. Defaults to current directory.
-   **Returns**: Comprehensive JSON report including project structure, dependency health, and Python compatibility.

### `repair_environment`
Attempts to automatically fix common issues found by diagnostics.
-   **Parameters**:
    -   `project_path` (optional, string): Path to project root.
    -   `auto_fix` (optional, bool): If `true`, applies changes. If `false`, only lists plan. Default: `true`.
-   **Returns**: JSON report of actions taken (e.g., created venv, synced deps).

### `sync_environment`
Syncs the environment with `pyproject.toml` or `uv.lock`.
-   **Parameters**:
    -   `upgrade` (optional, bool): Upgrade all packages.
    -   `locked` (optional, bool): Assert lockfile consistency.
-   **Returns**: Command output.

## Dependency Management

### `add_dependency`
Adds a package to the project.
-   **Parameters**:
    -   `package` (required, string): Name of package (e.g., "pandas", "requests>=2.0").
    -   `dev` (optional, bool): Add as a development dependency.
    -   `optional` (optional, string): Add to an optional group.
-   **Returns**: Success/failure message.

### `remove_dependency`
Removes a package from the project.
-   **Parameters**:
    -   `package` (required, string): Name of package.
    -   `dev` (optional, bool): Remove from dev dependencies.
-   **Returns**: Success/failure message.

### `export_requirements`
Exports the current locked dependencies to a standard format.
-   **Parameters**:
    -   `output_file` (optional, string): Filename. Default: "requirements.txt".
-   **Returns**: Confirmation message.

## Project Lifecycle

### `init_project`
Initialize a new Python project.
-   **Parameters**:
    -   `name` (required, string): Project name.
    -   `template` (optional, string): "app" or "lib". Default "app".
    -   `python_version` (optional, string): e.g., "3.12".
-   **Returns**: Success message.
