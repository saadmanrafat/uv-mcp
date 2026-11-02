"""Safe execution of uv subprocesses.

Guarantees provided by :func:`run_uv`:

* **No shell.** uv is executed directly with an argv list.
* **Clean environment.** Variables that would silently redirect uv to the
  *server's* own virtual environment (``VIRTUAL_ENV`` set by ``uv run``/``uvx``
  when launching this server) are removed, and colour/progress output is
  disabled so results are plain text.
* **Never interactive.** stdin is closed (or fed a single secret) so uv can never
  block waiting for a prompt.
* **Bounded.** Every call has a timeout; on expiry the whole process tree is
  killed. Output is truncated to a configurable size (keeping head and tail).
* **Serialised writes.** Mutating commands take a per-directory lock so two
  concurrent tool calls cannot race on the same ``uv.lock`` / ``.venv``.
* **Redacted.** Command lines and output are scrubbed of credentials.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import shlex
import signal
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from .config import Settings, get_settings
from .hints import hint_for
from .models import CommandResult
from .security import redact, redact_argv

logger = logging.getLogger("uv_mcp")

#: Variables stripped from the environment passed to uv.
_SCRUBBED_ENV = (
    "VIRTUAL_ENV",  # set by `uv run`/`uvx` for *this server's* env; would hijack `uv pip`
    "UV_RUN_RECURSION_DEPTH",
    "PYTHONHOME",
    "PYTHONEXECUTABLE",
    "__PYVENV_LAUNCHER__",
)
_FORCED_ENV = {
    "NO_COLOR": "1",
    "UV_NO_PROGRESS": "1",
    "TERM": "dumb",
    "CLICOLOR": "0",
    "PYTHONIOENCODING": "utf-8",
}
_HEARTBEAT_SECONDS = 5.0

_dir_locks: dict[str, asyncio.Lock] = {}


def _lock_for(key: str) -> asyncio.Lock:
    lock = _dir_locks.get(key)
    if lock is None:
        lock = _dir_locks[key] = asyncio.Lock()
    return lock


def build_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return the environment used for uv subprocesses."""
    env = {k: v for k, v in os.environ.items() if k not in _SCRUBBED_ENV}
    env.update(_FORCED_ENV)
    if extra:
        env.update(extra)
    return env


def truncate(text: str, limit: int) -> tuple[str, bool]:
    """Keep the first and last part of ``text`` if it exceeds ``limit`` characters."""
    if len(text) <= limit:
        return text, False
    head = int(limit * 0.4)
    tail = limit - head
    omitted = len(text) - head - tail
    return f"{text[:head]}\n... [{omitted} characters omitted] ...\n{text[-tail:]}", True


def format_command(argv: Sequence[str]) -> str:
    return "uv " + " ".join(shlex.quote(a) for a in redact_argv(argv))


def _kill_tree(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    with contextlib.suppress(ProcessLookupError, OSError):
        if sys.platform != "win32":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()


async def _heartbeat(label: str, started: float) -> None:
    """Send MCP progress notifications while a long command runs.

    Clients that supplied a progress token keep the call alive and can show the
    user that uv is still working. Without a token this is a no-op.
    """
    try:
        from fastmcp.server.dependencies import get_context

        ctx = get_context()
    except Exception:
        return
    while True:
        await asyncio.sleep(_HEARTBEAT_SECONDS)
        elapsed = time.monotonic() - started
        with contextlib.suppress(Exception):
            await ctx.report_progress(elapsed, None, f"{label} running for {elapsed:.0f}s")


async def run_uv(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
    stdin_data: str | None = None,
    mutating: bool = False,
    lock_key: str | None = None,
    secrets: Sequence[str] = (),
    settings: Settings | None = None,
) -> CommandResult:
    """Run ``uv *args`` and return a :class:`CommandResult`.

    Args:
        args: Arguments after ``uv``.
        cwd: Working directory (defaults to the workspace root).
        timeout: Seconds before the process tree is killed (defaults to settings).
        env: Extra environment variables (merged over the scrubbed environment).
        stdin_data: Text written to stdin (used to pass secrets without argv).
        mutating: Serialise with other mutating commands on the same ``lock_key``.
        lock_key: Lock scope; defaults to ``cwd``. Use ``"global"`` for
            machine-wide state such as Python installs or the cache.
        secrets: Literal strings to scrub from all output.
        settings: Override the active settings (tests).
    """
    settings = settings or get_settings()
    workdir = (cwd or settings.workspace_root).resolve()
    timeout = timeout or settings.timeout
    argv = list(args)
    command = format_command(argv)
    all_secrets = [s for s in secrets if s]
    if env:
        all_secrets += [v for k, v in env.items() if any(w in k.upper() for w in ("TOKEN", "PASSWORD", "SECRET"))]

    uv = settings.resolve_uv()
    if uv is None:
        return CommandResult(
            success=False,
            command=command,
            cwd=str(workdir),
            stderr="uv executable not found",
            hint=hint_for("", uv_missing=True),
        )

    lock: asyncio.Lock | contextlib.AbstractAsyncContextManager[None]
    lock = _lock_for(lock_key or str(workdir)) if mutating else contextlib.nullcontext()

    async with lock:
        logger.info("running %s (cwd=%s)", command, workdir)
        started = time.monotonic()
        kwargs: dict = {}
        if sys.platform != "win32":
            kwargs["start_new_session"] = True  # own process group -> killable as a tree
        else:  # pragma: no cover - exercised on Windows CI only
            kwargs["creationflags"] = 0x00000200  # CREATE_NEW_PROCESS_GROUP
        try:
            process = await asyncio.create_subprocess_exec(
                uv,
                *argv,
                cwd=str(workdir),
                env=build_env(env),
                stdin=asyncio.subprocess.PIPE if stdin_data is not None else asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **kwargs,
            )
        except (OSError, ValueError) as exc:
            return CommandResult(
                success=False,
                command=command,
                cwd=str(workdir),
                stderr=redact(str(exc), all_secrets),
                hint=hint_for(str(exc)),
            )

        heartbeat = asyncio.create_task(_heartbeat(command, started))
        timed_out = False
        stdout_b, stderr_b = b"", b""
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                process.communicate(stdin_data.encode() if stdin_data is not None else None),
                timeout=timeout,
            )
        except TimeoutError:
            timed_out = True
            _kill_tree(process)
            with contextlib.suppress(Exception):
                stdout_b, stderr_b = await asyncio.wait_for(process.communicate(), timeout=5)
        except asyncio.CancelledError:
            _kill_tree(process)
            raise
        finally:
            heartbeat.cancel()

        duration = round(time.monotonic() - started, 3)

    stdout = redact(stdout_b.decode("utf-8", errors="replace"), all_secrets)
    stderr = redact(stderr_b.decode("utf-8", errors="replace"), all_secrets)
    if timed_out:
        stderr = (stderr + f"\nuv-mcp: command timed out after {timeout:g}s and was terminated").strip()
    stdout, cut_out = truncate(stdout, settings.max_output_chars)
    stderr, cut_err = truncate(stderr, settings.max_output_chars)
    exit_code = None if timed_out else process.returncode
    success = exit_code == 0
    if not success:
        logger.warning("%s failed (exit=%s)", command, exit_code)
    return CommandResult(
        success=success,
        command=command,
        cwd=str(workdir),
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=duration,
        timed_out=timed_out,
        truncated=cut_out or cut_err,
        hint=None if success else hint_for(stderr, timed_out=timed_out),
    )
