"""Python interpreter management: uv python list / install / upgrade / uninstall / find / pin."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import Field

from ..models import CommandResult, PythonFindResult, PythonListResult, PythonPinResult
from ..parsing import last_line, load_json, parse_python_list
from ..registry import uv_tool
from ..security import ValidationError, require_values
from ._common import Args, ExtraArgs, ProjectPath, extend, project_dir, run

Versions = Annotated[
    list[str] | None,
    Field(description="Version requests such as '3.13', '3.12.4', 'pypy@3.10', '3.14t' (free-threaded)."),
]


@uv_tool(
    title="List Python installations (uv python list)",
    toolset="python",
    read_only=True,
    idempotent=True,
    open_world=True,
)
async def uv_python_list(
    request: Annotated[str | None, Field(description="Only list versions matching this request, e.g. '3.12'.")] = None,
    only_installed: Annotated[bool, Field(description="Hide versions that are only available for download.")] = False,
    all_versions: Annotated[
        bool, Field(description="Include every patch version, not just the latest per minor.")
    ] = False,
    all_platforms: Annotated[bool, Field(description="Include downloads for every OS, not just this one.")] = False,
    all_arches: Annotated[bool, Field(description="Include downloads for every CPU architecture.")] = False,
    show_urls: Annotated[bool, Field(description="Include download URLs.")] = False,
    extra_args: ExtraArgs = None,
) -> PythonListResult:
    """List Python interpreters found on this machine and versions uv can download.

    Entries with a null path are downloadable but not installed.
    """
    args = Args("python", "list", "--output-format", "json")
    args.flag(only_installed, "--only-installed").flag(all_versions, "--all-versions")
    args.flag(all_platforms, "--all-platforms").flag(all_arches, "--all-arches").flag(show_urls, "--show-urls")
    args.extra(extra_args)
    if request:
        args.positional([request], "request")
    result = await run(args)
    data = load_json(result.stdout) if result.success else None
    installations = parse_python_list(data)
    return extend(
        result, PythonListResult, installations=installations, stdout="" if data is not None else result.stdout
    )


@uv_tool(title="Install Python versions (uv python install)", toolset="python", idempotent=True, open_world=True)
async def uv_python_install(
    versions: Versions = None,
    default: Annotated[
        bool, Field(description="Also install `python`/`python3` executables on PATH for this version.")
    ] = False,
    reinstall: bool = False,
    upgrade: Annotated[bool, Field(description="Upgrade existing installs to the latest patch release.")] = False,
    force: Annotated[bool, Field(description="Replace existing python executables that uv did not install.")] = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Download and install uv-managed Python versions. With no versions, installs the version the project requires (or the latest)."""
    args = Args("python", "install").flag(default, "--default").flag(reinstall, "--reinstall")
    args.flag(upgrade, "--upgrade").flag(force, "--force").extra(extra_args).positional(versions, "version")
    return await run(args, mutating=True, lock_key="global:python")


@uv_tool(title="Upgrade Python versions (uv python upgrade)", toolset="python", idempotent=True, open_world=True)
async def uv_python_upgrade(versions: Versions = None, extra_args: ExtraArgs = None) -> CommandResult:
    """Upgrade uv-managed Python installs to their latest patch release (all of them if no versions are given)."""
    args = Args("python", "upgrade").extra(extra_args).positional(versions, "version")
    return await run(args, mutating=True, lock_key="global:python")


@uv_tool(title="Uninstall Python versions (uv python uninstall)", toolset="python", destructive=True, idempotent=True)
async def uv_python_uninstall(
    versions: Versions = None,
    all: Annotated[bool, Field(description="Uninstall every uv-managed Python version.")] = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Remove uv-managed Python installations. Virtual environments built on them will stop working."""
    if not versions and not all:
        raise ValidationError("Pass versions to uninstall, or all=true")
    if versions and all:
        raise ValidationError("Pass either versions or all=true, not both")
    args = Args("python", "uninstall").flag(all, "--all").extra(extra_args)
    if versions:
        args.positional(require_values(versions, "version"), "version")
    return await run(args, mutating=True, lock_key="global:python")


@uv_tool(title="Find a Python interpreter (uv python find)", toolset="python", read_only=True, idempotent=True)
async def uv_python_find(
    request: Annotated[
        str | None, Field(description="Version request, e.g. '3.12'. Defaults to the project's requirement.")
    ] = None,
    project_path: ProjectPath = None,
    system: Annotated[
        bool, Field(description="Ignore virtual environments and only consider system interpreters.")
    ] = False,
    script: Annotated[str | None, Field(description="Find the interpreter for this PEP 723 script.")] = None,
    extra_args: ExtraArgs = None,
) -> PythonFindResult:
    """Return the path of the interpreter uv would use (honouring .python-version, requires-python and .venv)."""
    cwd = project_dir(project_path)
    args = Args("python", "find").flag(system, "--system").opt("--script", script, "script").extra(extra_args)
    if request:
        args.positional([request], "request")
    result = await run(args, cwd=cwd)
    return extend(result, PythonFindResult, path=last_line(result.stdout) if result.success else None)


@uv_tool(title="Pin the project's Python version (uv python pin)", toolset="python", idempotent=True)
async def uv_python_pin(
    version: Annotated[
        str | None, Field(description="Version to pin, e.g. '3.12'. Omit to show the current pin.")
    ] = None,
    project_path: ProjectPath = None,
    global_pin: Annotated[
        bool, Field(description="Write the user-level default pin (uv --global) instead of the project's.")
    ] = False,
    resolved: Annotated[
        bool, Field(description="Pin the full interpreter version/path instead of the request as typed.")
    ] = False,
    remove: Annotated[bool, Field(description="Delete the .python-version pin.")] = False,
    extra_args: ExtraArgs = None,
) -> PythonPinResult:
    """Read or write .python-version, which selects the interpreter uv uses for the project."""
    cwd = project_dir(project_path)
    if remove and version:
        raise ValidationError("Pass either version or remove=true, not both")
    args = (
        Args("python", "pin")
        .flag(global_pin, "--global")
        .flag(resolved, "--resolved")
        .flag(remove, "--rm")
        .extra(extra_args)
    )
    if version:
        args.positional([version], "version")
    result = await run(args, cwd=cwd, mutating=bool(version or remove))
    pinned = None
    if result.success and not remove:
        line = last_line(result.stdout) or ""
        quoted = [q for q in re.findall(r"`([^`]+)`", line) if q != ".python-version"]
        pinned = quoted[-1] if quoted else (line or None)
    return extend(result, PythonPinResult, pinned=pinned)
