"""UV-Agent MCP Server - Main server implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

from .diagnostics import generate_diagnostic_report
from .actions import (
    repair_environment_action,
    add_dependency_action,
    check_uv_installation_action,
    get_install_instructions_action
)

# Initialize FastMCP server
mcp = FastMCP("uv-mcp")


def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """
    Safely serialize object to JSON string with error handling.
    
    Args:
        obj: Object to serialize
        indent: Indentation level for pretty printing
        
    Returns:
        JSON string representation of the object
    """
    try:
        return json.dumps(obj, indent=indent, default=str)
    except (TypeError, ValueError) as e:
        # Fallback: convert problematic values to strings
        error_msg = {
            "error": "JSON serialization failed",
            "details": str(e),
            "data": str(obj)
        }
        return json.dumps(error_msg, indent=indent)


@mcp.tool()
async def check_uv_installation() -> str:
    """
    Check if uv is installed and return version information.
    
    Returns:
        JSON string with installation status and version info
    """
    result = await check_uv_installation_action()
    return safe_json_dumps(result)


@mcp.tool()
async def install_uv() -> str:
    """
    Provide installation instructions for uv.
    
    Note: This tool cannot automatically install uv for security reasons.
    It provides platform-specific installation instructions instead.
    
    Returns:
        JSON string with installation instructions
    """
    result = get_install_instructions_action()
    return safe_json_dumps(result)


@mcp.tool()
async def diagnose_environment(project_path: Optional[str] = None) -> str:
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
        return safe_json_dumps({
            "error": f"Project directory does not exist: {project_path}",
            "overall_health": "critical"
        })
    
    # Generate diagnostic report
    report = await generate_diagnostic_report(project_dir)
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
    
    return safe_json_dumps(report)


@mcp.tool()
async def repair_environment(project_path: Optional[str] = None, auto_fix: bool = True) -> str:
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
    results = await repair_environment_action(project_path, auto_fix)
    return safe_json_dumps(results)


@mcp.tool()
async def add_dependency(
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
    result = await add_dependency_action(package, project_path, dev, optional)
    return safe_json_dumps(result)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
