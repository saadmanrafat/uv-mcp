"""Knowledge of uv's options, read from the installed uv's own ``--help``.

uv has over a thousand command options. Rather than hard-coding them (and drifting from whatever uv the user has
installed), uv-mcp parses ``uv <command> --help`` on demand and caches the result. This powers:

* ``uv_help``: agents can look up any option of any command, with its value type, choices and env var;
* ``extra_args`` validation: unknown or misspelled flags are rejected with suggestions before uv runs;
* the resolver options: only flags the command actually supports are emitted.
"""

from __future__ import annotations

import difflib
import functools
import os
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field

from .config import get_settings

#: Help sections whose options are accepted by every uv command.
GLOBAL_SECTIONS = frozenset({"Cache options", "Python options", "Global options"})

_SECTION_RE = re.compile(r"^([A-Z][A-Za-z ]+):$")
_OPTION_RE = re.compile(
    r"^\s{2,}(?:(?P<short>-[A-Za-z]), )?(?P<long>--[a-z0-9][a-z0-9-]*)(?:[ =]<(?P<value>[^>]+)>)?(?P<multi>\.\.\.)?(?P<rest>.*)$"
)
_SHORT_ONLY_RE = re.compile(r"^\s{2,}(?P<short>-[A-Za-z])(?:[ =]<(?P<value>[^>]+)>)?(?P<rest>\s{2,}.*)?$")
_CHOICES_RE = re.compile(r"\[possible values: ([^\]]+)\]")
_ENV_RE = re.compile(r"\[env:\s*\"?`?([A-Z][A-Z0-9_]*)`?=?[^\]]*\]")
_SUBCOMMAND_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_COMMAND_LINE_RE = re.compile(r"^  ([a-z][a-z0-9-]*)\s{2,}(\S.*)$")


@dataclass
class UVOption:
    flag: str
    short: str | None = None
    value: str | None = None
    scope: str = "command"  # "command" or "global"
    section: str = ""
    description: str = ""
    choices: list[str] = field(default_factory=list)
    env: str | None = None

    @property
    def takes_value(self) -> bool:
        return self.value is not None


@dataclass
class CommandHelp:
    path: tuple[str, ...]
    summary: str
    usage: str
    options: dict[str, UVOption]  # keyed by long flag
    shorts: dict[str, str]  # short flag -> long flag
    subcommands: dict[str, str] = field(default_factory=dict)  # name -> one-line summary

    def lookup(self, name: str) -> UVOption | None:
        if name.startswith("--"):
            return self.options.get(name)
        long = self.shorts.get(name)
        return self.options.get(long) if long else None


def _finish(opt: UVOption | None, desc: list[str]) -> None:
    if opt is None:
        return
    text = " ".join(part.strip() for part in desc if part.strip())
    choices = _CHOICES_RE.search(text)
    if choices:
        opt.choices = [c.strip() for c in choices.group(1).split(",") if c.strip()]
    env = _ENV_RE.search(text)
    if env:
        opt.env = env.group(1)
    opt.description = re.sub(r"\s*\[(?:env|possible values|default)[^\]]*\]", "", text).strip()


def parse_help(text: str, path: tuple[str, ...] = ()) -> CommandHelp:
    """Parse uv's long help output into structured options."""
    lines = text.splitlines()
    summary = next((ln.strip() for ln in lines if ln.strip()), "")
    usage = next((ln.strip()[len("Usage:") :].strip() for ln in lines if ln.startswith("Usage:")), "")
    options: dict[str, UVOption] = {}
    shorts: dict[str, str] = {}
    subcommands: dict[str, str] = {}
    section = ""
    current: UVOption | None = None
    desc: list[str] = []
    for line in lines:
        header = _SECTION_RE.match(line)
        if header:
            _finish(current, desc)
            current, desc = None, []
            section = header.group(1)
            continue
        if section == "Commands":
            cmd = _COMMAND_LINE_RE.match(line)
            if cmd and cmd.group(1) != "help":
                subcommands[cmd.group(1)] = cmd.group(2).strip()
            continue
        if section in ("", "Arguments", "Usage"):
            continue
        m = _OPTION_RE.match(line)
        if m:
            _finish(current, desc)
            current = UVOption(
                flag=m.group("long"),
                short=m.group("short"),
                value=m.group("value"),
                scope="global" if section in GLOBAL_SECTIONS else "command",
                section=section,
            )
            desc = [m.group("rest")]
            if current.flag not in ("--help", "--version"):
                options.setdefault(current.flag, current)
                if current.short:
                    shorts.setdefault(current.short, current.flag)
            continue
        if line.startswith(" ") and current is not None:
            desc.append(line)
        elif not line.strip():
            continue
        else:
            _finish(current, desc)
            current, desc = None, []
    _finish(current, desc)
    return CommandHelp(path=path, summary=summary, usage=usage, options=options, shorts=shorts, subcommands=subcommands)


def _uv_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env.update({"NO_COLOR": "1", "TERM": "dumb"})
    return env


@functools.lru_cache(maxsize=256)
def _load(uv: str, path: tuple[str, ...]) -> CommandHelp | None:
    try:
        proc = subprocess.run(
            [uv, *path, "--help"], capture_output=True, text=True, env=_uv_env(), timeout=15, stdin=subprocess.DEVNULL
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return parse_help(proc.stdout, path)


def command_help(path: Sequence[str]) -> CommandHelp | None:
    """Help for ``uv <path>`` from the installed uv, or None if uv or the command is unavailable."""
    path = tuple(path)
    if any(not _SUBCOMMAND_RE.match(p) for p in path):
        return None
    uv = get_settings().resolve_uv()
    if uv is None:
        return None
    return _load(uv, path)


def clear_cache() -> None:
    """Forget parsed help (call after uv itself changes, e.g. ``uv self update``)."""
    _load.cache_clear()


def suggest(name: str, help_: CommandHelp) -> list[str]:
    return difflib.get_close_matches(name, list(help_.options), n=3, cutoff=0.6)
