import subprocess
import logging

from pathlib import Path
from typing import Optional, List
from mcp.server.fastmcp import FastMCP, Context

from .uv_utils import run_uv_command

logger = logging.getLogger(__name__)

class ProjectTools:
    @staticmethod
    async def init_project(
        name: str,
        python_version: str = "3.13",
        path: Optional[str] = None,
        template: str = "app",
    ) -> str:
        """
        Initialize a new Python Project with uv

        Args:
            name: The name of the project.
            python_version: The Python version to use (e.g., "3.12", "3.13")
            path: Parent directory for the project. Defaults to the current.
            template: Project type ('app' for application, 'lib' for library).
        """
        try:
            base_path: Path = Path(path) if path else Path.cwd()
            project_dir = base_path / name
            init_args: List[str] = ["init", "--name", name, "--python", python_version]
            if template == "app":
                init_args.append("--app")
            else:
                init_args.append("--lib")

            success, stdout, stderr = await run_uv_command(init_args, cwd=base_path)
            if not success:
                return f"Failed to initialize project: {stderr}"

            success, stdout, stderr = await run_uv_command(
                ["python", "pin", python_version], cwd=project_dir
            )  # pin py version
            if not success:
                return f"Project initialized but failed to pin python version: {stderr}"

            return f"Successfully initialized project '{name}' with Python {python_version}"
        except Exception as e:
            logger.error(f"Error initializing project: {e}")
            return f"An unexpected error occurred: {str(e)}"

    @staticmethod
    async def sync_environment(
        project_path: Optional[str] = None, upgrade: bool = False, locked: bool = False
    ) -> str:
        """
        Sync the environment with pyproject.toml or uv.lock

        Args:
            project_path: Path to the project root.
            upgrade: If True, upgrades all packages to latest compatible versions.
            locked: If True, strictly asserts that uv.lock matches pyproject.toml
        """
        try:
            cmd: List[str] = ["sync"]
            if upgrade:
                cmd.append("--upgrade")
            if locked:
                cmd.append("--locked")
            
            project_dir = Path(project_path) if project_path else Path.cwd()
            success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)
            
            if success:
                return stdout if stdout else "Environment synced successfully."
            return f"Failed to sync environment: {stderr}"
        except Exception as e:
            logger.error(f"Error syncing environment: {e}")
            return f"An unexpected error occurred: {str(e)}"

    @staticmethod
    async def export_requirements(
        project_path: Optional[str] = None,
        file_format: str = "requirements-txt",
        output_file: Optional[str] = None,
    ) -> str:
        """
        Export dependencies to requirements.txt or other formats.
        """
        try:
            cmd = ["export", "--format", file_format]
            if output_file:
                cmd.extend(["--output-file", output_file])
            
            project_dir = Path(project_path) if project_path else Path.cwd()
            success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

            if not success:
                 return f"Failed to export requirements: {stderr}"

            if output_file:
                return f"Dependencies exported to {output_file}"
            return stdout
        except Exception as e:
            logger.error(f"Error exporting requirements: {e}")
            return f"An unexpected error occurred: {str(e)}"

    @staticmethod
    async def remove_dependency(
        package: str, project_path: Optional[str] = None, dev: bool = False
    ) -> str:
        """
        Remove a dependency from the project
        """
        try:
            cmd = ["remove", package]
            if dev:
                cmd.append("--dev")
            
            project_dir = Path(project_path) if project_path else Path.cwd()
            success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)
            
            if success:
                return stdout if stdout else f"Successfully removed {package}"
            return f"Failed to remove dependency: {stderr}"
        except Exception as e:
            logger.error(f"Error removing dependency: {e}")
            return f"An unexpected error occurred: {str(e)}"
