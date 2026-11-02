"""Parsers that turn uv's text/JSON output into typed models."""

from __future__ import annotations

import json
import re
from typing import Any

from .models import InstalledPackage, InstalledTool, PackageDetails, PythonInstallation


def load_json(text: str) -> Any | None:
    """Parse JSON, tolerating leading warning lines some uv versions emit on stdout."""
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener in ("{", "["):
        idx = text.find(opener)
        if idx > 0:
            try:
                return json.loads(text[idx:])
            except json.JSONDecodeError:
                continue
    return None


def parse_python_list(data: Any) -> list[PythonInstallation]:
    out: list[PythonInstallation] = []
    if not isinstance(data, list):
        return out
    for item in data:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        key = str(item.get("key", ""))
        out.append(
            PythonInstallation(
                key=key,
                version=str(item.get("version", "")),
                implementation=item.get("implementation"),
                path=path,
                url=item.get("url"),
                variant=item.get("variant"),
                managed=None
                if path is None
                else ("/uv/python/" in path.replace("\\", "/") or "\\uv\\python\\" in path),
            )
        )
    return out


def parse_pip_list(data: Any) -> list[InstalledPackage]:
    if not isinstance(data, list):
        return []
    return [
        InstalledPackage(
            name=str(d.get("name", "")),
            version=str(d.get("version", "")),
            latest_version=d.get("latest_version"),
            latest_filetype=d.get("latest_filetype"),
            editable_project_location=d.get("editable_project_location"),
        )
        for d in data
        if isinstance(d, dict)
    ]


def _split_list(value: str) -> list[str]:
    return [p.strip() for p in value.split(",") if p.strip()]


def parse_pip_show(text: str) -> list[PackageDetails]:
    """Parse ``uv pip show`` output (records separated by ``---``)."""
    packages: list[PackageDetails] = []
    for block in re.split(r"^---\s*$", text, flags=re.M):
        fields: dict[str, str] = {}
        files: list[str] = []
        in_files = False
        for line in block.splitlines():
            if in_files:
                if line.startswith((" ", "\t")):
                    files.append(line.strip())
                    continue
                in_files = False
            if line.strip() == "Files:":
                in_files = True
                continue
            if ":" in line and not line.startswith((" ", "\t")):
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
        if "Name" not in fields:
            continue
        packages.append(
            PackageDetails(
                name=fields["Name"],
                version=fields.get("Version"),
                location=fields.get("Location"),
                editable_project_location=fields.get("Editable project location"),
                requires=_split_list(fields.get("Requires", "")),
                required_by=_split_list(fields.get("Required-by", "")),
                files=files,
                fields=fields,
            )
        )
    return packages


_TOOL_LINE = re.compile(r"^(?P<name>\S+)\s+v(?P<version>\S+)(?P<rest>.*)$")
_EXE_LINE = re.compile(r"^-\s+(?P<exe>\S+)(?:\s+\((?P<path>[^)]*)\))?")
_PAREN = re.compile(r"\(([^)]*)\)")
_LATEST = re.compile(r"\[latest:\s*([^\]]+)\]")


def parse_tool_list(text: str) -> list[InstalledTool]:
    """Parse ``uv tool list`` output into tools and their executables."""
    tools: list[InstalledTool] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("warning:", "No tools installed")):
            continue
        exe = _EXE_LINE.match(line)
        if exe and tools:
            tools[-1].executables.append(exe.group("exe"))
            continue
        m = _TOOL_LINE.match(line)
        if m:
            rest = m.group("rest")
            paren = _PAREN.search(rest)
            latest = _LATEST.search(rest)
            tools.append(
                InstalledTool(
                    name=m.group("name"),
                    version=m.group("version"),
                    path=paren.group(1) if paren else None,
                    latest_version=latest.group(1).strip().lstrip("v") if latest else None,
                )
            )
    return tools


_SIZE_UNITS = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "TiB": 1024**4}


def parse_size(text: str) -> tuple[int | None, str | None]:
    """Parse ``uv cache size`` output (raw bytes, or human readable with --human)."""
    value = text.strip().splitlines()[-1].strip() if text.strip() else ""
    if value.isdigit():
        return int(value), None
    m = re.match(r"^([\d.]+)\s*([KMGT]?i?B)$", value)
    if m and m.group(2) in _SIZE_UNITS:
        return int(float(m.group(1)) * _SIZE_UNITS[m.group(2)]), value
    return None, value or None


def last_line(text: str) -> str | None:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else None
