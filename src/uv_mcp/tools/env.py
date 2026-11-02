"""Virtual environments: uv venv."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..config import get_settings
from ..models import VenvResult
from ..registry import uv_tool
from ..security import resolve_path
from ._common import Args, ExtraArgs, ProjectPath, PythonRequest, extend, project_dir, run


@uv_tool(title="Create a virtual environment (uv venv)", toolset="venv", open_world=True)
async def uv_venv(
    project_path: ProjectPath = None,
    path: Annotated[
        str | None, Field(description="Environment directory, relative to project_path (default: .venv).")
    ] = None,
    python: PythonRequest = None,
    seed: Annotated[
        bool, Field(description="Install pip (and setuptools/wheel on old Pythons) into the venv.")
    ] = False,
    clear: Annotated[bool, Field(description="Replace an existing environment at this path.")] = False,
    prompt: Annotated[str | None, Field(description="Prompt prefix shown when the venv is activated.")] = None,
    allow_existing: Annotated[bool, Field(description="Reuse an existing environment instead of failing.")] = False,
    system_site_packages: bool = False,
    relocatable: bool = False,
    extra_args: ExtraArgs = None,
) -> VenvResult:
    """Create a virtual environment. For uv projects, uv_sync creates and fills .venv automatically."""
    cwd = project_dir(project_path)
    target = resolve_path(path or ".venv", get_settings(), base=cwd, what="path")
    args = Args("venv").opt("--python", python, "python").flag(seed, "--seed").flag(clear, "--clear")
    args.opt("--prompt", prompt, "prompt").flag(system_site_packages, "--system-site-packages")
    args.flag(relocatable, "--relocatable").flag(allow_existing, "--allow-existing")
    args.extra(extra_args)
    args.argv.append(str(target))
    result = await run(args, cwd=cwd, mutating=True)
    return extend(result, VenvResult, path=str(target))
