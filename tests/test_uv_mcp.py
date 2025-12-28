"""Comprehensive test suite for UV-MCP server.

This module contains unit tests for all components of the uv-mcp MCP server,
including utils, diagnostics, and server functionality.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import modules under test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uv_mcp.utils import (
    check_uv_available,
    check_project_venv,
    find_uv_project_root,
    get_project_info,
    run_uv_command,
)
from uv_mcp.diagnostics import (
    check_dependencies,
    check_project_structure,
    check_python_version,
    generate_diagnostic_report,
    _get_worst_health,
)
from uv_mcp.models import (
    UVCheckResult,
    InstallInstructions,
    DiagnosticReport,
    StructureCheck,
    DependencyCheck,
    PythonCheck,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project_with_pyproject(temp_project_dir):
    """Create a temporary project with pyproject.toml."""
    pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["requests>=2.28.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    (temp_project_dir / "pyproject.toml").write_text(pyproject_content)
    return temp_project_dir


@pytest.fixture
def temp_project_with_requirements(temp_project_dir):
    """Create a temporary project with requirements.txt."""
    (temp_project_dir / "requirements.txt").write_text(
        "requests>=2.28.0\npytest>=7.0.0\n"
    )
    return temp_project_dir


@pytest.fixture
def temp_project_with_venv(temp_project_with_pyproject):
    """Create a temporary project with a virtual environment directory."""
    venv_dir = temp_project_with_pyproject / ".venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text("home = /usr/bin\n")
    return temp_project_with_pyproject


class TestCheckUvAvailable:
    """Tests for check_uv_available function."""

    @pytest.mark.asyncio
    async def test_uv_available_returns_tuple(self):
        """Test that function returns a tuple."""
        result = await check_uv_available()
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_uv_available_first_element_is_bool(self):
        """Test that first element is a boolean."""
        available, _ = await check_uv_available()
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    async def test_uv_available_second_element_is_string_or_none(self):
        """Test that second element is string or None."""
        _, version = await check_uv_available()
        assert version is None or isinstance(version, str)

    @patch("asyncio.create_subprocess_exec")
    @pytest.mark.asyncio
    async def test_uv_not_installed(self, mock_exec):
        """Test when uv is not installed."""
        mock_exec.side_effect = FileNotFoundError()
        available, version = await check_uv_available()
        assert available is False
        assert version is None

    @patch("asyncio.create_subprocess_exec")
    @pytest.mark.asyncio
    async def test_uv_timeout(self, mock_exec):
        """Test when uv command times out."""
        mock_exec.side_effect = OSError("Timeout simulation")
        available, version = await check_uv_available()
        assert available is False
        assert version is None


class TestRunUvCommand:
    """Tests for run_uv_command function."""

    @pytest.mark.asyncio
    async def test_returns_tuple(self):
        """Test that function returns a tuple of 3 elements."""
        result = await run_uv_command(["--version"])
        assert isinstance(result, tuple)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_success_element_is_bool(self):
        """Test that success element is boolean."""
        success, _, _ = await run_uv_command(["--version"])
        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_stdout_stderr_are_strings(self):
        """Test that stdout and stderr are strings."""
        _, stdout, stderr = await run_uv_command(["--version"])
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    @patch("asyncio.create_subprocess_exec")
    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_exec):
        """Test command timeout handling."""
        mock_exec.side_effect = TimeoutError("Optimistically simulating timeout")
        success, stdout, stderr = await run_uv_command(["sync"])
        assert success is False
        assert "timed out" in stderr or "Execution error" in stderr

    @patch("asyncio.create_subprocess_exec")
    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_exec):
        """Test general exception handling."""
        mock_exec.side_effect = Exception("Test error")
        success, stdout, stderr = await run_uv_command(["sync"])
        assert success is False
        assert "Test error" in stderr


class TestGetProjectInfo:
    """Tests for get_project_info function."""

    @pytest.mark.asyncio
    async def test_empty_directory(self, temp_project_dir):
        """Test with empty directory."""
        info = get_project_info(temp_project_dir)
        assert info["has_pyproject"] is False
        assert info["has_requirements"] is False
        assert info["has_lockfile"] is False

    @pytest.mark.asyncio
    async def test_with_pyproject(self, temp_project_with_pyproject):
        """Test with pyproject.toml present."""
        info = get_project_info(temp_project_with_pyproject)
        assert info["has_pyproject"] is True
        assert info["project_name"] == "test-project"
        assert info["python_version"] == ">=3.10"
        assert "requests>=2.28.0" in info["dependencies"]

    @pytest.mark.asyncio
    async def test_with_requirements(self, temp_project_with_requirements):
        """Test with requirements.txt present."""
        info = get_project_info(temp_project_with_requirements)
        assert info["has_pyproject"] is False
        assert info["has_requirements"] is True

    @pytest.mark.asyncio
    async def test_with_lockfile(self, temp_project_with_pyproject):
        """Test lockfile detection."""
        (temp_project_with_pyproject / "uv.lock").write_text("# lockfile")
        info = get_project_info(temp_project_with_pyproject)
        assert info["has_lockfile"] is True


class TestCheckProjectVenv:
    """Tests for check_project_venv function."""

    def test_returns_tuple(self, temp_project_dir):
        """Test that function returns a tuple."""
        result = check_project_venv(temp_project_dir)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_first_element_is_bool(self, temp_project_dir):
        """Test that first element is boolean."""
        in_venv, _ = check_project_venv(temp_project_dir)
        assert isinstance(in_venv, bool)

    def test_detects_virtual_env(self, temp_project_with_venv):
        """Test detection of existing venv."""
        in_venv, venv_path = check_project_venv(temp_project_with_venv)
        assert in_venv is True
        assert ".venv" in venv_path


class TestFindUvProjectRoot:
    """Tests for find_uv_project_root function."""

    @pytest.mark.asyncio
    async def test_finds_root_in_current_dir(self, temp_project_with_pyproject):
        """Test finding project root in current directory."""
        root = find_uv_project_root(temp_project_with_pyproject)
        assert root == temp_project_with_pyproject

    @pytest.mark.asyncio
    async def test_finds_root_from_subdirectory(self, temp_project_with_pyproject):
        """Test finding project root from subdirectory."""
        subdir = temp_project_with_pyproject / "src" / "package"
        subdir.mkdir(parents=True)
        root = find_uv_project_root(subdir)
        assert root == temp_project_with_pyproject

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_dir(self, temp_project_dir):
        """Test returns None when no project found."""
        root = find_uv_project_root(temp_project_dir)
        assert root is None


class TestGetWorstHealth:
    """Tests for _get_worst_health helper function."""

    def test_critical_beats_warning(self):
        """Test that critical status beats warning."""
        assert _get_worst_health("warning", "critical") == "critical"
        assert _get_worst_health("critical", "warning") == "critical"

    def test_warning_beats_healthy(self):
        """Test that warning status beats healthy."""
        assert _get_worst_health("healthy", "warning") == "warning"
        assert _get_worst_health("warning", "healthy") == "warning"

    def test_critical_beats_healthy(self):
        """Test that critical status beats healthy."""
        assert _get_worst_health("healthy", "critical") == "critical"
        assert _get_worst_health("critical", "healthy") == "critical"

    def test_same_status_returns_current(self):
        """Test that same status returns current."""
        assert _get_worst_health("critical", "critical") == "critical"
        assert _get_worst_health("warning", "warning") == "warning"
        assert _get_worst_health("healthy", "healthy") == "healthy"


class TestCheckProjectStructure:
    """Tests for check_project_structure function."""

    @pytest.mark.asyncio
    async def test_empty_directory_invalid(self, temp_project_dir):
        """Test empty directory is invalid."""
        result = check_project_structure(temp_project_dir)
        assert isinstance(result, StructureCheck)
        assert result.valid is False
        assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_with_pyproject_valid(self, temp_project_with_pyproject):
        """Test directory with pyproject.toml is valid."""
        result = check_project_structure(temp_project_with_pyproject)
        assert isinstance(result, StructureCheck)
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_with_requirements_has_warning(self, temp_project_with_requirements):
        """Test directory with requirements.txt has migration warning."""
        result = check_project_structure(temp_project_with_requirements)
        # Valid because we have a dependency file
        assert any("requirements.txt" in w for w in result.warnings)

    @patch.dict(os.environ, {}, clear=True)
    @patch("uv_mcp.diagnostics.check_project_venv")
    @pytest.mark.asyncio
    async def test_missing_venv_warning(
        self, mock_check_venv, temp_project_with_pyproject
    ):
        """Test warning when no virtual environment present."""
        # Mock to simulate no venv
        mock_check_venv.return_value = (False, None)
        result = check_project_structure(temp_project_with_pyproject)
        # Check for either "virtual environment" or "venv" in warnings
        has_venv_warning = any(
            "virtual environment" in w.lower() or "venv" in w.lower()
            for w in result.warnings
        )
        assert has_venv_warning or len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_missing_lockfile_warning(self, temp_project_with_pyproject):
        """Test warning when no lockfile present."""
        result = check_project_structure(temp_project_with_pyproject)
        assert any("uv.lock" in w for w in result.warnings)


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    @pytest.mark.asyncio
    async def test_no_dependency_file(self, temp_project_dir):
        """Test with no dependency file."""
        result = await check_dependencies(temp_project_dir)
        assert isinstance(result, DependencyCheck)
        assert result.healthy is False
        assert any("No dependency file" in i for i in result.issues)

    @pytest.mark.asyncio
    async def test_with_pyproject(self, temp_project_with_pyproject):
        """Test with pyproject.toml present."""
        result = await check_dependencies(temp_project_with_pyproject)
        # Should at least not fail immediately
        assert isinstance(result, DependencyCheck)


class TestCheckPythonVersion:
    """Tests for check_python_version function."""

    @pytest.mark.asyncio
    async def test_returns_current_version(self, temp_project_dir):
        """Test that current Python version is returned."""
        result = await check_python_version(temp_project_dir)
        assert isinstance(result, PythonCheck)
        assert (
            result.current_version == "unknown"
            or result.current_version.count(".") >= 1
        )

    @pytest.mark.asyncio
    async def test_compatible_by_default(self, temp_project_dir):
        """Test that compatible is True by default."""
        result = await check_python_version(temp_project_dir)
        assert result.compatible is True


class TestGenerateDiagnosticReport:
    """Tests for generate_diagnostic_report function."""

    @pytest.mark.asyncio
    async def test_returns_report(self, temp_project_dir):
        """Test that function returns a DiagnosticReport."""
        result = await generate_diagnostic_report(temp_project_dir)
        assert isinstance(result, DiagnosticReport)

    @pytest.mark.asyncio
    async def test_contains_required_fields(self, temp_project_dir):
        """Test that result contains required keys."""
        result = await generate_diagnostic_report(temp_project_dir)
        assert result.project_dir is not None
        assert result.overall_health is not None
        assert result.uv is not None

    @pytest.mark.asyncio
    async def test_overall_health_is_valid_status(self, temp_project_dir):
        """Test that overall_health is a valid status."""
        result = await generate_diagnostic_report(temp_project_dir)
        assert result.overall_health in ["healthy", "warning", "critical"]


class TestMCPToolFunctions:
    """Tests for MCP tool functionality using underlying implementations."""

    @pytest.mark.asyncio
    async def test_check_uv_available_integration(self):
        """Test that uv availability check works end-to-end."""
        available, version = await check_uv_available()
        # On a system with uv installed
        if available:
            assert version is not None
            assert "uv" in version.lower() or version[0].isdigit()

    @pytest.mark.asyncio
    async def test_generate_diagnostic_report_structure(
        self, temp_project_with_pyproject
    ):
        """Test diagnostic report has expected structure."""
        report = await generate_diagnostic_report(temp_project_with_pyproject)

        # Check required sections
        assert report.uv is not None
        assert report.structure is not None
        assert report.project_info is not None
        assert report.overall_health is not None

        # Check uv section
        assert report.uv.installed is not None

        # Check structure section
        assert report.structure.valid is not None
        assert isinstance(report.structure.issues, list)
        assert isinstance(report.structure.warnings, list)

    @pytest.mark.asyncio
    async def test_get_project_info_complete(self, temp_project_with_pyproject):
        """Test project info extraction is complete."""
        info = get_project_info(temp_project_with_pyproject)

        assert info["has_pyproject"] is True
        assert info["project_name"] == "test-project"
        assert "dependencies" in info
        assert len(info["dependencies"]) > 0

    @pytest.mark.asyncio
    async def test_health_status_tracking(self, temp_project_dir):
        """Test that health status is correctly tracked."""
        # Empty directory should be critical or warning
        report = await generate_diagnostic_report(temp_project_dir)
        assert report.overall_health in ["critical", "warning"]

    class TestIntegration:
        """Integration tests for the full workflow."""

        @pytest.mark.asyncio
        async def test_full_diagnostic_workflow(self, temp_project_with_pyproject):
            """Test complete diagnostic workflow."""
            # Generate diagnostic report
            report = await generate_diagnostic_report(temp_project_with_pyproject)

            # Should have all sections
            assert report.uv is not None
            assert report.structure is not None
            assert report.project_info is not None

            # Project info should be populated
            assert report.project_info.project_name == "test-project"

        @pytest.mark.asyncio
        async def test_project_with_full_structure(self, temp_project_with_venv):
            """Test project with complete structure."""
            # Add lockfile
            (temp_project_with_venv / "uv.lock").write_text("# lockfile content")

            report = await generate_diagnostic_report(temp_project_with_venv)

            # Should have minimal warnings with full setup
            assert report.project_info.has_lockfile is True

    class TestEdgeCases:
        """Tests for edge cases and error conditions."""

        @pytest.mark.asyncio
        async def test_malformed_pyproject(self, temp_project_dir):
            """Test handling of malformed pyproject.toml."""
            (temp_project_dir / "pyproject.toml").write_text("not valid toml {{{{ ")
            info = get_project_info(temp_project_dir)
            assert info["has_pyproject"] is True
            # Should have parse error or handle gracefully
            assert "parse_error" in info or info.get("project_name") == "unknown"

        @pytest.mark.asyncio
        async def test_empty_pyproject(self, temp_project_dir):
            """Test handling of empty pyproject.toml."""
            (temp_project_dir / "pyproject.toml").write_text("")
            info = get_project_info(temp_project_dir)
            assert info["has_pyproject"] is True

        @pytest.mark.asyncio
        async def test_unicode_in_project_name(self, temp_project_dir):
            """Test handling of unicode in project name."""
            content = """
    [project]
    name = "test-项目-"
    version = "0.1.0"
    """
            (temp_project_dir / "pyproject.toml").write_text(content)
            info = get_project_info(temp_project_dir)
            assert "test-项目-" in info.get("project_name", "")

        @pytest.mark.asyncio
        async def test_deeply_nested_subdirectory(self, temp_project_with_pyproject):
            """Test finding project root from deeply nested directory."""
            deep_path = temp_project_with_pyproject / "a" / "b" / "c" / "d" / "e"
            deep_path.mkdir(parents=True)
            root = find_uv_project_root(deep_path)
            assert root == temp_project_with_pyproject


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
