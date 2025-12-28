"""Actions for modifying the environment."""

import json
import logging
from pathlib import Path

from .models import (
    CacheOperationResult,
    DependencyItem,
    DependencyListResult,
    DependencyOperationResult,
    InstallInstructions,
    InstallMethod,
    OutdatedCheckResult,
    OutdatedPackage,
    PackageInfoResult,
    PythonInstallResult,
    PythonListResult,
    PythonPinResult,
    PythonVersion,
    RepairAction,
    RepairResult,
    TreeAnalysisResult,
    UVCheckResult,
)
from .utils import (
    check_project_venv,
    check_uv_available,
    find_uv_project_root,
    run_uv_command,
)

logger = logging.getLogger(__name__)


async def check_uv_installation_action() -> UVCheckResult:
    """
    Check if uv is installed and return version information.

    Returns:
        UVCheckResult with installation status
    """
    available, version = await check_uv_available()

    message = f"uv is installed: {version}" if available else "uv is not installed"
    installation_instructions = None

    if not available:
        installation_instructions = {
            "linux_mac": "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "windows": 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"',
            "pip": "pip install uv",
            "docs": "https://docs.astral.sh/uv/getting-started/installation/",
        }

    return UVCheckResult(
        installed=available,
        version=version,
        message=message,
        installation_instructions=installation_instructions,
    )


def get_install_instructions_action() -> InstallInstructions:
    """
    Provide installation instructions for uv.

    Returns:
        InstallInstructions with installation instructions
    """
    return InstallInstructions(
        message="uv installation instructions",
        methods={
            "standalone_installer": {
                "linux_mac": InstallMethod(
                    command="curl -LsSf https://astral.sh/uv/install.sh | sh",
                    description="Download and run the official installer script",
                ),
                "windows": InstallMethod(
                    command='powershell -c "irm https://astral.sh/uv/install.ps1 | iex"',
                    description="Download and run the official PowerShell installer",
                ),
            },
            "pip": InstallMethod(
                command="pip install uv",
                description="Install via pip (requires Python already installed)",
            ),
            "homebrew": InstallMethod(
                command="brew install uv",
                description="Install via Homebrew (macOS/Linux)",
            ),
            "cargo": InstallMethod(
                command="cargo install --git https://github.com/astral-sh/uv uv",
                description="Build from source using Cargo (Rust)",
            ),
        },
        verification=InstallMethod(
            command="uv --version",
            description="Verify installation by checking the version",
        ),
        documentation="https://docs.astral.sh/uv/getting-started/installation/",
    )


async def _repair_init_project(
    project_dir: Path, auto_fix: bool
) -> RepairAction | None:
    """Internal helper to repair/initialize a project."""
    if (project_dir / "pyproject.toml").exists():
        return None

    if auto_fix:
        logger.info(f"Initializing new project in {project_dir}")
        success, stdout, stderr = await run_uv_command(
            ["init", "--no-readme"], cwd=project_dir
        )
        return RepairAction(
            action="initialize_project",
            description="No pyproject.toml found, initializing new project",
            status="success" if success else "failed",
            output=stdout if success else None,
            error=stderr if not success else None,
        )

    return RepairAction(
        action="initialize_project",
        status="skipped",
        reason="auto_fix is disabled",
    )


async def _repair_venv(project_dir: Path, auto_fix: bool) -> RepairAction | None:
    """Internal helper to repair/create virtual environment."""
    venv_exists, _ = check_project_venv(project_dir)
    if venv_exists:
        return None

    if auto_fix:
        logger.info("Creating virtual environment")
        success, stdout, stderr = await run_uv_command(["venv"], cwd=project_dir)
        return RepairAction(
            action="create_venv",
            description="Creating virtual environment",
            status="success" if success else "failed",
            output="Virtual environment created at .venv" if success else None,
            error=stderr if not success else None,
        )

    return RepairAction(
        action="create_venv",
        status="skipped",
        reason="auto_fix is disabled",
    )


async def _repair_python_install(
    project_dir: Path, auto_fix: bool
) -> RepairAction | None:
    """Internal helper to ensure Python is installed."""
    if not (project_dir / "pyproject.toml").exists():
        return None

    py_success, _, _ = await run_uv_command(
        ["run", "python", "--version"], cwd=project_dir
    )

    if py_success:
        return None

    if auto_fix:
        logger.info("Installing python interpreter")
        success, stdout, stderr = await run_uv_command(
            ["python", "install"], cwd=project_dir
        )
        return RepairAction(
            action="install_python",
            description="Installing/updating Python interpreter",
            status="success" if success else "failed",
            output=(
                (stdout or "Python interpreter installed/verified") if success else None
            ),
            error=stderr if not success else None,
        )

    return RepairAction(
        action="install_python",
        status="skipped",
        reason="auto_fix is disabled",
    )


async def _repair_sync(project_dir: Path, auto_fix: bool) -> RepairAction | None:
    """Internal helper to sync dependencies."""
    if not (project_dir / "pyproject.toml").exists():
        return None

    if auto_fix:
        logger.info("Syncing dependencies")
        success, stdout, stderr = await run_uv_command(["sync"], cwd=project_dir)
        return RepairAction(
            action="sync_dependencies",
            description="Syncing project dependencies",
            status="success" if success else "failed",
            output="Dependencies synced successfully" if success else None,
            error=stderr if not success else None,
        )

    return RepairAction(
        action="sync_dependencies",
        status="skipped",
        reason="auto_fix is disabled",
    )


async def repair_environment_action(
    project_path: str | None = None, auto_fix: bool = True
) -> RepairResult:
    """
    Attempt to repair common environment issues.

    Returns:
        RepairResult with repair results
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        logger.error(f"Project directory does not exist: {project_dir}")
        return RepairResult(
            project_dir=str(project_dir),
            success=False,
            error=f"Project directory does not exist: {project_path}",
        )

    # Check if uv is available
    available, version = await check_uv_available()
    if not available:
        logger.error("uv not installed, cannot repair environment")
        return RepairResult(
            project_dir=str(project_dir),
            success=False,
            error="uv is not installed. Please install uv first using the install_uv tool.",
        )

    # Find project root
    root = find_uv_project_root(project_dir)
    project_root = str(root) if root else None
    if root:
        project_dir = root

    actions: list[RepairAction] = []

    # 1. Initialize project
    if action := await _repair_init_project(project_dir, auto_fix):
        actions.append(action)

    # 2. Create venv
    if action := await _repair_venv(project_dir, auto_fix):
        actions.append(action)

    # 3. Install Python
    if action := await _repair_python_install(project_dir, auto_fix):
        actions.append(action)

    # 4. Sync dependencies
    if action := await _repair_sync(project_dir, auto_fix):
        actions.append(action)

    # Determine overall success: True if no action failed
    overall_success = all(a.status != "failed" for a in actions)

    return RepairResult(
        project_dir=str(project_dir),
        actions=actions,
        success=overall_success,
        project_root=project_root,
    )


async def add_dependency_action(
    package: str,
    project_path: str | None = None,
    dev: bool = False,
    optional: str | None = None,
) -> DependencyOperationResult:
    """
    Add a new dependency to the project.

    Returns:
        DependencyOperationResult
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        return DependencyOperationResult(
            package=package,
            project_dir=str(project_dir),
            success=False,
            error=f"Project directory does not exist: {project_path}",
        )

    # Check if uv is available
    available, version = await check_uv_available()
    if not available:
        return DependencyOperationResult(
            package=package,
            project_dir=str(project_dir),
            success=False,
            error="uv is not installed. Please install uv first using the install_uv tool.",
        )

    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    # Check for pyproject.toml
    if not (project_dir / "pyproject.toml").exists():
        return DependencyOperationResult(
            package=package,
            project_dir=str(project_dir),
            success=False,
            error="No pyproject.toml found. Initialize a project first using repair_environment.",
        )

    # Build command
    cmd = ["add", package]

    if dev:
        cmd.append("--dev")

    if optional:
        cmd.extend(["--optional", optional])

    # Execute command
    logger.info(f"Adding dependency {package} to {project_dir}")
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    return DependencyOperationResult(
        package=package,
        project_dir=str(project_dir),
        success=success,
        dev=dev,
        optional=optional,
        message=(
            f"Successfully added {package}" if success else f"Failed to add {package}"
        ),
        output=stdout if success else None,
        error=stderr if not success else None,
    )


async def remove_dependency_action(
    package: str,
    project_path: str | None = None,
    dev: bool = False,
    optional: str | None = None,
) -> DependencyOperationResult:
    """
    Remove a dependency from the project.

    Returns:
        DependencyOperationResult
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        return DependencyOperationResult(
            package=package,
            project_dir=str(project_dir),
            success=False,
            error=f"Project directory does not exist: {project_path}",
        )

    # Check if uv is available
    available, version = await check_uv_available()
    if not available:
        return DependencyOperationResult(
            package=package,
            project_dir=str(project_dir),
            success=False,
            error="uv is not installed. Please install uv first using the install_uv tool.",
        )

    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    # Check for pyproject.toml
    if not (project_dir / "pyproject.toml").exists():
        return DependencyOperationResult(
            package=package,
            project_dir=str(project_dir),
            success=False,
            error="No pyproject.toml found.",
        )

    # Build command
    cmd = ["remove", package]

    if dev:
        cmd.append("--dev")

    if optional:
        cmd.extend(["--optional", optional])

    # Execute command
    logger.info(f"Removing dependency {package} from {project_dir}")
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    return DependencyOperationResult(
        package=package,
        project_dir=str(project_dir),
        success=success,
        dev=dev,
        optional=optional,
        message=(
            f"Successfully removed {package}"
            if success
            else f"Failed to remove {package}"
        ),
        output=stdout if success else None,
        error=stderr if not success else None,
    )


async def list_python_versions_action() -> PythonListResult:
    """
    List installed Python versions.

    Returns:
        PythonListResult
    """
    success, stdout, stderr = await run_uv_command(["python", "list"])

    if not success:
        logger.error(f"Failed to list python versions: {stderr}")
        return PythonListResult(versions=[], output=stderr)

    versions = []
    # Simple parsing strategy: split lines, try to extract first token as version
    # uv python list output example:
    # cpython-3.12.0-linux-x86_64-gnu     /path/to/python     <managed>
    for line in stdout.splitlines():
        parts = line.split()
        if not parts:
            continue

        version_str = parts[0]
        path = parts[1] if len(parts) > 1 else None
        origin = parts[2] if len(parts) > 2 else None

        versions.append(PythonVersion(version=version_str, path=path, origin=origin))

    return PythonListResult(versions=versions, output=stdout)


async def install_python_version_action(version: str) -> PythonInstallResult:
    """
    Install a specific Python version.

    Returns:
        PythonInstallResult
    """
    logger.info(f"Installing Python version: {version}")
    success, stdout, stderr = await run_uv_command(["python", "install", version])

    return PythonInstallResult(
        version=version,
        success=success,
        output=stdout if success else None,
        error=stderr if not success else None,
    )


async def pin_python_version_action(
    version: str, project_path: str | None = None
) -> PythonPinResult:
    """
    Pin the project to a specific Python version.

    Returns:
        PythonPinResult
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        return PythonPinResult(
            version=version,
            project_dir=str(project_dir),
            success=False,
            error=f"Project directory does not exist: {project_path}",
        )

    # Find project root to ensure we pin in the right place
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    logger.info(f"Pinning Python {version} in {project_dir}")
    success, stdout, stderr = await run_uv_command(
        ["python", "pin", version], cwd=project_dir
    )

    return PythonPinResult(
        version=version,
        project_dir=str(project_dir),
        success=success,
        output=stdout if success else None,
        error=stderr if not success else None,
    )


def _get_uv_pip_args(project_dir: Path) -> list[str]:
    """
    Helper to get common uv pip arguments, specifically targeting the project's venv.
    """
    args = []
    venv_exists, venv_path = check_project_venv(project_dir)
    if venv_exists and venv_path:
        args.extend(["--python", venv_path])
    return args


async def list_dependencies_action(
    project_path: str | None = None, tree: bool = False
) -> DependencyListResult:
    """
    List project dependencies, either as a flat list or a tree.

    Args:
        project_path: Path to the project root.
        tree: If True, returns a tree visualization. If False, returns a flat list.
    """
    project_dir = Path(project_path) if project_path else Path.cwd()
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    if tree:
        # Use 'uv tree' for hierarchical view
        # uv tree automatically respects the project structure (pyproject.toml/uv.lock)
        success, stdout, stderr = await run_uv_command(["tree"], cwd=project_dir)
        if not success:
            return DependencyListResult(
                project_dir=str(project_dir),
                is_tree=True,
                count=0,
                success=False,
                error=stderr,
            )
        return DependencyListResult(
            project_dir=str(project_dir),
            is_tree=True,
            tree_output=stdout,
            count=len(stdout.splitlines()),  # Rough proxy for count
            success=True,
        )
    else:
        # Use 'uv pip list --format=json' for flat list
        cmd = ["pip", "list", "--format=json"]
        cmd.extend(_get_uv_pip_args(project_dir))

        success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)
        if not success:
            return DependencyListResult(
                project_dir=str(project_dir),
                is_tree=False,
                count=0,
                success=False,
                error=stderr,
            )

        try:
            data = json.loads(stdout)
            deps = [
                DependencyItem(
                    name=d.get("name", "unknown"),
                    version=d.get("version", "unknown"),
                    editable=d.get("editable", False),
                    location=d.get("location"),
                    installer=d.get("installer"),
                )
                for d in data
            ]
            return DependencyListResult(
                project_dir=str(project_dir),
                is_tree=False,
                dependencies=deps,
                count=len(deps),
                success=True,
            )
        except json.JSONDecodeError:
            return DependencyListResult(
                project_dir=str(project_dir),
                is_tree=False,
                count=0,
                success=False,
                error="Failed to parse JSON output from uv pip list",
            )


async def show_package_info_action(
    package_name: str, project_path: str | None = None
) -> PackageInfoResult:
    """
    Show detailed information about a package.
    """
    project_dir = Path(project_path) if project_path else Path.cwd()
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    cmd = ["pip", "show", package_name]
    cmd.extend(_get_uv_pip_args(project_dir))

    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    if not success:
        return PackageInfoResult(
            name=package_name, success=False, error=stderr or "Package not found"
        )

    # Parse 'key: value' output
    data = {}
    current_key = None
    for line in stdout.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            data[key.lower()] = value.strip()
            current_key = key.lower()
        elif current_key and line.startswith("  "):
            # Continuation line (e.g. for Requires)
            data[current_key] += f", {line.strip()}"

    return PackageInfoResult(
        name=data.get("name", package_name),
        version=data.get("version"),
        location=data.get("location"),
        requires=[r.strip() for r in data.get("requires", "").split(",") if r.strip()],
        required_by=[
            r.strip() for r in data.get("required-by", "").split(",") if r.strip()
        ],
        metadata=data,
        success=True,
    )


async def check_outdated_packages_action(
    project_path: str | None = None,
) -> OutdatedCheckResult:
    """
    Check for outdated packages.
    """
    project_dir = Path(project_path) if project_path else Path.cwd()
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    cmd = ["pip", "list", "--outdated", "--format=json"]
    cmd.extend(_get_uv_pip_args(project_dir))

    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    if not success:
        return OutdatedCheckResult(
            project_dir=str(project_dir),
            outdated_packages=[],
            count=0,
            success=False,
            error=stderr,
        )

    try:
        data = json.loads(stdout)
        outdated = [
            OutdatedPackage(
                name=d.get("name", "unknown"),
                version=d.get("version", "unknown"),
                latest_version=d.get("latest_version", "unknown"),
                type=d.get("type"),
            )
            for d in data
        ]
        return OutdatedCheckResult(
            project_dir=str(project_dir),
            outdated_packages=outdated,
            count=len(outdated),
            success=True,
        )
    except json.JSONDecodeError:
        return OutdatedCheckResult(
            project_dir=str(project_dir),
            outdated_packages=[],
            count=0,
            success=False,
            error="Failed to parse JSON output",
        )


async def analyze_dependency_tree_action(
    project_path: str | None = None,
) -> TreeAnalysisResult:
    """
    Analyze the dependency tree.
    """
    project_dir = Path(project_path) if project_path else Path.cwd()
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    success, stdout, stderr = await run_uv_command(["tree"], cwd=project_dir)

    if not success:
        return TreeAnalysisResult(
            project_dir=str(project_dir),
            tree_output="",
            success=False,
            error=stderr,
        )

    # Basic analysis: calculate max depth based on indentation
    lines = stdout.splitlines()
    max_depth = 0
    for line in lines:
        # uv tree uses unicode characters, but indentation is still present
        # Typical branch: ├── package v1.0.0
        # We can count leading special chars or spaces.
        # This is a rough heuristic.
        indent = len(line) - len(line.lstrip(" ├─└│"))
        depth = indent // 4  # Assuming ~4 chars per level
        if depth > max_depth:
            max_depth = depth

    return TreeAnalysisResult(
        project_dir=str(project_dir),
        tree_output=stdout,
        depth=max_depth,
        success=True,
    )


async def clear_cache_action(package: str | None = None) -> CacheOperationResult:
    """Clear uv cache for a specific package or all packages."""
    cmd = ["cache", "clean"]
    if package:
        cmd.append(package)

    success, stdout, stderr = await run_uv_command(cmd)
    return CacheOperationResult(
        operation="clean",
        package=package,
        success=success,
        message="Cache cleared successfully" if success else "Failed to clear cache",
        output=stdout if success else None,
        error=stderr if not success else None,
    )
