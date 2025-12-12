# UV-Agent Gemini CLI Extension - Quick Start

## Installation

### Step 1: Navigate to the extension directory

```bash
cd /home/saadman/uv-mcp
```

### Step 2: Link the extension to Gemini CLI

```bash
gemini extensions link .
```

When prompted, type `Y` to confirm the installation.

### Step 3: Restart Gemini CLI

After linking, restart your Gemini CLI session for the changes to take effect.

## Verification

The UV-Agent tools should now be available in your Gemini CLI session. You can verify by asking:

- "Check if uv is installed"
- "Diagnose my Python environment"
- "What UV-Agent tools are available?"

## Available Tools

1. **check_uv_installation** - Check if uv is installed
2. **install_uv** - Get installation instructions for uv
3. **diagnose_environment** - Comprehensive environment health check
4. **repair_environment** - Automatically fix environment issues
5. **add_dependency** - Add dependencies to your project

## Uninstallation

To remove the extension:

```bash
gemini extensions unlink uv-agent
```

## Usage Examples

### Example 1: Check Environment Health
```
User: "Diagnose my Python environment"
```

### Example 2: Fix Broken Environment
```
User: "My Python environment is broken, can you fix it?"
```

### Example 3: Add Dependencies
```
User: "Add requests and pytest as a dev dependency"
```

## Troubleshooting

### Extension not found
Make sure you're in the correct directory (`/home/saadman/uv-mcp`) when running the link command.

### Tools not available
Restart your Gemini CLI session after linking the extension.

### uv not installed
Use the `install_uv` tool to get platform-specific installation instructions.

## More Information

See [README.md](README.md) for complete documentation.
