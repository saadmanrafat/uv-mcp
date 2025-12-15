"""Actions for modifying the environment."""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .uv_utils import (
    check_uv_available,
    check_project_venv,
    find_uv_project_root,
    run_uv_command,
)


async def check_uv_installation_action() -> Dict[str, Any]:
    """
    Check if uv is installed and return version information.

    Returns:
        Dictionary with installation status
    """
    available, version = await check_uv_available()

    result = {"installed": available, "version": version, "message": ""}

    if available:
        result["message"] = f"uv is installed: {version}"
    else:
        result["message"] = "uv is not installed"
        result["installation_instructions"] = {
            "linux_mac": "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "windows": 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"',
            "pip": "pip install uv",
            "docs": "https://docs.astral.sh/uv/getting-started/installation/",
        }

    return result


def get_install_instructions_action() -> Dict[str, Any]:
    """
    Provide installation instructions for uv.

    Returns:
        Dictionary with installation instructions
    """
    return {
        "message": "uv installation instructions",
        "methods": {
            "standalone_installer": {
                "linux_mac": {
                    "command": "curl -LsSf https://astral.sh/uv/install.sh | sh",
                    "description": "Download and run the official installer script",
                },
                "windows": {
                    "command": 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"',
                    "description": "Download and run the official PowerShell installer",
                },
            },
            "pip": {
                "command": "pip install uv",
                "description": "Install via pip (requires Python already installed)",
            },
            "homebrew": {
                "command": "brew install uv",
                "description": "Install via Homebrew (macOS/Linux)",
            },
            "cargo": {
                "command": "cargo install --git https://github.com/astral-sh/uv uv",
                "description": "Build from source using Cargo (Rust)",
            },
        },
        "verification": {
            "command": "uv --version",
            "description": "Verify installation by checking the version",
        },
        "documentation": "https://docs.astral.sh/uv/getting-started/installation/",
    }


async def repair_environment_action(
    project_path: Optional[str] = None, auto_fix: bool = True
) -> Dict[str, Any]:
    """
    Attempt to repair common environment issues.

    Returns:
        Dictionary with repair results
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        return {
            "error": f"Project directory does not exist: {project_path}",
            "success": False,
        }

    # Check if uv is available
    available, version = await check_uv_available()
    if not available:
        return {
            "error": "uv is not installed. Please install uv first using the install_uv tool.",
            "success": False,
        }

    results = {
        "project_dir": str(project_dir),
        "timestamp": datetime.now().isoformat(),
        "actions": [],
        "success": True,
    }

    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root
        results["project_root"] = str(root)

    # Check for pyproject.toml
    if not (project_dir / "pyproject.toml").exists():
        if auto_fix:
            results["actions"].append(
                {
                    "action": "initialize_project",
                    "description": "No pyproject.toml found, initializing new project",
                }
            )

            success, stdout, stderr = await run_uv_command(
                ["init", "--no-readme"], cwd=project_dir
            )

            if success:
                results["actions"][-1]["status"] = "success"
                results["actions"][-1]["output"] = stdout
            else:
                results["actions"][-1]["status"] = "failed"
                results["actions"][-1]["error"] = stderr
                results["success"] = False
        else:
            results["actions"].append(
                {
                    "action": "initialize_project",
                    "status": "skipped",
                    "reason": "auto_fix is disabled",
                }
            )

    # Check for virtual environment
    venv_exists, venv_path = check_project_venv(project_dir)

    if not venv_exists:
        if auto_fix:
            results["actions"].append(
                {"action": "create_venv", "description": "Creating virtual environment"}
            )

            # 'uv venv' creates .venv in CWD
            success, stdout, stderr = await run_uv_command(["venv"], cwd=project_dir)

            if success:
                results["actions"][-1]["status"] = "success"
                results["actions"][-1][
                    "output"
                ] = "Virtual environment created at .venv"
            else:
                results["actions"][-1]["status"] = "failed"
                results["actions"][-1]["error"] = stderr
                results["success"] = False
        else:
            results["actions"].append(
                {
                    "action": "create_venv",
                    "status": "skipped",
                    "reason": "auto_fix is disabled",
                }
            )

    # Check Python version availability
    # If we have a venv, check if it works. If not (or if we just created it),
    # ensure the required python version is installed.
    # We use 'uv python install' which respects .python-version or requires-python
    if (project_dir / "pyproject.toml").exists():
        # Only try to install python if we suspect an issue or just to be safe during repair
        # A simple check is to see if 'uv run python --version' works
        py_success, _, _ = await run_uv_command(
            ["run", "python", "--version"], cwd=project_dir
        )

        if not py_success:
            if auto_fix:
                results["actions"].append(
                    {
                        "action": "install_python",
                        "description": "Installing/updating Python interpreter",
                    }
                )

                # 'uv python install'
                success, stdout, stderr = await run_uv_command(
                    ["python", "install"], cwd=project_dir
                )

                if success:
                    results["actions"][-1]["status"] = "success"
                    results["actions"][-1]["output"] = (
                        stdout or "Python interpreter installed/verified"
                    )
                else:
                    results["actions"][-1]["status"] = "failed"
                    results["actions"][-1]["error"] = stderr
                    # Don't fail overall if this fails, might be network issue or already installed but other issue
            else:
                results["actions"].append(
                    {
                        "action": "install_python",
                        "status": "skipped",
                        "reason": "auto_fix is disabled",
                    }
                )

    # Sync dependencies if pyproject.toml exists
    if (project_dir / "pyproject.toml").exists():
        if auto_fix:
            results["actions"].append(
                {
                    "action": "sync_dependencies",
                    "description": "Syncing project dependencies",
                }
            )

            success, stdout, stderr = await run_uv_command(["sync"], cwd=project_dir)

            if success:
                results["actions"][-1]["status"] = "success"
                results["actions"][-1]["output"] = "Dependencies synced successfully"
            else:
                results["actions"][-1]["status"] = "failed"
                results["actions"][-1]["error"] = stderr
                # Don't mark overall as failed, sync might fail for valid reasons
        else:
            results["actions"].append(
                {
                    "action": "sync_dependencies",
                    "status": "skipped",
                    "reason": "auto_fix is disabled",
                }
            )

    return results


async def add_dependency_action(
    package: str,
    project_path: Optional[str] = None,
    dev: bool = False,
    optional: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add a new dependency to the project.

    Returns:
        Dictionary with operation results
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        return {
            "error": f"Project directory does not exist: {project_path}",
            "success": False,
        }

    # Check if uv is available
    available, version = await check_uv_available()
    if not available:
        return {
            "error": "uv is not installed. Please install uv first using the install_uv tool.",
            "success": False,
        }

    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    # Check for pyproject.toml
    if not (project_dir / "pyproject.toml").exists():
        return {
            "error": "No pyproject.toml found. Initialize a project first using repair_environment.",
            "success": False,
        }

    # Build command
    cmd = ["add", package]

    if dev:
        cmd.append("--dev")

    if optional:
        cmd.extend(["--optional", optional])

    # Execute command
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    result = {
        "package": package,
        "project_dir": str(project_dir),
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "dev": dev,
        "optional": optional,
    }

    if success:
        result["message"] = f"Successfully added {package}"
        result["output"] = stdout
    else:
        result["message"] = f"Failed to add {package}"
        result["error"] = stderr

    return result


async def remove_dependency_action(
    package: str,
    project_path: Optional[str] = None,
    dev: bool = False,
    optional: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Remove a dependency from the project.

    Returns:
        Dictionary with operation results
    """
    project_dir = Path(project_path) if project_path else Path.cwd()

    if not project_dir.exists():
        return {
            "error": f"Project directory does not exist: {project_path}",
            "success": False,
        }

    # Check if uv is available
    available, version = await check_uv_available()
    if not available:
        return {
            "error": "uv is not installed. Please install uv first using the install_uv tool.",
            "success": False,
        }

    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root

    # Check for pyproject.toml
    if not (project_dir / "pyproject.toml").exists():
        return {"error": "No pyproject.toml found.", "success": False}

    # Build command
    cmd = ["remove", package]

    if dev:
        cmd.append("--dev")

    if optional:
        cmd.extend(["--optional", optional])

    # Execute command
    success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

    result = {
        "package": package,
        "project_dir": str(project_dir),
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "dev": dev,
        "optional": optional,
    }

    if success:
        result["message"] = f"Successfully removed {package}"
        result["output"] = stdout
    else:
        result["message"] = f"Failed to remove {package}"
        result["error"] = stderr

    return result
