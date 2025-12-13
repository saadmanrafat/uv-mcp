# Troubleshooting Guide

## Common Issues

### Error: spawn uv ENOENT

**Problem**: When the MCP server starts, you see:
```
Error during discovery for server 'uv-mcp': Connection failed for 'uv-mcp': spawn uv ENOENT
```

**Root Cause**: The Gemini CLI cannot find the `uv` executable in its PATH when spawning the MCP server process.

**Solution**: The extension configuration now includes PATH environment setup. If you still see this error:

1. **Verify uv is installed**:
   ```bash
   which uv
   uv --version
   ```

2. **Check your uv installation location**:
   - Common locations: `~/.local/bin/uv`, `~/.cargo/bin/uv`, or `/usr/local/bin/uv`

3. **Ensure the extension has the latest config**:
   ```bash
   cd /path/to/uv-mcp
   git pull origin main
   gemini extensions unlink uv-mcp
   gemini extensions link .
   ```

4. **Restart Gemini CLI** after relinking the extension

The extension configuration automatically adds `~/.local/bin` to PATH, which is where `uv` is typically installed.

---

## Installation Issues

### EACCES: permission denied, mkdtemp '/tmp/gemini-extension...'

**Problem**: When running `gemini extensions install https://github.com/saadmanrafat/uv-mcp`, you get:
```
EACCES: permission denied, mkdtemp '/tmp/gemini-extensionXXXXXX'
```

**Root Cause**: This is a known issue with the Gemini CLI where it fails to create temporary directories in `/tmp` on some Linux systems, even when permissions are correct.

**Solution 1: Use TMPDIR environment variable** (Recommended for installation from GitHub)

```bash
# Create a user-specific temp directory
mkdir -p ~/.tmp

# Install using the custom temp directory
TMPDIR=$HOME/.tmp gemini extensions install https://github.com/saadmanrafat/uv-mcp
```

**Solution 2: Use local linking** (Recommended for development)

If you have the repository cloned locally:

```bash
cd /path/to/uv-mcp
gemini extensions link .
```

This approach:
- Avoids the temp directory issue entirely
- Is better for development (changes reflect immediately)
- Doesn't require downloading from GitHub

**Permanent Fix**: Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export TMPDIR=$HOME/.tmp
```

Then restart your shell or run `source ~/.bashrc`.

## Extension Name Mismatch

If you installed from GitHub before the rename was pushed, you might see "uv-agent" instead of "uv-mcp". To fix:

```bash
# Uninstall the old extension
gemini extensions uninstall uv-agent

# Reinstall with the new name (after changes are pushed to GitHub)
TMPDIR=$HOME/.tmp gemini extensions install https://github.com/saadmanrafat/uv-mcp
```

Or use the local link method:

```bash
gemini extensions unlink uv-agent
cd /path/to/uv-mcp
gemini extensions link .
```

## Verification

After installation, verify the extension is working:

```bash
# List installed extensions
gemini extensions list

# Test the tools (in a Gemini CLI session)
# Ask: "Check if uv is installed"
# Ask: "What UV-MCP tools are available?"
```

## Additional Issues

### Tools not available after installation

1. **Restart Gemini CLI**: Close and reopen your Gemini CLI session
2. **Check extension status**: Run `gemini extensions list` to ensure it's enabled
3. **Check logs**: Look for errors in the Gemini CLI output

### uv not found

The extension requires `uv` to be installed on your system. Install it using:

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

Then ask the extension: "Check if uv is installed" to verify.

## Getting Help

If you encounter other issues:

1. Check the [README.md](README.md) for general usage information
2. Review [CONTRIBUTING.md](CONTRIBUTING.md) for development setup
3. Open an issue on [GitHub](https://github.com/saadmanrafat/uv-mcp/issues)
