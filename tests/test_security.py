from __future__ import annotations

import sys
from pathlib import Path

import pytest

from uv_mcp.config import Settings
from uv_mcp.security import (
    ValidationError,
    redact,
    redact_argv,
    resolve_path,
    safe_env,
    safe_extra_args,
    safe_value,
)


@pytest.mark.parametrize("value", ["--index-url=https://evil", "-e", "-r/etc/passwd"])
def test_safe_value_rejects_flag_injection(value: str) -> None:
    with pytest.raises(ValidationError, match="must not start with '-'"):
        safe_value(value, "package")


@pytest.mark.parametrize("value", ["a\x00b", "requests\n--index-url x", "a\rb"])
def test_safe_value_rejects_control_characters(value: str) -> None:
    with pytest.raises(ValidationError):
        safe_value(value, "package")


@pytest.mark.parametrize(
    "value", ["requests", "fastapi[standard]>=0.115", "git+https://github.com/a/b@v1", "./local/pkg", "numpy==2.*"]
)
def test_safe_value_accepts_requirement_specifiers(value: str) -> None:
    assert safe_value(value, "package") == value


def test_safe_value_rejects_empty_and_oversized() -> None:
    with pytest.raises(ValidationError):
        safe_value("   ", "package")
    with pytest.raises(ValidationError):
        safe_value("a" * 5000, "package")


def test_relative_paths_resolve_against_workspace_not_cwd(tmp_path: Path) -> None:
    settings = Settings(workspace_root=tmp_path)
    assert resolve_path("sub/dir", settings) == (tmp_path / "sub" / "dir").resolve()
    assert resolve_path(None, settings) == tmp_path.resolve()


def test_confinement_blocks_escape(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    settings = Settings(workspace_root=root, allowed_roots=(root.resolve(),))
    assert resolve_path("inner", settings) == (root / "inner").resolve()
    with pytest.raises(ValidationError, match="outside the allowed roots"):
        resolve_path("../outside", settings)
    with pytest.raises(ValidationError, match="outside the allowed roots"):
        resolve_path("/etc", settings)


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges on Windows")
def test_confinement_blocks_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    (root / "link").symlink_to(tmp_path)
    settings = Settings(workspace_root=root, allowed_roots=(root.resolve(),))
    with pytest.raises(ValidationError):
        resolve_path("link", settings)


def test_must_exist(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="does not exist"):
        resolve_path("nope", Settings(workspace_root=tmp_path), must_exist=True)


def test_extra_args_relocation_flags_blocked_only_when_confined(tmp_path: Path) -> None:
    free = Settings(workspace_root=tmp_path)
    assert safe_extra_args(["--directory", "/x"], free) == ["--directory", "/x"]
    confined = Settings(workspace_root=tmp_path, allowed_roots=(tmp_path,))
    for flag in (["--directory", "/x"], ["--project=/x"], ["--config-file", "c.toml"]):
        with pytest.raises(ValidationError, match="not allowed"):
            safe_extra_args(flag, confined)
    assert safe_extra_args(["--offline", "--no-build-isolation"], confined) == ["--offline", "--no-build-isolation"]


def test_extra_args_reject_control_characters(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        safe_extra_args(["--offline\n"], Settings(workspace_root=tmp_path))


def test_safe_env() -> None:
    assert safe_env({"FOO": "1", "_BAR2": "x"}) == {"FOO": "1", "_BAR2": "x"}
    for bad in ({"1X": "a"}, {"A-B": "a"}, {"A": "x\x00"}):
        with pytest.raises(ValidationError):
            safe_env(bad)


def test_redact_url_credentials_and_tokens() -> None:
    text = (
        "fetching https://user:hunter2@pypi.example.com/simple and "
        "https://__token__@idx.example.com/ with pypi-AgEIcHlwaS5vcmcCJGFiY2RlZmdo and ghp_abcdefghijklmnopqrstuvwxyz0123"
    )
    out = redact(text)
    assert "hunter2" not in out and "user:" not in out
    assert "__token__" not in out
    assert "pypi-AgEI" not in out
    assert "ghp_" not in out
    assert "pypi.example.com/simple" in out


def test_redact_explicit_secrets() -> None:
    assert redact("token is s3cret-value!", ["s3cret-value"]) == "token is ***!"


def test_redact_argv() -> None:
    argv = ["publish", "--token", "abc123", "--password=pw", "-t", "/target", "--index-url", "https://u:p@h/simple"]
    out = redact_argv(argv)
    assert out == [
        "publish",
        "--token",
        "***",
        "--password=***",
        "-t",
        "/target",
        "--index-url",
        "https://***@h/simple",
    ]
