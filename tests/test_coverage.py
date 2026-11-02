"""uv-mcp must cover every command the installed uv offers.

If this fails after a uv upgrade, uv gained a command: add a tool for it (or an entry in
src/uv_mcp/coverage.py explaining how it is covered) and regenerate the tool reference.
"""

from __future__ import annotations

import os
import re
import subprocess

import pytest

from uv_mcp.coverage import COVERAGE, Blocked
from uv_mcp.registry import REGISTRY
from uv_mcp.tools.meta import _BLOCKED

from .conftest import requires_uv

_COMMAND_LINE = re.compile(r"^  ([a-z][a-z0-9-]*)\s{2,}\S")
#: Registered tools that are not a single uv command.
_NOT_COMMANDS = {"uv_info", "uv_command", "uv_project_info", "uv_diagnose", "uv_repair"}


def _subcommands(*path: str) -> list[str]:
    env = {**os.environ, "NO_COLOR": "1"}
    env.pop("VIRTUAL_ENV", None)
    out = subprocess.run(["uv", *path, "--help"], capture_output=True, text=True, env=env, check=True).stdout
    names: list[str] = []
    in_commands = False
    for line in out.splitlines():
        if line.strip() == "Commands:":
            in_commands = True
            continue
        if in_commands:
            if not line.strip():
                break
            m = _COMMAND_LINE.match(line)
            if m:
                names.append(m.group(1))
    return names


def _uv_command_paths() -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()
    for top in _subcommands():
        subs = _subcommands(top) if top != "help" else []
        if subs:
            paths.update((top, sub) for sub in subs)
        else:
            paths.add((top,))
    return paths


@requires_uv
def test_every_uv_command_is_covered() -> None:
    discovered = _uv_command_paths()
    assert len(discovered) > 40, f"help parsing looks broken: {sorted(discovered)}"
    missing = sorted(" ".join(p) for p in discovered - COVERAGE.keys())
    assert not missing, (
        f"uv has commands uv-mcp does not cover: {missing}. Add a tool (see CLAUDE.md) or an entry in "
        "src/uv_mcp/coverage.py."
    )


def test_coverage_points_at_real_tools() -> None:
    for path, how in COVERAGE.items():
        if isinstance(how, Blocked):
            continue
        assert how in REGISTRY, f"uv {' '.join(path)} maps to unknown tool {how}"


def test_every_command_tool_is_in_the_coverage_map() -> None:
    mapped = {how for how in COVERAGE.values() if isinstance(how, str)}
    unmapped = sorted(set(REGISTRY) - mapped - _NOT_COMMANDS)
    assert not unmapped, f"tools missing from coverage.COVERAGE: {unmapped}"


def test_blocked_commands_are_refused_by_uv_command() -> None:
    assert {p: c.reason for p, c in COVERAGE.items() if isinstance(c, Blocked)} == _BLOCKED
    assert ("auth", "token") in _BLOCKED


@pytest.mark.parametrize("path", sorted(p for p, c in COVERAGE.items() if isinstance(c, str) and c.startswith("uv_")))
def test_tool_names_mirror_the_cli(path: tuple[str, ...]) -> None:
    how = COVERAGE[path]
    if how in _NOT_COMMANDS:
        return
    assert how == "uv_" + "_".join(part.replace("-", "_") for part in path)
