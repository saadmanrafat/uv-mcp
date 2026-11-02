"""Shared parameter types and helpers for tool modules."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Annotated, TypeVar

from pydantic import Field

from ..config import get_settings
from ..models import CommandResult
from ..runner import run_uv
from ..security import resolve_project_dir, safe_extra_args, safe_value, safe_values

# --------------------------------------------------------------------------- #
# Reusable parameter annotations (keep descriptions short: they cost context).
# --------------------------------------------------------------------------- #

ProjectPath = Annotated[
    str | None,
    Field(description="Project directory, absolute or relative to the workspace root (default: workspace root)."),
]
ExtraArgs = Annotated[
    list[str] | None,
    Field(description="Extra raw uv flags, e.g. ['--offline']."),
]
PythonRequest = Annotated[
    str | None,
    Field(description="Python to use: version ('3.12'), 'pypy@3.10' or a path."),
]
Member = Annotated[
    str | None,
    Field(description="Workspace member (--package)."),
]
Script = Annotated[
    str | None,
    Field(description="PEP 723 script to operate on instead of the project."),
]
Groups = Annotated[list[str] | None, Field(description="Dependency groups to include (--group).")]
Extras = Annotated[list[str] | None, Field(description="Optional-dependency extras to include (--extra).")]
Frozen = Annotated[bool, Field(description="Use uv.lock without updating it.")]
Locked = Annotated[bool, Field(description="Fail if uv.lock is out of date.")]
TimeoutSeconds = Annotated[
    float | None,
    Field(description="Timeout in seconds (default: server setting).", gt=0, le=86_400),
]

R = TypeVar("R", bound=CommandResult)


class Args:
    """Small argv builder that validates values as they are added."""

    def __init__(self, *base: str) -> None:
        self.argv: list[str] = list(base)

    def flag(self, enabled: bool | None, name: str) -> Args:
        if enabled:
            self.argv.append(name)
        return self

    def opt(self, name: str, value: str | None, what: str | None = None) -> Args:
        if value is not None and str(value).strip():
            self.argv += [name, safe_value(str(value), what or name)]
        return self

    def path_opt(self, name: str, value: Path | None) -> Args:
        if value is not None:
            self.argv += [name, str(value)]
        return self

    def many(self, name: str, values: Iterable[str] | None, what: str | None = None) -> Args:
        for v in safe_values(values, what or name):
            self.argv += [name, v]
        return self

    def positional(self, values: Iterable[str] | None, what: str) -> Args:
        self.argv += safe_values(values, what)
        return self

    def extra(self, extra_args: Sequence[str] | None) -> Args:
        self.argv += safe_extra_args(extra_args, get_settings())
        return self

    def dependency_selection(
        self,
        *,
        extras: Sequence[str] | None = None,
        all_extras: bool = False,
        groups: Sequence[str] | None = None,
        all_groups: bool = False,
        no_dev: bool = False,
        only_dev: bool = False,
    ) -> Args:
        self.many("--extra", extras, "extra")
        self.flag(all_extras, "--all-extras")
        self.many("--group", groups, "group")
        self.flag(all_groups, "--all-groups")
        self.flag(no_dev, "--no-dev")
        self.flag(only_dev, "--only-dev")
        return self


def project_dir(project_path: str | None) -> Path:
    return resolve_project_dir(project_path, get_settings())


async def run(
    args: Args | Sequence[str],
    *,
    cwd: Path | None = None,
    mutating: bool = False,
    lock_key: str | None = None,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
    stdin_data: str | None = None,
    secrets: Sequence[str] = (),
) -> CommandResult:
    argv = args.argv if isinstance(args, Args) else list(args)
    return await run_uv(
        argv,
        cwd=cwd,
        mutating=mutating,
        lock_key=lock_key,
        timeout=timeout,
        env=env,
        stdin_data=stdin_data,
        secrets=secrets,
    )


def extend(result: CommandResult, cls: type[R], **fields: object) -> R:
    """Upgrade a base :class:`CommandResult` into a richer subclass."""
    return cls(**{**result.model_dump(), **fields})


def frozen_if_read_only(args: Args) -> Args:
    """In read-only mode, stop commands that implicitly lock from rewriting uv.lock."""
    if get_settings().read_only and "--frozen" not in args.argv and "--locked" not in args.argv:
        args.argv.append("--frozen")
    return args
