# UV-Agent Extension

UV-Agent is a powerful MCP server that helps you manage Python environments using `uv`, the fast Python package manager.

## Available Tools

You have access to the following tools for managing Python environments:

### 1. check_uv_installation
Check if `uv` is installed on the system and get version information.

**When to use:** Before performing any uv operations, or when troubleshooting environment issues.

### 2. install_uv
Get platform-specific installation instructions for `uv`.

**When to use:** When `uv` is not installed and the user needs to install it.

### 3. diagnose_environment
Perform a comprehensive health check of a Python environment.

**What it checks:**
- UV installation and version
- Project structure (pyproject.toml, requirements.txt)
- Virtual environment status
- Dependency health and conflicts
- Python version compatibility
- Lockfile presence

**When to use:** 
- User reports environment issues
- Before making changes to a project
- To understand the current state of a Python project
- When troubleshooting dependency problems

### 4. repair_environment
Automatically fix common Python environment issues.

**What it can fix:**
- Create virtual environment if missing
- Initialize new project with pyproject.toml
- Sync dependencies from lockfile
- Update outdated packages

**When to use:**
- After diagnosing issues with the environment
- When a project is missing critical files
- To set up a new development environment
- When dependencies are out of sync

**Parameters:**
- `project_path`: Optional path to project directory
- `auto_fix`: Set to `true` to automatically apply fixes (default: true)

### 5. add_dependency
Add new dependencies to a Python project.

**What it does:**
- Adds package to pyproject.toml
- Updates lockfile automatically
- Installs the package in the virtual environment

**When to use:**
- User wants to add a new package to their project
- Adding development dependencies
- Adding optional dependency groups

**Parameters:**
- `package`: Package name with optional version (e.g., "requests>=2.28.0")
- `project_path`: Optional path to project directory
- `dev`: Set to `true` for development dependencies
- `optional`: Optional dependency group name (e.g., "test", "docs")

### 6. remove_dependency
Remove a dependency from the project.

**What it does:**
- Removes package from pyproject.toml
- Updates lockfile automatically
- Uninstalls the package from the virtual environment

**When to use:**
- User wants to remove a package
- Cleaning up unused dependencies

**Parameters:**
- `package`: Package name (e.g., "requests")
- `project_path`: Optional path to project directory
- `dev`: Set to `true` to remove from development dependencies
- `optional`: Optional dependency group name

## Best Practices

1. **Always diagnose first**: Before attempting repairs, use `diagnose_environment` to understand what's wrong.

2. **Check uv installation**: If any tool fails, verify `uv` is installed using `check_uv_installation`.

3. **Be specific with versions**: When adding dependencies, encourage users to specify version constraints for reproducibility.

4. **Explain actions**: When using `repair_environment`, explain what repairs will be made before applying them.

5. **Verify after changes**: After repairs or adding dependencies, run `diagnose_environment` again to confirm the environment is healthy.

## Example Workflows

### Workflow 1: New Project Setup
1. Check if uv is installed (`check_uv_installation`)
2. Repair environment to initialize project (`repair_environment`)
3. Add initial dependencies (`add_dependency`)
4. Verify setup (`diagnose_environment`)

### Workflow 2: Troubleshooting Issues
1. Diagnose the environment (`diagnose_environment`)
2. Explain issues found to the user
3. Offer to repair (`repair_environment`)
4. Verify fixes worked (`diagnose_environment`)

### Workflow 3: Adding Dependencies
1. Check current project state (`diagnose_environment`)
2. Add requested packages (`add_dependency`)
3. Confirm successful installation

## Error Handling

- If `uv` is not installed, use `install_uv` to provide installation instructions
- If a project directory doesn't exist, inform the user clearly
- If repairs fail, explain the error and suggest manual steps
- Always provide context about what went wrong and how to fix it

## Notes

- All tools return JSON responses for easy parsing
- The `repair_environment` tool can be run in dry-run mode by setting `auto_fix=false`
- Virtual environments are created in `.venv` by default
- The tools automatically find the project root by searching for `pyproject.toml`
