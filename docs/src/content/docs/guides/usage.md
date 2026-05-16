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

## Build & Distribution (v0.7.2+)

New workflows for packaging and distributing your Python projects.

### Building Packages

**Intent**: Create distributable packages for PyPI or local installation.

> "Build wheel and source distributions for this project."
> "Create a PyPI-ready package."
> "Build only a wheel file."

**System Actions**:
-   `build_project`: Creates wheel (.whl) and source distribution (.tar.gz) files.
    - Supports selective building (wheel-only or sdist-only)
    - Custom output directories
    - Returns list of created artifacts

**Example Workflow**:
```bash
# 1. Ensure project is ready
> "Diagnose the environment"

# 2. Update lockfile
> "Update the lockfile"

# 3. Build packages
> "Build wheel and source distributions"

# Result: dist/myproject-0.1.0.tar.gz and dist/myproject-0.1.0-py3-none-any.whl
```

### Lockfile Management

**Intent**: Update dependency lockfile without installing packages.

> "Update the lockfile."
> "Regenerate uv.lock without syncing."
> "Lock dependencies to current versions."

**System Actions**:
-   `lock_project`: Updates `uv.lock` to reflect `pyproject.toml` changes without installing.

**Use Cases**:
- After manually editing `pyproject.toml`
- Before committing to version control
- In CI/CD pipelines for reproducible builds

### Cache Management

**Intent**: Clear package cache to resolve issues or free space.

> "Clear the package cache."
> "Remove cached version of requests."
> "Fix corrupted package installation."

**System Actions**:
-   `clear_cache`: Removes cached package data (entire cache or specific package).

**When to Use**:
- Corrupted package installations
- Checksum mismatch errors
- Disk space constraints
- Dependency resolution failures

**Example Scenarios**:
```bash
# Clear entire cache
> "Clear all cached packages"

# Clear specific package
> "Clear the cache for numpy"

# After clearing, reinstall
> "Sync the environment"
```

## Virtual Environment & Script Execution (v1.0.0+)

### Creating Virtual Environments Explicitly

**Intent**: Create a new `.venv` with specific options.

> "Create a virtual environment with seed packages."
> "Make the venv relocatable."
> "Clear the existing venv and recreate it."

**System Actions**:
- `create_venv`: Creates `.venv` with `--seed`, `--relocatable`, `--clear`, `--system-site-packages`.

### Running Scripts & Commands

**Intent**: Execute arbitrary commands inside the project's environment.

> "Run pytest in the project."
> "Execute python -m my_module with temporary dependencies."

**System Actions**:
- `run_script`: Executes `uv run` with optional `--with` temporary packages.

## Project Version & Formatting (v1.0.0+)

### Version Management

**Intent**: Read, set, or bump the project version.

> "What is the current project version?"
> "Bump the minor version."
> "Set version to 2.0.0."

**System Actions**:
- `project_version`: Wraps `uv version` with `--bump` and `--dry-run` support.

### Code Formatting

**Intent**: Format Python code with Ruff.

> "Format the codebase."
> "Check if files are formatted without making changes."
> "Show a diff of formatting changes."

**System Actions**:
- `format_code`: Runs `uv format` with `--check` or `--diff`.

## Pip Compatibility (v1.0.0+)

### Legacy Requirements Workflows

**Intent**: Work with legacy `requirements.txt` files.

> "Compile requirements.in to requirements.txt."
> "Sync environment from requirements.txt."
> "Freeze installed packages to requirements format."
> "Install packages imperatively without pyproject.toml."

**System Actions**:
- `pip_compile`: Compiles `requirements.in` → `requirements.txt`.
- `pip_sync_requirements`: Syncs from `requirements.txt`.
- `pip_freeze`: Lists installed packages in requirements format.
- `pip_install` / `pip_uninstall`: Imperative pip-style operations.

## Tool Management (v1.0.0+)

### Managing Global CLI Tools

**Intent**: Install, upgrade, or remove globally available Python CLI tools.

> "Install ruff as a global tool."
> "List all installed tools."
> "Upgrade black."
> "Uninstall httpie."

**System Actions**:
- `tool_install`: Installs a tool globally.
- `tool_upgrade`: Upgrades one or all tools.
- `tool_list`: Lists installed tools.
- `tool_uninstall`: Removes a tool.

## Cache Introspection (v1.0.0+)

### Inspecting Cache State

**Intent**: Understand cache disk usage and prune stale entries.

> "Show the cache directory path."
> "How much disk space is the cache using?"
> "Prune unreachable cache objects."

**System Actions**:
- `cache_dir`: Shows cache directory.
- `cache_size`: Shows human-readable cache size.
- `prune_cache`: Removes unreachable cache entries.

## Workspace Introspection & Self-Healing (v0.8.0+)

### Ephemeral Tool Execution

**Intent**: Run a CLI tool one time without permanently installing it.

> "Run ruff check on this codebase."
> "Lint with black without installing black globally."
> "Type-check with mypy as a one-off."

**System Action**:
- `run_ephemeral_tool`: Invokes `uv tool run` (the `uvx` proxy) for a single execution.
  - `package`: The PyPI package name (e.g. `"ruff"`, `"black"`, `"mypy"`).
  - `command`: Arguments passed to the tool (e.g. `["check", "."]`).
  - `project_path`: Optional working directory.
  - **Returns**: `EphemeralToolResult` with `stdout`, `stderr`, `return_code`, and `success`.

**When to Use**:
- You need a formatter or linter once and do not want to pollute the global environment.
- Running a temporary script that depends on a package you do not wish to install permanently.
- CI pipelines where you want the exact version specified in the command.

**Example**:
```bash
> "Run ruff check ."
# System: run_ephemeral_tool(package="ruff", command=["check", "."])
# stdout -> linting results
# stderr -> errors only if the tool fails
```

### Monorepo Workspace Manifest

**Intent**: Inspect a multi-package repo managed by `uv` workspaces.

> "Show me workspace members."
> "What dependencies does the api package have?"
> "Build a topological graph of this monorepo."

**System Action**:
- `get_workspace_manifest`: Parses `[tool.uv.workspace]` from the root `pyproject.toml` and recursively reads each member's metadata.
  - **Returns**: `WorkspaceManifest` containing the root directory, `is_workspace` boolean, and a `members` list. Each member includes `name`, absolute `path`, and `dependencies`.

**When to Use**:
- You are working inside a monorepo and want to know which packages exist and how they relate.
- You need a dependency graph for documentation or deployment ordering.
- You want to identify workspace drift (members listed but missing from disk).

**Example**:
```bash
> "Show workspace members."
# System: get_workspace_manifest(project_path="/home/user/monorepo")
# -> Members: [{"name": "api", "path": "/.../api", "dependencies": [...]}, ...]
```

### Self-Healing Diagnostics

**Intent**: Automatically detect and fix a broken environment.

> "My imports are failing, fix the environment."
> "Why is pandas missing?"
> "Heal this broken project."

**System Action**:
- `self_heal_environment`: Runs `uv pip check`, captures `ModuleNotFoundError` signatures with regex, and attempts to recover.
  - Triggers `uv sync` automatically.
  - Extracts missing package names and appends recommended `uv add <pkg>` actions.
  - **Returns**: `SelfHealingDiagnostics` with:
    - `success`: whether all remediation steps succeeded.
    - `actions`: list of `HealingAction` objects (`pip_check`, `sync`).
    - `missing_packages`: extracted package names (e.g. `["pandas", "numpy"]`).
    - `recommendations`: actionable human-readable suggestions.

**When to Use**:
- After switching branches where `pyproject.toml` changed.
- When a teammate's environment is missing dependencies the lockfile expects.
- Before a demo or deployment where the project must be runnable immediately.

**Example**:
```bash
> "Heal the environment."
# System: self_heal_environment()
# missing_packages -> ["pandas"]
# recommendations -> ["Package 'pandas' is missing. Suggested fix: uv add pandas"]
# actions -> [{"type": "sync", "success": true}]
```

## Advanced Python Management (v1.0.0+)

### Finding & Inspecting Installations

**Intent**: Locate or inspect Python interpreters managed by `uv`.

> "Where is the Python 3.12 binary installed by uv?"
> "Show all uv-managed Python installations."
> "What is the uv Python installation directory?"

**System Actions**:
- `find_python`: Wraps `uv python find`. Returns `PythonListResult` with version string and absolute path for each match.
  - Optional `version` filter (e.g. `"3.12"`).
- `python_dir`: Wraps `uv python dir`. Returns `CacheInfoResult` with the directory path for uv's Python cache.

**When to Use**:
- You need the exact interpreter path for a CI matrix.
- You want to know how much disk space uv-managed Pythons consume.
- Debugging PATH issues where the wrong Python is being picked up.

**Example**:
```bash
> "Find Python 3.12."
# System: find_python(version="3.12")
# versions -> [{"version": "3.12.4", "path": "/home/user/.local/share/uv/python/cpython-3.12.4-linux-x86_64-gnu/bin/python3.12"}]

> "Show uv Python directory."
# System: python_dir()
# path -> /home/user/.local/share/uv/python
```

### Upgrading & Uninstalling Runtimes

**Intent**: Maintain uv-managed Python interpreters over time.

> "Upgrade my Python 3.12 installation to the latest patch."
> "Remove Python 3.11 to reclaim disk space."

**System Actions**:
- `upgrade_python_version`: Wraps `uv python upgrade`. Patches an installed version (e.g. `3.12.3` → `3.12.4`).
  - **Returns**: `PythonInstallResult` with `success`, `output`, and `error`.
- `uninstall_python_version`: Wraps `uv python uninstall`. Removes a specific version entirely.
  - **Returns**: `PythonInstallResult` with operation status.

**When to Use**:
- You want the latest patch release without reinstalling the entire project.
- You maintain multiple Python versions for testing and need to rotate them.
- Disk space is constrained and unused interpreters should be removed.

**Example**:
```bash
> "Upgrade Python 3.12 to the latest patch."
# System: upgrade_python_version(version="3.12")
# output -> "Updated cpython-3.12.4"

> "Uninstall Python 3.11."
# System: uninstall_python_version(version="3.11")
# -> success: true
```

## Publishing & Self Management (v1.0.0+)

### Publishing Packages

**Intent**: Upload distributions to PyPI or a private index.

> "Publish the project to PyPI."
> "Dry-run the publish step."

**System Actions**:
- `publish_project`: Wraps `uv publish` with `--dry-run` support.

### Updating uv Itself

**Intent**: Keep the uv binary up to date.

> "Update uv to the latest version."
> "What version of uv is installed?"

**System Actions**:
- `self_update`: Updates the uv binary.
- `self_version`: Displays uv binary version.

## Error Handling & Troubleshooting (v0.7.2+)

### Understanding Error Messages

All tools now provide structured errors with actionable suggestions:

```json
{
  "error": "No pyproject.toml found in /path/to/project",
  "error_code": "PYPROJECT_MISSING",
  "suggestion": "Initialize the project with init_project or repair_environment"
}
```

### Common Issues & Solutions

**UV Not Installed**:
> "How do I install uv?"

System provides platform-specific installation commands.

**Missing Dependencies**:
> "Why can't I import pandas?"
> "Sync the environment"

System detects and installs missing packages.

**Version Conflicts**:
> "Fix dependency conflicts"
> "Clear cache and sync environment"

System suggests clearing cache and updating lockfile.

**Corrupted Packages**:
> "Package installation is broken"
> "Clear cache for [package-name]"

System removes corrupted cache and reinstalls.

### Diagnostic Workflow

For any environment issue:

1. **Diagnose**: `> "Diagnose the environment"`
2. **Review Issues**: Check returned diagnostics
3. **Repair**: `> "Repair the environment"`
4. **Verify**: `> "Diagnose again"`

If issues persist:
- Clear cache: `> "Clear the package cache"`
- Update lockfile: `> "Update lockfile"`
- Sync environment: `> "Sync environment"`
