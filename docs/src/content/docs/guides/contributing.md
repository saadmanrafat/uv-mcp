---
title: Contributing
description: Guide for contributing to UV-MCP
---

# Contributing

Thank you for your interest in contributing to UV-Agent! We welcome contributions from the community.

## Development Setup

1.  **Fork and clone the repository**:
    ```bash
    git clone https://github.com/saadmanrafat/uv-mcp
    cd uv-mcp
    ```

2.  **Install dependencies**:
    We use `uv` for dependency management.
    ```bash
    uv sync
    ```

3.  **Link for Gemini CLI (Optional)**:
    If you are developing for Gemini CLI, you can link your local version:
    ```bash
    gemini extensions link .
    ```

## Running Tests

We use `pytest` for our test suite. All changes must pass existing tests, and new features should include new tests.

```bash
# Run the full test suite
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=uv_mcp
```

## Making Changes

1.  **Create a Branch**: Always work on a feature branch (`feat/new-tool`, `fix/bug-name`).
2.  **Edit Code**:
    *   `src/uv_mcp/server.py`: Add new tool definitions here.
    *   `src/uv_mcp/actions.py`: Implement the logic here.
3.  **Add Tests**: Update `tests/` with unit tests for your changes.
4.  **Verify**: Run `uv run pytest` to ensure no regressions.

## Submitting a Pull Request

1.  Push your branch to your fork.
2.  Open a Pull Request against the `main` branch.
3.  Describe your changes clearly in the PR description.
4.  Ensure the CI/CD pipeline passes.

## Style Guide

*   Follow PEP 8 guidelines.
*   Use type hints for all function arguments and return values.
*   Include docstrings (Google style or standard) for all public functions.
*   Keep functions small and focused on a single task.
