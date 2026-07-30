# Changelog

## [Unreleased]

### Security
- **Workspace root enforcement**: All `project_path` arguments are now validated against `UV_MCP_WORKSPACE_ROOT` (when set) via new `resolve_project_path()` and `assert_within_workspace()` helpers in `utils.py`. Paths that resolve outside the configured root are rejected before any subprocess is spawned.
- **Output path boundary checks**: `uv_build_project` (`output_dir`), `uv_export_requirements` (`output_file`), and `uv_pip_compile` (`input_file`, `output_file`) now resolve output paths relative to the project directory and validate them against the workspace root, preventing arbitrary file writes.
- **Export format allowlist**: `export_requirements` now rejects unknown `file_format` values; only `requirements-txt` and `pylock` are accepted.
- **Package name validation**: A shared `validate_package_name()` function (centralised in `utils.py`) rejects malformed package names across `uv_run_ephemeral_tool`, `uv_tool_install`, `uv_tool_upgrade`, `uv_tool_uninstall`, and `with_packages` in `uv_run_script`.
- **Tool allowlist**: `UV_MCP_ALLOWED_TOOLS` environment variable (comma-separated) restricts which packages may be run or installed via `uv_run_ephemeral_tool`, `uv_tool_install`, and `uv_tool_upgrade`.
- **Project name validation**: `uv_initialize_project` now rejects names containing path separators or `..` traversal sequences, and validates `python_version` format before any filesystem operation.

### Added
- VS Code (GitHub Copilot) and Cursor client configuration instructions in installation docs, including step-by-step new-user setup and per-project one-liner commands.
- `UV_MCP_ALLOWED_TOOLS` declared as a configurable setting in `gemini-extension.json`.
- Security configuration section in `docs/guides/installation.md` documenting both `UV_MCP_WORKSPACE_ROOT` and `UV_MCP_ALLOWED_TOOLS`.

### Fixed
- Three pre-existing test failures on macOS caused by `/var` → `/private/var` symlink resolution; assertions now compare against `.resolve()` output consistently.

---

## [1.0.0] - 2026-05-16

### The Stop Shop Release — 100% uv CLI Coverage

This release expands UV-MCP from **22 → 45 MCP tools**, covering every command exposed by `uv --help`.

### Added (23 New Tools)

- **Virtual Environment**: `uv_create_venv` (`uv venv`) with `--seed`, `--relocatable`, `--clear`, `--system-site-packages`
- **Script Execution**: `uv_run_script` (`uv run`) with temporary `--with` dependency injection
- **Project Lifecycle**: `uv_project_version` (`uv version`), `uv_format_code` (`uv format`)
- **Pip Compatibility**: `uv_pip_compile`, `uv_pip_sync_requirements`, `uv_pip_freeze`, `uv_pip_install`, `uv_pip_uninstall`
- **Tool Management**: `uv_tool_install`, `uv_tool_upgrade`, `uv_tool_list`, `uv_tool_uninstall`
- **Cache Introspection**: `uv_prune_cache`, `uv_cache_dir`, `uv_cache_size`
- **Python Management**: `uv_find_python`, `uv_python_dir`, `uv_upgrade_python_version`, `uv_uninstall_python_version`
- **Publishing**: `uv_publish_project` (`uv publish`) with `--dry-run`
- **Self Management**: `uv_self_update`, `uv_self_version`

### New Pydantic Models

`VenvResult`, `ScriptRunResult`, `VersionResult`, `FormatResult`, `PipCompileResult`, `PipSyncResult`, `PipFreezeResult`, `ToolListResult`, `CacheInfoResult`, `PublishResult`, `SelfUpdateResult`

### Metrics
- **Total MCP Tools**: 45 (100% of uv CLI surface area)
- **Breaking Changes**: 0
- **Test Status**: 138 passed, 1 skipped

---

## [0.8.0] - 2026-05-16

### Added
- **Ephemeral Tool Runner**: New `uv_run_ephemeral_tool` MCP tool executing commands via `uv tool run` (`uvx` proxy)
  - Package name + command arguments -> stdout/stderr with typed `EphemeralToolResult`
- **Workspace Introspection**: New `uv_get_workspace_manifest` MCP tool for monorepo / microservice configurations
  - Parses `tool.uv.workspace.members` from `pyproject.toml`
  - Returns `WorkspaceManifest` with root, members, and dependencies
- **Self-Healing Diagnostics**: New `uv_self_heal_environment` wrapper tool
  - Captures `ModuleNotFoundError` and layout exceptions via regex
  - Automatically triggers `uv sync` and returns `SelfHealingDiagnostics` remedy payload
- **ANSI-Free Output**: Subprocess environment now injects `UV_COLOR=never` and `TERM=dumb` unconditionally
- **Concurrency Lockfile Protection**: `asyncio.Lock()` serializes mutating uv commands (`add`, `remove`, `sync`, `lock`) to prevent `uv.lock` deadlocks
- **Absolute Path Resolution**: All tool schemas now enforce `.resolve()` on user-provided `project_path`, eliminating relative path drift
- **New Models**: `EphemeralToolResult`, `WorkspaceManifest`, `WorkspaceMember`, `SelfHealingDiagnostics`, `HealingAction`

### Fixed
- **Docker Health Check**: Updated async invocation to match renamed `utils` module (was `uv_utils`)
- **Type Safety**: Docker label version bump to 0.8.0; `mypy --strict` now passes on entire `src/uv_mcp`

### Changed
- `ProjectTools` refactored to return strict Pydantic models (`ProjectInitResult`, `SyncResult`, `ExportResult`) instead of raw strings
- `pyproject.toml` and `__init__.py` synchronized to `0.8.0`

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

### Added
- **Cache Management**: New `uv_clear_cache` tool to clear uv package cache (all or specific packages)
  - Helps resolve corrupted package issues
  - Free up disk space
  - Returns detailed operation results with `CacheOperationResult` model
- **Lock Management**: New `uv_lock_project` tool to update lockfile without syncing environment
  - Update uv.lock after manual pyproject.toml edits
  - Ensure lockfile consistency
  - Prepare projects for deployment
- **Build Tool**: New `uv_build_project` tool to build distributable packages
  - Create wheel and source distributions
  - Support custom output directories
  - Returns list of created artifacts
  - Ready for PyPI publishing workflow
- **Enhanced Error Handling**: New `errors.py` module with comprehensive error management
  - 7 custom exception classes with actionable suggestions (`UVMCPError`, `UVNotInstalledError`, `ProjectNotFoundError`, etc.)
  - Smart error suggestion engine (`get_error_suggestion()`) that parses stderr
  - Error codes for programmatic handling (UV_NOT_FOUND, PYPROJECT_MISSING, etc.)
  - Context-aware help for common issues (network, permissions, conflicts, etc.)
- **Comprehensive Edge Case Tests**: New `test_edge_cases.py` suite with 56 tests
  - Command execution boundaries (empty output, large data, special characters, concurrent ops)
  - Project info parsing (symlinks, circular refs, large files, unusual names)
  - Virtual environment detection (missing configs, broken symlinks, multiple candidates)
  - Project root finding (deep nesting, multiple pyprojects, permission handling)
  - Dependency operations (complex versions, package name variations)
  - Environment repair scenarios (UV missing, auto-fix disabled, partial failures)
  - Python version management (empty output, exotic versions, malformed data)
  - Cache operations (special characters, concurrent operations)
  - Error suggestions (empty errors, long messages, multiple patterns)
  - Diagnostics edge cases (empty dirs, corrupted files, missing dependencies)
  - Boundary conditions (name lengths, dependency sizes, special paths)
  - Race conditions (concurrent operations, parallel reports)
  - Error recovery (retry after timeout, broken state recovery)
  - Memory & performance (1000+ dependencies, 10MB+ output)
  - Platform-specific (Windows paths, Unicode paths)

### Fixed
- Fixed pytest async marker warnings in `test_utils_extended.py`
- Fixed `CacheOperationResult` model to have proper default values
- All 134 tests now pass cleanly (133 passed, 1 intentionally skipped)

### Changed
- Updated `clear_cache_action` to use new `CacheOperationResult` model structure
- Enhanced server.py with 3 new MCP tools
- Improved test coverage to 85%+ on critical modules

### Technical Details
- Total MCP tools: 19 (3 new)
- Test suite: 134 tests (56 new edge cases)
- Execution time: ~2.5 seconds
- Code coverage: 87-100% on new modules
- 100% backward compatible
- Zero breaking changes

## [0.6.1] - 2025-12-16

### Added
- **Dependency Inspection**: Added a suite of tools for deep dependency analysis:
    - `list_dependencies`: Lists all installed packages in the project's environment.
    - `show_package_info`: Retrieves detailed metadata for a specific package.
    - `check_outdated_packages`: Identifies packages that have newer versions available.
    - `analyze_dependency_tree`: Visualizes the dependency tree to understand package relationships.

### Fixed
- **Environment Isolation**: Fixed critical bug where `uv pip` commands were inspecting the MCP server's own environment instead of the target project's virtual environment. All tools now explicitly target the project's venv.
- **Test Isolation**: Improved test suite to prevent environment leakage between tests and the host system.

## [0.5.3] - 2025-12-16

### Fixed
- Fixed GitHub Actions CI/CD workflow syntax error affecting release creation.
- Ensured proper release asset upload by using a fresh tag.

## [0.5.2] - 2025-12-16

### Refactor
- **Modern Python**: Updated codebase to use modern Python features and type hints (Python 3.10+ style).
- **File Renaming**: Renamed `uv_utils.py` to `utils.py` and `project_tools.py` to `tools.py` for standard conventions.
- **Pydantic Integration**: Implemented Pydantic models for all tool inputs and outputs, ensuring robust type safety and structured responses.
- **Error Handling**: Introduced a custom exception hierarchy (`UVError`, `UVCommandError`, `UVTimeoutError`) for better error management.
- **Code Structure**: Decomposed complex functions in `actions.py` into smaller, readable helper functions.

### Changed
- Default Python version for `init_project` is now 3.12.
- Updated all internal imports to reflect file renaming.

## [0.5.0] - 2025-12-15

### Documentation
- Added comprehensive user documentation powered by Astro Starlight.
- Added Usage Guide, Installation Guide, Architecture Overview, and Tool Reference.
- Enabled search functionality in the documentation site.

### Changed
- Removed unicode characters (emojis) from tool output messages for better compatibility.
- Improved error handling in `project_tools.py` with `try-except` blocks.
- Fixed typo in `init_project` method name.
- Updated documentation build workflow to prevent concurrent deployment conflicts.

## [0.4.0] - 2025-12-14

### Added
- `remove_dependency` tool - Remove packages from pyproject.toml and the environment.
- `install_python` action in `repair_environment` - Automatically installs the required Python version if missing.
- Tests for `remove_dependency` and improved test coverage.

### Fixed
- Fixed `check_python_version` to correctly detect the project's Python version.
- Fixed `check_dependencies` to correctly interpret `uv pip check` output.
- Fixed race conditions and `await` errors in the test suite.

## [0.1.0] - 2025-12-13

### Added
- Initial release of UV-Agent MCP server
- `check_uv_installation` tool - Check if uv is installed and get version info
- `install_uv` tool - Get platform-specific installation instructions
- `diagnose_environment` tool - Comprehensive environment health check
- `repair_environment` tool - Automatically fix common environment issues
- `add_dependency` tool - Add dependencies to Python projects
- Gemini CLI extension support with `gemini-extension.json`
- AI instruction file (`GEMINI.md`) for optimal tool usage
- Comprehensive test suite with 5 verification tests
- Full documentation (README, Quick Start Guide)
- Example MCP configuration for Claude Desktop

### Features
- Automatic project root detection
- Virtual environment management
- Dependency conflict detection
- Python version compatibility checking
- Lockfile synchronization
- JSON-formatted responses for all tools

### Technical Details
- Built with FastMCP 2.14.0
- Python 3.10+ support
- UV 0.6.16 compatibility
- 86 dependencies installed and tested
- All tests passing

[Unreleased]: https://github.com/saadmanrafat/uv-mcp/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/saadmanrafat/uv-mcp/compare/v0.8.0...v1.0.0
[0.8.0]: https://github.com/saadmanrafat/uv-mcp/compare/v0.7.2...v0.8.0
[0.7.2]: https://github.com/saadmanrafat/uv-mcp/compare/v0.6.4...v0.7.2
[0.6.4]: https://github.com/saadmanrafat/uv-mcp/compare/v0.6.1...v0.6.4
[0.6.1]: https://github.com/saadmanrafat/uv-mcp/compare/v0.5.3...v0.6.1
[0.5.3]: https://github.com/saadmanrafat/uv-mcp/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/saadmanrafat/uv-mcp/compare/v0.5.0...v0.5.2
[0.5.0]: https://github.com/saadmanrafat/uv-mcp/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/saadmanrafat/uv-mcp/compare/v0.1.0...v0.4.0
[0.1.0]: https://github.com/saadmanrafat/uv-mcp/releases/tag/v0.1.0
