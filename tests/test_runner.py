from __future__ import annotations

import time
from pathlib import Path

import pytest

from uv_mcp.config import Settings
from uv_mcp.runner import build_env, run_uv, truncate

from .conftest import posix_only


def test_build_env_scrubs_server_virtualenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/opt/uv-mcp/.venv")
    monkeypatch.setenv("UV_RUN_RECURSION_DEPTH", "1")
    monkeypatch.setenv("KEEP_ME", "yes")
    env = build_env({"EXTRA": "1"})
    assert "VIRTUAL_ENV" not in env
    assert "UV_RUN_RECURSION_DEPTH" not in env
    assert env["KEEP_ME"] == "yes"
    assert env["EXTRA"] == "1"
    assert env["NO_COLOR"] == "1" and env["UV_NO_PROGRESS"] == "1"


def test_truncate_keeps_head_and_tail() -> None:
    text = "HEAD" + "x" * 1000 + "TAIL"
    out, cut = truncate(text, 100)
    assert cut
    assert out.startswith("HEAD") and out.endswith("TAIL")
    assert "characters omitted" in out
    assert truncate("short", 100) == ("short", False)


async def test_missing_uv_reports_hint(tmp_path: Path) -> None:
    settings = Settings(workspace_root=tmp_path, uv_path=str(tmp_path / "does-not-exist"))
    result = await run_uv(["--version"], settings=settings)
    assert not result.success
    assert result.exit_code is None
    assert "not installed" in (result.hint or "")


@posix_only
async def test_exit_code_and_output_are_returned(tmp_path: Path, fake_uv) -> None:
    uv = fake_uv("print('out:' + ' '.join(argv)); print('err', file=sys.stderr); sys.exit(3)")
    settings = Settings(workspace_root=tmp_path, uv_path=uv)
    result = await run_uv(["add", "requests"], settings=settings)
    assert result.exit_code == 3
    assert not result.success
    assert result.stdout.strip() == "out:add requests"
    assert result.stderr.strip() == "err"
    assert result.command == "uv add requests"
    assert result.cwd == str(tmp_path.resolve())


@posix_only
async def test_stdin_is_closed_so_prompts_cannot_hang(tmp_path: Path, fake_uv) -> None:
    uv = fake_uv("data = sys.stdin.read(); print(repr(data))")
    result = await run_uv(["x"], settings=Settings(workspace_root=tmp_path, uv_path=uv, timeout=10))
    assert result.success
    assert result.stdout.strip() == "''"


@posix_only
async def test_stdin_data_is_delivered(tmp_path: Path, fake_uv) -> None:
    uv = fake_uv("print('got', len(sys.stdin.read().strip()))")
    result = await run_uv(["x"], stdin_data="secret\n", settings=Settings(workspace_root=tmp_path, uv_path=uv))
    assert result.stdout.strip() == "got 6"


@posix_only
async def test_timeout_kills_process_tree(tmp_path: Path, fake_uv) -> None:
    marker = tmp_path / "child-survived"
    uv = fake_uv(
        f"""
        import subprocess
        subprocess.Popen([sys.executable, "-c", "import time; time.sleep(3); open({str(marker)!r}, 'w').write('x')"])
        time.sleep(30)
        """
    )
    started = time.monotonic()
    result = await run_uv(["x"], settings=Settings(workspace_root=tmp_path, uv_path=uv, timeout=1))
    assert time.monotonic() - started < 10
    assert result.timed_out and not result.success and result.exit_code is None
    assert "timed out" in result.stderr
    assert "timeout" in (result.hint or "").lower()
    time.sleep(3.5)
    assert not marker.exists(), "grandchild process should have been killed with the process group"


@posix_only
async def test_secrets_are_redacted_from_output_and_command(tmp_path: Path, fake_uv) -> None:
    uv = fake_uv("print('using', os.environ.get('UV_PUBLISH_TOKEN'), 'https://bob:pw@idx/simple')")
    result = await run_uv(
        ["publish", "--token", "tok-123456"],
        env={"UV_PUBLISH_TOKEN": "tok-123456"},
        settings=Settings(workspace_root=tmp_path, uv_path=uv),
    )
    assert "tok-123456" not in result.stdout
    assert "tok-123456" not in result.command
    assert "bob:pw" not in result.stdout


@posix_only
async def test_output_truncation_flag(tmp_path: Path, fake_uv) -> None:
    uv = fake_uv("print('y' * 5000)")
    result = await run_uv(["x"], settings=Settings(workspace_root=tmp_path, uv_path=uv, max_output_chars=200))
    assert result.truncated
    assert len(result.stdout) < 400


@posix_only
async def test_failure_hint_from_stderr(tmp_path: Path, fake_uv) -> None:
    uv = fake_uv(
        "print('error: No `pyproject.toml` found in current directory or any parent directory', file=sys.stderr); sys.exit(2)"
    )
    result = await run_uv(["sync"], settings=Settings(workspace_root=tmp_path, uv_path=uv))
    assert "uv_init" in (result.hint or "")
