"""UV-Agent MCP Server - Main server implementation."""

import logging
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

from .actions import (
    add_dependency_action,
    check_uv_installation_action,
    get_install_instructions_action,
    remove_dependency_action,
    repair_environment_action,
)
from .diagnostics import generate_diagnostic_report
from .models import (
    DependencyOperationResult,
    DiagnosticReport,
    DiagnosticReportSummary,
    InstallInstructions,
    RepairResult,
    UVCheckResult,
)
from .tools import ProjectTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uv-mcp")

# Initialize FastMCP server
mcp = FastMCP("uv-mcp")


@mcp.tool()
async def check_uv_installation() -> UVCheckResult:
    """
    Check if uv is installed and return version information.

    Returns:
        UVCheckResult with installation status and version info
    """
    return await check_uv_installation_action()


@mcp.tool()
async def install_uv() -> InstallInstructions:
    """
    Provide installation instructions for uv.

    Note: This tool cannot automatically install uv for security reasons.
    It provides platform-specific installation instructions instead.

    Returns:
        InstallInstructions with installation instructions
    """
    return get_install_instructions_action()


@mcp.tool()
async def diagnose_environment(project_path: str | None = None) -> DiagnosticReport:
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
        DiagnosticReport with comprehensive diagnostic report
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        return DiagnosticReport(
            project_dir=str(project_path or "."),
            overall_health="critical",
            critical_issues=[f"Project directory does not exist: {project_path}"],
        )

    # Generate diagnostic report
    report = await generate_diagnostic_report(project_dir)
    report.timestamp = datetime.now().isoformat()

    # Add summary
    issues_count = 0
    warnings_count = 0

    if report.structure:
        issues_count += len(report.structure.issues)
        warnings_count += len(report.structure.warnings)

    if report.dependencies:
        issues_count += len(report.dependencies.issues)
        warnings_count += len(report.dependencies.warnings)

    if report.python:
        issues_count += len(report.python.issues)
        warnings_count += len(report.python.warnings)

    report.summary = DiagnosticReportSummary(
        overall_health=report.overall_health,
        issues_count=issues_count,
        warnings_count=warnings_count,
    )

    return report


@mcp.tool()
async def repair_environment(
    project_path: str | None = None, auto_fix: bool = True
) -> RepairResult:
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
        RepairResult with repair actions taken and results
    """
    return await repair_environment_action(project_path, auto_fix)


@mcp.tool()
async def add_dependency(
    package: str,
    project_path: str | None = None,
    dev: bool = False,
    optional: str | None = None,
) -> DependencyOperationResult:
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
        DependencyOperationResult with operation results
    """
    return await add_dependency_action(package, project_path, dev, optional)


@mcp.tool()
async def remove_dependency(
    package: str,
    project_path: str | None = None,
    dev: bool = False,
    optional: str | None = None,
) -> DependencyOperationResult:
    """
    Remove a dependency from the project.

    This tool uses 'uv remove' to remove a package from the project's dependencies.
    It automatically updates pyproject.toml and the lockfile.

    Args:
        package: Package name (e.g., "requests")
        project_path: Path to the project directory (defaults to current directory)
        dev: Whether to remove from development dependencies (default: False)
        optional: Optional dependency group name (e.g., "test", "docs")

    Returns:
        DependencyOperationResult with operation results
    """
    return await remove_dependency_action(package, project_path, dev, optional)


@mcp.tool()
async def init_project(
    name: str, python_version: str = "3.12", template: str = "app"
) -> str:
    """Initialize a new Python project (app or lib) with a specific Python version."""
    return await ProjectTools.init_project(name, python_version, template=template)


@mcp.tool()
async def sync_environment(upgrade: bool = False, locked: bool = False) -> str:
    """Sync the environment. Use this to install missing deps or ensure lockfile consistency."""
    return await ProjectTools.sync_environment(upgrade=upgrade, locked=locked)


@mcp.tool()
async def export_requirements(output_file: str = "requirements.txt") -> str:
    """Export the current locked dependencies to a requirements.txt file."""
    return await ProjectTools.export_requirements(output_file=output_file)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
