"""Environment diagnostics for Python projects using uv."""

import sys
from pathlib import Path

from .models import (
    DependencyCheck,
    DiagnosticReport,
    ProjectInfo,
    PythonCheck,
    StructureCheck,
    UVInfo,
    VirtualEnvInfo,
)
from .utils import (
    check_project_venv,
    check_uv_available,
    find_uv_project_root,
    get_project_info,
    run_uv_command,
)


def check_project_structure(project_dir: Path | None = None) -> StructureCheck:
    """
    Validate project file structure.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        StructureCheck with structure validation results
    """
    if project_dir is None:
        project_dir = Path.cwd()

    valid = True
    issues = []
    warnings = []

    # Check for project configuration
    if not (project_dir / "pyproject.toml").exists():
        if not (project_dir / "requirements.txt").exists():
            valid = False
            issues.append("No pyproject.toml or requirements.txt found")
        else:
            warnings.append(
                "Using requirements.txt instead of pyproject.toml (consider migrating)"
            )

    # Check for virtual environment
    venv_exists, _ = check_project_venv(project_dir)
    if not venv_exists:
        warnings.append("No .venv detected in project root")

    # Check for lockfile
    if (project_dir / "pyproject.toml").exists() and not (
        project_dir / "uv.lock"
    ).exists():
        warnings.append("No uv.lock file found (run 'uv lock' to create)")

    return StructureCheck(valid=valid, issues=issues, warnings=warnings)


async def check_dependencies(project_dir: Path | None = None) -> DependencyCheck:
    """
    Analyze dependency health.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        DependencyCheck with dependency analysis results
    """
    if project_dir is None:
        project_dir = Path.cwd()

    healthy = True
    issues = []
    warnings = []
    installed_packages = None

    # Get project info
    info = get_project_info(project_dir)

    if not info["has_pyproject"] and not info["has_requirements"]:
        healthy = False
        issues.append("No dependency file found")
        return DependencyCheck(healthy=healthy, issues=issues)

    # Check for dependency conflicts using uv pip check
    success, stdout, stderr = await run_uv_command(["pip", "check"], cwd=project_dir)

    if not success:
        # If command failed, check if it's because of broken requirements (exit code 1)
        # or some other error. uv pip check prints issues to stdout/stderr.
        if (
            "No broken requirements found" not in stdout
            and "No broken requirements found" not in stderr
        ):
            healthy = False
            # Determine if it's a "broken requirements" issue or "tool failed" issue
            # Usually broken requirements will have details in stdout/stderr
            if stdout.strip() or stderr.strip():
                issues.append(
                    f"Dependency conflicts detected: {stdout.strip() or stderr.strip()}"
                )
            else:
                issues.append(f"Failed to check dependencies: {stderr}")

    # Check if dependencies are installed
    if info["has_pyproject"]:
        success, stdout, stderr = await run_uv_command(["pip", "list"], cwd=project_dir)
        if success:
            lines = stdout.strip().split("\n")
            installed_count = max(0, len(lines) - 2)  # Prevent negative counts
            installed_packages = installed_count
        else:
            warnings.append("Could not list installed packages")

    return DependencyCheck(
        healthy=healthy,
        issues=issues,
        warnings=warnings,
        installed_packages=installed_packages,
    )


async def check_python_version(project_dir: Path | None = None) -> PythonCheck:
    """
    Validate Python version requirements.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        PythonCheck with Python version validation results
    """

    if project_dir is None:
        project_dir = Path.cwd()

    compatible = True
    current_version = "unknown"
    source = "unknown"
    issues = []
    warnings = []
    required_version = None

    info = get_project_info(project_dir)
    required = info.get("python_version")

    # Check the actual python version in the environment
    # Try using 'uv run python --version' which runs in the project's environment
    success, stdout, stderr = await run_uv_command(
        ["run", "python", "--version"], cwd=project_dir
    )

    if success:
        # Output is like "Python 3.12.0"
        version_str = stdout.strip().split()[-1]
        current_version = version_str
        source = "virtual_env"
    else:
        # Fallback to system python check if uv run fails (e.g. no venv yet)
        # But report that we are falling back
        warnings.append(
            "Could not determine project Python version (env might be missing)"
        )
        source = "system_fallback"
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        warnings.append(f"Using system Python {current_version} for comparison")

    if required and required != "unknown":
        required_version = str(required)

        # specific version check logic could be improved with 'packaging' library
        # but for now we do string matching if exact version is required
        if "==" in required:
            exact_version = required.split("==")[1].strip()
            if current_version != "unknown" and exact_version not in current_version:
                compatible = False
                issues.append(
                    f"Python version mismatch: need {exact_version}, have {current_version}"
                )
        elif ">=" in required:
            # Just a warning for now as we don't fully parse semver here
            pass

    return PythonCheck(
        compatible=compatible,
        current_version=current_version,
        source=source,
        issues=issues,
        warnings=warnings,
        required_version=required_version,
    )


def _get_worst_health(current: str, new: str) -> str:
    """
    Compare two health statuses and return the worse one.

    Args:
        current: Current health status
        new: New health status to compare

    Returns:
        The worse of the two statuses
    """
    severity = {"healthy": 0, "warning": 1, "critical": 2}
    current_severity = severity.get(current, 0)
    new_severity = severity.get(new, 0)
    return current if current_severity >= new_severity else new


async def generate_diagnostic_report(
    project_dir: Path | None = None,
) -> DiagnosticReport:
    """
    Generate a comprehensive environment health report.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        DiagnosticReport
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    overall_health = "healthy"
    # Removed unused critical_issues list

    # Check uv installation
    uv_available, uv_version = await check_uv_available()
    uv_info = UVInfo(installed=uv_available, version=uv_version)

    if not uv_available:
        return DiagnosticReport(
            project_dir=str(project_dir),
            overall_health="critical",
            uv=uv_info,
            critical_issues=["uv is not installed"],
        )

    # Check project structure
    structure = check_project_structure(project_dir)

    if not structure.valid:
        overall_health = _get_worst_health(overall_health, "critical")
    elif structure.warnings:
        overall_health = _get_worst_health(overall_health, "warning")

    # Check dependencies
    dependencies = await check_dependencies(project_dir)

    if not dependencies.healthy:
        overall_health = _get_worst_health(overall_health, "critical")

    # Check Python version
    python_check = await check_python_version(project_dir)

    if not python_check.compatible:
        overall_health = _get_worst_health(overall_health, "critical")

    # Check virtual environment
    venv_exists, venv_path = check_project_venv(project_dir)
    virtual_env = VirtualEnvInfo(
        active=venv_exists,
        path=venv_path,
    )

    # Get project info
    info_dict = get_project_info(project_dir)
    project_info = ProjectInfo(**info_dict)

    return DiagnosticReport(
        project_dir=str(project_dir),
        overall_health=overall_health,
        uv=uv_info,
        structure=structure,
        dependencies=dependencies,
        python=python_check,
        virtual_env=virtual_env,
        project_info=project_info,
    )
