"""End-to-end tests against the real uv binary, through the MCP protocol.

Tests that need no network use projects without third-party dependencies.
Tests marked ``network`` download from PyPI and are skipped with ``-m 'not network'``.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from uv_mcp.config import Settings

from .conftest import call, call_error, requires_uv

pytestmark = requires_uv

PY = f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture
async def project(client, workspace: Path) -> Path:
    data = await call(client, "uv_init", {"path": "demo", "python": PY, "vcs": "none"})
    assert data["success"], data
    return Path(data["path"])


async def test_info(client, workspace: Path) -> None:
    data = await call(client, "uv_info")
    assert data["uv_installed"] and data["uv_version"]
    assert data["workspace_root"] == str(workspace.resolve())
    assert data["directories"]["cache"]
    assert data["workspace_is_project"] is False
    assert any("not inside a uv project" in n for n in data["notes"])


async def test_project_lifecycle(client, project: Path) -> None:
    info = await call(client, "uv_project_info", {"project_path": "demo"})
    assert info["name"] == "demo" and info["has_pyproject"] and not info["has_lockfile"]
    assert info["python_version_file"] == PY

    lock = await call(client, "uv_lock", {"project_path": "demo"})
    assert lock["success"], lock
    assert (project / "uv.lock").exists()
    assert (await call(client, "uv_lock", {"project_path": "demo", "check": True}))["success"]

    sync = await call(client, "uv_sync", {"project_path": "demo"})
    assert sync["success"], sync
    assert (project / ".venv").is_dir()

    ran = await call(
        client, "uv_run", {"project_path": "demo", "command": ["python", "-c", "import sys; print(sys.prefix)"]}
    )
    assert ran["success"] and ran["exit_code"] == 0
    assert str(project / ".venv") in ran["stdout"]

    failed = await call(client, "uv_run", {"project_path": "demo", "command": ["python", "-c", "raise SystemExit(7)"]})
    assert not failed["success"] and failed["exit_code"] == 7

    env = await call(
        client,
        "uv_run",
        {
            "project_path": "demo",
            "command": ["python", "-c", "import os; print(os.environ['GREETING'])"],
            "env": {"GREETING": "hi"},
        },
    )
    assert env["stdout"].strip() == "hi"

    version = await call(client, "uv_version", {"project_path": "demo"})
    assert version["version"] == "0.1.0" and version["package_name"] == "demo"
    # Default bump re-locks and syncs, so the environment stays consistent for uv_diagnose below.
    bumped = await call(client, "uv_version", {"project_path": "demo", "bump": ["minor"]})
    assert bumped["success"], bumped
    assert bumped["previous_version"] == "0.1.0" and bumped["version"] == "0.2.0"

    tree = await call(client, "uv_tree", {"project_path": "demo"})
    assert tree["success"] and "demo" in tree["stdout"]

    export = await call(client, "uv_export", {"project_path": "demo", "no_hashes": True})
    assert export["success"], export

    diag = await call(client, "uv_diagnose", {"project_path": "demo"})
    assert diag["overall"] == "healthy", diag["findings"]
    assert "sync" in diag["checks_run"]


async def test_relative_project_path_uses_workspace_root(client, project: Path) -> None:
    data = await call(client, "uv_python_find", {"project_path": "demo"})
    assert data["success"], data
    assert data["path"]


async def test_diagnose_and_repair_broken_environment(client, project: Path) -> None:
    assert (await call(client, "uv_sync", {"project_path": "demo"}))["success"]
    (project / "uv.lock").unlink()
    shutil.rmtree(project / ".venv")

    diag = await call(client, "uv_diagnose", {"project_path": "demo"})
    checks = {f["check"] for f in diag["findings"]}
    assert {"lockfile", "venv"} <= checks
    assert diag["overall"] == "warning"

    plan = await call(client, "uv_repair", {"project_path": "demo", "dry_run": True})
    assert [s["step"] for s in plan["steps"]] == ["lock", "sync"]
    assert all(s["status"] == "planned" for s in plan["steps"])
    assert not (project / "uv.lock").exists()

    fixed = await call(client, "uv_repair", {"project_path": "demo"})
    assert fixed["success"], fixed
    assert (project / "uv.lock").exists() and (project / ".venv").is_dir()
    assert all(f["severity"] == "info" for f in fixed["remaining_findings"])


async def test_diagnose_without_project(client, workspace: Path) -> None:
    (workspace / "requirements.txt").write_text("requests\n")
    diag = await call(client, "uv_diagnose")
    assert diag["overall"] == "error"
    assert diag["findings"][0]["check"] == "project"
    assert "requirements.txt" in diag["findings"][0]["fix"]


async def test_missing_project_gives_hint(client, workspace: Path) -> None:
    data = await call(client, "uv_sync", {"extra_args": ["--offline"]})
    assert not data["success"]
    assert data["hint"] and "uv_init" in data["hint"]


async def test_nonexistent_project_path_is_a_tool_error(client) -> None:
    assert "does not exist" in await call_error(client, "uv_sync", {"project_path": "nope"})


async def test_venv_and_pip_tools(client, workspace: Path) -> None:
    venv = await call(client, "uv_venv", {"path": "env", "python": PY})
    assert venv["success"], venv
    assert venv["path"] == str((workspace / "env").resolve())
    again = await call(client, "uv_venv", {"path": "env", "python": PY})
    assert not again["success"] and "clear" in (again["hint"] or "")
    assert (await call(client, "uv_venv", {"path": "env", "python": PY, "clear": True, "seed": True}))["success"]

    listed = await call(client, "uv_pip_list", {"python": str(workspace / "env")})
    assert listed["success"], listed
    assert any(p["name"] == "pip" for p in listed["packages"])
    assert listed["stdout"] == ""

    shown = await call(client, "uv_pip_show", {"packages": ["pip"], "python": str(workspace / "env")})
    assert shown["packages"][0]["name"] == "pip"

    assert (await call(client, "uv_pip_check", {"python": str(workspace / "env")}))["success"]
    frozen = await call(client, "uv_pip_freeze", {"python": str(workspace / "env")})
    assert "pip==" in frozen["stdout"]


async def test_server_virtualenv_does_not_leak_into_pip(
    client, workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When launched via `uv run`/`uvx`, VIRTUAL_ENV points at the server's own env; uv pip must ignore it."""
    assert (await call(client, "uv_venv", {"python": PY}))["success"]
    monkeypatch.setenv("VIRTUAL_ENV", sys.prefix)
    listed = await call(client, "uv_pip_list")
    assert listed["success"], listed
    assert not any(p["name"] == "fastmcp" for p in listed["packages"]), "listed the server's own environment"


async def test_python_tools(client) -> None:
    listed = await call(client, "uv_python_list", {"only_installed": True})
    assert listed["success"] and listed["installations"]
    assert all(i["path"] for i in listed["installations"])
    found = await call(client, "uv_python_find", {"request": PY})
    assert found["success"] and found["path"]


async def test_python_pin(client, project: Path) -> None:
    current = await call(client, "uv_python_pin", {"project_path": "demo"})
    assert current["success"] and current["pinned"] == PY
    assert (project / ".python-version").read_text().strip() == PY


async def test_cache_and_tool_list(client) -> None:
    size = await call(client, "uv_cache_size")
    assert size["success"] and size["size_bytes"] is not None
    tools = await call(client, "uv_tool_list")
    assert tools["success"]


async def test_uv_command_escape_hatch(client, project: Path) -> None:
    data = await call(client, "uv_command", {"args": ["--version"]})
    assert data["success"] and data["stdout"].startswith("uv ")
    data = await call(client, "uv_command", {"args": ["python", "dir"]})
    assert data["success"]


async def test_read_only_tree_does_not_create_lockfile(workspace: Path, make_client, client, project: Path) -> None:
    async with make_client(Settings(workspace_root=workspace, read_only=True)) as ro:
        data = await call(ro, "uv_tree", {"project_path": "demo"})
    assert not data["success"]
    assert "--frozen" in data["command"]
    assert not (project / "uv.lock").exists()


@pytest.mark.network
async def test_add_remove_and_audit(client, project: Path) -> None:
    added = await call(client, "uv_add", {"project_path": "demo", "packages": ["iniconfig"]})
    assert added["success"], added
    assert "iniconfig" in (project / "pyproject.toml").read_text()
    ran = await call(client, "uv_run", {"project_path": "demo", "command": ["python", "-c", "import iniconfig"]})
    assert ran["success"], ran

    dev = await call(client, "uv_add", {"project_path": "demo", "packages": ["pluggy"], "dev": True})
    assert dev["success"], dev
    info = await call(client, "uv_project_info", {"project_path": "demo"})
    assert any(d.startswith("pluggy") for d in info["dependency_groups"]["dev"])

    tree = await call(client, "uv_tree", {"project_path": "demo", "packages": ["iniconfig"], "invert": True})
    assert "demo" in tree["stdout"]

    removed = await call(client, "uv_remove", {"project_path": "demo", "packages": ["iniconfig"]})
    assert removed["success"], removed
    assert "iniconfig" not in (project / "pyproject.toml").read_text()


@pytest.mark.network
async def test_build(client, workspace: Path) -> None:
    init = await call(client, "uv_init", {"path": "lib", "kind": "lib", "python": PY, "vcs": "none"})
    assert init["success"], init
    built = await call(client, "uv_build", {"project_path": "lib"})
    assert built["success"], built
    assert any(a.endswith(".whl") for a in built["artifacts"])
    assert all(Path(a).exists() for a in built["artifacts"])


@pytest.mark.network
async def test_tool_run(client) -> None:
    data = await call(client, "uv_tool_run", {"command": ["pycowsay", "moo"]})
    assert data["success"], data
    assert "moo" in data["stdout"]
