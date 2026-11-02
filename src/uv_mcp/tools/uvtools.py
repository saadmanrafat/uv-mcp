"""Python CLI tools: uv tool run (uvx) / install / upgrade / uninstall / list."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..models import CommandResult, ToolListResult
from ..parsing import parse_tool_list
from ..registry import uv_tool
from ..security import ValidationError, require_values, safe_env, safe_value
from ._common import Args, ExtraArgs, PythonRequest, TimeoutSeconds, extend, project_dir, run

_TOOL_LOCK = "global:tools"


@uv_tool(
    title="Run a tool without installing it (uvx / uv tool run)", toolset="tool", destructive=True, open_world=True
)
async def uv_tool_run(
    command: Annotated[
        list[str],
        Field(
            description="Tool executable and arguments, e.g. ['ruff', 'check', '.'] or ['pycowsay', 'hi'].",
            min_length=1,
        ),
    ],
    from_package: Annotated[
        str | None,
        Field(
            description="Package providing the executable when names differ or to pin a version, e.g. 'httpie', 'ruff==0.6.0'."
        ),
    ] = None,
    with_packages: Annotated[
        list[str] | None, Field(description="Extra packages to install alongside the tool.")
    ] = None,
    project_path: Annotated[
        str | None, Field(description="Working directory for the tool (default: workspace root).")
    ] = None,
    python: PythonRequest = None,
    isolated: Annotated[bool, Field(description="Ignore any installed version of the tool.")] = False,
    env: Annotated[dict[str, str] | None, Field(description="Extra environment variables.")] = None,
    timeout_seconds: TimeoutSeconds = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Run a Python command-line tool in a cached, ephemeral environment (what `uvx` does).

    Ideal for one-off linters, formatters and generators without adding them to the project.
    """
    cwd = project_dir(project_path)
    program = safe_value(command[0], "command[0]")
    if any("\x00" in a for a in command):
        raise ValidationError("command arguments must not contain NUL bytes")
    args = (
        Args("tool", "run").opt("--from", from_package, "from_package").many("--with", with_packages, "with_packages")
    )
    args.opt("--python", python, "python").flag(isolated, "--isolated").extra(extra_args)
    args.argv += ["--", program, *command[1:]]
    return await run(args, cwd=cwd, env=safe_env(env), timeout=timeout_seconds)


@uv_tool(title="Install a CLI tool (uv tool install)", toolset="tool", idempotent=True, open_world=True)
async def uv_tool_install(
    package: Annotated[
        str, Field(description="Package to install, optionally with a version or URL, e.g. 'ruff', 'black==24.1.0'.")
    ],
    with_packages: Annotated[
        list[str] | None, Field(description="Extra packages to include in the tool's environment.")
    ] = None,
    editable: bool = False,
    force: Annotated[bool, Field(description="Overwrite executables that already exist on PATH.")] = False,
    upgrade: bool = False,
    python: PythonRequest = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Install a Python CLI tool into its own isolated environment and put its executables on PATH (user-wide)."""
    args = Args("tool", "install").many("--with", with_packages, "with_packages").flag(editable, "--editable")
    args.flag(force, "--force").flag(upgrade, "--upgrade").opt("--python", python, "python").extra(extra_args)
    args.argv.append(safe_value(package, "package"))
    return await run(args, mutating=True, lock_key=_TOOL_LOCK)


@uv_tool(title="Upgrade installed tools (uv tool upgrade)", toolset="tool", idempotent=True, open_world=True)
async def uv_tool_upgrade(
    packages: Annotated[list[str] | None, Field(description="Tools to upgrade.")] = None,
    all: Annotated[bool, Field(description="Upgrade every installed tool.")] = False,
    python: PythonRequest = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Upgrade installed tools to the latest versions their constraints allow."""
    if bool(packages) == bool(all):
        raise ValidationError("Pass either packages or all=true")
    args = Args("tool", "upgrade").flag(all, "--all").opt("--python", python, "python").extra(extra_args)
    args.positional(packages, "package")
    return await run(args, mutating=True, lock_key=_TOOL_LOCK)


@uv_tool(title="Uninstall tools (uv tool uninstall)", toolset="tool", destructive=True, idempotent=True)
async def uv_tool_uninstall(
    packages: Annotated[list[str] | None, Field(description="Tools to uninstall.")] = None,
    all: Annotated[bool, Field(description="Uninstall every tool.")] = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Remove installed tools and their executables."""
    if bool(packages) == bool(all):
        raise ValidationError("Pass either packages or all=true")
    args = Args("tool", "uninstall").flag(all, "--all").extra(extra_args)
    if packages:
        args.positional(require_values(packages, "package"), "package")
    return await run(args, mutating=True, lock_key=_TOOL_LOCK)


@uv_tool(title="List installed tools (uv tool list)", toolset="tool", read_only=True, idempotent=True)
async def uv_tool_list(
    outdated: Annotated[
        bool, Field(description="Only show tools with newer versions available (queries the index).")
    ] = False,
    extra_args: ExtraArgs = None,
) -> ToolListResult:
    """List tools installed with uv tool install, their versions and executables."""
    args = Args("tool", "list", "--show-paths").flag(outdated, "--outdated").extra(extra_args)
    result = await run(args)
    tools = parse_tool_list(result.stdout) if result.success else []
    return extend(result, ToolListResult, tools=tools, stdout="" if tools else result.stdout)
