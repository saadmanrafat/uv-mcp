---
title: Tool Reference
description: Technical API reference for the UV-MCP server capabilities.
---

# Tool Reference

This section documents the public API exposed by the UV-MCP server. These tools are designed to be invoked by the AI agent but can also be understood as Python function signatures.

## Core Diagnostics

Tools for assessing and restoring system health.

### `diagnose_environment`

Performs a comprehensive health check of the current project context.

-   **Signature**: `diagnose_environment(project_path: str = ".") -> dict`
-   **Description**: Analyzes the project structure, including `pyproject.toml` validity, virtual environment status, and dependency synchronization.
-   **Parameters**:
    -   `project_path` (optional): Absolute or relative path to the project root. Defaults to current directory.
-   **Returns**: A JSON object containing diagnostic data (e.g., `is_uv_installed`, `venv_exists`, `out_of_sync_packages`).

### `repair_environment`

Attempts to automatically resolve issues identified by diagnostics.

-   **Signature**: `repair_environment(project_path: str = None, auto_fix: bool = True) -> dict`
-   **Description**: Executes remediation steps such as creating a missing `.venv` or running `uv sync`.
-   **Parameters**:
    -   `project_path` (optional): Path to project root.
    -   `auto_fix` (optional): If `True`, applies changes. If `False`, returns a plan of intended actions.
-   **Returns**: A summary of actions taken and their outcomes.

### `check_uv_installation`

Verifies the presence of the `uv` binary.

-   **Signature**: `check_uv_installation() -> dict`
-   **Description**: Checks if `uv` is in the system PATH and retrieves its version.
-   **Returns**: JSON object with `installed` (bool) and `version` (str).

### `install_uv`

Provides platform-specific installation instructions.

-   **Signature**: `install_uv() -> dict`
-   **Description**: Returns valid shell commands to install `uv` on Linux, macOS, and Windows.
-   **Returns**: JSON map of platform to installation command.

## Package Management

Tools for modifying the dependency graph.

### `add_dependency`

Installs a new package and updates the lockfile.

-   **Signature**: `add_dependency(package: str, project_path: str = None, dev: bool = False, optional: str = None) -> str`
-   **Description**: Wrapper for `uv add`.
-   **Parameters**:
    -   `package`: Package specifier (e.g., "pandas", "requests>=2.31").
    -   `dev` (optional): If `True`, adds to development dependencies.
    -   `optional` (optional): Name of an optional dependency group.
-   **Returns**: Output log of the operation.

### `remove_dependency`

Uninstalls a package.

-   **Signature**: `remove_dependency(package: str, project_path: str = None, dev: bool = False) -> str`
-   **Description**: Wrapper for `uv remove`.
-   **Parameters**:
    -   `package`: Name of the package to remove.
    -   `dev` (optional): If `True`, removes from development dependencies.
-   **Returns**: Output log of the operation.

### `sync_environment`

Synchronizes the environment with the lockfile.

-   **Signature**: `sync_environment(locked: bool = False, upgrade: bool = False) -> str`
-   **Description**: Ensures the virtual environment exactly matches `uv.lock`.
-   **Parameters**:
    -   `locked`: If `True`, fails if `uv.lock` needs updating.
    -   `upgrade`: If `True`, attempts to upgrade packages within constraints.
-   **Returns**: Output log.

### `export_requirements`

Generates a legacy requirements file.

-   **Signature**: `export_requirements(output_file: str = "requirements.txt") -> str`
-   **Description**: Exports locked dependencies to `requirements.txt` format.
-   **Returns**: Success confirmation.

## Inspection

Tools for deep analysis of the dependency graph.

### `list_dependencies`

Enumerates installed packages.

-   **Signature**: `list_dependencies(project_path: str = None, tree: bool = False) -> list`
-   **Description**: Returns a flat list of all packages currently installed in the environment.
-   **Parameters**:
    -   `project_path` (optional): Path to project root.
    -   `tree` (optional): If `True`, returns a visual tree structure. If `False`, returns a flat list.
-   **Returns**: List of objects containing `name` and `version`, or a tree string.

### `analyze_dependency_tree`

Visualizes package hierarchy.

-   **Signature**: `analyze_dependency_tree(project_path: str = None) -> str`
-   **Description**: Generates a tree view showing which packages depend on which.
-   **Returns**: String representation of the dependency tree.

### `show_package_info`

Retrieves package metadata.

-   **Signature**: `show_package_info(package_name: str, project_path: str = None) -> dict`
-   **Description**: Fetches details like installed version, required python version, and location.
-   **Returns**: JSON metadata object.

### `check_outdated_packages`

Audits for newer versions.

-   **Signature**: `check_outdated_packages(project_path: str = None) -> list`
-   **Description**: Compares installed versions against the PyPI registry.
-   **Returns**: List of packages with `current` and `latest` versions.

## Project & Python Management

Tools for lifecycle and runtime control.

### `init_project`

Bootstraps a new codebase.

-   **Signature**: `init_project(name: str, python_version: str = "3.12", template: str = "app") -> str`
-   **Description**: Creates a new directory with a valid `pyproject.toml`.
-   **Parameters**:
    -   `name`: Name of the project.
    -   `python_version`: Target Python version.
    -   `template`: "app" or "lib".
-   **Returns**: Success message.

### `list_python_versions`

Enumerates available interpreters.

-   **Signature**: `list_python_versions() -> list`
-   **Description**: Lists Python versions managed by `uv`.
-   **Returns**: List of version strings.

### `install_python_version`

Downloads a new interpreter.

-   **Signature**: `install_python_version(version: str) -> str`
-   **Description**: Installs a specific Python version (e.g., "3.11", "pypy@3.10").
-   **Returns**: Success status.

### `pin_python_version`

Sets the project's Python version.

-   **Signature**: `pin_python_version(version: str) -> str`
-   **Description**: Updates `.python-version` to lock the project to a specific runtime.
-   **Returns**: Success status.
