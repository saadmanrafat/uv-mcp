"""Higher-level helpers: project introspection, health check and repair."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..config import get_settings
from ..diagnostics import diagnose, project_info, repair
from ..models import DiagnosticReport, ProjectInfo, RepairResult
from ..registry import uv_tool
from ._common import ProjectPath, project_dir


@uv_tool(
    title="Summarise a project (pyproject, lockfile, venv)", toolset="diagnostics", read_only=True, idempotent=True
)
async def uv_project_info(project_path: ProjectPath = None) -> ProjectInfo:
    """Read pyproject.toml and the project tree: name, version, requires-python, dependencies, groups, extras,
    scripts, workspace members, lockfile, .python-version and .venv. Fast; runs no commands."""
    return project_info(project_dir(project_path))


@uv_tool(title="Diagnose environment health", toolset="diagnostics", read_only=True, idempotent=True, open_world=True)
async def uv_diagnose(project_path: ProjectPath = None) -> DiagnosticReport:
    """Check that uv works, the project is valid, an interpreter is available, uv.lock is current, .venv exists
    and matches the lockfile, and installed packages are consistent. Each finding includes a suggested fix."""
    return await diagnose(project_dir(project_path), get_settings())


@uv_tool(title="Repair the project environment", toolset="diagnostics", idempotent=True, open_world=True)
async def uv_repair(
    project_path: ProjectPath = None,
    dry_run: Annotated[bool, Field(description="Only return the planned steps without running them.")] = False,
) -> RepairResult:
    """Fix what uv_diagnose finds: install the required Python, recreate a broken .venv, refresh uv.lock and
    sync (reinstalling if packages are inconsistent). Never edits pyproject.toml. Re-diagnoses afterwards."""
    return await repair(project_dir(project_path), get_settings(), dry_run=dry_run)
