# UV-Agent MCP Server

A Model Context Protocol (MCP) server for `uv` - the fast Python package manager. UV-Agent provides environment diagnostics, repair capabilities, and dependency management through a Gemini CLI extension.

## Features

UV-Agent exposes 5 powerful tools for managing Python environments:

### **check_uv_installation**
Check if `uv` is installed and get version information.

### **install_uv**
Get platform-specific installation instructions for `uv`.

### **diagnose_environment**
Comprehensive environment health check that analyzes:
- uv installation and version
- Project structure (pyproject.toml, requirements.txt)
- Virtual environment status
- Dependency health and conflicts
- Python version compatibility
- Lockfile presence

### **repair_environment**
Automatically fix common environment issues:
- Create virtual environment if missing
- Initialize new project with pyproject.toml
- Sync dependencies from lockfile
- Update outdated packages

### **add_dependency**
Add new dependencies to your project:
- Supports version specifications
- Development dependencies
- Optional dependency groups
- Automatic pyproject.toml and lockfile updates

## Installation

### Prerequisites

- Python 3.10 or higher
- `uv` package manager (will be checked/installed by the server)
- Gemini CLI

### Install from GitHub (Recommended)

```bash
# Install the latest stable version
gemini extensions install https://github.com/yourusername/uv-agent

# Install a specific version
gemini extensions install https://github.com/yourusername/uv-agent --ref=v0.1.0

# Install development version
gemini extensions install https://github.com/yourusername/uv-agent --ref=dev
```

After installation, restart your Gemini CLI session to activate the extension.

### Install from Local Directory (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/uv-agent
cd uv-agent

# Install dependencies
uv sync

# Link for development
gemini extensions link .
```

## Usage

### Running the Server

The server runs in stdio mode for MCP communication:

```bash
uv run uv-agent
```

### Configuration for Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "uv-agent": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/saadman/uv-mcp",
        "run",
        "uv-agent"
      ]
    }
  }
}
```

### Configuration for Gemini CLI Extension

UV-Agent can be installed as a Gemini CLI extension for seamless integration.

#### Install as Extension

```bash
# Navigate to the UV-Agent directory
cd /home/saadman/uv-mcp

# Link the extension to Gemini CLI
gemini extensions link .
```

After linking, restart your Gemini CLI session. The UV-Agent tools will be automatically available.

#### Uninstall Extension

```bash
# Unlink the extension
gemini extensions unlink uv-agent
```

#### Manual Configuration (Alternative)

If you prefer manual configuration, add this to your Gemini settings:

```json
{
  "mcpServers": {
    "uv-agent": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/saadman/uv-mcp",
        "run",
        "uv-agent"
      ]
    }
  }
}
```

## Example Workflows

### Diagnosing a Project

Ask your LLM:
> "Use uv-agent to diagnose my Python environment"

The agent will:
1. Check if uv is installed
2. Analyze project structure
3. Check dependencies for conflicts
4. Validate Python version
5. Report virtual environment status

### Repairing an Environment

Ask your LLM:
> "My Python environment is broken. Can you fix it?"

The agent will:
1. Create a virtual environment if needed
2. Initialize pyproject.toml if missing
3. Sync all dependencies
4. Report all actions taken

### Adding Dependencies

Ask your LLM:
> "Add requests and pytest as a dev dependency to my project"

The agent will:
1. Add requests to dependencies
2. Add pytest to dev dependencies
3. Update pyproject.toml
4. Update lockfile

## Tool Reference

### check_uv_installation()

Returns JSON with:
```json
{
  "installed": true,
  "version": "uv 0.5.0",
  "message": "✓ uv is installed: uv 0.5.0"
}
```

### install_uv()

Returns installation instructions for all platforms.

### diagnose_environment(project_path: Optional[str] = None)

**Parameters:**
- `project_path`: Path to project directory (optional, defaults to current directory)

**Returns:** Comprehensive diagnostic report with health status, issues, and warnings.

### repair_environment(project_path: Optional[str] = None, auto_fix: bool = True)

**Parameters:**
- `project_path`: Path to project directory (optional)
- `auto_fix`: Whether to automatically apply fixes (default: True)

**Returns:** List of actions taken and their results.

### add_dependency(package: str, project_path: Optional[str] = None, dev: bool = False, optional: Optional[str] = None)

**Parameters:**
- `package`: Package name with optional version (e.g., "requests>=2.28.0")
- `project_path`: Path to project directory (optional)
- `dev`: Add as development dependency (default: False)
- `optional`: Optional dependency group name (e.g., "test", "docs")

**Returns:** Operation result with success status and output.

## Development

### Project Structure

```
uv-mcp/
├── src/
│   └── uv_agent/
│       ├── __init__.py
│       ├── server.py          # Main MCP server
│       ├── uv_utils.py        # uv command utilities
│       └── diagnostics.py     # Environment diagnostics
├── gemini-extension.json      # Gemini CLI extension manifest
├── GEMINI.md                  # Extension instructions for AI
├── GEMINI_CLI_QUICKSTART.md   # Quick start guide
├── pyproject.toml
├── README.md
├── test_tools.py              # Verification test suite
└── .gitignore
```

### Testing

```bash
# Test uv detection
uv run python -c "from uv_agent.uv_utils import check_uv_available; print(check_uv_available())"

# Run the server
uv run uv-agent

# Test with MCP Inspector (if available)
npx @modelcontextprotocol/inspector uv run uv-agent
```

## Troubleshooting

### uv not found

If the server reports that `uv` is not installed:

1. Use the `install_uv` tool to get installation instructions
2. Install uv using your preferred method
3. Verify with `uv --version`

### Permission errors

If you encounter permission errors when creating virtual environments:

```bash
# Ensure you have write permissions in the project directory
chmod +w /path/to/project
```

### Import errors

If you see import errors for `tomllib`:

- Python 3.11+: `tomllib` is built-in
- Python 3.10: Install `tomli`: `uv add tomli`

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run python test_tools.py`
5. Submit a pull request

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Links

- [uv Documentation](https://docs.astral.sh/uv/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://gofastmcp.com/)
- [Gemini CLI Extensions](https://geminicli.com/docs/extensions/getting-started-extensions/)
