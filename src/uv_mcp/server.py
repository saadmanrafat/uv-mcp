"""UV-Agent MCP Server - Main server implementation."""

import logging
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

from .actions import (
    add_dependency_action,
    analyze_dependency_tree_action,
    check_outdated_packages_action,
    check_uv_installation_action,
    clear_cache_action,
    get_install_instructions_action,
    install_python_version_action,
    list_dependencies_action,
    list_python_versions_action,
    pin_python_version_action,
    remove_dependency_action,
    repair_environment_action,
    show_package_info_action,
)
from .diagnostics import generate_diagnostic_report
from .models import (
    CacheOperationResult,
    DependencyListResult,
    DependencyOperationResult,
    DiagnosticReport,
    DiagnosticReportSummary,
    InstallInstructions,
    OutdatedCheckResult,
    PackageInfoResult,
    ProjectInitResult,
    PythonInstallResult,
    PythonListResult,
    PythonPinResult,
    RepairResult,
    SyncResult,
    TreeAnalysisResult,
    UVCheckResult,
)
from .tools import ProjectTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uv-mcp")

# Initialize FastMCP server
mcp = FastMCP("uv-mcp")


@mcp.tool()
async def uv_check_installation() -> UVCheckResult:
    """
    Check if uv is installed and return version information.

    Returns:
        UVCheckResult with installation status and version info
    """
    return await check_uv_installation_action()


@mcp.tool()
async def uv_install() -> InstallInstructions:
    """
    Provide installation instructions for uv.

    Note: This tool cannot automatically install uv for security reasons.
    It provides platform-specific installation instructions instead.

    Returns:
        InstallInstructions with installation instructions
    """
    return get_install_instructions_action()


@mcp.tool()
async def uv_diagnose_environment(project_path: str | None = None) -> DiagnosticReport:
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
async def uv_repair_environment(
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
async def uv_add_dependency(
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
async def uv_remove_dependency(
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
async def uv_initialize_project(
    name: str, python_version: str = "3.12", template: str = "app"
) -> ProjectInitResult:
    """Initialize a new Python project (app or lib) with a specific Python version."""
    return await ProjectTools.init_project(name, python_version, template=template)


@mcp.tool()
async def uv_sync_environment(
    upgrade: bool = False, locked: bool = False
) -> SyncResult:
    """Sync the environment. Use this to install missing deps or ensure lockfile consistency."""
    return await ProjectTools.sync_environment(upgrade=upgrade, locked=locked)


@mcp.tool()
async def uv_export_requirements(output_file: str = "requirements.txt") -> SyncResult:
    """Export the current locked dependencies to a requirements.txt file."""
    return await ProjectTools.export_requirements(output_file=output_file)


@mcp.tool()
async def uv_list_python_versions() -> PythonListResult:
    """
    List installed Python versions managed by uv.

    Returns:
        PythonListResult containing a list of versions and raw output.
    """
    return await list_python_versions_action()


@mcp.tool()
async def uv_install_python_version(version: str) -> PythonInstallResult:
    """
    Install a specific Python version using uv.

    Args:
        version: The version to install (e.g., "3.12", "3.13", "pypy@3.10")

    Returns:
        PythonInstallResult with success status.
    """
    return await install_python_version_action(version)


@mcp.tool()
async def uv_pin_python_version(
    version: str,
    project_path: str | None = None,
) -> PythonPinResult:
    """
    Pin the current project to use a specific Python version.

    This updates the .python-version file in the project root.

    Args:
        version: The version to pin (e.g., "3.12")

    Returns:
        PythonPinResult with success status.
    """
    return await pin_python_version_action(version, project_path)


@mcp.tool()
async def uv_list_dependencies(
    project_path: str | None = None, tree: bool = False
) -> DependencyListResult:
    """
    List project dependencies.

    Args:
        project_path: Path to the project root.
        tree: If True, returns a visual tree structure. If False, returns a flat list.

    Returns:
        DependencyListResult with dependencies.
    """
    return await list_dependencies_action(project_path, tree)


@mcp.tool()
async def uv_show_package_info(
    package_name: str, project_path: str | None = None
) -> PackageInfoResult:
    """
    Show detailed information about a specific package.

    Args:
        package_name: The name of the package to inspect.
        project_path: Optional path to the project root.

    Returns:
        PackageInfoResult with metadata.
    """
    return await show_package_info_action(package_name, project_path)


@mcp.tool()
async def uv_check_outdated_packages(
    project_path: str | None = None,
) -> OutdatedCheckResult:
    """
    Check for outdated packages in the environment.

    Args:
        project_path: Path to the project root.

    Returns:
        OutdatedCheckResult with a list of outdated packages.
    """
    return await check_outdated_packages_action(project_path)


@mcp.tool()
async def uv_analyze_dependency_tree(
    project_path: str | None = None,
) -> TreeAnalysisResult:
    """
    Analyze the dependency tree for structure and depth.

    Args:
        project_path: Path to the project root.

    Returns:
        TreeAnalysisResult with the tree output and metrics.
    """
    return await analyze_dependency_tree_action(project_path)


@mcp.tool()
async def uv_clear_cache(package: str | None = None) -> CacheOperationResult:
    """
    Clear the uv cache.

    This can help resolve issues with corrupted packages or free up disk space.
    If a package name is provided, only that package's cache will be cleared.
    Otherwise, the entire cache is cleared.

    Args:
        package: Optional specific package name to clear from cache

    Returns:
        CacheOperationResult with operation status
    """
    return await clear_cache_action(package)


@mcp.tool()
async def uv_lock_project(project_path: str | None = None) -> SyncResult:
    """
    Create or update the uv.lock file without installing dependencies.

    This is useful to update the lockfile after manually editing pyproject.toml
    without syncing the environment.

    Args:
        project_path: Path to the project directory (defaults to current directory)

    Returns:
        SyncResult with operation status
    """
    from pathlib import Path
    from .utils import run_uv_command, find_uv_project_root

    project_dir = Path(project_path) if project_path else Path.cwd()
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    logger.info(f"Locking project in {project_dir}")
    success, stdout, stderr = await run_uv_command(["lock"], cwd=project_dir)

    return SyncResult(
        project_dir=str(project_dir),
        success=success,
        message=(
            "Lockfile updated successfully" if success else "Failed to update lockfile"
        ),
        output=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_build_project(
    project_path: str | None = None,
    wheel: bool = True,
    sdist: bool = True,
    output_dir: str | None = None,
) -> dict:
    """
    Build the project into distributable packages.

    Creates wheel and/or source distribution files that can be uploaded to PyPI
    or installed elsewhere.

    Args:
        project_path: Path to the project directory (defaults to current directory)
        wheel: Build a wheel package (default: True)
        sdist: Build a source distribution (default: True)
        output_dir: Output directory for built packages (default: dist/)

    Returns:
        Dict with build results including artifacts created
    """
    from pathlib import Path
    from .utils import run_uv_command, find_uv_project_root

    project_dir = Path(project_path) if project_path else Path.cwd()
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    cmd = ["build"]

    # Add format flags
    if wheel and not sdist:
        cmd.append("--wheel")
    elif sdist and not wheel:
        cmd.append("--sdist")
    # If both are True (default), build both formats

    if output_dir:
        cmd.extend(["--out-dir", output_dir])

    logger.info(f"Building project in {project_dir}")
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    # Parse output to find artifacts
    artifacts = []
    if success:
        dist_dir = Path(output_dir) if output_dir else project_dir / "dist"
        if dist_dir.exists():
            artifacts = [str(f.name) for f in dist_dir.iterdir() if f.is_file()]

    return {
        "project_dir": str(project_dir),
        "output_dir": str(output_dir) if output_dir else str(project_dir / "dist"),
        "success": success,
        "artifacts": artifacts,
        "message": "Build completed successfully" if success else "Build failed",
        "output": stdout if success else None,
        "error": stderr if not success else None,
    }


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
