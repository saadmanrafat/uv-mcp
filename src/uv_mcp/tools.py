import logging
from pathlib import Path

from .models import ProjectInitResult, SyncResult, ExportResult
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
    ) -> ProjectInitResult:
        """
        Initialize a new Python Project with uv

        Args:
            name: The name of the project.
            python_version: The Python version to use (e.g., "3.12", "3.13")
            path: Parent directory for the project. Defaults to the current.
            template: Project type ('app' for application, 'lib' for library).

        Returns:
            ProjectInitResult describing the result of the operation.
        """
        base_path: Path = Path(path).resolve() if path else Path.cwd().resolve()
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
            return ProjectInitResult(
                project_name=name,
                project_dir=str(project_dir),
                python_version=python_version,
                template=template,
                success=False,
                error=f"Failed to initialize project: {stderr}",
            )

        logger.info("Pinning python version")
        pin_success, pin_stdout, pin_stderr = await run_uv_command(
            ["python", "pin", python_version], cwd=project_dir
        )

        if not pin_success:
            logger.warning(
                f"Project initialized but failed to pin python version: {pin_stderr}"
            )
            return ProjectInitResult(
                project_name=name,
                project_dir=str(project_dir),
                python_version=python_version,
                template=template,
                success=False,
                error=f"Project initialized but failed to pin python version: {pin_stderr}",
            )

        created_files = ["pyproject.toml", ".python-version"]
        return ProjectInitResult(
            project_name=name,
            project_dir=str(project_dir),
            python_version=python_version,
            template=template,
            success=True,
            message=f"Successfully initialized project '{name}' with Python {python_version}",
            created_files=created_files,
        )

    @staticmethod
    async def sync_environment(
        project_path: str | None = None, upgrade: bool = False, locked: bool = False
    ) -> SyncResult:
        """
        Sync the environment with pyproject.toml or uv.lock

        Args:
            project_path: Path to the project root.
            upgrade: If True, upgrades all packages to latest compatible versions.
            locked: If True, strictly asserts that uv.lock matches pyproject.toml

        Returns:
            SyncResult with operation status.
        """
        cmd: list[str] = ["sync"]
        if upgrade:
            cmd.append("--upgrade")
        if locked:
            cmd.append("--locked")

        project_dir = Path(project_path).resolve() if project_path else Path.cwd().resolve()
        logger.info(f"Syncing environment in {project_dir}")

        success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

        return SyncResult(
            project_dir=str(project_dir),
            success=success,
            upgraded=upgrade,
            locked=locked,
            message="Environment synced successfully." if success else f"Failed to sync environment: {stderr}",
            output=stdout if success else None,
            error=stderr if not success else None,
        )

    @staticmethod
    async def export_requirements(
        project_path: str | None = None,
        file_format: str = "requirements-txt",
        output_file: str | None = None,
    ) -> ExportResult:
        """
        Export dependencies to requirements.txt or other formats.

        Args:
            project_path: Path to project root.
            file_format: Format to export (default: requirements-txt).
            output_file: Optional file to write output to.

        Returns:
            ExportResult with operation status.
        """
        cmd = ["export", "--format", file_format]
        if output_file:
            cmd.extend(["--output-file", output_file])

        project_dir = Path(project_path).resolve() if project_path else Path.cwd().resolve()
        logger.info(f"Exporting requirements from {project_dir}")

        success, stdout, stderr = await run_uv_command(cmd, cwd=project_dir)

        return ExportResult(
            project_dir=str(project_dir),
            file_format=file_format,
            output_file=output_file,
            success=success,
            content=stdout if success and not output_file else None,
            message=f"Dependencies exported to {output_file}" if success and output_file else (
                "Export completed successfully." if success else f"Failed to export requirements: {stderr}"
            ),
            error=stderr if not success else None,
        )
