"""Structured results returned by uv-mcp tools.

Every tool that shells out to uv returns a :class:`CommandResult` (or a subclass
that adds parsed fields). The shape is deliberately uniform so an agent can rely
on ``success``, ``exit_code``, ``stdout``, ``stderr`` and ``hint`` everywhere.
When uv's output has been fully parsed into typed fields, ``stdout`` is left
empty to save context.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CommandResult(BaseModel):
    """Outcome of a single uv invocation."""

    success: bool = Field(description="True when uv exited with status 0.")
    command: str = Field(description="The uv command that ran (secrets redacted).")
    cwd: str = Field(description="Directory the command ran in.")
    exit_code: int | None = Field(
        default=None, description="Process exit status; null if uv could not be started or timed out."
    )
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    timed_out: bool = False
    truncated: bool = Field(default=False, description="True when stdout/stderr were shortened.")
    hint: str | None = Field(default=None, description="Suggested next step when something failed.")


# --------------------------------------------------------------------------- #
# Project
# --------------------------------------------------------------------------- #


class InitResult(CommandResult):
    path: str = Field(description="The project directory (or script file) that was created.")


class VersionResult(CommandResult):
    package_name: str | None = None
    version: str | None = None
    previous_version: str | None = None


class BuildResult(CommandResult):
    out_dir: str | None = None
    artifacts: list[str] = Field(default_factory=list, description="Absolute paths of built files.")


class ExportResult(CommandResult):
    output_file: str | None = None


class AuditResult(CommandResult):
    report: Any | None = Field(default=None, description="Parsed JSON report, when available.")


# --------------------------------------------------------------------------- #
# Python
# --------------------------------------------------------------------------- #


class PythonInstallation(BaseModel):
    key: str
    version: str
    implementation: str | None = None
    path: str | None = Field(default=None, description="Interpreter path; null if only downloadable.")
    managed: bool | None = Field(default=None, description="True if installed and managed by uv.")
    url: str | None = None
    variant: str | None = None


class PythonListResult(CommandResult):
    installations: list[PythonInstallation] = Field(default_factory=list)


class PythonFindResult(CommandResult):
    path: str | None = None


class PythonPinResult(CommandResult):
    pinned: str | None = Field(default=None, description="The pinned version request, if any.")


# --------------------------------------------------------------------------- #
# pip
# --------------------------------------------------------------------------- #


class InstalledPackage(BaseModel):
    name: str
    version: str
    latest_version: str | None = None
    latest_filetype: str | None = None
    editable_project_location: str | None = None


class PipListResult(CommandResult):
    packages: list[InstalledPackage] = Field(default_factory=list)


class PackageDetails(BaseModel):
    name: str
    version: str | None = None
    location: str | None = None
    editable_project_location: str | None = None
    requires: list[str] = Field(default_factory=list)
    required_by: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    fields: dict[str, str] = Field(default_factory=dict, description="Every raw field uv reported.")


class PipShowResult(CommandResult):
    packages: list[PackageDetails] = Field(default_factory=list)


class PipCompileResult(CommandResult):
    output_file: str | None = None


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #


class InstalledTool(BaseModel):
    name: str
    version: str | None = None
    executables: list[str] = Field(default_factory=list)
    path: str | None = None
    latest_version: str | None = None


class ToolListResult(CommandResult):
    tools: list[InstalledTool] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Environment / meta
# --------------------------------------------------------------------------- #


class VenvResult(CommandResult):
    path: str


class CacheSizeResult(CommandResult):
    size_bytes: int | None = None
    human: str | None = None


class SelfUpdateResult(CommandResult):
    previous_version: str | None = None
    new_version: str | None = None


class UVDirectories(BaseModel):
    cache: str | None = None
    python_installs: str | None = None
    python_bin: str | None = None
    tools: str | None = None
    tool_bin: str | None = None
    credentials: str | None = None


class ServerInfo(BaseModel):
    """Everything an agent needs to orient itself before calling other tools."""

    server_version: str
    uv_installed: bool
    uv_version: str | None = None
    uv_path: str | None = None
    platform: str
    workspace_root: str
    workspace_is_project: bool = Field(description="True if workspace_root (or a parent) has a pyproject.toml.")
    read_only: bool
    toolsets: list[str]
    allowed_roots: list[str] = Field(default_factory=list)
    directories: UVDirectories | None = None
    install_instructions: dict[str, str] | None = Field(default=None, description="Present only when uv is missing.")
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Diagnostics
# --------------------------------------------------------------------------- #

Severity = Literal["info", "warning", "error"]


class Finding(BaseModel):
    severity: Severity
    check: str
    message: str
    fix: str | None = Field(default=None, description="Suggested remedy, usually a uv-mcp tool call.")


class EnvironmentInfo(BaseModel):
    path: str
    exists: bool
    python_version: str | None = None
    python_path: str | None = None


class ProjectInfo(BaseModel):
    """Static facts read from pyproject.toml and the project tree (no network)."""

    project_dir: str
    has_pyproject: bool
    name: str | None = None
    version: str | None = None
    dynamic: list[str] = Field(default_factory=list)
    requires_python: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    optional_dependencies: dict[str, list[str]] = Field(default_factory=dict)
    dependency_groups: dict[str, list[str]] = Field(default_factory=dict)
    scripts: dict[str, str] = Field(default_factory=dict)
    build_backend: str | None = None
    is_package: bool | None = Field(
        default=None, description="True if the project is built and installed as a package."
    )
    workspace_members: list[str] = Field(default_factory=list, description="Resolved member directories.")
    workspace_root: str | None = Field(default=None, description="Enclosing workspace root, if any.")
    has_lockfile: bool = False
    python_version_file: str | None = Field(default=None, description="Contents of .python-version.")
    has_requirements_txt: bool = False
    environment: EnvironmentInfo | None = None
    parse_error: str | None = None


class DiagnosticReport(BaseModel):
    project_dir: str
    overall: Literal["healthy", "warning", "error"]
    uv_version: str | None = None
    project: ProjectInfo | None = None
    findings: list[Finding] = Field(default_factory=list)
    checks_run: list[str] = Field(default_factory=list)


class RepairStep(BaseModel):
    step: str
    reason: str
    status: Literal["planned", "success", "failed", "skipped"]
    command: str | None = None
    output: str | None = None


class RepairResult(BaseModel):
    project_dir: str
    success: bool
    dry_run: bool
    steps: list[RepairStep] = Field(default_factory=list)
    remaining_findings: list[Finding] = Field(default_factory=list)
