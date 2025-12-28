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

-   **Signature**: `pin_python_version(version: str, project_path: str = None) -> dict`
-   **Description**: Updates `.python-version` to lock the project to a specific runtime.
-   **Parameters**:
    -   `version`: Python version (e.g., "3.12", "3.11").
    -   `project_path` (optional): Path to project root.
-   **Returns**: Success status with PythonPinResult.

## Build & Distribution (v0.6.4+)

New tools for building and distributing Python packages.

### `build_project`

Builds distributable packages for PyPI or local installation.

-   **Signature**: `build_project(project_path: str = None, wheel: bool = True, sdist: bool = True, output_dir: str = None) -> dict`
-   **Description**: Creates wheel and/or source distributions from your project.
-   **Parameters**:
    -   `project_path` (optional): Path to project root.
    -   `wheel` (optional): Build wheel package (.whl). Default: `True`.
    -   `sdist` (optional): Build source distribution (.tar.gz). Default: `True`.
    -   `output_dir` (optional): Custom output directory. Default: "dist/".
-   **Returns**: Dict with build results including list of created artifacts.
-   **Example**:
    ```python
    result = await build_project(wheel=True, sdist=True)
    # Returns: {"success": True, "artifacts": ["dist/myapp-0.1.0.tar.gz", "dist/myapp-0.1.0-py3-none-any.whl"]}
    ```

### `lock_project`

Updates the lockfile without syncing the environment.

-   **Signature**: `lock_project(project_path: str = None) -> dict`
-   **Description**: Creates or updates `uv.lock` to match `pyproject.toml` dependencies without installing them.
-   **Parameters**:
    -   `project_path` (optional): Path to project root.
-   **Returns**: SyncResult with operation status.
-   **Use Cases**:
    -   After manually editing `pyproject.toml`
    -   Before committing to ensure lockfile consistency
    -   To update lockfile for deployment pipelines
-   **Example**:
    ```python
    result = await lock_project()
    # Updates uv.lock without installing packages
    ```

### `clear_cache`

Clears the UV package cache to resolve corrupted packages or free disk space.

-   **Signature**: `clear_cache(package: str = None) -> dict`
-   **Description**: Removes cached package data. Can clear entire cache or specific package.
-   **Parameters**:
    -   `package` (optional): Specific package name to clear. If omitted, clears entire cache.
-   **Returns**: CacheOperationResult with operation details.
-   **Use Cases**:
    -   Resolve corrupted package installations
    -   Fix checksum mismatch errors
    -   Free up disk space
    -   Troubleshoot dependency resolution issues
-   **Examples**:
    ```python
    # Clear entire cache
    await clear_cache()
    
    # Clear specific package
    await clear_cache(package="requests")
    ```

## Error Handling (v0.6.4+)

Enhanced error reporting with actionable suggestions.

### Error Response Format

All tools now return structured errors with:

-   **error_code**: Machine-readable error identifier (e.g., "UV_NOT_FOUND", "PYPROJECT_MISSING")
-   **message**: Human-readable error description
-   **suggestion**: Actionable steps to resolve the issue
-   **timestamp**: When the error occurred

### Common Error Codes

| Error Code | Description | Suggestion |
|------------|-------------|------------|
| `UV_NOT_FOUND` | UV is not installed | Install UV using provided installation commands |
| `PYPROJECT_MISSING` | No pyproject.toml found | Initialize project with `init_project` or `repair_environment` |
| `PROJECT_NOT_FOUND` | Project directory doesn't exist | Check path or create directory |
| `DEPENDENCY_CONFLICT` | Version conflicts detected | Check constraints, update lockfile, or upgrade packages |
| `VENV_MISSING` | Virtual environment not found | Run `repair_environment` to create .venv |
| `PACKAGE_NOT_FOUND` | Package doesn't exist in PyPI | Verify package name on pypi.org |
| `INVALID_PYTHON_VERSION` | Python version incompatible | Check available versions with `list_python_versions` |

### Example Error Response

```json
{
  "success": false,
  "error": "uv is not installed on this system",
  "error_code": "UV_NOT_FOUND",
  "suggestion": "Install uv using: curl -LsSf https://astral.sh/uv/install.sh | sh\nOr use the install_uv tool for platform-specific instructions"
}
```
