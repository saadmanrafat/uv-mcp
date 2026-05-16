# uv-mcp | Rules, Backlog & Release Automation

## Project Overview
An elegant Model Context Protocol (MCP) server providing autonomous tools for managing the `uv` package manager ecosystem (virtual environments, project sync, dependency tracking, and lockfile diagnostics).

## Tech Stack
- **Runtime:** Python 3.12+ managed entirely via `uv`
- **Libraries:** Pydantic v2, `fastmcp`, SQLModel
- **Quality Layer:** Strict typing (`mypy --strict`), structured JSON logs

## Architecture Philosophy
- **Hexagonal Architecture:** Decouple Core Domain logic (dependency processing rules) from Application Adapters (FastMCP tool registration interfaces) and Infrastructure (Shell subprocess controllers).
- **Determinism:** Every MCP tool input schema must be explicitly derived from a declarative Pydantic model. Never return raw, untyped dictionaries for JSON-RPC payloads.

## Operational Commands
- Sync environment: `uv sync`
- Run typecheck: `uv run mypy src/uv_mcp --strict`
- Run test suite: `uv run pytest`
- Audit linting: `uv run ruff check .`
- Check git state: `git status --porcelain`

## Code Style & Conventions
- **Explicit Types:** Full type annotations required everywhere. Avoid `Any`. Use `Mapping`/`Sequence` instead of mutable types for arguments.
- **Error Boundaries:** Subprocess execution errors must be caught inside Infrastructure wrappers and converted to standard MCP JSON-RPC error codes (e.g., `-32603` for internal execution faults). Never leak raw Python stack traces into the tool text outputs.

---

## Core Backlog: Bugs & Feature Implementation

### 1. Existing Feature Bug Fixes
- **ANSI Output Pollution:** Intercept all subprocess streams (`stdout`/`stderr`). Enforce clean text responses across the execution proxy layer by explicitly injecting environment mappings (`UV_COLOR=never`, `TERM=dumb`).
- **Concurrent Lockfile Contention:** Protect mutating shell operations (`uv add`, `uv remove`, `uv sync`) using an asynchronous FIFO gate (`asyncio.Lock()`) registered at the application core router layer.
- **Path Drift Resolution:** Enforce absolute filesystem resolution. Tool input schemas must normalize incoming paths using `Path.resolve()` and explicitly bind targets via the `--directory` system flag.

### 2. New Feature Specs
- **Ephemeral Tool Runner (`uvx` Proxy):** Register an MCP tool named `run_ephemeral_tool(package: str, command: list[str])`. Execute logic using `uvx --from {package} {command[0]} {command[1:]}` under a strict absolute execution path boundary.
- **Workspace Introspection Engine:** Implement `get_workspace_manifest()`. Use a secure parser to scan the root configurations, pull `[tool.uv.workspace]` definitions, mapping sub-project dependencies into a topological JSON graph payload.
- **Self-Healing Diagnostics Handler:** Inject a regex monitoring pattern over failing process pipelines. Catch signatures like `ModuleNotFoundError: No module named '...'`, extract the target string identifier, and append a diagnostic payload suggesting the correct correction command (`uv add <package>`).

---

## Release & Automation Workflow Rules
When commanded to tag or release a version, follow this sequence exactly:
1. **Validation Gate:** Execute `uv run mypy . --strict` and `uv run pytest`. Abort if any error code is non-zero.
2. **Clean Status Audit:** Run `git status --porcelain`. The directory must be completely clean before continuing.
3. **Changelog Mutation:** Open `CHANGELOG.md`. Move to the line below the `## [Unreleased]` anchor block and insert a formatted version section: `## [X.Y.Z] - YYYY-MM-DD`. Parse recent commit data to populate subheaders (`### Added`, `### Changed`, `### Fixed`).
4. **Version Sync:** Access `pyproject.toml` and synchronize the `version` variable string inside the `[project]` configuration block to match the target release.
5. **Release Commit:** Execute a single commit holding the tracking changes: `git commit -am "chore(release): bump version to X.Y.Z"`.
6. **Tag and Push Automation:**
   - Cut an annotated git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
   - Push both the tracking branch updates and the annotated tag simultaneously: `git push origin main && git push origin vX.Y.Z`
