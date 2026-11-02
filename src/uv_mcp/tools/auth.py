"""Credentials for private indexes: uv auth login / logout.

There is deliberately no tool that *reads* a stored token back (``uv auth
token``): returning secrets into a model's context is an exfiltration risk.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..models import CommandResult
from ..registry import uv_tool
from ..security import ValidationError, safe_value
from ._common import Args, run

Service = Annotated[
    str, Field(description="Index domain or URL, e.g. 'pypi.example.com' or 'https://pkgs.dev.azure.com/org/'.")
]


@uv_tool(title="Store index credentials (uv auth login)", toolset="auth", idempotent=True)
async def uv_auth_login(
    service: Service,
    token: Annotated[str | None, Field(description="Access token (sent to uv over stdin, never echoed back).")] = None,
    username: str | None = None,
    password: Annotated[str | None, Field(description="Password (sent over stdin, never echoed back).")] = None,
) -> CommandResult:
    """Save credentials for a package index in uv's credential store so later installs can authenticate."""
    if bool(token) == bool(password):
        raise ValidationError("Pass exactly one of token or password")
    if password and not username:
        raise ValidationError("username is required with password")
    args = Args("auth", "login").opt("--username", username, "username")
    args.argv += ["--token", "-"] if token else ["--password", "-"]
    args.argv.append(safe_value(service, "service"))
    secret = token or password or ""
    return await run(args, stdin_data=secret + "\n", mutating=True, lock_key="global:auth", secrets=[secret])


@uv_tool(title="Remove index credentials (uv auth logout)", toolset="auth", destructive=True, idempotent=True)
async def uv_auth_logout(service: Service, username: str | None = None) -> CommandResult:
    """Delete stored credentials for a package index."""
    args = Args("auth", "logout").opt("--username", username, "username")
    args.argv.append(safe_value(service, "service"))
    return await run(args, mutating=True, lock_key="global:auth")
