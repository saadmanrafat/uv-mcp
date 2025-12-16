---
title: Contributing
description: Guidelines for contributing to the UV-MCP project.
---

# Contributing

Thank you for your interest in improving UV-MCP. We follow standard open-source practices and use `uv` for all development workflows.

## Development Setup

### 1. Fork and Clone
Fork the repository to your GitHub account, then clone it locally:

```bash
git clone https://github.com/YOUR_USERNAME/uv-mcp.git
cd uv-mcp
```

### 2. Initialize Environment
Use `uv` to sync dependencies and set up the development virtual environment:

```bash
uv sync
```

This command reads `pyproject.toml` and installs all necessary dependencies, including dev tools like `pytest`.

## Testing

We prioritize reliability. Ensure all tests pass before submitting changes.

### Run All Tests
Execute the full test suite:

```bash
uv run pytest
```

### Targeted Testing
To test specific components (e.g., tool definitions):

```bash
uv run python test_tools.py
```

## Workflow for New Features

1.  **Branching**: Create a feature branch (`feat/new-tool` or `fix/bug-fix`).
2.  **Implementation**:
    -   Add core logic to `actions.py` or `diagnostics.py`.
    -   Expose the new capability in `server.py` using the `@mcp.tool()` decorator.
3.  **Documentation**: Update `src/content/docs/reference/tools.md` with the new API signature.
4.  **Verification**: Add a corresponding test case in `tests/`.

## Code Standards

-   **Type Safety**: All function signatures must include Python type hints.
-   **Formatting**: We adhere to PEP 8.
-   **Docstrings**: Public functions must include clear docstrings describing parameters and return values.

## Submitting a Pull Request

1.  Push your branch to your fork.
2.  Open a Pull Request against the `main` branch of the upstream repository.
3.  Provide a clear description of the problem solved and the solution implemented.
