import logging
from pathlib import Path
from typing import Optional

from .models import ProjectInitResult, SyncResult
from .utils import run_uv_command

logger = logging.getLogger(__name__)


class ProjectTools:
    """Tools for project management using uv."""

    @staticmethod
    async def init_project(
        name: str,
        python_version: str = "3.12",
        path: str | None = None,
        template: str = "app",
    ) -> ProjectInitResult | str:
        """
        Initialize a new Python Project with uv

        Args:
            name: The name of the project.
            python_version: The Python version to use (e.g., "3.12", "3.13")
            path: Parent directory for the project. Defaults to the current.
            template: Project type ('app' for application, 'lib' for library).

        Returns:
            A message describing the result of the operation.
        """
        try:
            base_path: Path = Path(path) if path else Path.cwd()
            project_dir = base_path / name

            logger.info(
                f"Initializing project '{name}' in {base_path} with Python {python_version}"
            )

            init_args: list[str] = ["init", "--name", name, "--python", python_version]
            if template == "app":
                init_args.append("--app")
            else:
                init_args.append("--lib")

            success, stdout, stderr = await run_uv_command(init_args, cwd=base_path)
            if not success:
                logger.error(f"Failed to initialize project: {stderr}")
                return f"Failed to initialize project: {stderr}"

            logger.info("Pinning python version")
            success, stdout, stderr = await run_uv_command(
                ["python", "pin", python_version], cwd=project_dir
            )  # pin py version

            if not success:
                logger.warning(
                    f"Project initialized but failed to pin python version: {stderr}"
                )
                return f"Project initialized but failed to pin python version: {stderr}"

            return f"Successfully initialized project '{name}' with Python {python_version}"
        except Exception as e:
            logger.error(f"Error initializing project: {e}")
            return f"An unexpected error occurred: {str(e)}"

    @staticmethod
    async def sync_environment(
        project_path: str | None = None, upgrade: bool = False, locked: bool = False
    ) -> SyncResult | str:
        """
        Sync the environment with pyproject.toml or uv.lock

        Args:
            project_path: Path to the project root.
            upgrade: If True, upgrades all packages to latest compatible versions.
            locked: If True, strictly asserts that uv.lock matches pyproject.toml

        Returns:
            Output of the sync command or error message.
        """
        try:
            cmd: list[str] = ["sync"]
            if upgrade:
                cmd.append("--upgrade")
            if locked:
                cmd.append("--locked")

            project_dir = Path(project_path) if project_path else Path.cwd()
            logger.info(f"Syncing environment in {project_dir}")

            success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

            if success:
                return stdout if stdout else "Environment synced successfully."

            logger.error(f"Failed to sync environment: {stderr}")
            return f"Failed to sync environment: {stderr}"
        except Exception as e:
            logger.error(f"Error syncing environment: {e}")
            return f"An unexpected error occurred: {str(e)}"

    @staticmethod
    async def export_requirements(
        project_path: str | None = None,
        file_format: str = "requirements-txt",
        output_file: str | None = None,
    ) -> SyncResult | str:
        """
        Export dependencies to requirements.txt or other formats.

        Args:
            project_path: Path to project root.
            file_format: Format to export (default: requirements-txt).
            output_file: Optional file to write output to.

        Returns:
            Exported requirements or status message.
        """
        try:
            cmd = ["export", "--format", file_format]
            if output_file:
                cmd.extend(["--output-file", output_file])

            project_dir = Path(project_path) if project_path else Path.cwd()
            logger.info(f"Exporting requirements from {project_dir}")

            success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

            if not success:
                logger.error(f"Failed to export requirements: {stderr}")
                return f"Failed to export requirements: {stderr}"

            if output_file:
                return f"Dependencies exported to {output_file}"
            return stdout
        except Exception as e:
            logger.error(f"Error exporting requirements: {e}")
            return f"An unexpected error occurred: {str(e)}"
