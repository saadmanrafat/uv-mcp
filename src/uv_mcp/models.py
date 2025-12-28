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


class PythonVersion(BaseModel):
    version: str
    path: str | None = None
    origin: str | None = None


class PythonListResult(BaseModel):
    versions: list[PythonVersion]
    output: str


class PythonInstallResult(BaseModel):
    version: str
    success: bool
    output: str | None = None
    error: str | None = None


class PythonPinResult(BaseModel):
    version: str
    project_dir: str
    success: bool
    output: str | None = None
    error: str | None = None


class DependencyItem(BaseModel):
    name: str
    version: str
    editable: bool = False
    location: str | None = None
    installer: str | None = None


class DependencyListResult(BaseModel):
    project_dir: str
    dependencies: list[DependencyItem] = []
    tree_output: str | None = None
    is_tree: bool
    count: int
    success: bool
    error: str | None = None


class PackageInfoResult(BaseModel):
    name: str
    version: str | None = None
    location: str | None = None
    requires: list[str] = []
    required_by: list[str] = []
    metadata: dict[str, str] = {}  # License, Author, etc.
    success: bool
    error: str | None = None


class OutdatedPackage(BaseModel):
    name: str
    version: str
    latest_version: str
    type: str | None = None  # e.g., "wheel", "sdist"


class OutdatedCheckResult(BaseModel):
    project_dir: str
    outdated_packages: list[OutdatedPackage]
    count: int
    success: bool
    error: str | None = None


class TreeAnalysisResult(BaseModel):
    project_dir: str
    tree_output: str
    depth: int | None = None
    success: bool
    error: str | None = None


class ProjectInitResult(BaseModel):
    """Result of project initialization."""

    project_name: str
    project_dir: str
    python_version: str
    template: str  # "app" or "lib"
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    message: str | None = None
    error: str | None = None
    created_files: list[str] = []  # ["pyproject.toml", ".python-version", ...]


class SyncResult(BaseModel):
    """Result of environment sync operation."""

    project_dir: str
    success: bool
    upgraded: bool = False  # Was --upgrade used?
    locked: bool = False  # Was --locked used?
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    packages_installed: int | None = None
    packages_updated: int | None = None
    message: str | None = None
    output: str | None = None
    error: str | None = None


class ExportResult(BaseModel):
    """Result of requirements export operation."""

    project_dir: str
    file_format: str  # "requirements-txt", etc.
    output_file: str | None = None  # If file was written
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    content: str | None = None  # If exported to stdout
    line_count: int | None = None
    message: str | None = None
    error: str | None = None


class BuildResult(BaseModel):
    """Result of package build operation."""

    project_dir: str
    output_dir: str
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    artifacts: list[str] = (
        []
    )  # ["dist/myapp-0.1.0.tar.gz", "dist/myapp-0.1.0-py3-none-any.whl"]
    message: str | None = None
    error: str | None = None


class CacheOperationResult(BaseModel):
    """Result of cache operations."""

    operation: str = "clean"  # "clean", "prune", "info"
    package: str | None = None  # Specific package if applicable
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    cache_size_before: str | None = None  # "1.2 GB"
    cache_size_after: str | None = None  # "500 MB"
    space_freed: str | None = None  # "700 MB"
    message: str | None = None
    output: str | None = None
    error: str | None = None
