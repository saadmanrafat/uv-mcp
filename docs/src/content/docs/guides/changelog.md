---
title: Changelog
description: Release history and version updates for UV-MCP.
---

# Changelog

## [0.8.0] - 2026-05-16

### Added
- **Ephemeral Tool Runner (`uvx` proxy)**: `uv_run_ephemeral_tool(package, command)` executes ephemeral tools via `uv tool run --from <pkg>` with typed `EphemeralToolResult`.
- **Workspace Introspection Engine**: `uv_get_workspace_manifest()` parses `[tool.uv.workspace]` members from `pyproject.toml` and returns a `WorkspaceManifest` with topological dependency graph.
- **Self-Healing Diagnostics Handler**: `uv_self_heal_environment()` captures `ModuleNotFoundError` signatures via regex, triggers `uv sync`, and yields per-package `uv add <pkg>` recommendations in a `SelfHealingDiagnostics` payload.
- **ANSI-Free Subprocess Environment**: All `uv` invocations now unconditionally inject `UV_COLOR=never` and `TERM=dumb` to guarantee clean, parseable streams.
- **Concurrency Lockfile Gate**: `asyncio.Lock()` serializes mutating commands (`add`, `remove`, `sync`, `lock`) to prevent `uv.lock` deadlocks under concurrent MCP tool calls.
- **Absolute Path Resolution**: Every `project_path` input is normalized with `Path.resolve()` before being passed to `uv --directory`.
- **New Pydantic Models**: `EphemeralToolResult`, `WorkspaceManifest`, `WorkspaceMember`, `SelfHealingDiagnostics`, `HealingAction`.

### Fixed
- **Docker Health Check** updated to use `uv_mcp.utils` (previously referenced non-existent `uv_mcp.uv_utils`).
- **Docker image label** bumped to `0.8.0`.
- **Type safety**: `errors.py` and `server.py` tightened for `--strict` compliance.

### Changed
- `ProjectTools` refactored from raw `str` returns to strictly typed Pydantic models (`ProjectInitResult`, `SyncResult`, `ExportResult`).

---

## [0.7.2] - 2026-02-07

### Added
- **Configuration Module**: Centralized `config.py` for timeouts, limits, and retry policies.
- **Concurrency Limits**: `MAX_CONCURRENT_COMMANDS` prevents resource exhaustion.
- **Core Utilities**: Improved `validate_project_path` and `check_uv_available` (zombie process fix).
- **Output Limits**: Truncation for large dependency trees and sync outputs to avoid MCP payload limits.
- **Docstrings**: Added comprehensive docstrings with examples to all actions.
- **Tests**: New `test_error_paths.py` covering edge cases and missing files.

### Fixed
- **Resource Leaks**: Fixed zombie processes in `check_uv_available`.
- **Timeouts**: Fixed cascading timeouts in `run_uv_command`.
- **Bug Fixes**:
    - Fixed `KeyError` in `show_package_info`.
    - Fixed list slicing in `list_dependencies`.
    - Fixed logic in `check_dependencies` regarding return codes.
    - Fixed validation in `check_outdated_packages`.
- **Safety**: Added rigorous project path validation across all tools.

## [0.6.4] - 2025-12-28

### Major Release

This release adds powerful new build and cache management tools, comprehensive error handling, and extensive edge case testing.

### New Features

#### Build & Distribution Tools

- **`build_project`**: Build wheel and source distributions
  ```python
  result = await build_project(wheel=True, sdist=True)
  # Creates dist/myapp-0.1.0.tar.gz and .whl files
  ```

- **`lock_project`**: Update lockfile without syncing environment
  ```python
  await lock_project()  # Updates uv.lock only
  ```

- **`clear_cache`**: Clear UV package cache
  ```python
  await clear_cache()  # Clear entire cache
  await clear_cache(package="requests")  # Clear specific package
  ```

#### Enhanced Error Handling

- **7 Custom Exception Classes**: Structured errors with error codes
  - `UVNotInstalledError` - UV not found
  - `ProjectNotFoundError` - Missing project directory
  - `PyProjectNotFoundError` - No pyproject.toml
  - `DependencyConflictError` - Version conflicts
  - `VirtualEnvMissingError` - Missing .venv
  - `PackageNotFoundError` - Package not in PyPI
  - `InvalidPythonVersionError` - Python version issues

- **Smart Error Suggestions**: Context-aware help messages
  ```json
  {
    "error": "uv is not installed",
    "error_code": "UV_NOT_FOUND",
    "suggestion": "Install uv using: curl -LsSf https://astral.sh/uv/install.sh | sh"
  }
  ```

- **Error Suggestion Engine**: Automatically parses stderr and provides actionable advice

#### Comprehensive Testing

- **56 New Edge Case Tests** covering:
  - Command execution boundaries (empty output, large data, special characters)
  - Concurrent operations and race conditions
  - Platform variations (Windows/Unix paths, Unicode)
  - Error recovery scenarios
  - Memory and performance (1000+ dependencies, 10MB+ output)
  - Boundary conditions (name lengths, dependency sizes)

### Bug Fixes

- Fixed pytest async marker warnings in test suite
- Fixed `CacheOperationResult` model default values
- All 134 tests now pass cleanly (133 passed, 1 intentionally skipped)

### Documentation

Added 6 comprehensive documentation files:
- `IMPROVEMENTS.md` - Technical changelog
- `SUMMARY.md` - Executive overview
- `QUICK_REFERENCE.md` - Usage guide
- `TEST_REPORT.md` - Test documentation
- `NAMING_CONVENTIONS.md` - MCP naming compliance
- `FINAL_SUMMARY.md` - Complete project report

### Metrics

- **Total MCP Tools**: 19 (↑ 3 new)
- **Total Tests**: 134 (↑ 56 new)
- **Pass Rate**: 99.3%
- **Test Execution**: ~2.5 seconds
- **Code Coverage**: 85%+ on critical modules
- **Breaking Changes**: 0 (100% backward compatible)

---

## [0.6.1] - 2025-12-16

### Added

- **Dependency Inspection Suite**: Deep dependency analysis tools
  - `list_dependencies`: List all installed packages
  - `show_package_info`: Detailed package metadata
  - `check_outdated_packages`: Find packages with updates available
  - `analyze_dependency_tree`: Visualize dependency relationships

### Fixed

- **Environment Isolation**: Fixed bug where `uv pip` inspected wrong environment
- **Test Isolation**: Improved test suite isolation from host system

---

## [0.5.3] - 2025-12-16

### Fixed

- GitHub Actions CI/CD workflow syntax error
- Release asset upload process

---

## [0.5.2] - 2025-12-16

### Refactor

- **Modern Python**: Updated to Python 3.10+ style with type hints
- **File Renaming**: Standardized naming (`uv_utils.py` → `utils.py`)
- **Pydantic Integration**: All inputs/outputs use Pydantic models
- **Error Handling**: Custom exception hierarchy
- **Code Structure**: Decomposed complex functions for readability

### Changed

- Default Python version: 3.12
- Updated all imports for new file structure

---

## [0.5.0] - 2025-12-15

### Documentation

- Comprehensive docs powered by Astro Starlight
- Usage guide, installation guide, architecture overview
- Tool reference documentation
- Search functionality

### Changed

- Removed unicode emojis for better compatibility
- Improved error handling in project tools
- Fixed typos and improved documentation workflow

---

## [0.4.0] - 2025-12-14

### Added

- `remove_dependency` tool
- Auto-install Python in `repair_environment`
- Comprehensive test coverage

### Fixed

- `check_python_version` detection
- `check_dependencies` output parsing
- Race conditions in test suite

---

## [0.1.0] - 2025-12-13

### Initial Release

- Core tools: check, install, diagnose, repair, add
- Gemini CLI extension support
- Comprehensive test suite
- Full documentation
- Example configurations

### Features

- Automatic project root detection
- Virtual environment management
- Dependency conflict detection
- Python version compatibility
- Lockfile synchronization
- JSON-formatted responses

---

## Version Comparison Links

- [Unreleased](https://github.com/saadmanrafat/uv-mcp/compare/v0.8.0...HEAD)
- [0.8.0](https://github.com/saadmanrafat/uv-mcp/compare/v0.7.2...v0.8.0)
- [0.7.2](https://github.com/saadmanrafat/uv-mcp/compare/v0.6.4...v0.7.2)
- [0.6.4](https://github.com/saadmanrafat/uv-mcp/compare/v0.6.1...v0.6.4)
- [0.6.1](https://github.com/saadmanrafat/uv-mcp/compare/v0.5.3...v0.6.1)
- [0.5.3](https://github.com/saadmanrafat/uv-mcp/compare/v0.5.2...v0.5.3)
- [0.5.2](https://github.com/saadmanrafat/uv-mcp/compare/v0.5.0...v0.5.2)
- [0.5.0](https://github.com/saadmanrafat/uv-mcp/compare/v0.4.0...v0.5.0)
- [0.4.0](https://github.com/saadmanrafat/uv-mcp/compare/v0.1.0...v0.4.0)
- [0.1.0](https://github.com/saadmanrafat/uv-mcp/releases/tag/v0.1.0)
