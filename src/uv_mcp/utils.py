"""Utility functions for interacting with uv."""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_CHECK_TIMEOUT,
    DEFAULT_COMMAND_TIMEOUT,
    MAX_CONCURRENT_COMMANDS,
)

# Configure logger
logger = logging.getLogger(__name__)


class UVError(Exception):
    """Base exception for UV operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UVNotFoundError(UVError):
    """Raised when uv executable is not found."""

    pass


class ProjectNotFoundError(UVError):
    """Raised when project directory does not exist."""

    pass


class PyProjectNotFoundError(UVError):
    """Raised when pyproject.toml is missing."""

    pass


class UVCommandError(UVError):
    """Raised when a uv command fails."""

    def __init__(self, command: list[str], return_code: int, stderr: str):
        self.command = command
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(
            f"Command '{' '.join(command)}' failed with code {return_code}: {stderr}"
        )


class UVTimeoutError(UVError):
    """Raised when a uv command times out."""

    def __init__(self, command: list[str], timeout: float):
        self.command = command
        self.timeout = timeout
        super().__init__(
            f"Command '{' '.join(command)}' timed out after {timeout} seconds"
        )


async def check_uv_available() -> tuple[bool, str | None]:
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
            logger.debug("uv executable not found in PATH")
            return False, None

        process = await asyncio.create_subprocess_exec(
            "uv",
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=DEFAULT_CHECK_TIMEOUT
        )

        if process.returncode == 0:
            version = stdout_bytes.decode().strip()
            return True, version

        logger.warning(
            f"uv --version failed with code {process.returncode}: {stderr_bytes.decode()}"
        )
        return False, None
    except asyncio.TimeoutError:
        logger.warning("uv --version timed out")
        return False, None
    except (FileNotFoundError, OSError) as e:
        logger.error(f"Error checking uv availability: {e}")
        return False, None
    finally:
        if process:
            try:
                if process.returncode is None:
                    process.kill()
                    # no await process.wait() here to avoid potential hanging if something is wrong,
                    # but typically kill() + OS cleanup is enough for zombification protection 
                    # in this specific check context. 
                    # For strictness, we can attempt wait() with timeout if needed, 
                    # but just kill is usually sufficient for simple checks.
            except (ProcessLookupError, OSError):
                pass


# Global semaphore for concurrency limiting
_COMMAND_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_COMMANDS)


async def run_uv_command(
    args: list[str],
    cwd: Path | None = None,
    timeout: float = DEFAULT_COMMAND_TIMEOUT,
    env: dict[str, str] | None = None,
) -> tuple[bool, str, str]:
    """
    Execute a uv command with given arguments.

    Args:
        args: List of command arguments (e.g., ["add", "requests"])
        cwd: Working directory for the command
        timeout: Timeout in seconds (default: 120.0)
        env: Optional dictionary of environment variables

    Returns:
        Tuple of (success, stdout, stderr)
    """
    async with _COMMAND_SEMAPHORE:
        process = None
        try:
            logger.debug(f"Running uv command: uv {' '.join(args)} in {cwd or 'cwd'}")
            process = await asyncio.create_subprocess_exec(
                "uv",
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            stdout = stdout_bytes.decode()
            stderr = stderr_bytes.decode()

            if process.returncode != 0:
                logger.warning(f"uv command failed: {stderr}")
                return False, stdout, stderr

            return True, stdout, stderr

        except asyncio.TimeoutError:
            logger.error(f"uv command timed out after {timeout}s: uv {' '.join(args)}")
            if process:
                try:
                    if process.returncode is None:
                        process.kill()
                    await process.communicate()
                except (ProcessLookupError, OSError):
                    pass
            return False, "", f"Command timed out after {timeout} seconds"

        except Exception as e:
            logger.error(f"Unexpected error running uv command: {e}")
            if process:
                try:
                    if process.returncode is None:
                        process.kill()
                    await process.communicate()
                except (ProcessLookupError, OSError):
                    pass
            return False, "", str(e)


def get_project_info(project_dir: Path | None = None) -> dict[str, Any]:
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

    info: dict[str, Any] = {
        "has_pyproject": pyproject_path.exists(),
        "has_requirements": (project_dir / "requirements.txt").exists(),
        "has_lockfile": (project_dir / "uv.lock").exists(),
        "project_dir": str(project_dir),
        "dependencies": [],
        "project_name": "unknown",
        "python_version": "unknown",
    }

    if info["has_pyproject"]:
        try:
            import tomllib
        except ImportError:
            # Python < 3.11
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                info["parse_error"] = "tomllib/tomli not available"
                logger.error("tomllib/tomli not available for parsing pyproject.toml")
                return info

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                project_table = data.get("project", {})
                info["project_name"] = project_table.get("name", "unknown")
                info["python_version"] = project_table.get("requires-python", "unknown")
                info["dependencies"] = project_table.get("dependencies", [])
        except Exception as e:
            info["parse_error"] = str(e)
            logger.error(f"Error parsing pyproject.toml: {e}")

    return info


def check_project_venv(project_dir: Path) -> tuple[bool, str | None]:
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


def find_uv_project_root(start_dir: Path | None = None) -> Path | None:
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


def validate_project_path(path: str | None) -> Path:
    """
    Validate project path and return Path object.

    Args:
        path: Path string or None

    Returns:
        Path object pointing to project directory

    Raises:
        ProjectNotFoundError: If directory does not exist
    """
    project_dir = Path(path) if path else Path.cwd()
    if not project_dir.exists():
        raise ProjectNotFoundError(f"Project directory does not exist: {path}")
    return project_dir
