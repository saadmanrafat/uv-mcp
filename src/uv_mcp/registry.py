"""A tiny registry so tools can be declared once and filtered at server start-up.

Tools are declared with :func:`uv_tool`, which records MCP annotations and the
toolset they belong to. :func:`uv_mcp.server.create_server` then registers only
the tools allowed by the active :class:`~uv_mcp.config.Settings` (toolset
selection and read-only mode).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mcp_types import ToolAnnotations


@dataclass(frozen=True)
class ToolSpec:
    fn: Callable[..., Any]
    name: str
    title: str
    toolset: str | None
    read_only: bool
    destructive: bool
    idempotent: bool
    open_world: bool

    @property
    def annotations(self) -> ToolAnnotations:
        return ToolAnnotations(
            title=self.title,
            readOnlyHint=self.read_only,
            destructiveHint=self.destructive if not self.read_only else False,
            idempotentHint=self.idempotent,
            openWorldHint=self.open_world,
        )


REGISTRY: dict[str, ToolSpec] = {}


def uv_tool(
    *,
    title: str,
    toolset: str | None,
    read_only: bool = False,
    destructive: bool = False,
    idempotent: bool = False,
    open_world: bool = False,
    name: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Declare an MCP tool.

    Args:
        title: Human readable title shown by clients.
        toolset: Toolset name (``None`` = always registered).
        read_only: The tool never changes files, environments or remote state.
        destructive: The tool may delete or overwrite something that is hard to restore.
        idempotent: Repeating the call with the same arguments has no further effect.
        open_world: The tool may talk to the network (package indexes, GitHub...).
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        if tool_name in REGISTRY:
            raise RuntimeError(f"Duplicate tool name: {tool_name}")
        REGISTRY[tool_name] = ToolSpec(
            fn=fn,
            name=tool_name,
            title=title,
            toolset=toolset,
            read_only=read_only,
            destructive=destructive,
            idempotent=idempotent,
            open_world=open_world,
        )
        return fn

    return decorator
