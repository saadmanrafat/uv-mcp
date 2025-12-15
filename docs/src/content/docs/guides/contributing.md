---
title: Contributing
description: How to contribute to the UV-MCP open source project.
---

# Contributing

We welcome contributions! Whether you're fixing a bug, adding a new feature, or improving documentation, your help is appreciated.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork**:
    ```bash
    git clone https://github.com/your-username/uv-mcp
    cd uv-mcp
    ```
3.  **Install dependencies** using `uv`:
    ```bash
    uv sync
    ```

## Development Environment

We use `uv` for dependency management and `pytest` for testing.

### Running Tests

Run the test suite to ensure everything is working:

```bash
uv run pytest
```

Or run the specific tool test script:

```bash
uv run python test_tools.py
```

## Adding a New Tool

1.  **Define the Logic**: Add the implementation function in `src/uv_mcp/actions.py` or a new module.
2.  **Expose the Tool**: Add the `@mcp.tool()` decorator in `src/uv_mcp/server.py` and call your implementation.
3.  **Add Tests**: specific unit tests in `tests/`.
4.  **Update Documentation**: Add the tool to `docs/src/content/docs/reference/tools.md`.

## Pull Request Process

1.  Create a feature branch: `git checkout -b feature/my-cool-feature`.
2.  Commit your changes with clear messages.
3.  Push to your fork and submit a Pull Request.
4.  Wait for review!

## Code Style

-   Follow standard Python PEP 8 conventions.
-   Use type hints (`mypy` compatible).
-   Include docstrings for all public functions.