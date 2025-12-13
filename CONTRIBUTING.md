# Contributing to UV-Agent

Thank you for your interest in contributing to UV-Agent! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- `uv` package manager
- Git
- Gemini CLI (for testing)

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/saadmanrafat/uv-mcp
   cd uv-mcp
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Link the extension for development**:
   ```bash
   gemini extensions link .
   ```

4. **Run tests**:
   ```bash
   uv run python test_tools.py
   ```

## Development Workflow

### Making Changes

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes in the appropriate files:
   - `src/uv_mcp/server.py` - MCP server and tools
   - `src/uv_mcp/uv_utils.py` - UV utility functions
   - `src/uv_mcp/diagnostics.py` - Environment diagnostics

3. Test your changes:
   ```bash
   uv run python test_tools.py
   ```

4. Update documentation if needed:
   - `README.md` - Main documentation
   - `GEMINI.md` - AI instructions
   - `CHANGELOG.md` - Add entry under [Unreleased]

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions
- Keep functions focused and single-purpose

### Testing

All changes should include tests. Add test cases to `test_tools.py` or create new test files as needed.

```bash
# Run all tests
uv run python test_tools.py

# Test the MCP server
uv run uv-mcp
```

## Submitting Changes

### Pull Request Process

1. **Update the changelog**:
   Add your changes to `CHANGELOG.md` under the `[Unreleased]` section.

2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test additions/changes
   - `refactor:` - Code refactoring

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request**:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template

### PR Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Ensure all tests pass
- Update documentation as needed
- Keep PRs focused on a single feature/fix

## Adding New Tools

To add a new MCP tool:

1. **Define the tool in `server.py`**:
   ```python
   @mcp.tool()
   def your_tool_name(param: str) -> str:
       """
       Tool description.
       
       Args:
           param: Parameter description
           
       Returns:
           JSON string with results
       """
       # Implementation
       return json.dumps(result, indent=2)
   ```

2. **Add utility functions** in `uv_utils.py` or `diagnostics.py`

3. **Update `GEMINI.md`** with tool usage instructions

4. **Add tests** in `test_tools.py`

5. **Update `README.md`** with tool documentation

## Reporting Issues

### Bug Reports

When reporting bugs, please include:
- UV-Agent version
- Python version
- UV version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

For feature requests, please describe:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered
- How it benefits other users

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn and grow

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Review the documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to UV-Agent! 🚀
