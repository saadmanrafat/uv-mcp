"""Project workflow tools: uv init / add / remove / sync / lock / run / tree /
export / version / format / check / audit."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..config import get_settings
from ..models import AuditResult, CommandResult, ExportResult, InitResult, VersionResult
from ..parsing import load_json
from ..registry import uv_tool
from ..security import ValidationError, require_values, resolve_path, safe_env, safe_value
from ._common import (
    Args,
    ExtraArgs,
    Extras,
    Frozen,
    Groups,
    Locked,
    Member,
    ProjectPath,
    PythonRequest,
    Script,
    TimeoutSeconds,
    extend,
    frozen_if_read_only,
    project_dir,
    run,
)

Packages = Annotated[
    list[str],
    Field(
        description="Requirement specifiers: names with optional extras/versions ('httpx', 'fastapi[standard]>=0.115'), "
        "git URLs ('git+https://github.com/org/repo@v1') or local paths.",
        min_length=1,
    ),
]
NoSync = Annotated[
    bool, Field(description="Update pyproject.toml/uv.lock but do not sync the environment (--no-sync).")
]


@uv_tool(title="Create a project or script (uv init)", toolset="project")
async def uv_init(
    path: Annotated[
        str | None,
        Field(
            description="Directory to create the project in, or the .py file for kind='script'. "
            "Relative to the workspace root; defaults to the workspace root itself."
        ),
    ] = None,
    name: Annotated[str | None, Field(description="Project name (defaults to the directory name).")] = None,
    kind: Annotated[
        Literal["app", "lib", "script"],
        Field(description="'app' (default), 'lib' (an installable library) or 'script' (a single PEP 723 script)."),
    ] = "app",
    package: Annotated[
        bool, Field(description="For kind='app': make it an installable package with a build system.")
    ] = False,
    bare: Annotated[
        bool, Field(description="Only create pyproject.toml (no README, sample code, .python-version or git).")
    ] = False,
    python: PythonRequest = None,
    build_backend: Annotated[
        str | None, Field(description="Build backend for packaged projects, e.g. 'uv', 'hatch', 'setuptools'.")
    ] = None,
    vcs: Annotated[
        Literal["git", "none"] | None, Field(description="Version control to initialise (default: git).")
    ] = None,
    no_workspace: Annotated[bool, Field(description="Do not add the project to an enclosing workspace.")] = False,
    extra_args: ExtraArgs = None,
) -> InitResult:
    """Create a new uv project (pyproject.toml, .python-version, README, sample code) or a PEP 723 script.

    Use this instead of writing pyproject.toml by hand. Follow up with uv_add to add dependencies.
    """
    settings = get_settings()
    target = resolve_path(path, settings, what="path")
    if target.exists() and kind != "script" and not target.is_dir():
        raise ValidationError(f"{target} exists and is not a directory")
    if kind == "script" and target.exists():
        raise ValidationError(f"{target} already exists")
    cwd = target.parent if kind == "script" or not target.exists() else target
    while not cwd.exists():
        cwd = cwd.parent

    args = Args("init")
    args.flag(kind == "app", "--app").flag(kind == "lib", "--lib").flag(kind == "script", "--script")
    args.flag(package and kind == "app", "--package").flag(bare, "--bare")
    args.opt("--name", name, "name").opt("--python", python, "python")
    args.opt("--build-backend", build_backend, "build_backend").opt("--vcs", vcs)
    args.flag(no_workspace, "--no-workspace").extra(extra_args)
    args.argv.append(str(target))
    result = await run(args, cwd=cwd, mutating=True, lock_key=str(target))
    return extend(result, InitResult, path=str(target))


@uv_tool(title="Add dependencies (uv add)", toolset="project", open_world=True)
async def uv_add(
    packages: Packages,
    project_path: ProjectPath = None,
    dev: Annotated[bool, Field(description="Add to the 'dev' dependency group.")] = False,
    group: Annotated[str | None, Field(description="Add to this dependency group (e.g. 'test', 'lint').")] = None,
    optional: Annotated[str | None, Field(description="Add to this optional-dependency extra.")] = None,
    editable: Annotated[bool, Field(description="Add local path dependencies as editable.")] = False,
    index: Annotated[
        str | None, Field(description="Named or URL index to resolve these packages from (--index).")
    ] = None,
    member: Member = None,
    script: Script = None,
    no_sync: NoSync = False,
    locked: Locked = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Add dependencies to pyproject.toml, update uv.lock and sync the project environment.

    This is the right way to install packages for a project; prefer it over uv_pip_install.
    """
    cwd = project_dir(project_path)
    args = Args("add").flag(dev, "--dev").opt("--group", group, "group").opt("--optional", optional, "optional")
    args.flag(editable, "--editable").opt("--index", index, "index")
    args.opt("--package", member, "member").opt("--script", script, "script")
    args.flag(no_sync, "--no-sync").flag(locked, "--locked").extra(extra_args)
    args.positional(require_values(packages, "package"), "package")
    return await run(args, cwd=cwd, mutating=True)


@uv_tool(title="Remove dependencies (uv remove)", toolset="project", open_world=True)
async def uv_remove(
    packages: Annotated[list[str], Field(description="Package names to remove.", min_length=1)],
    project_path: ProjectPath = None,
    dev: Annotated[bool, Field(description="Remove from the 'dev' dependency group.")] = False,
    group: Annotated[str | None, Field(description="Remove from this dependency group.")] = None,
    optional: Annotated[str | None, Field(description="Remove from this optional-dependency extra.")] = None,
    member: Member = None,
    script: Script = None,
    no_sync: NoSync = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Remove dependencies from pyproject.toml, update uv.lock and sync the environment."""
    cwd = project_dir(project_path)
    args = Args("remove").flag(dev, "--dev").opt("--group", group, "group").opt("--optional", optional, "optional")
    args.opt("--package", member, "member").opt("--script", script, "script")
    args.flag(no_sync, "--no-sync").extra(extra_args)
    args.positional(require_values(packages, "package"), "package")
    return await run(args, cwd=cwd, mutating=True)


@uv_tool(title="Sync the project environment (uv sync)", toolset="project", idempotent=True, open_world=True)
async def uv_sync(
    project_path: ProjectPath = None,
    extras: Extras = None,
    all_extras: bool = False,
    groups: Groups = None,
    all_groups: bool = False,
    no_dev: Annotated[bool, Field(description="Exclude the dev group.")] = False,
    upgrade: Annotated[bool, Field(description="Upgrade all packages to the latest allowed versions.")] = False,
    upgrade_packages: Annotated[list[str] | None, Field(description="Upgrade only these packages.")] = None,
    reinstall: Annotated[bool, Field(description="Reinstall every package (fixes corrupted installs).")] = False,
    check: Annotated[bool, Field(description="Only check whether the environment is in sync; change nothing.")] = False,
    member: Member = None,
    all_packages: Annotated[bool, Field(description="Sync every workspace member.")] = False,
    script: Script = None,
    frozen: Frozen = False,
    locked: Locked = False,
    python: PythonRequest = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Make the project's .venv match uv.lock exactly (creating the venv and lockfile if needed).

    Run this after cloning a project, after editing pyproject.toml by hand, or to repair a broken environment.
    """
    cwd = project_dir(project_path)
    args = Args("sync").dependency_selection(
        extras=extras, all_extras=all_extras, groups=groups, all_groups=all_groups, no_dev=no_dev
    )
    args.flag(upgrade, "--upgrade").many("--upgrade-package", upgrade_packages, "upgrade_packages")
    args.flag(reinstall, "--reinstall").flag(check, "--check")
    args.opt("--package", member, "member").flag(all_packages, "--all-packages").opt("--script", script, "script")
    args.flag(frozen, "--frozen").flag(locked, "--locked").opt("--python", python, "python").extra(extra_args)
    return await run(args, cwd=cwd, mutating=not check)


@uv_tool(title="Update the lockfile (uv lock)", toolset="project", idempotent=True, open_world=True)
async def uv_lock(
    project_path: ProjectPath = None,
    upgrade: Annotated[bool, Field(description="Allow upgrading every package.")] = False,
    upgrade_packages: Annotated[list[str] | None, Field(description="Allow upgrading only these packages.")] = None,
    check: Annotated[bool, Field(description="Only check whether uv.lock is up to date; write nothing.")] = False,
    script: Script = None,
    python: PythonRequest = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Resolve dependencies and write uv.lock without touching the environment."""
    cwd = project_dir(project_path)
    args = Args("lock").flag(upgrade, "--upgrade").many("--upgrade-package", upgrade_packages, "upgrade_packages")
    args.flag(check, "--check").opt("--script", script, "script")
    args.opt("--python", python, "python").extra(extra_args)
    return await run(args, cwd=cwd, mutating=not check)


@uv_tool(
    title="Run a command in the project environment (uv run)", toolset="project", destructive=True, open_world=True
)
async def uv_run(
    command: Annotated[
        list[str],
        Field(
            description="Program and arguments, e.g. ['python', 'main.py'], ['pytest', '-x'], ['python', '-m', 'mymod'] "
            "or ['script.py'] for a PEP 723 script. Not run through a shell.",
            min_length=1,
        ),
    ],
    project_path: ProjectPath = None,
    with_packages: Annotated[
        list[str] | None, Field(description="Extra packages available only for this run (--with).")
    ] = None,
    env: Annotated[dict[str, str] | None, Field(description="Extra environment variables for the command.")] = None,
    env_file: Annotated[str | None, Field(description="Load environment variables from this .env file.")] = None,
    isolated: Annotated[bool, Field(description="Run in a temporary environment, leaving .venv untouched.")] = False,
    no_project: Annotated[
        bool, Field(description="Ignore the current project (useful for standalone scripts).")
    ] = False,
    no_sync: Annotated[bool, Field(description="Do not sync the environment before running.")] = False,
    extras: Extras = None,
    groups: Groups = None,
    no_dev: bool = False,
    member: Member = None,
    frozen: Frozen = False,
    locked: Locked = False,
    python: PythonRequest = None,
    timeout_seconds: TimeoutSeconds = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Run a command or script inside the project's environment, syncing it first.

    Use this to run tests, scripts, linters and Python one-liners with the project's dependencies.
    The command's exit status is returned in exit_code (non-zero is reported as success=false).
    """
    cwd = project_dir(project_path)
    program = safe_value(command[0], "command[0]")
    settings = get_settings()
    args = Args("run").many("--with", with_packages, "with_packages")
    if env_file:
        args.path_opt("--env-file", resolve_path(env_file, settings, base=cwd, what="env_file", must_exist=True))
    args.flag(isolated, "--isolated").flag(no_project, "--no-project").flag(no_sync, "--no-sync")
    args.dependency_selection(extras=extras, groups=groups, no_dev=no_dev)
    args.opt("--package", member, "member").flag(frozen, "--frozen").flag(locked, "--locked")
    args.opt("--python", python, "python").extra(extra_args)
    args.argv += ["--", program, *command[1:]]
    for arg in command[1:]:
        if "\x00" in arg:
            raise ValidationError("command arguments must not contain NUL bytes")
    return await run(args, cwd=cwd, env=safe_env(env), timeout=timeout_seconds)


@uv_tool(
    title="Show the dependency tree (uv tree)", toolset="project", read_only=True, idempotent=True, open_world=True
)
async def uv_tree(
    project_path: ProjectPath = None,
    depth: Annotated[int | None, Field(description="Maximum display depth.", ge=0, le=255)] = None,
    packages: Annotated[list[str] | None, Field(description="Only show the tree rooted at these packages.")] = None,
    invert: Annotated[bool, Field(description="Show reverse dependencies: who depends on `packages`.")] = False,
    outdated: Annotated[bool, Field(description="Annotate packages that have newer versions available.")] = False,
    extras: Extras = None,
    groups: Groups = None,
    no_dev: bool = False,
    script: Script = None,
    frozen: Annotated[bool, Field(description="Read uv.lock as-is (otherwise a stale lockfile is refreshed).")] = False,
    python: PythonRequest = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Display the project's resolved dependency tree from uv.lock. Use invert=true to find why a package is installed."""
    cwd = project_dir(project_path)
    args = Args("tree")
    if depth is not None:
        args.argv += ["--depth", str(depth)]
    args.many("--package", packages, "packages").flag(invert, "--invert").flag(outdated, "--outdated")
    args.dependency_selection(extras=extras, groups=groups, no_dev=no_dev)
    args.opt("--script", script, "script").flag(frozen, "--frozen").opt("--python", python, "python").extra(extra_args)
    return await run(frozen_if_read_only(args), cwd=cwd)


@uv_tool(title="Export the lockfile (uv export)", toolset="project", read_only=True, idempotent=True, open_world=True)
async def uv_export(
    project_path: ProjectPath = None,
    format: Annotated[
        Literal["requirements.txt", "pylock.toml", "cyclonedx1.5"],
        Field(description="Output format; cyclonedx1.5 produces an SBOM."),
    ] = "requirements.txt",
    output_file: Annotated[
        str | None,
        Field(description="Write to this file (relative to the project). Omit to return the content in stdout."),
    ] = None,
    no_hashes: bool = False,
    no_emit_project: Annotated[bool, Field(description="Leave the project itself out of the output.")] = False,
    extras: Extras = None,
    groups: Groups = None,
    no_dev: bool = False,
    member: Member = None,
    frozen: Frozen = False,
    locked: Locked = False,
    extra_args: ExtraArgs = None,
) -> ExportResult:
    """Export uv.lock as requirements.txt, pylock.toml or a CycloneDX SBOM (e.g. for Docker or other tools)."""
    settings = get_settings()
    cwd = project_dir(project_path)
    args = Args("export").opt("--format", format)
    out = None
    if output_file:
        if settings.read_only:
            raise ValidationError("output_file cannot be used in read-only mode; omit it to get the content back")
        out = resolve_path(output_file, settings, base=cwd, what="output_file")
        args.path_opt("--output-file", out)
    args.flag(no_hashes, "--no-hashes").flag(no_emit_project, "--no-emit-project")
    args.dependency_selection(extras=extras, groups=groups, no_dev=no_dev)
    args.opt("--package", member, "member").flag(frozen, "--frozen").flag(locked, "--locked").extra(extra_args)
    result = await run(frozen_if_read_only(args), cwd=cwd, mutating=out is not None)
    return extend(result, ExportResult, output_file=str(out) if out else None)


BumpKind = Literal["major", "minor", "patch", "stable", "alpha", "beta", "rc", "post", "dev"]


@uv_tool(title="Read or bump the project version (uv version)", toolset="project")
async def uv_version(
    project_path: ProjectPath = None,
    value: Annotated[str | None, Field(description="Set the version to exactly this value, e.g. '1.4.0'.")] = None,
    bump: Annotated[
        list[BumpKind] | None,
        Field(description="Bump components in order, e.g. ['minor'] or ['patch', 'beta'].", max_length=4),
    ] = None,
    dry_run: Annotated[bool, Field(description="Compute the new version without writing it.")] = False,
    member: Member = None,
    no_sync: NoSync = False,
    frozen: Frozen = False,
    extra_args: ExtraArgs = None,
) -> VersionResult:
    """Read the project's version, or set/bump it in pyproject.toml (re-locking and syncing unless told not to)."""
    cwd = project_dir(project_path)
    if value and bump:
        raise ValidationError("Pass either value or bump, not both")
    changing = bool(value or bump) and not dry_run

    previous = None
    if value or bump:
        current = await run(Args("version", "--output-format", "json").opt("--package", member, "member"), cwd=cwd)
        data = load_json(current.stdout) if current.success else None
        previous = data.get("version") if isinstance(data, dict) else None

    args = Args("version", "--output-format", "json")
    for part in bump or []:
        args.argv += ["--bump", part]
    args.flag(dry_run, "--dry-run").opt("--package", member, "member").flag(no_sync, "--no-sync")
    args.flag(frozen, "--frozen").extra(extra_args)
    if value:
        args.argv.append(safe_value(value, "value"))
    result = await run(args, cwd=cwd, mutating=changing)
    data = load_json(result.stdout) if result.success else None
    fields: dict[str, object] = {"previous_version": previous}
    if isinstance(data, dict):
        fields.update(package_name=data.get("package_name"), version=data.get("version"), stdout="")
    return extend(result, VersionResult, **fields)


@uv_tool(title="Format code with Ruff (uv format)", toolset="project", idempotent=True, open_world=True)
async def uv_format(
    project_path: ProjectPath = None,
    check: Annotated[bool, Field(description="Only report files that would change; modify nothing.")] = False,
    diff: Annotated[bool, Field(description="Show the formatting diff instead of writing files.")] = False,
    ruff_args: Annotated[
        list[str] | None, Field(description="Arguments passed through to `ruff format`, e.g. file paths.")
    ] = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Format the project's Python code with Ruff (installed on demand by uv)."""
    cwd = project_dir(project_path)
    args = Args("format").flag(check, "--check").flag(diff, "--diff").extra(extra_args)
    if ruff_args:
        args.argv.append("--")
        args.argv += Args().extra(ruff_args).argv
    return await run(args, cwd=cwd, mutating=not (check or diff))


@uv_tool(title="Type-check the project (uv check)", toolset="project", idempotent=True, open_world=True)
async def uv_check(
    project_path: ProjectPath = None,
    member: Member = None,
    all_packages: bool = False,
    script: Script = None,
    extras: Extras = None,
    groups: Groups = None,
    isolated: Annotated[bool, Field(description="Check without syncing or modifying the project environment.")] = False,
    frozen: Frozen = False,
    locked: Locked = False,
    python: PythonRequest = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Run uv's project checks (static type checking with ty). Requires a recent uv; experimental in uv."""
    cwd = project_dir(project_path)
    args = Args("check").opt("--package", member, "member").flag(all_packages, "--all-packages")
    args.opt("--script", script, "script").dependency_selection(extras=extras, groups=groups)
    args.flag(isolated or get_settings().read_only, "--isolated").flag(frozen, "--frozen").flag(locked, "--locked")
    args.opt("--python", python, "python").extra(extra_args)
    return await run(args, cwd=cwd)


@uv_tool(
    title="Audit dependencies for vulnerabilities (uv audit)",
    toolset="project",
    read_only=True,
    idempotent=True,
    open_world=True,
)
async def uv_audit(
    project_path: ProjectPath = None,
    no_dev: bool = False,
    ignore: Annotated[
        list[str] | None, Field(description="Vulnerability IDs to ignore (e.g. 'GHSA-xxxx', 'PYSEC-...').")
    ] = None,
    script: Script = None,
    frozen: Frozen = False,
    locked: Locked = False,
    extra_args: ExtraArgs = None,
) -> AuditResult:
    """Check the locked dependencies against known vulnerability databases (OSV). Experimental in uv."""
    cwd = project_dir(project_path)
    args = Args("audit", "--output-format", "json").flag(no_dev, "--no-dev").many("--ignore", ignore, "ignore")
    args.opt("--script", script, "script").flag(frozen, "--frozen").flag(locked, "--locked").extra(extra_args)
    result = await run(frozen_if_read_only(args), cwd=cwd)
    report = load_json(result.stdout)
    return extend(result, AuditResult, report=report, stdout="" if report is not None else result.stdout)
