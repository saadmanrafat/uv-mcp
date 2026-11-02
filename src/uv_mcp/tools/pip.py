"""The pip-compatible interface: uv pip install / uninstall / list / show / freeze /
tree / check / compile / sync.

These operate on an *environment* rather than a project. Without ``python`` or
``system``, uv targets the virtual environment in the project directory (or a
parent). Prefer the project tools (uv_add, uv_sync) for uv-managed projects.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..config import get_settings
from ..models import CommandResult, PipCompileResult, PipListResult, PipShowResult
from ..parsing import load_json, parse_pip_list, parse_pip_show
from ..registry import uv_tool
from ..security import ValidationError, require_values, resolve_path
from ._common import Args, ExtraArgs, ProjectPath, Resolver, extend, project_dir, run

EnvPython = Annotated[
    str | None,
    Field(
        description="Target environment: venv path, python path or version (default: .venv in project_path or a parent)."
    ),
]
System = Annotated[
    bool,
    Field(description="Target the system Python. Avoid unless the user asked for it."),
]
Constraints = Annotated[list[str] | None, Field(description="Constraint files (-c) limiting resolved versions.")]
Overrides = Annotated[list[str] | None, Field(description="Override files forcing specific versions.")]
Requirements = Annotated[
    list[str] | None,
    Field(description="Requirement files (requirements.txt, pyproject.toml, pylock.toml), relative to project_path."),
]


def _files(paths: list[str] | None, base, what: str) -> list[str]:
    settings = get_settings()
    return [str(resolve_path(p, settings, base=base, what=what, must_exist=True)) for p in paths or []]


@uv_tool(title="Install packages into an environment (uv pip install)", toolset="pip", open_world=True)
async def uv_pip_install(
    packages: Annotated[list[str] | None, Field(description="Requirement specifiers to install.")] = None,
    requirements: Requirements = None,
    editable: Annotated[list[str] | None, Field(description="Local paths to install in editable mode (-e).")] = None,
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    break_system_packages: Annotated[
        bool, Field(description="Allow modifying an externally-managed (PEP 668) Python.")
    ] = False,
    target: Annotated[
        str | None, Field(description="Install into this directory instead of an environment (--target).")
    ] = None,
    constraints: Constraints = None,
    overrides: Overrides = None,
    extras: Annotated[list[str] | None, Field(description="Extras to install from pyproject.toml inputs.")] = None,
    all_extras: bool = False,
    groups: Annotated[list[str] | None, Field(description="Dependency groups to install from pyproject.toml.")] = None,
    no_deps: Annotated[bool, Field(description="Install only the named packages, not their dependencies.")] = False,
    upgrade: bool = False,
    reinstall: bool = False,
    compile_bytecode: bool = False,
    python_version: Annotated[str | None, Field(description="Resolve for this Python version, e.g. '3.11'.")] = None,
    dry_run: bool = False,
    resolver: Resolver = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Install packages into a virtual environment without recording them in pyproject.toml.

    For uv projects use uv_add instead so the dependency is declared and locked.
    """
    cwd = project_dir(project_path)
    req_files = _files(requirements, cwd, "requirements file")
    edits = _files(editable, cwd, "editable path")
    if not packages and not req_files and not edits:
        raise ValidationError("Pass packages, requirements or editable")
    args = Args("pip", "install").opt("--python", python, "python").flag(system, "--system")
    args.flag(break_system_packages, "--break-system-packages")
    if target:
        args.path_opt("--target", resolve_path(target, get_settings(), base=cwd, what="target"))
    args.flag(upgrade, "--upgrade").flag(reinstall, "--reinstall").flag(dry_run, "--dry-run")
    for f in req_files:
        args.argv += ["-r", f]
    for e in edits:
        args.argv += ["-e", e]
    for f in _files(constraints, cwd, "constraints file"):
        args.argv += ["--constraints", f]
    for f in _files(overrides, cwd, "overrides file"):
        args.argv += ["--overrides", f]
    args.many("--extra", extras, "extra").flag(all_extras, "--all-extras").many("--group", groups, "group")
    args.flag(no_deps, "--no-deps").flag(compile_bytecode, "--compile-bytecode")
    args.opt("--python-version", python_version, "python_version").resolver(resolver)
    args.extra(extra_args).positional(packages, "package")
    return await run(args, cwd=cwd, mutating=not dry_run)


@uv_tool(
    title="Uninstall packages from an environment (uv pip uninstall)", toolset="pip", destructive=True, idempotent=True
)
async def uv_pip_uninstall(
    packages: Annotated[list[str], Field(description="Package names to uninstall.", min_length=1)],
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    dry_run: bool = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Remove packages from a virtual environment (does not edit pyproject.toml; use uv_remove for projects)."""
    cwd = project_dir(project_path)
    args = Args("pip", "uninstall").opt("--python", python, "python").flag(system, "--system")
    args.flag(dry_run, "--dry-run").extra(extra_args).positional(require_values(packages, "package"), "package")
    return await run(args, cwd=cwd, mutating=not dry_run)


@uv_tool(title="List installed packages (uv pip list)", toolset="pip", read_only=True, idempotent=True)
async def uv_pip_list(
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    outdated: Annotated[
        bool, Field(description="Only list packages with newer versions available (queries the index).")
    ] = False,
    editable_only: Annotated[bool, Field(description="Only list editable installs.")] = False,
    extra_args: ExtraArgs = None,
) -> PipListResult:
    """List the packages installed in an environment, with versions (and latest versions when outdated=true)."""
    cwd = project_dir(project_path)
    args = Args("pip", "list", "--format", "json").opt("--python", python, "python").flag(system, "--system")
    args.flag(outdated, "--outdated").flag(editable_only, "--editable").extra(extra_args)
    result = await run(args, cwd=cwd)
    data = load_json(result.stdout) if result.success else None
    return extend(
        result, PipListResult, packages=parse_pip_list(data), stdout="" if data is not None else result.stdout
    )


@uv_tool(title="Show package details (uv pip show)", toolset="pip", read_only=True, idempotent=True)
async def uv_pip_show(
    packages: Annotated[list[str], Field(description="Installed package names.", min_length=1)],
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    files: Annotated[bool, Field(description="Also list the files each package installed.")] = False,
    extra_args: ExtraArgs = None,
) -> PipShowResult:
    """Show version, location, requirements and reverse dependencies of installed packages."""
    cwd = project_dir(project_path)
    args = Args("pip", "show").opt("--python", python, "python").flag(system, "--system").flag(files, "--files")
    args.extra(extra_args).positional(require_values(packages, "package"), "package")
    result = await run(args, cwd=cwd)
    parsed = parse_pip_show(result.stdout)
    return extend(result, PipShowResult, packages=parsed, stdout="" if parsed else result.stdout)


@uv_tool(title="Freeze installed packages (uv pip freeze)", toolset="pip", read_only=True, idempotent=True)
async def uv_pip_freeze(
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    exclude_editable: bool = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Print the environment's installed packages in requirements.txt format (in stdout)."""
    cwd = project_dir(project_path)
    args = Args("pip", "freeze").opt("--python", python, "python").flag(system, "--system")
    args.flag(exclude_editable, "--exclude-editable").extra(extra_args)
    return await run(args, cwd=cwd)


@uv_tool(title="Show the environment's dependency tree (uv pip tree)", toolset="pip", read_only=True, idempotent=True)
async def uv_pip_tree(
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    packages: Annotated[list[str] | None, Field(description="Only show the tree for these packages.")] = None,
    depth: Annotated[int | None, Field(ge=0, le=255)] = None,
    invert: Annotated[bool, Field(description="Show reverse dependencies.")] = False,
    outdated: bool = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Display the dependency tree of the packages installed in an environment."""
    cwd = project_dir(project_path)
    args = Args("pip", "tree").opt("--python", python, "python").flag(system, "--system")
    args.many("--package", packages, "packages").flag(invert, "--invert").flag(outdated, "--outdated")
    if depth is not None:
        args.argv += ["--depth", str(depth)]
    return await run(args.extra(extra_args), cwd=cwd)


@uv_tool(title="Check installed packages are compatible (uv pip check)", toolset="pip", read_only=True, idempotent=True)
async def uv_pip_check(
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Verify that installed packages have compatible, non-missing dependencies. success=false means problems were found."""
    cwd = project_dir(project_path)
    args = Args("pip", "check").opt("--python", python, "python").flag(system, "--system").extra(extra_args)
    return await run(args, cwd=cwd)


@uv_tool(title="Compile requirements (uv pip compile)", toolset="pip", idempotent=True, open_world=True)
async def uv_pip_compile(
    src_files: Annotated[
        list[str],
        Field(
            description="Input files: requirements.in, pyproject.toml, setup.cfg... (relative to project_path).",
            min_length=1,
        ),
    ],
    project_path: ProjectPath = None,
    output_file: Annotated[
        str | None, Field(description="Write the pinned result here. Omit to return it in stdout.")
    ] = None,
    format: Literal["requirements.txt", "pylock.toml"] | None = None,
    universal: Annotated[bool, Field(description="Produce a platform-independent resolution.")] = False,
    generate_hashes: bool = False,
    upgrade: bool = False,
    upgrade_packages: Annotated[list[str] | None, Field(description="Allow upgrading only these packages.")] = None,
    extras: Annotated[list[str] | None, Field(description="Extras to include (pyproject.toml inputs).")] = None,
    all_extras: bool = False,
    groups: Annotated[list[str] | None, Field(description="Dependency groups to include (pyproject.toml).")] = None,
    constraints: Constraints = None,
    overrides: Overrides = None,
    no_deps: bool = False,
    no_header: bool = False,
    python_version: Annotated[str | None, Field(description="Resolve for this Python version, e.g. '3.11'.")] = None,
    resolver: Resolver = None,
    extra_args: ExtraArgs = None,
) -> PipCompileResult:
    """Resolve loose requirements into a fully pinned requirements.txt or pylock.toml."""
    settings = get_settings()
    cwd = project_dir(project_path)
    args = Args("pip", "compile")
    args.argv += _files(src_files, cwd, "source file")
    out = None
    if output_file:
        out = resolve_path(output_file, settings, base=cwd, what="output_file")
        args.path_opt("--output-file", out)
    args.opt("--format", format).flag(universal, "--universal").flag(generate_hashes, "--generate-hashes")
    args.flag(upgrade, "--upgrade").many("--upgrade-package", upgrade_packages, "upgrade_packages")
    args.many("--extra", extras, "extra").flag(all_extras, "--all-extras").many("--group", groups, "group")
    for f in _files(constraints, cwd, "constraints file"):
        args.argv += ["--constraints", f]
    for f in _files(overrides, cwd, "overrides file"):
        args.argv += ["--overrides", f]
    args.flag(no_deps, "--no-deps").flag(no_header, "--no-header")
    args.opt("--python-version", python_version, "python_version").resolver(resolver).extra(extra_args)
    result = await run(args, cwd=cwd, mutating=out is not None)
    return extend(result, PipCompileResult, output_file=str(out) if out else None)


@uv_tool(
    title="Sync an environment to a lock file (uv pip sync)",
    toolset="pip",
    destructive=True,
    idempotent=True,
    open_world=True,
)
async def uv_pip_sync(
    src_files: Annotated[list[str], Field(description="Pinned requirements.txt or pylock.toml files.", min_length=1)],
    project_path: ProjectPath = None,
    python: EnvPython = None,
    system: System = False,
    constraints: Constraints = None,
    compile_bytecode: bool = False,
    dry_run: bool = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Make an environment contain exactly the listed packages, uninstalling everything else."""
    cwd = project_dir(project_path)
    args = Args("pip", "sync")
    args.argv += _files(src_files, cwd, "source file")
    for f in _files(constraints, cwd, "constraints file"):
        args.argv += ["--constraints", f]
    args.opt("--python", python, "python").flag(system, "--system").flag(compile_bytecode, "--compile-bytecode")
    args.flag(dry_run, "--dry-run").extra(extra_args)
    return await run(args, cwd=cwd, mutating=not dry_run)
