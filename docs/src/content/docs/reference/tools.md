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

## Workspace & Introspection (v0.8.0+)

### `run_ephemeral_tool`

Runs an ephemeral CLI tool via `uv tool run` (`uvx` proxy) without permanently installing it.

-   **Signature**: `run_ephemeral_tool(package: str, command: list[str], project_path: str = None) -> EphemeralToolResult`
-   **Description**: Instantly executes a package command using the `uvx` proxy. The tool is downloaded, cached, and executed in a single step. No global `venv` or `bin/` entry is created, and the package does not appear in `uv tool list`.
-   **Parameters**:
    -   `package` (str): Package name on PyPI (e.g., `"ruff"`, `"black"`, `"mypy"`, `"httpie"`).
    -   `command` (list[str]): Arguments passed to the tool (e.g., `["check", "."]` or `["-v", "http://example.com"]`).
    -   `project_path` (str | None): Absolute path to the project directory. The subprocess runs with this as the working directory.
-   **Returns**: `EphemeralToolResult`:
    -   `package`: Name of the executed package.
    -   `command`: The argument list that was passed.
    -   `stdout`: Standard output from the tool.
    -   `stderr`: Standard error from the tool.
    -   `return_code`: Exit code (0 on success, 1 on failure).
    -   `success`: Boolean indicating whether the command exited successfully.
    -   `error`: Populated with `stderr` when `success` is `False`.
-   **When to Use**:
    - One-off formatting, linting, or type-checking tasks.
    - CI pipelines where you want the exact version specified in the command.
    - Temporary scripts that depend on a package you do not wish to install permanently.
    - Exploring a tool before deciding to install it globally.
-   **Example**:
    ```python
    # Lint with ruff without installing it
    result = await run_ephemeral_tool(package="ruff", command=["check", "."])
    # result.stdout -> linting diagnostics
    # result.return_code -> 0 (clean) or non-zero (issues found)

    # Format a file with black
    result = await run_ephemeral_tool(package="black", command=["--diff", "src/"])
    # result.stdout -> unified diff of formatting changes
    ```

### `get_workspace_manifest`

Introspects a monorepo's workspace tree defined in `pyproject.toml`.

-   **Signature**: `get_workspace_manifest(project_path: str = None) -> WorkspaceManifest`
-   **Description**: Parses `[tool.uv.workspace]` members and recursively collects each sub-project's metadata (name, absolute path, dependencies) into a topological JSON graph.
-   **Parameters**:
    -   `project_path` (optional): Root directory of the workspace.
-   **Returns**: `WorkspaceManifest` with `root` path, `is_workspace` flag, and `members` list (each containing `name`, `path`, and `dependencies`).
-   **Example**:**
    ```python
    result = await get_workspace_manifest(project_path="/home/user/monorepo")
    # result.members -> [{"name": "api", "path": "/home/user/monorepo/api", "dependencies": [...]}, ...]
    ```

### `self_heal_environment`

Self-healing diagnostics that monitors `uv pip check` output for `ModuleNotFoundError` signatures.

-   **Signature**: `self_heal_environment(project_path: str = None) -> SelfHealingDiagnostics`
-   **Description**: Runs a lightweight dependency check, regex-captures missing packages, automatically triggers `uv sync`, and appends targeted `uv add` commands as actionable recommendations.
-   **Parameters**:
    -   `project_path` (optional): Project directory to analyze.
-   **Returns**: `SelfHealingDiagnostics` payload:
    -   `success`: Whether all actions succeeded.
    -   `actions`: List of `HealingAction` objects (`pip_check`, `sync`).
    -   `missing_packages`: Extracted package names (`list[str]`).
    -   `recommendations`: Actionable suggestions (e.g., "Package 'pandas' is missing. Suggested fix: uv add pandas").
-   **Example**:**
    ```python
    result = await self_heal_environment()
    # result.missing_packages -> ["pandas", "numpy"]
    # result.recommendations -> ["Package 'pandas' is missing. Suggested fix: uv add pandas", ...]
    ```

## Build & Distribution (v0.7.2+)

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

## Virtual Environment (v1.0.0+)

### `create_venv`

Create a virtual environment for the project.

-   **Signature**: `create_venv(project_path: str = None, seed: bool = False, clear: bool = False, relocatable: bool = False, system_site_packages: bool = False) -> VenvResult`
-   **Description**: Creates `.venv` with optional seed packages, clear mode, relocatable flag, or system site packages access.
-   **Returns**: `VenvResult` with the created venv path.

## Script Execution (v1.0.0+)

### `run_script`

Run a command inside the project's environment.

-   **Signature**: `run_script(command: list[str], project_path: str = None, with_packages: list[str] = None) -> ScriptRunResult`
-   **Description**: Executes arbitrary commands via `uv run`. Supports temporary `--with` packages.
-   **Example**:
    ```python
    await run_script(command=["python", "-c", "print(1)"], with_packages=["requests"])
    ```

## Project Lifecycle (v1.0.0+)

### `project_version`

Read or update the project's version.

-   **Signature**: `project_version(value: str = None, bump: str = None, project_path: str = None, dry_run: bool = False) -> VersionResult`
-   **Description**: Wraps `uv version`. Supports setting an exact value or bumping (major, minor, patch).

### `format_code`

Format Python code using Ruff.

-   **Signature**: `format_code(project_path: str = None, check: bool = False, diff: bool = False) -> FormatResult`
-   **Description**: Runs `uv format` with optional `--check` or `--diff` modes.

## Pip Compatibility (v1.0.0+)

### `pip_compile`

Compile `requirements.in` to a pinned `requirements.txt`.

-   **Signature**: `pip_compile(input_file: str = "requirements.in", output_file: str = "requirements.txt", project_path: str = None) -> PipCompileResult`
-   **Description**: Wraps `uv pip compile`.

### `pip_sync_requirements`

Sync environment from a `requirements.txt`.

-   **Signature**: `pip_sync_requirements(requirements_file: str = "requirements.txt", project_path: str = None) -> PipSyncResult`
-   **Description**: Wraps `uv pip sync`.

### `pip_freeze`

Freeze installed packages.

-   **Signature**: `pip_freeze(project_path: str = None) -> PipFreezeResult`
-   **Description**: Wraps `uv pip freeze`.

### `pip_install`

Imperatively install packages.

-   **Signature**: `pip_install(packages: list[str], project_path: str = None) -> DependencyOperationResult`
-   **Description**: Wraps `uv pip install`.

### `pip_uninstall`

Imperatively uninstall packages.

-   **Signature**: `pip_uninstall(packages: list[str], project_path: str = None) -> DependencyOperationResult`
-   **Description**: Wraps `uv pip uninstall`.

## Tool Management (v1.0.0+)

### `tool_install`

Permanently install a CLI tool.

-   **Signature**: `tool_install(package: str) -> ToolListResult`
-   **Description**: Wraps `uv tool install`.

### `tool_upgrade`

Upgrade installed tools.

-   **Signature**: `tool_upgrade(package: str = None) -> ToolListResult`
-   **Description**: Wraps `uv tool upgrade`.

### `tool_list`

List installed tools.

-   **Signature**: `tool_list() -> ToolListResult`
-   **Description**: Wraps `uv tool list`.

### `tool_uninstall`

Uninstall a tool.

-   **Signature**: `tool_uninstall(package: str) -> ToolListResult`
-   **Description**: Wraps `uv tool uninstall`.

## Cache Introspection (v1.0.0+)

### `prune_cache`

Prune unreachable cache objects.

-   **Signature**: `prune_cache() -> CacheInfoResult`
-   **Description**: Wraps `uv cache prune`.

### `cache_dir`

Show the cache directory path.

-   **Signature**: `cache_dir() -> CacheInfoResult`
-   **Description**: Wraps `uv cache dir`.

### `cache_size`

Show cache disk usage.

-   **Signature**: `cache_size() -> CacheInfoResult`
-   **Description**: Wraps `uv cache size`.

## Python Management (v1.0.0+)

### `find_python`

Locates Python installations managed by `uv`.

-   **Signature**: `find_python(version: str = None) -> PythonListResult`
-   **Description**: Wraps `uv python find`. Searches the uv-managed Python cache for matching interpreters and returns their absolute paths. If `version` is omitted, all managed installations are returned.
-   **Parameters**:
    -   `version` (str | None): Version filter (e.g., `"3.12"`, `"3.11"`). Omit to list all.
-   **Returns**: `PythonListResult` containing a `versions` list of `PythonVersion` objects:
    -   `version`: The version string (e.g., `"cpython-3.12.4"`).
    -   `path`: Absolute filesystem path to the interpreter binary.
    ```
-   **When to Use**:
    - You need the exact interpreter path for a CI matrix.
    - Debugging PATH issues where the wrong Python is being picked up.
    - Verifying that a required version is installed before pinning it.
-   **Example**:
    ```python
    result = await find_python(version="3.12")
    # result.versions -> [
    #   {"version": "cpython-3.12.4", "path": "/home/user/.local/share/uv/python/cpython-3.12.4-linux-x86_64-gnu/bin/python3.12"}
    # ]
    ```

### `python_dir`

Shows the root directory where uv stores managed Python interpreters.

-   **Signature**: `python_dir() -> CacheInfoResult`
-   **Description**: Wraps `uv python dir`. Returns the absolute path to the directory containing all downloaded and installed Python runtimes. This is useful for disk-space audits and debugging path issues.
-   **Returns**: `CacheInfoResult`:
    -   `operation`: `"dir"`
    -   `path`: Absolute directory path.
    -   `success`: Boolean indicating whether the query succeeded.
    -   `error`: Error message if the query failed.
-   **When to Use**:
    - You want to know how much disk space uv-managed Pythons consume.
    - You are provisioning CI runners and need to pre-warm a specific Python cache directory.
-   **Example**:
    ```python
    result = await python_dir()
    # result.path -> /home/user/.local/share/uv/python
    ```
### `upgrade_python_version`

Upgrades a uv-managed Python installation to the latest available patch for the given minor version.

-   **Signature**: `upgrade_python_version(version: str) -> PythonInstallResult`
-   **Description**: Wraps `uv python upgrade`. For example, if you have `3.12.3` installed and `3.12.4` is available, calling `upgrade_python_version("3.12")` updates the interpreter in-place without breaking existing virtual environments because `uv` tracks interpreters by full version string.
-   **Parameters**:
    -   `version` (str): The version specifier to upgrade (e.g., `"3.12"`, `"3.11"`, `"pypy@3.10"`).
-   **Returns**: `PythonInstallResult`:
    -   `version`: The version string that was requested.
    -   `success`: Whether the upgrade completed successfully.
    -   `output`: Diagnostic output from `uv python upgrade` (e.g., `"Updated cpython-3.12.4"`).
    -   `error`: Error message if the upgrade failed.
-   **When to Use**:
    - A new patch release ships security fixes and you want to update without reinstalling the entire project.
    - CI pipelines need the latest patch before running tests.
    - You maintain multiple Python versions and want to rotate them to the latest patch.
-   **Example**:
    ```python
    result = await upgrade_python_version(version="3.12")
    # result.output -> "Updated cpython-3.12.4"
    # result.success -> True
    ```

### `uninstall_python_version`

Removes a uv-managed Python interpreter to reclaim disk space.

-   **Signature**: `uninstall_python_version(version: str) -> PythonInstallResult`
-   **Description**: Wraps `uv python uninstall`. Deletes the interpreter and its cached artifacts from the uv-managed Python directory. Warning: any virtual environments created with this exact interpreter will become invalid.
-   **Parameters**:
    -   `version` (str): The version string to uninstall (e.g., `"3.11"`, `"pypy@3.10"`).
-   **Returns**: `PythonInstallResult`:
    -   `version`: The version string that was requested.
    -   `success`: Whether the uninstallation completed successfully.
    -   `output`: Diagnostic output from `uv python uninstall`.
    -   `error`: Error message if the operation failed.
-   **When to Use**:
    - Disk space is constrained and an old Python version is no longer needed.
    - You rotated CI runner images and want to clean up unused versions.
    - A broken Python installation needs to be removed before reinstallation.
-   **Example**:
    ```python
    result = await uninstall_python_version(version="3.11")
    # result.success -> True
    ```
## Distribution & Publishing (v1.0.0+)

### `publish_project`

Publish distributions to an index.

-   **Signature**: `publish_project(project_path: str = None, files: list[str] = None, dry_run: bool = False, token: str = None) -> PublishResult`
-   **Description**: Wraps `uv publish`. Supports dry-run mode.

## Self Management (v1.0.0+)

### `self_update`

Update the uv binary.

-   **Signature**: `self_update() -> SelfUpdateResult`
-   **Description**: Wraps `uv self update`.

### `self_version`

Display the uv binary version.

-   **Signature**: `self_version() -> SelfUpdateResult`
-   **Description**: Wraps `uv self version`.

## Error Handling (v0.7.2+)

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
