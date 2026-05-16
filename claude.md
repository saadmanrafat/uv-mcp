# CLAUDE.md | Feature Deficit & Gap Analysis

## Project Status Overview
The current `uv-mcp` server successfully bridges basic python project operations (`init`, `sync`, `lock`, `build`, `add`, `remove`), basic `uv python` operations, and key `uv pip` inspection tools. However, it completely lacks several of the native, primitive toolsets provided by the `uv` ecosystem.

This document identifies all missing `uv` features absent from the current implementation to guide upcoming feature-parity sprint cycles.

---

## Missing Feature Backlog

### 1. Ephemeral Run & Tool Management Layer (`uv run` & `uvx` / `uv tool`)
* **Deficit:** The codebase lacks any implementation wrapper around `uv run` to execute arbitrary shell commands or individual modules inside an environmentally isolated lockfile boundary.
* **Deficit:** The server lacks support for the `uv tool` ecosystem (`uv tool install`, `uv tool run`, `uv tool list`). Calling agents have no method to fetch, run, or globally handle standalone developer utilities (e.g., `ruff`, `black`, `mypy`) ephemerally outside target workspace setups.

### 2. PEP 723 Inline Script Metadata Support
* **Deficit:** Modern `uv` can directly read and run isolated single-file Python scripts that declare their own embedded dependency blocks via inline comments (PEP 723, e.g., `# /// script\n# dependencies = ["requests"]\n# ///`).
* **Deficit:** `uv-mcp` enforces a rigid project framework anchored to a structured `pyproject.toml` file layout. Agents cannot pass a standalone file to be parsed, resolved, and run dynamically in an independent clean environment context.

### 3. Distribution Registry Publishing (`uv publish`)
* **Deficit:** While `uv_build_project` exists to assemble source distributions and wheel binaries into local `dist/` directories, the final upstream publishing segment (`uv publish`) is missing.
* **Deficit:** Agents cannot upload built build configurations to PyPI or alternative private enterprise OCI/PyPI registries directly via the server interface.

### 4. Advanced `uv pip` Quality & Diagnostic Primitives
* **Deficit (`uv pip compile`):** There is no engine tool mapping to compile legacy requirements structures (`requirements.in`) directly into locked requirement outputs without spinning up or modifying a top-level workspace project model.
* **Deficit (`uv pip sync`):** The server does not expose a low-level target matching function to overwrite a target virtual environment state to mirror a raw flat dependency list exactly, meaning it lacks automated environment pruning logic.
* **Deficit (`uv pip check`):** There is no dedicated interface tool exposing environment tracking checks to catch structural dependency depth mismatches or conflicting packages explicitly.

### 5. Configurable Virtual Environment Settings (`uv venv`)
* **Deficit:** The internal helper `_repair_venv` fires an unconfigured, raw `uv venv` shell subprocess execution.
* **Deficit:** It misses crucial parameterization extensions native to `uv venv`, including choosing user prompts (`--prompt`), allowing global access configurations (`--system-site-packages`), or deciding whether to explicitly seed core packages into the generated environment directories.

### 6. Granular Cache Tuning & Maintenance (`uv cache`)
* **Deficit:** Cache control inside `actions.py` maps solely to basic target deletions via `uv cache clean`.
* **Deficit:** Advanced layout utility tools are entirely unmapped, such as `uv cache prune` (to automatically sweep stale or dangling index data while protecting active environment lock mappings) and `uv cache dir` (to cleanly query the local platform cache storage directory).

### 7. Native Core Updates (`uv self update`)
* **Deficit:** The server lacks the capability to update its own engine binary lifecycle platform via `uv self update`. It remains completely dependent on external environment adjustments or static parent Docker image tag layers to pull critical execution performance or patch changes.
