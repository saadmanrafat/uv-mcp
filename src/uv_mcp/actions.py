"""Actions for modifying the environment."""

import logging
from pathlib import Path

from .models import (
    DependencyOperationResult,
    InstallInstructions,
    InstallMethod,
    RepairAction,
    RepairResult,
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
