"""Packaging: uv build and uv publish."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from ..config import get_settings
from ..models import BuildResult, CommandResult
from ..registry import uv_tool
from ..security import resolve_path, safe_value, safe_values
from ._common import Args, ExtraArgs, Member, ProjectPath, PythonRequest, extend, project_dir, run

_BUILT_RE = re.compile(r"Successfully built (.+?)\s*$", re.M)


@uv_tool(title="Build sdist and wheel (uv build)", toolset="build", idempotent=True, open_world=True)
async def uv_build(
    project_path: ProjectPath = None,
    out_dir: Annotated[
        str | None, Field(description="Output directory, relative to project_path (default: dist/).")
    ] = None,
    sdist: Annotated[bool, Field(description="Build only a source distribution.")] = False,
    wheel: Annotated[bool, Field(description="Build only a wheel.")] = False,
    member: Member = None,
    all_packages: Annotated[bool, Field(description="Build every workspace member.")] = False,
    clear: Annotated[bool, Field(description="Empty the output directory first.")] = False,
    build_constraints: Annotated[
        list[str] | None, Field(description="Constraint files for build dependencies (-b).")
    ] = None,
    no_build_logs: Annotated[bool, Field(description="Hide build backend output.")] = False,
    force_pep517: Annotated[bool, Field(description="Always build through PEP 517, even with uv_build.")] = False,
    python: PythonRequest = None,
    extra_args: ExtraArgs = None,
) -> BuildResult:
    """Build the project into distributable archives. Both sdist and wheel are built unless one is selected."""
    cwd = project_dir(project_path)
    out = resolve_path(out_dir, get_settings(), base=cwd, what="out_dir") if out_dir else None
    args = Args("build").path_opt("--out-dir", out).flag(sdist, "--sdist").flag(wheel, "--wheel")
    args.opt("--package", member, "member").flag(all_packages, "--all-packages").flag(clear, "--clear")
    for f in build_constraints or []:
        args.path_opt(
            "--build-constraints", resolve_path(f, get_settings(), base=cwd, what="build constraints", must_exist=True)
        )
    args.flag(no_build_logs, "--no-build-logs").flag(force_pep517, "--force-pep517")
    args.opt("--python", python, "python").extra(extra_args)
    result = await run(args, cwd=cwd, mutating=True)
    artifacts = []
    for match in _BUILT_RE.findall(result.stderr + "\n" + result.stdout):
        p = Path(match.strip())
        artifacts.append(str(p if p.is_absolute() else (cwd / p).resolve()))
    return extend(
        result,
        BuildResult,
        out_dir=str(out) if out else (str(Path(artifacts[0]).parent) if artifacts else None),
        artifacts=artifacts,
    )


@uv_tool(title="Publish distributions (uv publish)", toolset="build", destructive=True, open_world=True)
async def uv_publish(
    project_path: ProjectPath = None,
    files: Annotated[list[str] | None, Field(description="Files or globs to upload (default: dist/*).")] = None,
    dry_run: Annotated[
        bool,
        Field(
            description="Validate without uploading. Defaults to true: set false only when the user asked to publish."
        ),
    ] = True,
    index: Annotated[str | None, Field(description="Name of an index from [[tool.uv.index]] to publish to.")] = None,
    publish_url: Annotated[
        str | None, Field(description="Upload endpoint, e.g. https://test.pypi.org/legacy/.")
    ] = None,
    check_url: Annotated[
        str | None, Field(description="Index URL used to skip files that are already uploaded.")
    ] = None,
    trusted_publishing: Literal["automatic", "always", "never"] | None = None,
    token: Annotated[
        str | None,
        Field(
            description="API token. Prefer trusted publishing or UV_PUBLISH_TOKEN in the server env; never echoed back."
        ),
    ] = None,
    username: str | None = None,
    password: Annotated[str | None, Field(description="Password (never echoed back).")] = None,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Upload built distributions to PyPI or another index. Irreversible: a version can never be re-uploaded.

    Runs as a dry run unless dry_run=false is passed explicitly. Credentials are passed to uv
    through environment variables, never on the command line, and are redacted from output.
    """
    cwd = project_dir(project_path)
    env: dict[str, str] = {}
    if token:
        env["UV_PUBLISH_TOKEN"] = token
    if username:
        env["UV_PUBLISH_USERNAME"] = safe_value(username, "username")
    if password:
        env["UV_PUBLISH_PASSWORD"] = password
    args = Args("publish").flag(dry_run, "--dry-run").opt("--index", index, "index")
    args.opt("--publish-url", publish_url, "publish_url").opt("--check-url", check_url, "check_url")
    args.opt("--trusted-publishing", trusted_publishing).extra(extra_args)
    args.argv += safe_values(files, "file")
    return await run(args, cwd=cwd, env=env, mutating=True, secrets=[s for s in (token, password) if s])
