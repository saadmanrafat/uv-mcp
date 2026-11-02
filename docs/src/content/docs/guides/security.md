---
title: Security
description: What uv-mcp protects against, what it deliberately allows, and how to lock it down further.
---

uv-mcp lets an AI agent drive uv on your machine. That is inherently powerful: installing a package runs
its build scripts, and `uv run` executes code. uv-mcp does not pretend otherwise. Its job is to make sure
the agent can only do what each tool says, that nothing leaks, and that you can restrict it further.

## Guarantees

**No shell, ever.** uv is executed directly with an argument list. Shell metacharacters in any argument
are just characters.

**No argument injection.** Values the agent supplies as package names, versions, paths, group names and
so on are rejected if they start with `-`, so `"--index-url=https://evil.example"` cannot be smuggled in
where a package name was expected. NUL bytes and newlines are rejected everywhere. Commands passed to
`uv run` and `uvx` are placed after a `--` separator.

**Predictable target environment.** When a client launches the server through `uvx` or `uv run`, the
server's own `VIRTUAL_ENV` is set. uv-mcp removes it (and related variables) before calling uv, so
`uv pip` commands act on your project's `.venv`, never on the server's private environment.

**Never interactive.** stdin is closed, so uv can never hang waiting for a password or confirmation.

**Bounded.** Every command has a timeout. On expiry the whole process group is killed, including
children such as test runners started by `uv run`. Output is capped per stream.

**Secrets stay out of the conversation.**

- `uv_publish` sends tokens and passwords to uv through environment variables, and `uv_auth_login`
  sends them over stdin, never on the command line where other processes could read them.
- Credentials are redacted from every command line and every line of output: passwords in URLs
  (`https://user:pass@host`), PyPI tokens (`pypi-...`), GitHub tokens, and any secret passed to a tool.
- There is no tool that reads a stored credential back. `uv auth token` is refused by `uv_command`.

**Honest annotations.** Every tool declares MCP hints: `readOnlyHint`, `destructiveHint`,
`idempotentHint`, `openWorldHint`. Clients use them to decide when to ask you before a call. For example,
`uv_run`, `uv_tool_run`, `uv_publish`, `uv_cache_clean` and the uninstall tools are marked destructive.

**Safe defaults for irreversible actions.** `uv_publish` is a dry run unless the agent explicitly passes
`dry_run: false`, and the server instructions tell agents to do that only when you asked to publish.

**Serialised writes.** Mutating commands on the same project take a lock, so two parallel tool calls
cannot race on `uv.lock` or `.venv`.

## What is deliberately allowed

- `uv_run` and `uv_tool_run` execute arbitrary programs, because that is their purpose. Treat approving
  them like approving a shell command.
- Installing packages runs third-party code (build backends, sdists). This is true of uv and pip
  themselves.
- `extra_args` passes additional options to uv. Each one is checked against the installed uv's options for
  that command (unknown flags, missing values and invalid choices are refused), and it cannot escape the
  argument list or the path confinement described below. Options can still change behaviour, for example
  adding an index.
- `uv_command` runs any uv subcommand except the blocked ones (`auth token`, `python update-shell`,
  `tool update-shell`). Remove it entirely with `--no-raw-command`.

## Locking it down

| Goal | Setting |
|---|---|
| The agent may inspect but never change anything | `--read-only` |
| Keep the agent inside your code directory | `UV_MCP_ALLOWED_ROOTS=/home/me/code` |
| No machine-wide changes (Python installs, global tools, cache, uv updates) | `UV_MCP_TOOLSETS=project,pip,venv,diagnostics` |
| No escape hatch | `--no-raw-command` |
| Ask before anything that writes | Configure your client to require approval for tools without `readOnlyHint` |

## Reporting a vulnerability

Please report security issues privately through
[GitHub security advisories](https://github.com/saadmanrafat/uv-mcp/security/advisories/new) rather than
public issues.
