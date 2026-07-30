"""UV-Agent MCP Server - Main server implementation."""

import logging
import os
import re
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
    BuildResult,
    CacheInfoResult,
    CacheOperationResult,
    DependencyListResult,
    DependencyOperationResult,
    DiagnosticReport,
    DiagnosticReportSummary,
    EphemeralToolResult,
    ExportResult,
    FormatResult,
    HealingAction,
    InstallInstructions,
    OutdatedCheckResult,
    PackageInfoResult,
    PipCompileResult,
    PipFreezeResult,
    PipSyncResult,
    ProjectInitResult,
    PublishResult,
    PythonInstallResult,
    PythonListResult,
    PythonPinResult,
    PythonVersion,
    RepairResult,
    ScriptRunResult,
    SelfHealingDiagnostics,
    SelfUpdateResult,
    SyncResult,
    ToolListResult,
    TreeAnalysisResult,
    UVCheckResult,
    VenvResult,
    VersionResult,
    WorkspaceManifest,
    WorkspaceMember,
)
from .tools import ProjectTools
from .utils import assert_within_workspace, resolve_project_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uv-mcp")

# Valid PyPI package name: letters/digits/hyphens/underscores/dots, optional
# extras [extra,...] and optional version specifier (>=1.0, ==1.0, etc.).
# Newlines, semicolons and pipe characters are unconditionally rejected.
_PACKAGE_NAME_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*"
    r"(?:\[[A-Za-z0-9,\s._-]+\])?"
    r"(?:[><=!~]{1,2}[A-Za-z0-9.*+!-]+(?:,[><=!~]{1,2}[A-Za-z0-9.*+!-]+)*)?$"
)
_PACKAGE_NAME_FORBIDDEN = frozenset("\n\r;|`$")


def _get_allowed_tools() -> frozenset[str] | None:
    """Return the normalised allowlist from UV_MCP_ALLOWED_TOOLS, or None if unset."""
    raw = os.environ.get("UV_MCP_ALLOWED_TOOLS", "").strip()
    if not raw:
        return None
    return frozenset(name.strip().lower() for name in raw.split(",") if name.strip())


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
    project_dir = resolve_project_path(project_path)

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
async def uv_export_requirements(output_file: str = "requirements.txt") -> ExportResult:
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

    project_dir = resolve_project_path(project_path)
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
) -> BuildResult:
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
        BuildResult with build results including artifacts created
    """
    from pathlib import Path
    from .utils import run_uv_command, find_uv_project_root

    project_dir = resolve_project_path(project_path)
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
        resolved_output_dir = (project_dir / output_dir).resolve()
        assert_within_workspace(resolved_output_dir)
        cmd.extend(["--out-dir", str(resolved_output_dir)])

    logger.info(f"Building project in {project_dir}")
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    # Parse output to find artifacts
    artifacts: list[str] = []
    if success:
        dist_dir = (project_dir / output_dir).resolve() if output_dir else project_dir / "dist"
        if dist_dir.exists():
            artifacts = [str(f.name) for f in dist_dir.iterdir() if f.is_file()]

    return BuildResult(
        project_dir=str(project_dir),
        output_dir=str((project_dir / output_dir).resolve()) if output_dir else str(project_dir / "dist"),
        success=success,
        artifacts=artifacts,
        message="Build completed successfully" if success else "Build failed",
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_run_ephemeral_tool(
    package: str,
    command: list[str],
    project_path: str | None = None,
) -> EphemeralToolResult:
    """
    Run an ephemeral tool via `uvx` without installing it permanently.

    Args:
        package: The package name to run (e.g., "ruff", "black", "mypy").
        command: Arguments to pass to the tool.
        project_path: Optional project directory to run in.

    Returns:
        EphemeralToolResult with stdout, stderr, and exit code.
    """
    from .utils import run_uv_command

    # Validate package name format
    if not package or not _PACKAGE_NAME_RE.match(package) or any(c in package for c in _PACKAGE_NAME_FORBIDDEN):
        return EphemeralToolResult(
            package=package,
            command=command,
            success=False,
            error="Invalid package name",
            return_code=1,
        )

    # Enforce allowlist when UV_MCP_ALLOWED_TOOLS is configured
    allowed = _get_allowed_tools()
    if allowed is not None:
        base_name = _PACKAGE_NAME_RE.match(package).group(0).split("[")[0].lower()  # type: ignore[union-attr]
        if base_name not in allowed:
            return EphemeralToolResult(
                package=package,
                command=command,
                success=False,
                error=f"Package '{base_name}' is not in the configured allowed tools list (UV_MCP_ALLOWED_TOOLS)",
                return_code=1,
            )

    cwd = resolve_project_path(project_path) if project_path else None

    args = ["tool", "run", "--from", package, *command]
    success, stdout, stderr = await run_uv_command(args, cwd=cwd)

    return EphemeralToolResult(
        package=package,
        command=command,
        success=success,
        stdout=stdout if stdout else None,
        stderr=stderr if stderr else None,
        return_code=0 if success else 1,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_get_workspace_manifest(
    project_path: str | None = None,
) -> WorkspaceManifest:
    """
    Introspect a workspace tree for monorepo / microservice configurations.

    Args:
        project_path: Path to the project root (defaults to cwd).

    Returns:
        WorkspaceManifest with members and dependency metadata.
    """
    from pathlib import Path
    from .utils import find_uv_project_root

    project_dir = resolve_project_path(project_path)
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    # Check if workspace config exists in pyproject.toml
    workspace_members: list[str] = []
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore

        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            tool_uv = data.get("tool", {}).get("uv", {})
            workspace = tool_uv.get("workspace", {})
            raw_members = workspace.get("members", [])
            if isinstance(raw_members, list):
                workspace_members = raw_members
        except Exception:
            pass

    members: list[WorkspaceMember] = []

    if workspace_members:
        for pattern in workspace_members:
            resolved = list(project_dir.glob(pattern))
            for member_dir in resolved:
                if member_dir.is_dir() and (member_dir / "pyproject.toml").exists():
                    try:
                        with open(member_dir / "pyproject.toml", "rb") as f:
                            data = tomllib.load(f)
                        name = data.get("project", {}).get("name", member_dir.name)
                        deps = data.get("project", {}).get("dependencies", [])
                        members.append(
                            WorkspaceMember(
                                name=name,
                                path=str(member_dir.resolve()),
                                dependencies=deps if isinstance(deps, list) else [],
                            )
                        )
                    except Exception:
                        members.append(
                            WorkspaceMember(
                                name=member_dir.name,
                                path=str(member_dir.resolve()),
                                dependencies=[],
                            )
                        )
    else:
        # No workspace declared: treat root as sole member
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            name = data.get("project", {}).get("name", project_dir.name)
            deps = data.get("project", {}).get("dependencies", [])
            members.append(
                WorkspaceMember(
                    name=name,
                    path=str(project_dir),
                    dependencies=deps if isinstance(deps, list) else [],
                )
            )
        except Exception:
            members.append(
                WorkspaceMember(
                    name=project_dir.name,
                    path=str(project_dir),
                    dependencies=[],
                )
            )

    return WorkspaceManifest(
        root=str(project_dir),
        is_workspace=bool(workspace_members),
        members=members,
    )


@mcp.tool()
async def uv_self_heal_environment(
    project_path: str | None = None,
) -> SelfHealingDiagnostics:
    """
    Self-healing environment diagnostics.

    Captures ModuleNotFoundError or layout exceptions, extracts missing
    package names via regex, and returns a structured remedy payload.

    Args:
        project_path: Path to the project directory (defaults to current directory).

    Returns:
        SelfHealingDiagnostics with detected issues and recommended actions.
    """
    import re
    from .utils import run_uv_command, validate_project_path, find_uv_project_root

    try:
        project_dir = validate_project_path(project_path)
    except Exception as e:
        return SelfHealingDiagnostics(
            success=False,
            error=str(e),
        )

    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    actions: list[HealingAction] = []
    missing_packages: list[str] = []
    recommendations: list[str] = []

    # Attempt a lightweight check: uv pip check
    success, stdout, stderr = await run_uv_command(
        ["pip", "check"], cwd=project_dir
    )

    if not success:
        # Extract missing packages from stderr
        pattern = re.compile(
            r"No module named ['\"]?(\w+)['\"]?",
            re.IGNORECASE,
        )
        found = pattern.findall(stderr)
        missing_packages.extend(found)

        # Also try generic package name extraction (e.g., "requires <package>")
        req_pattern = re.compile(
            r"requires\s+(\w+)[,;\s]",
            re.IGNORECASE,
        )
        missing_packages.extend(req_pattern.findall(stderr))

        actions.append(
            HealingAction(
                action="pip_check",
                status="failed",
                error=stderr,
            )
        )
    else:
        actions.append(
            HealingAction(
                action="pip_check",
                status="success",
                output=stdout,
            )
        )

    # Attempt sync to heal missing packages
    if missing_packages:
        unique_packages = list(set(missing_packages))
        for pkg in unique_packages:
            recommendations.append(
                f"Package '{pkg}' is missing. Suggested fix: uv add {pkg}"
            )
        sync_success, sync_out, sync_err = await run_uv_command(
            ["sync"], cwd=project_dir
        )
        actions.append(
            HealingAction(
                action="sync",
                status="success" if sync_success else "failed",
                output=sync_out if sync_success else None,
                error=sync_err if not sync_success else None,
            )
        )
        if sync_success:
            recommendations.append("Environment synced successfully.")
        else:
            recommendations.append(
                "Sync failed. Consider running uv_repair_environment(auto_fix=True)."
            )
    else:
        recommendations.append("No missing packages detected. Environment appears healthy.")

    return SelfHealingDiagnostics(
        success=all(a.status == "success" for a in actions),
        actions=actions,
        missing_packages=list(set(missing_packages)),
        recommendations=recommendations,
    )


@mcp.tool()
async def uv_create_venv(
    project_path: str | None = None,
    seed: bool = False,
    clear: bool = False,
    relocatable: bool = False,
    system_site_packages: bool = False,
) -> VenvResult:
    """
    Create a new virtual environment for the project.

    Args:
        project_path: Path to project directory (defaults to current directory).
        seed: Install seed packages (pip, setuptools, wheel) into the venv.
        clear: Remove any existing files at the target venv path.
        relocatable: Make the virtual environment relocatable.
        system_site_packages: Give venv access to system site packages.

    Returns:
        VenvResult with the venv path and creation status.
    """
    from pathlib import Path
    from .utils import run_uv_command, find_uv_project_root

    project_dir = resolve_project_path(project_path)
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    cmd = ["venv"]
    if seed:
        cmd.append("--seed")
    if clear:
        cmd.append("--clear")
    if relocatable:
        cmd.append("--relocatable")
    if system_site_packages:
        cmd.append("--system-site-packages")

    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    venv_path = project_dir / ".venv"
    return VenvResult(
        path=str(venv_path),
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_run_script(
    command: list[str],
    project_path: str | None = None,
    with_packages: list[str] | None = None,
) -> ScriptRunResult:
    """
    Run a command or script inside the project's environment.

    Args:
        command: The command + arguments to execute (e.g., ["python", "-c", "print(1)"]).
        project_path: Optional project directory.
        with_packages: Temporary packages to install for this run only.

    Returns:
        ScriptRunResult with stdout, stderr, and return code.
    """
    from pathlib import Path
    from .utils import run_uv_command

    project_dir = resolve_project_path(project_path) if project_path else None

    cmd: list[str] = ["run"]
    if with_packages:
        for pkg in with_packages:
            cmd.extend(["--with", pkg])
    cmd.extend(command)

    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    return ScriptRunResult(
        command=command,
        success=success,
        stdout=stdout if stdout else None,
        stderr=stderr if stderr else None,
        return_code=0 if success else 1,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_project_version(
    value: str | None = None,
    bump: str | None = None,
    project_path: str | None = None,
    dry_run: bool = False,
) -> VersionResult:
    """
    Read or update the project's version in pyproject.toml.

    Args:
        value: Set the version to this exact string (e.g., "1.2.3").
        bump: Bump semantics: major, minor, patch.
        project_path: Project directory (defaults to current directory).
        dry_run: If True, do not write changes.

    Returns:
        VersionResult with the current (and optionally previous) version.
    """
    from pathlib import Path
    from .utils import run_uv_command, find_uv_project_root

    project_dir = resolve_project_path(project_path)
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    cmd: list[str] = ["version"]
    if bump:
        cmd.extend(["--bump", bump])
    if dry_run:
        cmd.append("--dry-run")
    if value:
        cmd.append(value)

    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    previous = None
    current = ""
    if success and stdout:
        lines = stdout.strip().splitlines()
        if lines:
            current = lines[-1].strip()

    return VersionResult(
        version=current,
        previous_version=previous,
        project_dir=str(project_dir),
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_format_code(
    project_path: str | None = None,
    check: bool = False,
    diff: bool = False,
) -> FormatResult:
    """
    Format Python code in the project using Ruff.

    Args:
        project_path: Project directory (defaults to current directory).
        check: If True, only check if files are formatted (no changes).
        diff: If True, show a diff of formatting changes.

    Returns:
        FormatResult with formatting status.
    """
    from pathlib import Path
    from .utils import run_uv_command, find_uv_project_root

    project_dir = resolve_project_path(project_path)
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    cmd: list[str] = ["format"]
    if check:
        cmd.append("--check")
    if diff:
        cmd.append("--diff")

    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    return FormatResult(
        project_dir=str(project_dir),
        success=success,
        check_only=check,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_pip_compile(
    input_file: str = "requirements.in",
    output_file: str = "requirements.txt",
    project_path: str | None = None,
) -> PipCompileResult:
    """
    Compile a requirements.in file to a pinned requirements.txt.

    Args:
        input_file: Source requirements file (default: requirements.in).
        output_file: Output pinned requirements file (default: requirements.txt).
        project_path: Project directory (defaults to current directory).

    Returns:
        PipCompileResult with the generated requirements content.
    """
    from pathlib import Path
    from .utils import run_uv_command

    project_dir = resolve_project_path(project_path)

    resolved_input = (project_dir / input_file).resolve()
    assert_within_workspace(resolved_input)
    resolved_output = (project_dir / output_file).resolve()
    assert_within_workspace(resolved_output)

    cmd = ["pip", "compile", str(resolved_input), "--output-file", str(resolved_output)]
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    content = None
    line_count = None
    if success:
        out_path = resolved_output
        if out_path.exists():
            content = out_path.read_text()
            line_count = len(content.splitlines())

    return PipCompileResult(
        input_file=input_file,
        output_file=output_file,
        success=success,
        content=content,
        line_count=line_count,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_pip_sync_requirements(
    requirements_file: str = "requirements.txt",
    project_path: str | None = None,
) -> PipSyncResult:
    """
    Sync the environment with a requirements.txt file.

    Args:
        requirements_file: Path to the requirements file (default: requirements.txt).
        project_path: Project directory (defaults to current directory).

    Returns:
        PipSyncResult with sync status.
    """
    from pathlib import Path
    from .utils import run_uv_command

    project_dir = resolve_project_path(project_path)

    cmd = ["pip", "sync", requirements_file]
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    return PipSyncResult(
        requirements_file=requirements_file,
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_pip_freeze(
    project_path: str | None = None,
) -> PipFreezeResult:
    """
    Freeze installed packages into requirements format.

    Args:
        project_path: Project directory (defaults to current directory).

    Returns:
        PipFreezeResult with the frozen requirements text.
    """
    from pathlib import Path
    from .utils import run_uv_command

    project_dir = resolve_project_path(project_path)

    success, stdout, stderr = await run_uv_command(["pip", "freeze"], cwd=project_dir)

    return PipFreezeResult(
        success=success,
        requirements=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_pip_install(
    packages: list[str],
    project_path: str | None = None,
) -> DependencyOperationResult:
    """
    Install packages imperatively using uv pip install.

    Args:
        packages: List of package specifiers (e.g., ["requests", "numpy>=1.24"]).
        project_path: Project directory (defaults to current directory).

    Returns:
        DependencyOperationResult with install status.
    """
    from pathlib import Path
    from .utils import run_uv_command

    project_dir = resolve_project_path(project_path)

    cmd = ["pip", "install", *packages]
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    return DependencyOperationResult(
        package=", ".join(packages),
        project_dir=str(project_dir),
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_pip_uninstall(
    packages: list[str],
    project_path: str | None = None,
) -> DependencyOperationResult:
    """
    Uninstall packages imperatively using uv pip uninstall.

    Args:
        packages: List of package names to remove.
        project_path: Project directory (defaults to current directory).

    Returns:
        DependencyOperationResult with uninstall status.
    """
    from pathlib import Path
    from .utils import run_uv_command

    project_dir = resolve_project_path(project_path)

    cmd = ["pip", "uninstall", "-y", *packages]
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    return DependencyOperationResult(
        package=", ".join(packages),
        project_dir=str(project_dir),
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_tool_install(
    package: str,
) -> ToolListResult:
    """
    Permanently install a Python CLI tool via uv tool install.

    Args:
        package: Package name (e.g., "ruff", "black", "httpie").

    Returns:
        ToolListResult with installation status.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["tool", "install", package])

    return ToolListResult(
        tools=[package] if success else [],
        count=1 if success else 0,
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_tool_upgrade(
    package: str | None = None,
) -> ToolListResult:
    """
    Upgrade installed uv tools. If no package is specified, upgrades all.

    Args:
        package: Specific package to upgrade, or None for all.

    Returns:
        ToolListResult with upgrade status.
    """
    from .utils import run_uv_command

    cmd = ["tool", "upgrade"]
    if package:
        cmd.append(package)

    success, stdout, stderr = await run_uv_command(cmd)

    return ToolListResult(
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_tool_list() -> ToolListResult:
    """
    List all tools installed via uv tool install.

    Returns:
        ToolListResult with installed tool names.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["tool", "list"])

    tools: list[str] = []
    if success and stdout:
        for line in stdout.strip().splitlines():
            parts = line.split()
            if parts:
                tools.append(parts[0])

    return ToolListResult(
        tools=tools,
        count=len(tools),
        success=success,
        output=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_tool_uninstall(
    package: str,
) -> ToolListResult:
    """
    Uninstall a tool previously installed via uv tool install.

    Args:
        package: Package name to uninstall.

    Returns:
        ToolListResult with uninstall status.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["tool", "uninstall", package])

    return ToolListResult(
        tools=[],
        count=0,
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_prune_cache() -> CacheInfoResult:
    """
    Prune unreachable objects from the uv cache.

    Returns:
        CacheInfoResult with prune status.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["cache", "prune"])

    return CacheInfoResult(
        operation="prune",
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_cache_dir() -> CacheInfoResult:
    """
    Show the uv cache directory path.

    Returns:
        CacheInfoResult with the cache directory.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["cache", "dir"])

    return CacheInfoResult(
        operation="dir",
        path=stdout.strip() if success else None,
        success=success,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_cache_size() -> CacheInfoResult:
    """
    Show the uv cache disk usage.

    Returns:
        CacheInfoResult with human-readable size.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["cache", "size"])

    return CacheInfoResult(
        operation="size",
        size=stdout.strip() if success else None,
        success=success,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_find_python(
    version: str | None = None,
) -> PythonListResult:
    """
    Find a Python installation managed by uv.

    Args:
        version: Optional version to search for (e.g., "3.12").

    Returns:
        PythonListResult with matching installations.
    """
    from .utils import run_uv_command

    cmd = ["python", "find"]
    if version:
        cmd.append(version)

    success, stdout, stderr = await run_uv_command(cmd)

    versions: list[PythonVersion] = []
    if success and stdout:
        for line in stdout.strip().splitlines():
            parts = line.split()
            if parts:
                versions.append(
                    PythonVersion(
                        version=parts[0],
                        path=parts[1] if len(parts) > 1 else None,
                    )
                )

    return PythonListResult(
        versions=versions,
        output=stdout if success else stderr,
    )


@mcp.tool()
async def uv_python_dir() -> CacheInfoResult:
    """
    Show the uv Python installation directory.

    Returns:
        CacheInfoResult with the directory path.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["python", "dir"])

    return CacheInfoResult(
        operation="dir",
        path=stdout.strip() if success else None,
        success=success,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_upgrade_python_version(
    version: str,
) -> PythonInstallResult:
    """
    Upgrade an installed Python version to the latest patch.

    Args:
        version: Python version to upgrade (e.g., "3.12").

    Returns:
        PythonInstallResult with upgrade status.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["python", "upgrade", version])

    return PythonInstallResult(
        version=version,
        success=success,
        output=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_uninstall_python_version(
    version: str,
) -> PythonInstallResult:
    """
    Uninstall a Python version managed by uv.

    Args:
        version: Python version to uninstall (e.g., "3.11").

    Returns:
        PythonInstallResult with uninstall status.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["python", "uninstall", version])

    return PythonInstallResult(
        version=version,
        success=success,
        output=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_publish_project(
    project_path: str | None = None,
    files: list[str] | None = None,
    dry_run: bool = False,
    token: str | None = None,
) -> PublishResult:
    """
    Publish distributions (wheel / sdist) to a package index.

    Args:
        project_path: Project directory (defaults to current directory).
        files: Explicit files to publish (defaults to dist/*).
        dry_run: Perform a dry run without uploading.
        token: API token for the index (optional, for security consider env vars).

    Returns:
        PublishResult with upload status.
    """
    from pathlib import Path
    from .utils import run_uv_command, find_uv_project_root

    project_dir = resolve_project_path(project_path)
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    cmd: list[str] = ["publish"]
    if dry_run:
        cmd.append("--dry-run")
    if token:
        cmd.extend(["--token", token])
    if files:
        cmd.extend(files)

    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    artifacts = files if files else []
    if not artifacts and (project_dir / "dist").exists():
        artifacts = [str(f.name) for f in (project_dir / "dist").iterdir() if f.is_file()]

    return PublishResult(
        project_dir=str(project_dir),
        files=artifacts,
        success=success,
        dry_run=dry_run,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_self_update() -> SelfUpdateResult:
    """
    Update the uv binary to the latest version.

    Returns:
        SelfUpdateResult with previous and new version.
    """
    from .utils import run_uv_command, check_uv_available

    _, previous = await check_uv_available()

    success, stdout, stderr = await run_uv_command(["self", "update"])

    _, new_version = await check_uv_available()

    return SelfUpdateResult(
        previous_version=previous,
        new_version=new_version,
        success=success,
        message=stdout if success else None,
        error=stderr if not success else None,
    )


@mcp.tool()
async def uv_self_version() -> SelfUpdateResult:
    """
    Display the uv binary's version.

    Returns:
        SelfUpdateResult with version string.
    """
    from .utils import run_uv_command

    success, stdout, stderr = await run_uv_command(["--version"])

    return SelfUpdateResult(
        new_version=stdout.strip() if success else None,
        success=success,
        error=stderr if not success else None,
    )


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
