"""UV-Agent MCP Server - Main server implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .diagnostics import generate_diagnostic_report
from .uv_utils import (
    check_uv_available,
    check_virtual_env,
    find_uv_project_root,
    get_project_info,
    run_uv_command,
)

# Initialize FastMCP server
mcp = FastMCP("uv-mcp")


@mcp.tool()
def check_uv_installation() -> str:
    """
    Check if uv is installed and return version information.
    
    Returns:
        JSON string with installation status and version info
    """
    available, version = check_uv_available()
    
    result = {
        "installed": available,
        "version": version,
        "message": ""
    }
    
    if available:
        result["message"] = f"✓ uv is installed: {version}"
    else:
        result["message"] = "✗ uv is not installed"
        result["installation_instructions"] = {
            "linux_mac": "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "windows": "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"",
            "pip": "pip install uv",
            "docs": "https://docs.astral.sh/uv/getting-started/installation/"
        }
    
    return json.dumps(result, indent=2)


@mcp.tool()
def install_uv() -> str:
    """
    Provide installation instructions for uv.
    
    Note: This tool cannot automatically install uv for security reasons.
    It provides platform-specific installation instructions instead.
    
    Returns:
        JSON string with installation instructions
    """
    instructions = {
        "message": "uv installation instructions",
        "methods": {
            "standalone_installer": {
                "linux_mac": {
                    "command": "curl -LsSf https://astral.sh/uv/install.sh | sh",
                    "description": "Download and run the official installer script"
                },
                "windows": {
                    "command": "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"",
                    "description": "Download and run the official PowerShell installer"
                }
            },
            "pip": {
                "command": "pip install uv",
                "description": "Install via pip (requires Python already installed)"
            },
            "homebrew": {
                "command": "brew install uv",
                "description": "Install via Homebrew (macOS/Linux)"
            },
            "cargo": {
                "command": "cargo install --git https://github.com/astral-sh/uv uv",
                "description": "Build from source using Cargo (Rust)"
            }
        },
        "verification": {
            "command": "uv --version",
            "description": "Verify installation by checking the version"
        },
        "documentation": "https://docs.astral.sh/uv/getting-started/installation/"
    }
    
    return json.dumps(instructions, indent=2)


@mcp.tool()
def diagnose_environment(project_path: Optional[str] = None) -> str:
    """
    Analyze the health of a Python environment and project.
    
    This tool checks:
    - uv installation and version
    - Project structure (pyproject.toml, requirements.txt)
    - Virtual environment status
    - Dependency health and conflicts
    - Python version compatibility
    - Lockfile presence
    
    Args:
        project_path: Path to the project directory (defaults to current directory)
    
    Returns:
        JSON string with comprehensive diagnostic report
    """
    project_dir = Path(project_path) if project_path else Path.cwd()
    
    if not project_dir.exists():
        return json.dumps({
            "error": f"Project directory does not exist: {project_path}",
            "overall_health": "critical"
        }, indent=2)
    
    # Generate diagnostic report
    report = generate_diagnostic_report(project_dir)
    report["timestamp"] = datetime.now().isoformat()
    
    # Add summary
    issues_count = 0
    warnings_count = 0
    
    for section in ["structure", "dependencies", "python"]:
        if section in report:
            issues_count += len(report[section].get("issues", []))
            warnings_count += len(report[section].get("warnings", []))
    
    report["summary"] = {
        "overall_health": report["overall_health"],
        "issues_count": issues_count,
        "warnings_count": warnings_count
    }
    
    return json.dumps(report, indent=2)


@mcp.tool()
def repair_environment(project_path: Optional[str] = None, auto_fix: bool = True) -> str:
    """
    Attempt to repair common environment issues.
    
    This tool can:
    - Create a virtual environment if missing
    - Sync dependencies from lockfile
    - Initialize a new project with pyproject.toml
    - Update outdated packages
    
    Args:
        project_path: Path to the project directory (defaults to current directory)
        auto_fix: Whether to automatically apply fixes (default: True)
    
    Returns:
        JSON string with repair actions taken and results
    """
    project_dir = Path(project_path) if project_path else Path.cwd()
    
    if not project_dir.exists():
        return json.dumps({
            "error": f"Project directory does not exist: {project_path}",
            "success": False
        }, indent=2)
    
    # Check if uv is available
    available, version = check_uv_available()
    if not available:
        return json.dumps({
            "error": "uv is not installed. Please install uv first using the install_uv tool.",
            "success": False
        }, indent=2)
    
    results = {
        "project_dir": str(project_dir),
        "timestamp": datetime.now().isoformat(),
        "actions": [],
        "success": True
    }
    
    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root
        results["project_root"] = str(root)
    
    # Check for pyproject.toml
    if not (project_dir / "pyproject.toml").exists():
        if auto_fix:
            results["actions"].append({
                "action": "initialize_project",
                "description": "No pyproject.toml found, initializing new project"
            })
            
            success, stdout, stderr = run_uv_command(["init", "--no-readme"], cwd=project_dir)
            
            if success:
                results["actions"][-1]["status"] = "success"
                results["actions"][-1]["output"] = stdout
            else:
                results["actions"][-1]["status"] = "failed"
                results["actions"][-1]["error"] = stderr
                results["success"] = False
        else:
            results["actions"].append({
                "action": "initialize_project",
                "status": "skipped",
                "reason": "auto_fix is disabled"
            })
    
    # Check for virtual environment
    in_venv, venv_path = check_virtual_env()
    venv_exists = (project_dir / ".venv").exists()
    
    if not in_venv and not venv_exists:
        if auto_fix:
            results["actions"].append({
                "action": "create_venv",
                "description": "Creating virtual environment"
            })
            
            success, stdout, stderr = run_uv_command(["venv"], cwd=project_dir)
            
            if success:
                results["actions"][-1]["status"] = "success"
                results["actions"][-1]["output"] = "Virtual environment created at .venv"
            else:
                results["actions"][-1]["status"] = "failed"
                results["actions"][-1]["error"] = stderr
                results["success"] = False
        else:
            results["actions"].append({
                "action": "create_venv",
                "status": "skipped",
                "reason": "auto_fix is disabled"
            })
    
    # Sync dependencies if pyproject.toml exists
    if (project_dir / "pyproject.toml").exists():
        if auto_fix:
            results["actions"].append({
                "action": "sync_dependencies",
                "description": "Syncing project dependencies"
            })
            
            success, stdout, stderr = run_uv_command(["sync"], cwd=project_dir)
            
            if success:
                results["actions"][-1]["status"] = "success"
                results["actions"][-1]["output"] = "Dependencies synced successfully"
            else:
                results["actions"][-1]["status"] = "failed"
                results["actions"][-1]["error"] = stderr
                # Don't mark overall as failed, sync might fail for valid reasons
        else:
            results["actions"].append({
                "action": "sync_dependencies",
                "status": "skipped",
                "reason": "auto_fix is disabled"
            })
    
    return json.dumps(results, indent=2)


@mcp.tool()
def add_dependency(
    package: str,
    project_path: Optional[str] = None,
    dev: bool = False,
    optional: Optional[str] = None
) -> str:
    """
    Add a new dependency to the project.
    
    This tool uses 'uv add' to add a package to the project's dependencies.
    It automatically updates pyproject.toml and the lockfile.
    
    Args:
        package: Package name with optional version specifier (e.g., "requests" or "requests>=2.28.0")
        project_path: Path to the project directory (defaults to current directory)
        dev: Whether to add as a development dependency (default: False)
        optional: Optional dependency group name (e.g., "test", "docs")
    
    Returns:
        JSON string with operation results
    """
    project_dir = Path(project_path) if project_path else Path.cwd()
    
    if not project_dir.exists():
        return json.dumps({
            "error": f"Project directory does not exist: {project_path}",
            "success": False
        }, indent=2)
    
    # Check if uv is available
    available, version = check_uv_available()
    if not available:
        return json.dumps({
            "error": "uv is not installed. Please install uv first using the install_uv tool.",
            "success": False
        }, indent=2)
    
    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root
    
    # Check for pyproject.toml
    if not (project_dir / "pyproject.toml").exists():
        return json.dumps({
            "error": "No pyproject.toml found. Initialize a project first using repair_environment.",
            "success": False
        }, indent=2)
    
    # Build command
    cmd = ["add", package]
    
    if dev:
        cmd.append("--dev")
    
    if optional:
        cmd.extend(["--optional", optional])
    
    # Execute command
    success, stdout, stderr = run_uv_command(cmd, cwd=project_dir)
    
    result = {
        "package": package,
        "project_dir": str(project_dir),
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "dev": dev,
        "optional": optional
    }
    
    if success:
        result["message"] = f"Successfully added {package}"
        result["output"] = stdout
    else:
        result["message"] = f"Failed to add {package}"
        result["error"] = stderr
    
    return json.dumps(result, indent=2)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
