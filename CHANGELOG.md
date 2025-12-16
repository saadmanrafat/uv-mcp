# Changelog



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

[Unreleased]: https://github.com/saadmanrafat/uv-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/saadmanrafat/uv-mcp/releases/tag/v0.1.0
