# Changelog

All notable changes to UV-Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed `check_python_version` to correctly detect the project's Python version by running `uv run python --version` instead of reporting the MCP server's Python version.
- Fixed `check_dependencies` to correctly interpret `uv pip check` output, distinguishing between successful checks with no broken requirements and actual failures.
- Fixed race conditions and `await` errors in the test suite (`tests/test_uv_mcp.py`, `tests/test_diagnostics_context.py`).

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
