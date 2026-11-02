"""Project introspection, health checks and automated repair."""

from __future__ import annotations

import contextlib
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

from .config import Settings
from .models import DiagnosticReport, EnvironmentInfo, Finding, ProjectInfo, RepairResult, RepairStep
from .runner import run_uv

_SEVERITY = {"info": 0, "warning": 1, "error": 2}


# --------------------------------------------------------------------------- #
# Static introspection
# --------------------------------------------------------------------------- #


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def find_project_root(start: Path) -> Path | None:
    """Nearest directory at or above ``start`` that holds a pyproject.toml."""
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return None


def _workspace_members(root: Path, workspace: dict[str, Any]) -> list[Path]:
    members: set[Path] = set()
    for pattern in workspace.get("members", []) or []:
        if isinstance(pattern, str):
            members.update(p.resolve() for p in root.glob(pattern) if (p / "pyproject.toml").is_file())
    for pattern in workspace.get("exclude", []) or []:
        if isinstance(pattern, str):
            members.difference_update(p.resolve() for p in root.glob(pattern))
    return sorted(members)


def find_workspace_root(project: Path) -> Path | None:
    """Return the workspace root that contains ``project`` (which may be ``project`` itself)."""
    for candidate in (project, *project.parents):
        pyproject = candidate / "pyproject.toml"
        if not pyproject.is_file():
            continue
        try:
            workspace = _read_toml(pyproject).get("tool", {}).get("uv", {}).get("workspace")
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if isinstance(workspace, dict) and (
            candidate == project or project in _workspace_members(candidate, workspace)
        ):
            return candidate
    return None


def _stringify(items: Any) -> list[str]:
    out: list[str] = []
    for item in items or []:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and "include-group" in item:
            out.append(f"(include-group: {item['include-group']})")
        else:
            out.append(str(item))
    return out


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def inspect_environment(venv: Path) -> EnvironmentInfo:
    cfg = venv / "pyvenv.cfg"
    info = EnvironmentInfo(path=str(venv), exists=cfg.is_file())
    if not info.exists:
        return info
    try:
        for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
            key, _, value = line.partition("=")
            if key.strip() in ("version_info", "version") and value.strip():
                info.python_version = value.strip()
    except OSError:
        pass
    python = _venv_python(venv)
    info.python_path = str(python) if python.exists() else None
    return info


def project_info(start: Path) -> ProjectInfo:
    """Collect facts about the project at or above ``start`` without running uv."""
    root = find_project_root(start)
    if root is None:
        return ProjectInfo(
            project_dir=str(start),
            has_pyproject=False,
            has_requirements_txt=(start / "requirements.txt").is_file(),
        )
    info = ProjectInfo(project_dir=str(root), has_pyproject=True)
    info.has_requirements_txt = (root / "requirements.txt").is_file()
    try:
        data = _read_toml(root / "pyproject.toml")
    except (OSError, tomllib.TOMLDecodeError) as exc:
        info.parse_error = str(exc)
        return info

    project = data.get("project", {}) if isinstance(data.get("project"), dict) else {}
    tool_uv = data.get("tool", {}).get("uv", {}) if isinstance(data.get("tool"), dict) else {}
    info.name = project.get("name")
    info.version = project.get("version")
    info.dynamic = _stringify(project.get("dynamic"))
    info.requires_python = project.get("requires-python")
    info.dependencies = _stringify(project.get("dependencies"))
    info.optional_dependencies = {k: _stringify(v) for k, v in (project.get("optional-dependencies") or {}).items()}
    groups = {k: _stringify(v) for k, v in (data.get("dependency-groups") or {}).items()}
    legacy_dev = tool_uv.get("dev-dependencies")
    if legacy_dev:
        groups.setdefault("dev", []).extend(_stringify(legacy_dev))
    info.dependency_groups = groups
    info.scripts = {k: str(v) for k, v in (project.get("scripts") or {}).items()}
    build_system = data.get("build-system") or {}
    info.build_backend = build_system.get("build-backend")
    package_flag = tool_uv.get("package")
    info.is_package = bool(package_flag) if package_flag is not None else bool(build_system)

    workspace = tool_uv.get("workspace")
    if isinstance(workspace, dict):
        info.workspace_members = [str(p) for p in _workspace_members(root, workspace)]
    ws_root = find_workspace_root(root) or root
    info.workspace_root = str(ws_root) if ws_root != root else None

    info.has_lockfile = (ws_root / "uv.lock").is_file()
    for candidate in (root, *root.parents):
        pin = candidate / ".python-version"
        if pin.is_file():
            with contextlib.suppress(OSError, IndexError):
                info.python_version_file = pin.read_text(encoding="utf-8").strip().splitlines()[0]
            break
        if candidate == ws_root:
            break

    env_override = os.environ.get("UV_PROJECT_ENVIRONMENT")
    venv = Path(env_override) if env_override else ws_root / ".venv"
    if not venv.is_absolute():
        venv = ws_root / venv
    info.environment = inspect_environment(venv)
    return info


# --------------------------------------------------------------------------- #
# Health check
# --------------------------------------------------------------------------- #


def _network_failure(text: str) -> bool:
    lowered = text.lower()
    return any(s in lowered for s in ("error sending request", "failed to fetch", "dns error", "connection", "offline"))


def _unsupported(text: str) -> bool:
    lowered = text.lower()
    return "unexpected argument" in lowered or "unrecognized subcommand" in lowered


async def diagnose(start: Path, settings: Settings) -> DiagnosticReport:
    findings: list[Finding] = []
    checks: list[str] = []

    def add(severity: str, check: str, message: str, fix: str | None = None) -> None:
        findings.append(Finding(severity=severity, check=check, message=message, fix=fix))  # type: ignore[arg-type]

    uv_path = settings.resolve_uv()
    checks.append("uv")
    uv_version = None
    if uv_path is None:
        add("error", "uv", "uv is not installed or not on PATH.", "Install uv (uv_info lists the official commands).")
        return DiagnosticReport(project_dir=str(start), overall="error", findings=findings, checks_run=checks)
    ver = await run_uv(["--version"], settings=settings)
    uv_version = ver.stdout.strip() or None

    info = project_info(start)
    checks.append("project")
    if not info.has_pyproject:
        fix = "uv_init to create a project"
        if info.has_requirements_txt:
            fix = "uv_init, then uv_add with extra_args=['-r', 'requirements.txt'] to migrate requirements.txt"
        add("error", "project", f"No pyproject.toml found at or above {start}.", fix)
        return _report(start, uv_version, info, findings, checks)
    project_dir = Path(info.project_dir)
    lock_dir = Path(info.workspace_root or info.project_dir)

    checks.append("pyproject")
    if info.parse_error:
        add(
            "error",
            "pyproject",
            f"pyproject.toml is not valid TOML: {info.parse_error}",
            "Fix the syntax error in pyproject.toml.",
        )
        return _report(project_dir, uv_version, info, findings, checks)
    if info.name is None and info.workspace_members == []:
        add(
            "warning", "pyproject", "pyproject.toml has no [project] table, so uv treats it as a non-project workspace."
        )
    if info.name is not None and not info.requires_python:
        add(
            "warning",
            "requires_python",
            "[project] has no requires-python; resolution may pick incompatible versions.",
            "Add requires-python (e.g. '>=3.12') to pyproject.toml.",
        )

    checks.append("interpreter")
    find = await run_uv(["python", "find"], cwd=project_dir, settings=settings)
    if not find.success:
        add(
            "error",
            "interpreter",
            "No Python interpreter satisfies the project's requirements: " + _first_line(find.stderr),
            "uv_python_install (no versions) installs the version the project needs.",
        )

    checks.append("lockfile")
    if not info.has_lockfile:
        add("warning", "lockfile", "uv.lock does not exist, so installs are not reproducible.", "uv_lock")
    else:
        lock = await run_uv(["lock", "--check"], cwd=lock_dir, settings=settings)
        if not lock.success:
            if _network_failure(lock.stderr):
                add("info", "lockfile", "Could not verify uv.lock (network unavailable).")
            else:
                add("warning", "lockfile", "uv.lock is out of date with pyproject.toml.", "uv_lock")

    checks.append("venv")
    env = info.environment
    if env is None or not env.exists:
        add("warning", "venv", "The project environment (.venv) does not exist.", "uv_sync")
    elif env.python_path is None:
        add("error", "venv", f"The environment at {env.path} has no Python executable; it is broken.", "uv_repair")
    else:
        probe = await run_uv(
            ["pip", "list", "--python", env.path, "--format", "json"], cwd=project_dir, settings=settings
        )
        if not probe.success:
            add("error", "venv", f"The environment at {env.path} is unusable: {_first_line(probe.stderr)}", "uv_repair")
        else:
            checks.append("sync")
            sync_args = ["sync", "--check"] + (["--frozen"] if info.has_lockfile else [])
            sync = await run_uv(sync_args, cwd=project_dir, settings=settings)
            if not sync.success and not _unsupported(sync.stderr):
                if _network_failure(sync.stderr):
                    add("info", "sync", "Could not verify that the environment matches uv.lock (network unavailable).")
                else:
                    add(
                        "warning",
                        "sync",
                        "The environment does not match uv.lock (missing or extra packages).",
                        "uv_sync",
                    )
            checks.append("dependencies")
            check = await run_uv(["pip", "check", "--python", env.path], cwd=project_dir, settings=settings)
            if not check.success:
                detail = (check.stdout or check.stderr).strip()
                add(
                    "error",
                    "dependencies",
                    f"Installed packages have broken requirements: {detail[:500]}",
                    "uv_sync with reinstall=true",
                )

    return _report(project_dir, uv_version, info, findings, checks)


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("warning:"):
            return line
    return text.strip()


def _report(
    project_dir: Path, uv_version: str | None, info: ProjectInfo | None, findings: list[Finding], checks: list[str]
) -> DiagnosticReport:
    worst = max((_SEVERITY[f.severity] for f in findings), default=0)
    overall = {0: "healthy", 1: "warning", 2: "error"}[worst]
    return DiagnosticReport(
        project_dir=str(project_dir),
        overall=overall,
        uv_version=uv_version,
        project=info,
        findings=findings,
        checks_run=checks,
    )


# --------------------------------------------------------------------------- #
# Repair
# --------------------------------------------------------------------------- #


async def repair(start: Path, settings: Settings, *, dry_run: bool) -> RepairResult:
    report = await diagnose(start, settings)
    project_dir = Path(report.project_dir)
    by_check = {f.check: f for f in report.findings if f.severity != "info"}
    steps: list[tuple[str, str, list[str], Path]] = []

    if "uv" in by_check or "project" in by_check or "pyproject" in by_check:
        return RepairResult(
            project_dir=str(project_dir), success=False, dry_run=dry_run, remaining_findings=report.findings
        )
    lock_dir = Path(report.project.workspace_root or report.project.project_dir) if report.project else project_dir

    if "interpreter" in by_check:
        steps.append(("install_python", by_check["interpreter"].message, ["python", "install"], project_dir))
    if "venv" in by_check and by_check["venv"].severity == "error" and report.project and report.project.environment:
        steps.append(
            ("recreate_venv", by_check["venv"].message, ["venv", "--clear", report.project.environment.path], lock_dir)
        )
    if "lockfile" in by_check:
        steps.append(("lock", by_check["lockfile"].message, ["lock"], lock_dir))
    if "dependencies" in by_check:
        steps.append(("sync", by_check["dependencies"].message, ["sync", "--reinstall"], project_dir))
    elif {"venv", "sync", "lockfile", "interpreter"} & by_check.keys():
        reason = next(by_check[k].message for k in ("venv", "sync", "lockfile", "interpreter") if k in by_check)
        steps.append(("sync", reason, ["sync"], project_dir))

    from .runner import format_command

    results: list[RepairStep] = []
    success = True
    for name, reason, argv, cwd in steps:
        if dry_run:
            results.append(RepairStep(step=name, reason=reason, status="planned", command=format_command(argv)))
            continue
        if not success:
            results.append(RepairStep(step=name, reason=reason, status="skipped", command=format_command(argv)))
            continue
        res = await run_uv(argv, cwd=cwd, mutating=True, settings=settings)
        success = res.success
        results.append(
            RepairStep(
                step=name,
                reason=reason,
                status="success" if res.success else "failed",
                command=res.command,
                output=(res.stderr or res.stdout).strip()[-2000:] or None,
            )
        )

    remaining = report.findings if dry_run else (await diagnose(project_dir, settings)).findings
    remaining_problems = [f for f in remaining if f.severity != "info"]
    return RepairResult(
        project_dir=str(project_dir),
        success=success and (dry_run or not remaining_problems),
        dry_run=dry_run,
        steps=results,
        remaining_findings=remaining,
    )
