"""Every uv option is reachable: typed parameters, the `resolver` object, or validated `extra_args`."""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest

from uv_mcp.coverage import COVERAGE
from uv_mcp.flags import command_help, parse_help
from uv_mcp.registry import REGISTRY
from uv_mcp.security import ValidationError
from uv_mcp.tools._common import validate_options

from .conftest import call, call_error, requires_uv

SAMPLE_HELP = """\
Add dependencies to the project

Usage: uv add [OPTIONS] <PACKAGES|--requirements <REQUIREMENTS>>

Arguments:
  [PACKAGES]...  The packages to add

Options:
  -r, --requirements <REQUIREMENTS>
          Add the packages listed in the given files
      --dev
          Add the requirements to the development dependency group [env: UV_DEV=]
      --bounds <BOUNDS>
          The kind of version specifier to use [possible values: lower,
          major, minor, exact]
      --resolution <RESOLUTION>
          The strategy to use [env: UV_RESOLUTION=] [possible values: highest, lowest,
          lowest-direct]

Global options:
  -q, --quiet...                 Use quiet output
  -v, --verbose...               Use verbose output
      --offline                  Disable network access [env: UV_OFFLINE=]
  -p, --python <PYTHON>          The Python interpreter to use. [env:
                                 UV_PYTHON=]
"""


def test_parse_help_extracts_options() -> None:
    h = parse_help(SAMPLE_HELP, ("add",))
    assert h.summary == "Add dependencies to the project"
    assert h.usage.startswith("uv add")
    bounds = h.options["--bounds"]
    assert bounds.value == "BOUNDS" and bounds.choices == ["lower", "major", "minor", "exact"]
    assert h.options["--resolution"].env == "UV_RESOLUTION"
    assert h.options["--resolution"].choices == ["highest", "lowest", "lowest-direct"]
    assert h.options["--dev"].value is None and h.options["--dev"].scope == "command"
    assert h.options["--python"].scope == "global" and h.options["--python"].env == "UV_PYTHON"
    assert h.lookup("-r").flag == "--requirements"
    assert h.lookup("-q").flag == "--quiet"


@pytest.mark.parametrize(
    "args",
    [
        ["--dev"],
        ["--bounds", "major"],
        ["--bounds=minor"],
        ["--resolution", "lowest-direct", "--offline"],
        ["-r", "reqs.txt"],
        ["-rreqs.txt"],
        ["-p", "3.12"],
        ["-qq"],
        ["-qv"],
    ],
)
def test_validate_accepts_real_options(args: list[str]) -> None:
    assert validate_options(("add",), args, parse_help(SAMPLE_HELP, ("add",))) == args


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--resolutoin", "lowest"], "Did you mean --resolution"),
        (["--no-such-flag"], "has no option --no-such-flag"),
        (["--bounds", "banana"], "must be one of: lower, major, minor, exact"),
        (["--bounds"], "needs a value"),
        (["--dev=yes"], "does not take a value"),
        (["-Z"], "has no option -Z"),
        (["-qZ"], "Unknown combined short flags"),
        (["--"], "not allowed"),
    ],
)
def test_validate_rejects_bad_options(args: list[str], message: str) -> None:
    with pytest.raises(ValidationError, match=re.escape(message)):
        validate_options(("add",), args, parse_help(SAMPLE_HELP, ("add",)))


def test_validate_passes_through_without_help() -> None:
    assert validate_options(("add",), ["--anything"], None) == ["--anything"]


# --------------------------------------------------------------------------- #
# Against the installed uv
# --------------------------------------------------------------------------- #

_FLAG_RE = re.compile(r'"(--[a-z0-9][a-z0-9-]*)"')
_SKIP = {"uv_info", "uv_command", "uv_help", "uv_project_info", "uv_diagnose", "uv_repair"}


@requires_uv
@pytest.mark.parametrize("path", sorted(p for p, how in COVERAGE.items() if isinstance(how, str) and how not in _SKIP))
def test_every_flag_a_tool_uses_exists_in_uv(path: tuple[str, ...]) -> None:
    """Catches typos and options renamed or removed by uv (CI runs against the latest uv)."""
    help_ = command_help(path)
    if help_ is None:
        pytest.skip(f"uv {' '.join(path)} does not exist in this uv version")
    tool = COVERAGE[path]
    used = set(_FLAG_RE.findall(inspect.getsource(REGISTRY[tool].fn)))
    unknown = sorted(f for f in used if help_.lookup(f) is None)
    assert not unknown, f"{tool} passes options `uv {' '.join(path)}` does not have: {unknown}"


@requires_uv
def test_resolver_options_exist_wherever_offered() -> None:
    """--python-platform is command-specific (checked per call); every other resolver option must exist."""
    from uv_mcp.tools.meta import _RESOLVER_FLAGS

    universal = _RESOLVER_FLAGS - {"--python-platform"}
    offered = [
        (path, tool)
        for path, tool in COVERAGE.items()
        if isinstance(tool, str) and tool in REGISTRY and "resolver" in inspect.signature(REGISTRY[tool].fn).parameters
    ]
    assert len(offered) >= 9
    for path, tool in offered:
        help_ = command_help(path)
        missing = sorted(f for f in universal if help_.lookup(f) is None)
        assert not missing, f"{tool} offers resolver options uv {' '.join(path)} lacks: {missing}"
    assert command_help(("pip", "compile")).lookup("--python-platform") is not None


@requires_uv
async def test_unsupported_resolver_option_is_refused(client, workspace: Path) -> None:
    text = await call_error(client, "uv_lock", {"resolver": {"python_platform": "linux"}})
    assert "does not support --python-platform" in text


@requires_uv
async def test_uv_help_lists_options_and_how_to_pass_them(client) -> None:
    data = await call(client, "uv_help", {"command": "add"})
    assert data["tool"] == "uv_add"
    flags = {o["flag"]: o for o in data["options"]}
    assert data["total_options"] == len(flags) > 40
    assert flags["--dev"]["via"] == "parameter"
    assert flags["--resolution"]["via"] == "resolver"
    assert flags["--resolution"]["choices"] == ["highest", "lowest", "lowest-direct"]
    assert flags["--offline"]["scope"] == "global"
    extra = [o for o in data["options"] if o["via"] == "extra_args"]
    assert extra, "some rarely used options should be reachable through extra_args"

    filtered = await call(client, "uv_help", {"command": "add", "search": "git"})
    assert {"--rev", "--tag", "--branch"} <= {o["flag"] for o in filtered["options"]}

    top = await call(client, "uv_help", {"command": ""})
    assert {"add", "pip", "python", "tool"} <= set(top["subcommands"])
    group = await call(client, "uv_help", {"command": "pip"})
    assert "install" in group["subcommands"]


@requires_uv
async def test_uv_help_rejects_bad_commands(client) -> None:
    assert "Not a uv command" in await call_error(client, "uv_help", {"command": "add; rm -rf /"})
    assert "no command" in await call_error(client, "uv_help", {"command": "frobnicate"})


@requires_uv
async def test_extra_args_typos_are_caught_before_uv_runs(client) -> None:
    text = await call_error(client, "uv_sync", {"extra_args": ["--compile-bytecod"]})
    assert "Did you mean --compile-bytecode" in text and "uv_help" in text


@requires_uv
async def test_valid_extra_args_reach_uv(client, workspace: Path) -> None:
    data = await call(client, "uv_python_list", {"only_installed": True, "extra_args": ["--no-managed-python"]})
    assert data["success"], data
    assert "--no-managed-python" in data["command"]


PY = f"{sys.version_info.major}.{sys.version_info.minor}"


@requires_uv
async def test_resolver_options_are_passed_and_checked(client, workspace: Path) -> None:
    assert (await call(client, "uv_init", {"path": "demo", "python": PY, "vcs": "none"}))["success"]
    locked = await call(
        client,
        "uv_lock",
        {"project_path": "demo", "resolver": {"resolution": "lowest-direct", "prerelease": "allow", "offline": True}},
    )
    assert locked["success"], locked
    assert "--resolution lowest-direct" in locked["command"] and "--offline" in locked["command"]
    assert "--prerelease allow" in locked["command"]
    bad = await call_error(client, "uv_lock", {"project_path": "demo", "resolver": {"resolution": "newest"}})
    assert "resolution" in bad
    injected = await call_error(client, "uv_lock", {"project_path": "demo", "resolver": {"index": ["--evil"]}})
    assert "must not start with '-'" in injected
