# uv-mcp

[![PyPI](https://img.shields.io/pypi/v/uv-mcp-server?style=for-the-badge)](https://pypi.org/project/uv-mcp-server/)
![Python](https://img.shields.io/badge/Python-3.11%2B-FFE873?style=for-the-badge&logo=python&logoColor=white)
[![geminicli.com: featured extension](https://img.shields.io/badge/geminicli.com-featured%20extension-5F55AF?style=for-the-badge&logoColor=white)](https://geminicli.com/extensions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](LICENSE)

The MCP server for [uv](https://docs.astral.sh/uv/). It gives Claude Code, Codex, Gemini CLI and any other
MCP client the full uv toolchain: projects and lockfiles, dependencies, Python versions, virtual
environments, `uvx` tools, packaging, the pip interface and environment diagnostics, as safe, typed tools.

![](ext/uv_mcp_logo.png)

## Install

You only need [uv](https://docs.astral.sh/uv/getting-started/installation/). The server runs with `uvx`.

```bash
# Claude Code
claude mcp add --scope user --transport stdio uv -- uvx uv-mcp-server@latest

# Codex CLI (then set tool_timeout_sec = 600, see the docs)
codex mcp add uv -- uvx uv-mcp-server@latest

# Gemini CLI
gemini extensions install https://github.com/saadmanrafat/uv-mcp
```

Any other client: a stdio server with command `uvx` and args `["uv-mcp-server@latest"]`.
Per-client instructions, including Claude Desktop, Cursor, VS Code and OpenCode:
**[Installation guide](https://saadman.dev/uv-mcp/guides/installation/)**.

> The PyPI package is `uv-mcp-server`. `uv-mcp` on PyPI is an unrelated project.

## What agents get

- **46 tools named after the CLI**: `uv_init`, `uv_add`, `uv_remove`, `uv_sync`, `uv_lock`, `uv_run`,
  `uv_tree`, `uv_export`, `uv_version`, `uv_python_install`, `uv_python_pin`, `uv_venv`, `uv_tool_run` (uvx),
  `uv_pip_compile`, `uv_build`, `uv_publish`, `uv_audit`, ... plus `extra_args` on every tool and
  `uv_command` for anything else.
- **Structured results**: `success`, `exit_code`, `stdout`, `stderr` and an actionable `hint` on failure;
  package, Python and tool lists come back parsed.
- **Diagnose and repair**: `uv_diagnose` checks interpreter, lockfile, `.venv` and package consistency;
  `uv_repair` fixes what it finds.
- **Secure by design**: no shell, argument-injection guards, secrets passed via env/stdin and redacted from
  output, honest MCP annotations, read-only mode, path confinement, dry-run-by-default publishing.
- **Runs in the right place**: always your project's environment, never the server's own.

Ask your agent things like *"set this repo up and run the tests"*, *"add httpx and show me why urllib3 is
installed"*, *"switch this project to Python 3.13"* or *"my imports are broken, fix the environment"*.

## Configure

All optional, via env vars or flags (`uvx uv-mcp-server --help`):

| Setting | Purpose |
|---|---|
| `UV_MCP_WORKSPACE_ROOT` / `--workspace` | Default project directory (else `CLAUDE_PROJECT_DIR`, else cwd) |
| `UV_MCP_READ_ONLY` / `--read-only` | Only expose tools that change nothing |
| `UV_MCP_TOOLSETS` / `--toolsets` | e.g. `project,python,diagnostics` to save context |
| `UV_MCP_ALLOWED_ROOTS` / `--allowed-roots` | Refuse paths outside these directories |
| `UV_MCP_TIMEOUT` / `--timeout` | Per-command timeout in seconds (default 600) |

See [Configuration](https://saadman.dev/uv-mcp/guides/configuration/) and
[Security](https://saadman.dev/uv-mcp/guides/security/).

## Links

- Documentation: https://saadman.dev/uv-mcp/
- Tool reference: https://saadman.dev/uv-mcp/reference/tools/
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Demo video: https://www.youtube.com/watch?v=Tv2dUt73mM8
- Issues: https://github.com/saadmanrafat/uv-mcp/issues

Built by [Saadman Rafat](https://github.com/saadmanrafat) ([@saadmanrafat_](https://x.com/saadmanrafat_)).
