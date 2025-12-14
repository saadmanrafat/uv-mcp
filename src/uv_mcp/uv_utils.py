"""Utility functions for interacting with uv."""

import asyncio
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple


async def check_uv_available() -> Tuple[bool, Optional[str]]:
    """
    Check if uv is installed and available.
    
    Returns:
        Tuple of (is_available, version_string)
    """
    process = None
    try:
        # Use shutil.which to find the executable first
        uv_path = shutil.which("uv")
        if not uv_path:
            return False, None

        process = await asyncio.create_subprocess_exec(
            "uv", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=5)
        
        if process.returncode == 0:
            version = stdout_bytes.decode().strip()
            return True, version
        return False, None
    except (asyncio.TimeoutError, FileNotFoundError, OSError):
        if process:
            try:
                if process.returncode is None:
                    process.kill()
                await process.communicate()
            except (ProcessLookupError, OSError):
                pass
        return False, None


async def run_uv_command(args: list[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
    """
    Execute a uv command with given arguments.
    
    Args:
        args: List of command arguments (e.g., ["add", "requests"])
        cwd: Working directory for the command
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            "uv", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        # Increase timeout for network/install operations
        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=120)
        
        return process.returncode == 0, stdout_bytes.decode(), stderr_bytes.decode()
    except asyncio.TimeoutError:
        if process:
            try:
                if process.returncode is None:
                    process.kill()
                # Ensure we consume pipes and wait for exit
                await process.communicate()
            except (ProcessLookupError, OSError):
                pass
        return False, "", "Command timed out after 120 seconds"
    except Exception as e:
        if process:
            try:
                if process.returncode is None:
                    process.kill()
                await process.communicate()
            except (ProcessLookupError, OSError):
                pass
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


def check_project_venv(project_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Check if a virtual environment exists in the project directory.
    
    Args:
        project_dir: The project directory to check.
        
    Returns:
        Tuple of (exists, venv_path)
    """
    # Standard uv venv location
    venv_path = project_dir / ".venv"
    if venv_path.exists() and (venv_path / "pyvenv.cfg").exists():
        return True, str(venv_path)
    
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
