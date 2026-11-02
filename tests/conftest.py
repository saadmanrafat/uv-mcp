from __future__ import annotations

import os
import shutil
import stat
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client

from uv_mcp.config import Settings, set_settings
from uv_mcp.server import create_server

HAS_UV = shutil.which("uv") is not None
requires_uv = pytest.mark.skipif(not HAS_UV, reason="uv is not installed")
posix_only = pytest.mark.skipif(sys.platform == "win32", reason="uses a POSIX shebang script as a fake uv")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests independent from the developer's shell and from the server's own venv."""
    for var in (
        "UV_MCP_WORKSPACE_ROOT",
        "UV_MCP_ALLOWED_ROOTS",
        "UV_MCP_READ_ONLY",
        "UV_MCP_TOOLSETS",
        "UV_MCP_TIMEOUT",
        "UV_MCP_UV_PATH",
        "UV_MCP_ALLOW_RAW_COMMAND",
        "UV_NATIVE_TLS",
        "CLAUDE_PROJECT_DIR",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("UV_NO_PROGRESS", "1")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    return ws


@pytest.fixture
def settings(workspace: Path) -> Settings:
    s = Settings(workspace_root=workspace)
    set_settings(s)
    return s


@pytest.fixture
def make_client():
    def factory(settings: Settings) -> Client:
        return Client(create_server(settings))

    return factory


@pytest.fixture
async def client(settings: Settings, make_client):
    async with make_client(settings) as c:
        yield c


async def call(client: Client, tool: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    result = await client.call_tool(tool, args or {})
    assert result.structured_content is not None, result
    return result.structured_content


async def call_error(client: Client, tool: str, args: dict[str, Any] | None = None) -> str:
    result = await client.call_tool(tool, args or {}, raise_on_error=False)
    assert result.is_error, result
    return result.content[0].text


@pytest.fixture
def fake_uv(tmp_path: Path):
    """Create an executable that stands in for uv. ``body`` is Python run with ``argv`` available."""

    def factory(body: str) -> str:
        path = tmp_path / "fake-uv"
        path.write_text(
            f"#!{sys.executable}\nimport os, sys, time, json\nargv = sys.argv[1:]\n" + textwrap.dedent(body)
        )
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
        return str(path)

    return factory


def uv_env_ok() -> bool:
    return HAS_UV and os.environ.get("UV_MCP_SKIP_INTEGRATION") != "1"
