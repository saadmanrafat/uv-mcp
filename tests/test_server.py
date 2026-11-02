from __future__ import annotations

from pathlib import Path

import pytest

from uv_mcp.config import ALL_TOOLSETS, Settings, default_workspace_root, parse_toolsets
from uv_mcp.registry import REGISTRY
from uv_mcp.server import INSTRUCTIONS, compact_schema, enabled_specs, main

from .conftest import call_error, posix_only


async def test_lists_all_tools_with_annotations(client) -> None:
    tools = {t.name: t for t in await client.list_tools()}
    assert set(tools) == set(REGISTRY)
    assert tools["uv_pip_list"].annotations.read_only_hint is True
    assert tools["uv_publish"].annotations.destructive_hint is True
    assert tools["uv_add"].annotations.read_only_hint is False
    assert tools["uv_add"].annotations.open_world_hint is True
    for t in tools.values():
        assert t.description and t.title, t.name


async def test_instructions_are_sent(client) -> None:
    assert client.instructions == INSTRUCTIONS
    assert client.server_info.name == "uv-mcp"
    assert "uv_add" in INSTRUCTIONS and "uv_diagnose" in INSTRUCTIONS


async def test_optional_params_are_compacted(client) -> None:
    tool = next(t for t in await client.list_tools() if t.name == "uv_add")
    schema = tool.input_schema
    assert schema["properties"]["project_path"] == {
        "description": schema["properties"]["project_path"]["description"],
        "type": "string",
    }
    remove = next(t for t in await client.list_tools() if t.name == "uv_remove")
    assert remove.input_schema["required"] == ["packages"]


def test_compact_schema_keeps_non_null_defaults() -> None:
    schema = {"properties": {"a": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": "x"}}}
    assert compact_schema(schema)["properties"]["a"]["default"] == "x"


async def test_read_only_mode_exposes_only_read_only_tools(workspace: Path, make_client) -> None:
    settings = Settings(workspace_root=workspace, read_only=True)
    async with make_client(settings) as c:
        names = {t.name for t in await c.list_tools()}
    assert "uv_add" not in names and "uv_run" not in names and "uv_publish" not in names
    assert {"uv_tree", "uv_pip_list", "uv_diagnose", "uv_info", "uv_command"} <= names
    for name in names - {"uv_command"}:
        assert REGISTRY[name].read_only, name


async def test_toolset_selection(workspace: Path, make_client) -> None:
    settings = Settings(workspace_root=workspace, toolsets=frozenset({"python"}))
    async with make_client(settings) as c:
        names = {t.name for t in await c.list_tools()}
    assert names == {n for n, s in REGISTRY.items() if s.toolset in ("python", None)}


def test_raw_command_can_be_disabled(workspace: Path) -> None:
    names = {s.name for s in enabled_specs(Settings(workspace_root=workspace, allow_raw_command=False))}
    assert "uv_command" not in names


def test_parse_toolsets() -> None:
    assert parse_toolsets(None) == frozenset(ALL_TOOLSETS)
    assert parse_toolsets("all") == frozenset(ALL_TOOLSETS)
    assert parse_toolsets("project, Python") == {"project", "python"}
    with pytest.raises(ValueError, match="Unknown toolset"):
        parse_toolsets("project,bogus")


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UV_MCP_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("UV_MCP_READ_ONLY", "true")
    monkeypatch.setenv("UV_MCP_TIMEOUT", "42")
    s = Settings.from_env()
    assert s.workspace_root == tmp_path.resolve() and s.read_only and s.timeout == 42
    monkeypatch.setenv("UV_MCP_READ_ONLY", "maybe")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_workspace_root_resolution_order(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    explicit, claude = tmp_path / "explicit", tmp_path / "claude"
    explicit.mkdir()
    claude.mkdir()
    monkeypatch.chdir(tmp_path)
    assert default_workspace_root() == tmp_path.resolve()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(claude))
    assert default_workspace_root() == claude.resolve()
    monkeypatch.setenv("UV_MCP_WORKSPACE_ROOT", str(explicit))
    assert default_workspace_root() == explicit.resolve()
    # Unexpanded placeholders and missing directories are ignored rather than fatal.
    monkeypatch.setenv("UV_MCP_WORKSPACE_ROOT", "${workspacePath}")
    assert default_workspace_root() == claude.resolve()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "missing"))
    assert default_workspace_root() == tmp_path.resolve()


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["auth", "token", "example.com"], "not allowed"),
        (["auth", "-q", "token", "example.com"], "not allowed"),
        (["auth", "--no-cache", "token", "example.com"], "not allowed"),
        (["python", "--quiet", "update-shell"], "not allowed"),
        (["python", "update-shell"], "not allowed"),
        (["tool", "update-shell"], "not allowed"),
        (["--directory", "/tmp", "sync"], "must be a uv subcommand"),
        (["../../bin/sh"], "must be a uv subcommand"),
    ],
)
async def test_uv_command_refuses_dangerous_input(client, args, message) -> None:
    assert message in await call_error(client, "uv_command", {"args": args})


async def test_uv_command_read_only_restrictions(workspace: Path, make_client) -> None:
    async with make_client(Settings(workspace_root=workspace, read_only=True)) as c:
        assert "read-only" in await call_error(c, "uv_command", {"args": ["add", "requests"]})
        assert "read-only" in await call_error(c, "uv_command", {"args": ["cache", "clean"]})


async def test_flag_injection_is_rejected_before_uv_runs(client) -> None:
    text = await call_error(client, "uv_add", {"packages": ["--index-url=https://evil.example/simple"]})
    assert "must not start with '-'" in text
    text = await call_error(client, "uv_run", {"command": ["--with", "evil"]})
    assert "must not start with '-'" in text


async def test_paths_outside_allowed_roots_are_refused(workspace: Path, make_client, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    settings = Settings(workspace_root=workspace, allowed_roots=(workspace.resolve(),))
    async with make_client(settings) as c:
        assert "outside the allowed roots" in await call_error(c, "uv_sync", {"project_path": str(outside)})
        assert "not allowed" in await call_error(c, "uv_sync", {"extra_args": ["--project", str(outside)]})


@posix_only
async def test_publish_is_dry_run_and_token_is_not_on_argv(workspace: Path, make_client, fake_uv) -> None:
    uv = fake_uv("print(json.dumps({'argv': argv, 'token': os.environ.get('UV_PUBLISH_TOKEN')}))")
    async with make_client(Settings(workspace_root=workspace, uv_path=uv)) as c:
        result = await c.call_tool("uv_publish", {"token": "pypi-secretsecretsecretsecret"})
    data = result.structured_content
    assert "--dry-run" in data["command"]
    assert "secret" not in data["command"]
    assert "secret" not in data["stdout"]
    assert "--token" not in data["stdout"]


@posix_only
async def test_auth_login_sends_secret_over_stdin(workspace: Path, make_client, fake_uv) -> None:
    uv = fake_uv("print(json.dumps({'argv': argv, 'stdin_len': len(sys.stdin.read().strip())}))")
    async with make_client(Settings(workspace_root=workspace, uv_path=uv)) as c:
        result = await c.call_tool("uv_auth_login", {"service": "pkgs.example.com", "token": "abcd-secret-token"})
    data = result.structured_content
    assert '"--token", "-"' in data["stdout"]
    assert "abcd-secret-token" not in data["stdout"] + data["command"]
    assert '"stdin_len": 17' in data["stdout"]


def test_main_list_tools(capsys: pytest.CaptureFixture[str], workspace: Path) -> None:
    main(["--workspace", str(workspace), "--read-only", "--list-tools"])
    out = capsys.readouterr().out
    assert "uv_tree" in out and "uv_add" not in out


def test_main_rejects_bad_config(workspace: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--workspace", str(workspace), "--toolsets", "nope", "--list-tools"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit):
        main(["--workspace", str(workspace / "missing"), "--list-tools"])


def test_workspace_must_be_inside_allowed_roots(tmp_path: Path, workspace: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(SystemExit):
        main(["--workspace", str(workspace), "--allowed-roots", str(other), "--list-tools"])
