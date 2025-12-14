---
title: Tool Reference
description: API reference for UV-MCP tools
---

# Tool Reference

These are the tools exposed by the UV-MCP server.

## `check_uv_installation`

Checks if `uv` is installed on the system and returns version information.

**Returns:**
```json
{
  "installed": boolean,
  "version": string | null,
  "message": string
}
```

## `install_uv`

Returns platform-specific installation instructions for `uv`.

## `diagnose_environment`

Performs a comprehensive health check of the Python environment.

**Parameters:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `project_path` | `string` (optional) | Path to the project directory. Defaults to CWD. |

**Returns:** A JSON object containing health status, issues, warnings, and project structure details.

## `repair_environment`

Attempts to automatically fix common environment issues.

**Parameters:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `project_path` | `string` (optional) | Path to the project directory. |
| `auto_fix` | `boolean` | Whether to automatically apply fixes. Defaults to `true`. |

**Actions:**
*   Creates virtual environment (`uv venv`)
*   Initializes project (`uv init`)
*   Syncs dependencies (`uv sync`)
*   Installs Python interpreter (`uv python install`)

## `add_dependency`

Adds a new dependency to the project.

**Parameters:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `package` | `string` | Package name (e.g., "requests", "fastapi>=0.100"). |
| `project_path` | `string` (optional) | Path to the project directory. |
| `dev` | `boolean` | Add as a development dependency. |
| `optional` | `string` (optional) | Add to an optional dependency group. |

## `remove_dependency`

Removes a dependency from the project.

**Parameters:**

| Name | Type | Description |
| :--- | :--- | :--- |
| `package` | `string` | Package name to remove. |
| `project_path` | `string` (optional) | Path to the project directory. |
| `dev` | `boolean` | Remove from development dependencies. |
| `optional` | `string` (optional) | Remove from an optional dependency group. |
