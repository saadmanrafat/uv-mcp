"""uv cache management."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..models import CacheSizeResult, CommandResult
from ..parsing import parse_size
from ..registry import uv_tool
from ._common import Args, ExtraArgs, extend, run

_CACHE_LOCK = "global:cache"


@uv_tool(title="Clear the uv cache (uv cache clean)", toolset="cache", destructive=True, idempotent=True)
async def uv_cache_clean(
    packages: Annotated[
        list[str] | None, Field(description="Only remove entries for these packages (default: everything).")
    ] = None,
    force: Annotated[bool, Field(description="Remove even if another uv process holds the cache lock.")] = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Delete cached downloads and builds. Fixes corrupted-cache errors; later installs will re-download."""
    args = Args("cache", "clean").flag(force, "--force").extra(extra_args).positional(packages, "package")
    return await run(args, mutating=True, lock_key=_CACHE_LOCK)


@uv_tool(title="Prune unused cache entries (uv cache prune)", toolset="cache", idempotent=True)
async def uv_cache_prune(
    ci: Annotated[
        bool,
        Field(description="Also drop pre-built wheels, keeping only what is expensive to rebuild (for CI caches)."),
    ] = False,
    extra_args: ExtraArgs = None,
) -> CommandResult:
    """Remove unused and stale cache entries to reclaim disk space without losing what is in use."""
    args = Args("cache", "prune").flag(ci, "--ci").extra(extra_args)
    return await run(args, mutating=True, lock_key=_CACHE_LOCK)


@uv_tool(title="Show cache size (uv cache size)", toolset="cache", read_only=True, idempotent=True)
async def uv_cache_size() -> CacheSizeResult:
    """Report how much disk space the uv cache uses."""
    result = await run(Args("cache", "size"))
    size, _ = parse_size(result.stdout) if result.success else (None, None)
    human = await run(Args("cache", "size", "--human")) if result.success else None
    return extend(
        result,
        CacheSizeResult,
        size_bytes=size,
        human=(human.stdout.strip() or None) if human and human.success else None,
    )
