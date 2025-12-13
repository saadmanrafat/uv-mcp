"""Utility functions for interacting with uv."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def check_uv_available() -> Tuple[bool, Optional[str]]:
    """
    Check if uv is installed and available.
    
    Returns:
        Tuple of (is_available, version_string)
    """
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, None


def run_uv_command(args: list[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
    """
    Execute a uv command with given arguments.
    
    Args:
        args: List of command arguments (e.g., ["add", "requests"])
        cwd: Working directory for the command
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["uv"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 60 seconds"
    except Exception as e:
        return False, "", str(e)


def get_project_info(project_dir: Optional[Path] = None) -> dict:
    """
    Extract project metadata from pyproject.toml.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        
    Returns:
        Dictionary with project information
    """
    if project_dir is None:
        project_dir = Path.cwd()
    
    pyproject_path = project_dir / "pyproject.toml"
    
    info = {
        "has_pyproject": pyproject_path.exists(),
        "has_requirements": (project_dir / "requirements.txt").exists(),
        "has_lockfile": (project_dir / "uv.lock").exists(),
        "project_dir": str(project_dir)
    }
    
    if info["has_pyproject"]:
        try:
            import tomllib
        except ImportError:
            # Python < 3.11
            try:
                import tomli as tomllib
            except ImportError:
                info["parse_error"] = "tomllib/tomli not available"
                return info
        
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                info["project_name"] = data.get("project", {}).get("name", "unknown")
                info["python_version"] = data.get("project", {}).get("requires-python", "unknown")
                info["dependencies"] = data.get("project", {}).get("dependencies", [])
        except Exception as e:
            info["parse_error"] = str(e)
    
    return info


def check_virtual_env() -> Tuple[bool, Optional[str]]:
    """
    Check if running in a virtual environment.
    
    Returns:
        Tuple of (in_venv, venv_path)
    """
    # Check for virtual environment
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        return True, venv_path
    
    # Check if we're in a venv by looking at sys.prefix
    if sys.prefix != sys.base_prefix:
        return True, sys.prefix
    
    return False, None


def find_uv_project_root(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find the root directory of a uv project by looking for pyproject.toml.
    
    Args:
        start_dir: Directory to start searching from (defaults to current directory)
        
    Returns:
        Path to project root or None if not found
    """
    if start_dir is None:
        start_dir = Path.cwd()
    
    current = start_dir.resolve()
    
    # Search up the directory tree
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    
    # Check root directory
    if (current / "pyproject.toml").exists():
        return current
    
    return None


import os
