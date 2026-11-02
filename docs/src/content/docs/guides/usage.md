---
title: Usage
description: Everyday workflows with uv-mcp, the prompts that trigger them and the tool calls the agent makes.
---

You talk to your agent normally; it picks the tools. This page shows typical requests and the calls they
lead to, which is also a good mental model when reviewing what the agent did.

## Start a project

> *"Create a new FastAPI app called api with Python 3.13 and add pytest as a dev dependency."*

```json
uv_init       { "path": "api", "python": "3.13" }
uv_add        { "project_path": "api", "packages": ["fastapi[standard]"] }
uv_add        { "project_path": "api", "packages": ["pytest"], "dev": true }
```

Use `kind: "lib"` for an installable library and `kind: "script"` for a single-file PEP 723 script.

## Work on an existing project

> *"Set this repo up so I can run the tests."*

```json
uv_project_info {}
uv_sync         { "all_groups": true }
uv_run          { "command": ["pytest", "-q"] }
```

`uv_sync` creates `.venv`, installs the right Python if needed, and makes the environment match `uv.lock`.
`uv_run` syncs first too, so after the first sync the agent can simply run things.

## Manage dependencies

> *"Upgrade httpx, then show me why urllib3 is installed."*

```json
uv_sync  { "upgrade_packages": ["httpx"] }
uv_tree  { "packages": ["urllib3"], "invert": true }
```

| Request | Call |
|---|---|
| Add to a group | `uv_add { "packages": ["ruff"], "group": "lint" }` |
| Add an optional extra | `uv_add { "packages": ["redis"], "optional": "cache" }` |
| From a private index | `uv_add { "packages": ["internal-lib"], "resolver": { "index": ["corp=https://pkgs.corp/simple"] } }` |
| From git | `uv_add { "packages": ["git+https://github.com/org/repo"], "tag": "v1.2" }` |
| Platform-specific | `uv_add { "packages": ["pywin32"], "marker": "sys_platform == 'win32'" }` |
| Remove | `uv_remove { "packages": ["requests"] }` |
| Upgrade everything | `uv_lock { "upgrade": true }` then `uv_sync` |
| What is outdated? | `uv_tree { "outdated": true, "depth": 1 }` |
| Check for vulnerabilities | `uv_audit {}` (and `uv_tool_audit { "all": true }` for installed tools) |
| Export for Docker | `uv_export { "output_file": "requirements.txt", "no_dev": true }` |

The agent should never edit `uv.lock` by hand, and should prefer `uv_add`/`uv_remove` to editing
`pyproject.toml`, so the lockfile and environment stay consistent.

## Run code

> *"Run main.py with DEBUG=1."*

```json
uv_run { "command": ["python", "main.py"], "env": { "DEBUG": "1" } }
```

- A one-off extra package: `"with_packages": ["rich"]`.
- A script with inline metadata: `"command": ["script.py"]`.
- Without touching `.venv`: `"isolated": true`.
- A long job: `"timeout_seconds": 1800`.

A non-zero exit status is reported as `success: false` with the real `exit_code`, so failing tests are
easy to distinguish from a uv error (`hint` is set for the latter).

## Workspaces (monorepos)

> *"Which packages are in this workspace, and where is the api package?"*

```json
uv_workspace_list { "paths": true }
uv_workspace_dir  { "member": "api" }
uv_sync           { "all_packages": true }
```

Most project tools take `member` to act on one workspace package (uv's `--package`).

## Python versions

> *"Which Pythons do I have? Switch this project to 3.12."*

```json
uv_python_list    { "only_installed": true }
uv_python_install { "versions": ["3.12"] }
uv_python_pin     { "version": "3.12" }
uv_sync           {}
```

## One-off tools

> *"Lint the project with ruff without adding it as a dependency."*

```json
uv_tool_run { "command": ["ruff", "check", "."] }
```

This is `uvx`. Use `from_package` when the command and package names differ, for example
`{ "command": ["http", "GET", "example.com"], "from_package": "httpie" }`. To keep a tool installed
permanently, use `uv_tool_install`.

## Fix a broken environment

> *"I'm getting ModuleNotFoundError, fix it."*

```json
uv_diagnose {}
uv_repair   {}
```

`uv_diagnose` returns findings such as *uv.lock is out of date*, *.venv is missing*, *the environment's
interpreter is gone* or *installed packages have broken requirements*, each with a suggested fix.
`uv_repair` installs the required Python, recreates a broken `.venv`, re-locks and syncs (reinstalling when
packages are inconsistent), then diagnoses again. It never edits `pyproject.toml`. Pass `dry_run: true` to
see the plan first. If the missing module is not declared at all, the agent should add it with `uv_add`.

## Plain virtual environments and requirements files

For projects that are not managed by uv:

```json
uv_venv          { "python": "3.12" }
uv_pip_install   { "requirements": ["requirements.txt"] }
uv_pip_compile   { "src_files": ["requirements.in"], "output_file": "requirements.txt", "universal": true }
uv_pip_sync      { "src_files": ["requirements.txt"] }
uv_pip_list      { "outdated": true }
```

## Build and publish

> *"Build the package and publish it to TestPyPI."*

```json
uv_build   {}
uv_publish { "publish_url": "https://test.pypi.org/legacy/" }
uv_publish { "publish_url": "https://test.pypi.org/legacy/", "dry_run": false }
```

`uv_publish` is a dry run by default; the agent has to pass `dry_run: false` deliberately. Prefer trusted
publishing from CI, or put `UV_PUBLISH_TOKEN` in the server's `env` block, over pasting tokens into chat.

## Resolver options

Tools that resolve packages (`uv_add`, `uv_sync`, `uv_lock`, `uv_run`, `uv_export`, `uv_pip_install`,
`uv_pip_compile`, `uv_tool_run`, `uv_tool_install`) take a `resolver` object:

> *"Make sure this library still works with the oldest versions it claims to support."*

```json
uv_lock { "resolver": { "resolution": "lowest-direct" } }
uv_sync {}
uv_run  { "command": ["pytest", "-q"] }
```

| Field | Use |
|---|---|
| `resolution` | `highest` (default), `lowest`, `lowest-direct` |
| `prerelease` | `allow`, `if-necessary`, `explicit`, ... |
| `exclude_newer` | Reproduce the world as of a date: `"2025-01-31"` |
| `index`, `default_index` | Private or extra indexes (`name=url` or a URL) |
| `python_platform` | Resolve for another OS (pip, sync, run, tool) |
| `no_build`, `no_sources`, `offline` | Wheels only; ignore `[tool.uv.sources]`; cache only |

## Every other option

Every tool accepts `extra_args` for options without a dedicated parameter. They are checked against the
installed uv, so a typo fails fast with a suggestion instead of a confusing uv error:

```json
uv_sync { "extra_args": ["--link-mode", "copy"] }
```

To find an option, ask `uv_help`. It returns every option of a command, its allowed values and environment
variable, and whether to pass it as a parameter, in `resolver`, or in `extra_args`:

```json
uv_help { "command": "pip compile", "search": "hash" }
```

And `uv_command` runs any uv subcommand, including ones added in uv releases newer than your uv-mcp:

```json
uv_command { "args": ["self", "version", "--output-format", "json"] }
```
