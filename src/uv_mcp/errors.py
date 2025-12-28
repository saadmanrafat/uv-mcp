"""Enhanced error handling with actionable suggestions."""

from typing import Optional


class UVMCPError(Exception):
    """Base exception for UV-MCP with actionable suggestions."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.suggestion = suggestion
        self.error_code = error_code
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert error to a dictionary for JSON serialization."""
        result = {"error": self.message}
        if self.suggestion:
            result["suggestion"] = self.suggestion
        if self.error_code:
            result["error_code"] = self.error_code
        return result


class UVNotInstalledError(UVMCPError):
    """Raised when uv is not installed."""

    def __init__(self):
        super().__init__(
            message="uv is not installed on this system",
            suggestion="Install uv using: curl -LsSf https://astral.sh/uv/install.sh | sh\nOr use the uv_install tool for platform-specific instructions",
            error_code="UV_NOT_FOUND",
        )


class ProjectNotFoundError(UVMCPError):
    """Raised when project directory is not found."""

    def __init__(self, path: str):
        super().__init__(
            message=f"Project directory does not exist: {path}",
            suggestion=f"Check the path is correct or initialize a new project with uv_initialize_project",
            error_code="PROJECT_NOT_FOUND",
        )


class PyProjectNotFoundError(UVMCPError):
    """Raised when pyproject.toml is not found."""

    def __init__(self, project_dir: str):
        super().__init__(
            message=f"No pyproject.toml found in {project_dir}",
            suggestion="Initialize the project with uv_initialize_project or uv_repair_environment",
            error_code="PYPROJECT_MISSING",
        )


class DependencyConflictError(UVMCPError):
    """Raised when there are dependency conflicts."""

    def __init__(self, details: str):
        super().__init__(
            message=f"Dependency conflicts detected: {details}",
            suggestion="Try resolving conflicts by:\n1. Check version constraints in pyproject.toml\n2. Run uv_lock_project to regenerate lockfile\n3. Consider updating packages with uv_sync_environment(upgrade=True)",
            error_code="DEPENDENCY_CONFLICT",
        )


class VirtualEnvMissingError(UVMCPError):
    """Raised when virtual environment is missing."""

    def __init__(self, project_dir: str):
        super().__init__(
            message=f"No virtual environment found in {project_dir}",
            suggestion="Create a virtual environment with uv_repair_environment",
            error_code="VENV_MISSING",
        )


class PackageNotFoundError(UVMCPError):
    """Raised when a package is not found."""

    def __init__(self, package: str):
        super().__init__(
            message=f"Package not found: {package}",
            suggestion=f"Check the package name is correct. Search on PyPI: https://pypi.org/search/?q={package}",
            error_code="PACKAGE_NOT_FOUND",
        )


class InvalidPythonVersionError(UVMCPError):
    """Raised when Python version is invalid or incompatible."""

    def __init__(self, version: str, details: str = ""):
        super().__init__(
            message=f"Invalid or incompatible Python version: {version}. {details}",
            suggestion="Check available Python versions with uv_list_python_versions\nInstall a specific version with uv_install_python_version",
            error_code="INVALID_PYTHON_VERSION",
        )


def get_error_suggestion(stderr: str) -> Optional[str]:
    """
    Parse error messages and provide actionable suggestions.

    Args:
        stderr: The error output from a uv command

    Returns:
        Actionable suggestion string or None
    """
    stderr_lower = stderr.lower()

    # UV not found
    if "uv: command not found" in stderr_lower or "not found" in stderr_lower:
        return "Install uv using: curl -LsSf https://astral.sh/uv/install.sh | sh"

    # Missing pyproject.toml
    if (
        "no pyproject.toml" in stderr_lower
        or "pyproject.toml not found" in stderr_lower
    ):
        return "Initialize project with: uv_initialize_project or uv_repair_environment"

    # Permission denied
    if "permission denied" in stderr_lower:
        return "Check file permissions or run with appropriate privileges"

    # Network errors
    if (
        "connection" in stderr_lower
        or "network" in stderr_lower
        or "timeout" in stderr_lower
    ):
        return "Check your internet connection and try again. You may need to configure proxy settings."

    # Dependency resolution failures
    if "could not find a version" in stderr_lower or "no solution" in stderr_lower:
        return "Check version constraints in pyproject.toml. The requested versions may be incompatible."

    # Lock file issues
    if "lock" in stderr_lower and "outdated" in stderr_lower:
        return "Update the lockfile with: uv_lock_project"

    # Package not found
    if (
        "package not found" in stderr_lower
        or "no matching distribution" in stderr_lower
    ):
        return "Verify the package name is correct on PyPI: https://pypi.org"

    # Python version issues
    if "python version" in stderr_lower or "requires python" in stderr_lower:
        return "Install required Python version with: uv_install_python_version"

    return None
