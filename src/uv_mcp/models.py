from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UVCheckResult(BaseModel):
    installed: bool
    version: str | None = None
    message: str
    installation_instructions: dict[str, str] | None = None


class InstallMethod(BaseModel):
    command: str
    description: str


class InstallInstructions(BaseModel):
    message: str
    methods: dict[str, InstallMethod | dict[str, InstallMethod]]
    verification: InstallMethod
    documentation: str


class RepairAction(BaseModel):
    action: str
    description: str | None = None
    status: str | None = None
    output: str | None = None
    error: str | None = None
    reason: str | None = None


class RepairResult(BaseModel):
    project_dir: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    actions: list[RepairAction] = []
    success: bool
    project_root: str | None = None
    error: str | None = None


class DependencyOperationResult(BaseModel):
    package: str
    project_dir: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    success: bool
    dev: bool = False
    optional: str | None = None
    message: str | None = None
    output: str | None = None
    error: str | None = None


class StructureCheck(BaseModel):
    valid: bool
    issues: list[str] = []
    warnings: list[str] = []


class DependencyCheck(BaseModel):
    healthy: bool
    issues: list[str] = []
    warnings: list[str] = []
    installed_packages: int | None = None


class PythonCheck(BaseModel):
    compatible: bool
    current_version: str = "unknown"
    source: str = "unknown"
    issues: list[str] = []
    warnings: list[str] = []
    required_version: str | None = None


class UVInfo(BaseModel):
    installed: bool
    version: str | None = None


class VirtualEnvInfo(BaseModel):
    active: bool
    path: str | None = None


class ProjectInfo(BaseModel):
    has_pyproject: bool
    has_requirements: bool
    has_lockfile: bool
    project_dir: str
    project_name: str | None = None
    python_version: str | None = None
    dependencies: list[str] = []
    parse_error: str | None = None


class DiagnosticReportSummary(BaseModel):
    overall_health: str
    issues_count: int
    warnings_count: int


class DiagnosticReport(BaseModel):
    project_dir: str
    timestamp: str | None = None
    overall_health: str
    uv: UVInfo | None = None
    structure: StructureCheck | None = None
    dependencies: DependencyCheck | None = None
    python: PythonCheck | None = None
    virtual_env: VirtualEnvInfo | None = None
    project_info: ProjectInfo | None = None
    critical_issues: list[str] = []
    summary: DiagnosticReportSummary | None = None
