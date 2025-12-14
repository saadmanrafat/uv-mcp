"""Environment diagnostics for Python projects using uv."""

from pathlib import Path
from typing import Optional
import sys

from .uv_utils import (
    check_uv_available,
    get_project_info,
    check_project_venv,
    run_uv_command,
    find_uv_project_root
)


def check_project_structure(project_dir: Optional[Path] = None) -> dict:
    """
    Validate project file structure.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        
    Returns:
        Dictionary with structure validation results
    """
    if project_dir is None:
        project_dir = Path.cwd()
    
    results = {
        "valid": True,
        "issues": [],
        "warnings": []
    }
    
    # Check for project configuration
    if not (project_dir / "pyproject.toml").exists():
        if not (project_dir / "requirements.txt").exists():
            results["valid"] = False
            results["issues"].append("No pyproject.toml or requirements.txt found")
        else:
            results["warnings"].append("Using requirements.txt instead of pyproject.toml (consider migrating)")
    
    # Check for virtual environment
    venv_exists, _ = check_project_venv(project_dir)
    if not venv_exists:
        results["warnings"].append("No .venv detected in project root")
    
    # Check for lockfile
    if (project_dir / "pyproject.toml").exists() and not (project_dir / "uv.lock").exists():
        results["warnings"].append("No uv.lock file found (run 'uv lock' to create)")
    
    return results


async def check_dependencies(project_dir: Optional[Path] = None) -> dict:
    """
    Analyze dependency health.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        
    Returns:
        Dictionary with dependency analysis results
    """
    if project_dir is None:
        project_dir = Path.cwd()
    
    results = {
        "healthy": True,
        "issues": [],
        "warnings": []
    }
    
    # Get project info
    info = get_project_info(project_dir)
    
    if not info["has_pyproject"] and not info["has_requirements"]:
        results["healthy"] = False
        results["issues"].append("No dependency file found")
        return results
    
    # Check for dependency conflicts using uv pip check
    success, stdout, stderr = await run_uv_command(["pip", "check"], cwd=project_dir)
    
    if success:
        # Command succeeded, check the output
        if "No broken requirements found" in stdout or "No broken requirements found" in stderr:
            # All good, no conflicts
            pass
        else:
            # Command succeeded but found issues
            results["healthy"] = False
            results["issues"].append(f"Dependency conflicts detected in output")
    else:
        # Command failed
        results["healthy"] = False
        results["issues"].append(f"Failed to check dependencies: {stderr}")
    
    # Check if dependencies are installed
    if info["has_pyproject"]:
        success, stdout, stderr = await run_uv_command(["pip", "list"], cwd=project_dir)
        if success:
            lines = stdout.strip().split("\n")
            installed_count = max(0, len(lines) - 2)  # Prevent negative counts
            results["installed_packages"] = installed_count
        else:
            results["warnings"].append("Could not list installed packages")
    
    return results


def check_python_version(project_dir: Optional[Path] = None) -> dict:
    """
    Validate Python version requirements.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        
    Returns:
        Dictionary with Python version validation results
    """
    
    if project_dir is None:
        project_dir = Path.cwd()
    
    results = {
        "compatible": True,
        "current_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "issues": [],
        "warnings": []
    }
    
    info = get_project_info(project_dir)
    
    if "python_version" in info and info["python_version"] != "unknown":
        required = info["python_version"]
        results["required_version"] = required
        
        # Basic version check (simplified)
        if ">=" in required:
            # min_version = required.split(">=")[1].strip()
            results["warnings"].append(f"Project requires Python {required}")
        elif "==" in required:
            exact_version = required.split("==")[1].strip()
            if exact_version not in results["current_version"]:
                results["compatible"] = False
                results["issues"].append(f"Python version mismatch: need {exact_version}, have {results['current_version']}")
    
    return results


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


async def generate_diagnostic_report(project_dir: Optional[Path] = None) -> dict:
    """
    Generate a comprehensive environment health report.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        
    Returns:
        Dictionary with complete diagnostic report
    """
    if project_dir is None:
        project_dir = Path.cwd()
    
    # Find project root
    root = find_uv_project_root(project_dir)
    if root:
        project_dir = root
    
    report = {
        "project_dir": str(project_dir),
        "timestamp": None,  # Will be set by server
        "overall_health": "healthy"
    }
    
    # Check uv installation
    uv_available, uv_version = await check_uv_available()
    report["uv"] = {
        "installed": uv_available,
        "version": uv_version
    }
    
    if not uv_available:
        report["overall_health"] = "critical"
        report["critical_issues"] = ["uv is not installed"]
        return report
    
    # Check project structure
    structure = check_project_structure(project_dir)
    report["structure"] = structure
    
    if not structure["valid"]:
        report["overall_health"] = _get_worst_health(report["overall_health"], "critical")
    elif structure["warnings"]:
        report["overall_health"] = _get_worst_health(report["overall_health"], "warning")
    
    # Check dependencies
    dependencies = await check_dependencies(project_dir)
    report["dependencies"] = dependencies
    
    if not dependencies["healthy"]:
        report["overall_health"] = _get_worst_health(report["overall_health"], "critical")
    
    # Check Python version
    python_check = check_python_version(project_dir)
    report["python"] = python_check
    
    if not python_check["compatible"]:
        report["overall_health"] = _get_worst_health(report["overall_health"], "critical")
    
    # Check virtual environment
    venv_exists, venv_path = check_project_venv(project_dir)
    report["virtual_env"] = {
        "active": venv_exists, # in this context "active" just means exists in project
        "path": venv_path
    }
    
    # Get project info
    report["project_info"] = get_project_info(project_dir)
    
    return report
