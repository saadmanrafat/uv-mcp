from __future__ import annotations

from uv_mcp.parsing import load_json, parse_pip_show, parse_python_list, parse_size, parse_tool_list

TOOL_LIST = """\
black v26.5.1 (/home/u/.local/share/uv/tools/black)
- black (/home/u/.local/bin/black)
- blackd (/home/u/.local/bin/blackd)
ruff v0.16.9 [latest: 0.17.3]
- ruff
"""


def test_parse_tool_list_groups_executables_under_tools() -> None:
    tools = parse_tool_list(TOOL_LIST)
    assert [t.name for t in tools] == ["black", "ruff"]
    assert tools[0].version == "26.5.1"
    assert tools[0].executables == ["black", "blackd"]
    assert tools[0].path == "/home/u/.local/share/uv/tools/black"
    assert tools[1].executables == ["ruff"]
    assert tools[1].latest_version == "0.17.3"


def test_parse_tool_list_empty() -> None:
    assert parse_tool_list("No tools installed\n") == []


PIP_SHOW = """\
Name: requests
Version: 2.32.3
Location: /p/.venv/lib/python3.12/site-packages
Requires: certifi, charset-normalizer, idna, urllib3
Required-by:
Files:
  requests/__init__.py
  requests/api.py
---
Name: idna
Version: 3.10
Location: /p/.venv/lib/python3.12/site-packages
Requires:
Required-by: requests
"""


def test_parse_pip_show_multiple_packages() -> None:
    pkgs = parse_pip_show(PIP_SHOW)
    assert [p.name for p in pkgs] == ["requests", "idna"]
    assert pkgs[0].requires == ["certifi", "charset-normalizer", "idna", "urllib3"]
    assert pkgs[0].required_by == []
    assert pkgs[0].files == ["requests/__init__.py", "requests/api.py"]
    assert pkgs[1].required_by == ["requests"]


def test_parse_python_list() -> None:
    data = [
        {
            "key": "cpython-3.13.1-linux-x86_64-gnu",
            "version": "3.13.1",
            "path": "/home/u/.local/share/uv/python/cpython-3.13.1/bin/python3",
            "implementation": "cpython",
            "url": None,
        },
        {
            "key": "cpython-3.14.0-linux-x86_64-gnu",
            "version": "3.14.0",
            "path": None,
            "url": "https://example/x.tar.gz",
        },
        {"key": "cpython-3.12.0-linux-x86_64-gnu", "version": "3.12.0", "path": "/usr/bin/python3.12"},
    ]
    pys = parse_python_list(data)
    assert [p.managed for p in pys] == [True, None, False]
    assert pys[1].path is None and pys[1].url


def test_load_json_tolerates_preamble() -> None:
    assert load_json('warning: something\n{"a": 1}') == {"a": 1}
    assert load_json("[1, 2]") == [1, 2]
    assert load_json("not json") is None
    assert load_json("") is None


def test_parse_size() -> None:
    assert parse_size("123456\n") == (123456, None)
    assert parse_size("1.5MiB") == (1572864, "1.5MiB")
    assert parse_size("") == (None, None)
