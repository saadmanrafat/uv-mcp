"""uv-mcp: a Model Context Protocol server that exposes the uv CLI to AI agents."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("uv-mcp-server")
except PackageNotFoundError:  # pragma: no cover - running from a source tree
    __version__ = "2.0.0"

__all__ = ["__version__"]
