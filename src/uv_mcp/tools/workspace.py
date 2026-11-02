"""Workspaces: uv workspace list / dir / metadata."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..models import WorkspaceDirResult, WorkspaceListResult, WorkspaceMetadataResult
from ..parsing import last_line, load_json
from ..registry import uv_tool
from ._common import (
    Args,
    ExtraArgs,
    Frozen,
    Locked,
    Member,
    ProjectPath,
    Script,
    extend,
    frozen_if_read_only,
    project_dir,
    run,
)


@uv_tool(title="List workspace members (uv workspace list)", toolset="project", read_only=True, idempotent=True)
async def uv_workspace_list(
    project_path: ProjectPath = None,
    paths: Annotated[bool, Field(description="Return member paths instead of names.")] = False,
    scripts: Annotated[bool, Field(description="List standalone PEP 723 scripts in the workspace instead.")] = False,
    extra_args: ExtraArgs = None,
) -> WorkspaceListResult:
    """List the members of the uv workspace containing project_path (a single project is its own workspace)."""
    cwd = project_dir(project_path)
    args = Args("workspace", "list").flag(paths, "--paths").flag(scripts, "--scripts").extra(extra_args)
    result = await run(args, cwd=cwd)
    members = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()] if result.success else []
    return extend(result, WorkspaceListResult, members=members, stdout="" if members else result.stdout)


@uv_tool(title="Locate a workspace member (uv workspace dir)", toolset="project", read_only=True, idempotent=True)
async def uv_workspace_dir(
    project_path: ProjectPath = None,
    member: Member = None,
    extra_args: ExtraArgs = None,
) -> WorkspaceDirResult:
    """Return the workspace root directory, or the directory of one member."""
    cwd = project_dir(project_path)
    result = await run(Args("workspace", "dir").opt("--package", member, "member").extra(extra_args), cwd=cwd)
    return extend(result, WorkspaceDirResult, path=last_line(result.stdout) if result.success else None)


@uv_tool(
    title="Workspace metadata (uv workspace metadata)",
    toolset="project",
    read_only=True,
    idempotent=True,
    open_world=True,
)
async def uv_workspace_metadata(
    project_path: ProjectPath = None,
    script: Script = None,
    frozen: Frozen = False,
    locked: Locked = False,
    extra_args: ExtraArgs = None,
) -> WorkspaceMetadataResult:
    """Machine-readable description of the workspace: members, environment, interpreter and resolved packages.
    Experimental in uv; the schema may change."""
    cwd = project_dir(project_path)
    args = Args("workspace", "metadata").opt("--script", script, "script").flag(frozen, "--frozen")
    args.flag(locked, "--locked").extra(extra_args)
    result = await run(frozen_if_read_only(args), cwd=cwd)
    data = load_json(result.stdout) if result.success else None
    return extend(result, WorkspaceMetadataResult, metadata=data, stdout="" if data is not None else result.stdout)
