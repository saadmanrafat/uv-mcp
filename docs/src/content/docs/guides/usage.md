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

## Build & Distribution (v0.6.4+)

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

## Error Handling & Troubleshooting (v0.6.4+)

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
