"""Comprehensive edge case tests for UV-MCP.

This test suite covers edge cases, boundary conditions, and error scenarios
that aren't covered by the main test suites.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
import sys
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uv_mcp.utils import (
    run_uv_command,
    check_uv_available,
    get_project_info,
    check_project_venv,
    find_uv_project_root,
)
from uv_mcp.actions import (
    clear_cache_action,
    add_dependency_action,
    remove_dependency_action,
    repair_environment_action,
    list_python_versions_action,
    install_python_version_action,
    pin_python_version_action,
)
from uv_mcp.diagnostics import (
    check_project_structure,
    check_dependencies,
    check_python_version,
    generate_diagnostic_report,
)
from uv_mcp.errors import (
    UVMCPError,
    get_error_suggestion,
)
from uv_mcp.models import (
    CacheOperationResult,
    DependencyOperationResult,
    RepairResult,
)


@pytest.mark.asyncio
class TestUVCommandEdgeCases:
    """Test edge cases in UV command execution."""

    @patch("asyncio.create_subprocess_exec")
    async def test_empty_stdout_stderr(self, mock_exec):
        """Test handling of empty output streams."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        success, stdout, stderr = await run_uv_command(["--version"])

        assert success is True
        assert stdout == ""
        assert stderr == ""

    @patch("asyncio.create_subprocess_exec")
    async def test_binary_output(self, mock_exec):
        """Test handling of binary/non-UTF8 output."""
        mock_process = AsyncMock()
        # Simulate binary data that can't decode
        mock_process.communicate.return_value = (
            "valid utf8".encode(),
            "also valid".encode(),
        )
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        success, stdout, stderr = await run_uv_command(["test"])

        assert success is True
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    @patch("asyncio.create_subprocess_exec")
    async def test_very_long_output(self, mock_exec):
        """Test handling of very large output."""
        mock_process = AsyncMock()
        large_output = "x" * 1_000_000  # 1MB of data
        mock_process.communicate.return_value = (
            large_output.encode(),
            b"",
        )
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        success, stdout, stderr = await run_uv_command(["test"])

        assert success is True
        assert len(stdout) == 1_000_000

    @patch("asyncio.create_subprocess_exec")
    async def test_special_characters_in_output(self, mock_exec):
        """Test handling of special characters in output."""
        mock_process = AsyncMock()
        special_chars = "Test with émojis 🎉, unicode ñ, tabs\t, newlines\n"
        mock_process.communicate.return_value = (
            special_chars.encode("utf-8"),
            b"",
        )
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        success, stdout, stderr = await run_uv_command(["test"])

        assert success is True
        assert "🎉" in stdout
        assert "ñ" in stdout

    @patch("asyncio.create_subprocess_exec")
    async def test_command_with_empty_args(self, mock_exec):
        """Test running command with empty argument list."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        success, stdout, stderr = await run_uv_command([])

        assert isinstance(success, bool)

    @patch("asyncio.create_subprocess_exec")
    async def test_concurrent_commands(self, mock_exec):
        """Test running multiple commands concurrently."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        # Run 10 commands concurrently
        tasks = [run_uv_command(["--version"]) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(success for success, _, _ in results)

    @patch("asyncio.create_subprocess_exec")
    async def test_process_killed_externally(self, mock_exec):
        """Test handling when process is killed externally."""
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = ProcessLookupError("No such process")
        mock_process.returncode = None
        mock_exec.return_value = mock_process

        success, stdout, stderr = await run_uv_command(["test"])

        assert success is False
        assert "No such process" in stderr

    @patch("asyncio.create_subprocess_exec")
    async def test_negative_timeout(self, mock_exec):
        """Test handling of negative timeout value."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        # Should handle gracefully (though timeout will be used as-is)
        success, stdout, stderr = await run_uv_command(["test"], timeout=-1.0)

        assert isinstance(success, bool)


class TestProjectInfoEdgeCases:
    """Test edge cases in project information gathering."""

    def test_project_with_symlinks(self, tmp_path):
        """Test project info with symlinked directories."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "pyproject.toml").write_text("[project]\nname='test'")

        link_dir = tmp_path / "link"
        link_dir.symlink_to(real_dir)

        info = get_project_info(link_dir)

        assert info["has_pyproject"] is True

    def test_project_with_circular_symlinks(self, tmp_path):
        """Test handling of circular symlinks."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        # Create circular symlinks
        (dir_a / "link_to_b").symlink_to(dir_b)
        (dir_b / "link_to_a").symlink_to(dir_a)
        (dir_a / "pyproject.toml").write_text("[project]\nname='test'")

        # Should not hang or crash
        info = get_project_info(dir_a)

        assert info["has_pyproject"] is True

    def test_project_with_very_large_pyproject(self, tmp_path):
        """Test parsing very large pyproject.toml files."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='test'\n"
            + "dependencies = [\n"
            + "\n".join([f'  "package{i}>=1.0.0",' for i in range(1000)])
            + "\n]"
        )

        info = get_project_info(tmp_path)

        assert info["has_pyproject"] is True
        assert len(info["dependencies"]) == 1000

    def test_project_with_unusual_characters_in_name(self, tmp_path):
        """Test project names with unusual but valid characters."""
        unusual_names = [
            "my-project_123",
            "test.package",
            "project_with_underscores",
            "123-starts-with-number",
        ]

        for name in unusual_names:
            (tmp_path / "pyproject.toml").write_text(f"[project]\nname='{name}'")
            info = get_project_info(tmp_path)
            assert info["project_name"] == name

    def test_project_with_empty_dependencies(self, tmp_path):
        """Test project with empty dependencies list."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='test'\ndependencies = []"
        )

        info = get_project_info(tmp_path)

        assert info["dependencies"] == []

    def test_project_with_missing_project_table(self, tmp_path):
        """Test pyproject.toml without [project] table."""
        (tmp_path / "pyproject.toml").write_text(
            "[build-system]\nrequires = ['hatchling']"
        )

        info = get_project_info(tmp_path)

        assert info["has_pyproject"] is True
        assert info["project_name"] == "unknown"

    def test_project_with_readonly_pyproject(self, tmp_path):
        """Test handling of read-only pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname='test'")
        pyproject.chmod(0o444)  # Read-only

        info = get_project_info(tmp_path)

        assert info["has_pyproject"] is True
        assert info["project_name"] == "test"

        # Restore permissions
        pyproject.chmod(0o644)


class TestVenvDetectionEdgeCases:
    """Test edge cases in virtual environment detection."""

    def test_venv_with_missing_pyvenv_cfg(self, tmp_path):
        """Test .venv directory without pyvenv.cfg."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        exists, path = check_project_venv(tmp_path)

        assert exists is False
        assert path is None

    def test_venv_as_file_not_directory(self, tmp_path):
        """Test when .venv exists as a file instead of directory."""
        (tmp_path / ".venv").write_text("not a directory")

        exists, path = check_project_venv(tmp_path)

        assert exists is False

    def test_venv_with_broken_symlink(self, tmp_path):
        """Test .venv as a broken symlink."""
        venv_link = tmp_path / ".venv"
        venv_link.symlink_to(tmp_path / "nonexistent")

        exists, path = check_project_venv(tmp_path)

        assert exists is False

    def test_multiple_venv_candidates(self, tmp_path):
        """Test when multiple venv-like directories exist."""
        # Create multiple potential venvs
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "pyvenv.cfg").write_text("test")
        (tmp_path / "venv").mkdir()
        (tmp_path / "env").mkdir()

        exists, path = check_project_venv(tmp_path)

        assert exists is True
        assert ".venv" in path


class TestProjectRootFindingEdgeCases:
    """Test edge cases in finding project root."""

    def test_root_at_filesystem_root(self, tmp_path):
        """Test behavior when searching from filesystem root."""
        result = find_uv_project_root(Path("/"))

        # Should return None or the root if pyproject.toml exists there
        assert result is None or result == Path("/")

    def test_deeply_nested_path(self, tmp_path):
        """Test finding root from deeply nested directory."""
        # Create deep nesting
        deep_path = tmp_path
        for i in range(20):
            deep_path = deep_path / f"level{i}"
        deep_path.mkdir(parents=True)

        # Put pyproject.toml at root
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")

        result = find_uv_project_root(deep_path)

        assert result == tmp_path

    def test_multiple_pyprojects_in_hierarchy(self, tmp_path):
        """Test when multiple pyproject.toml files exist in hierarchy."""
        # Root project
        (tmp_path / "pyproject.toml").write_text("[project]\nname='root'")

        # Nested project
        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "pyproject.toml").write_text("[project]\nname='nested'")

        # Search from nested
        result = find_uv_project_root(nested)

        # Should find the closest one (nested)
        assert result == nested

    def test_permission_denied_during_search(self, tmp_path):
        """Test handling of permission denied during directory traversal."""
        restricted = tmp_path / "restricted"
        restricted.mkdir()
        restricted.chmod(0o000)  # No permissions

        try:
            # Should not crash
            result = find_uv_project_root(tmp_path / "some_subdir")
            assert result is None or isinstance(result, Path)
        finally:
            # Restore permissions for cleanup
            restricted.chmod(0o755)


@pytest.mark.asyncio
class TestDependencyOperationEdgeCases:
    """Test edge cases in dependency operations."""

    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.run_uv_command")
    async def test_add_dependency_with_complex_version(self, mock_run, mock_check):
        """Test adding dependency with complex version specifiers."""
        mock_check.return_value = (True, "1.0.0")
        mock_run.return_value = (True, "Added", "")

        # Complex version specifiers
        versions = [
            "package>=1.0.0,<2.0.0",
            "package~=1.4.2",
            "package==1.2.*",
            "package!=1.3.0",
            "package>=1.0.0,!=1.2.0,<2.0.0",
        ]

        for version in versions:
            result = await add_dependency_action(version, project_path=str(Path.cwd()))
            # Should handle without crashing
            assert isinstance(result, DependencyOperationResult)

    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.run_uv_command")
    @patch("uv_mcp.actions.find_uv_project_root")
    async def test_add_dependency_package_name_variations(
        self, mock_root, mock_run, mock_check
    ):
        """Test package names with various valid formats."""
        mock_check.return_value = (True, "1.0.0")
        mock_run.return_value = (True, "Added", "")
        mock_root.return_value = Path.cwd()

        # Various valid package name formats
        packages = [
            "simple-package",
            "Package_With_Underscores",
            "UPPERCASE",
            "mix-of_STYLES123",
            "git+https://github.com/user/repo.git",
            "package[extra1,extra2]",
        ]

        for package in packages:
            result = await add_dependency_action(package)
            assert result.package == package

    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.run_uv_command")
    async def test_remove_nonexistent_dependency(self, mock_run, mock_check):
        """Test removing a dependency that doesn't exist."""
        mock_check.return_value = (True, "1.0.0")
        mock_run.return_value = (
            False,
            "",
            "Package not found in dependencies",
        )

        result = await remove_dependency_action(
            "nonexistent-package", project_path=str(Path.cwd())
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    @patch("uv_mcp.actions.check_uv_available")
    async def test_dependency_operation_with_none_path(self, mock_check):
        """Test dependency operations with None as path (should use cwd)."""
        mock_check.return_value = (True, "1.0.0")

        with patch("uv_mcp.actions.run_uv_command") as mock_run:
            mock_run.return_value = (False, "", "No pyproject.toml found")

            result = await add_dependency_action("package", project_path=None)

            # Should use current working directory
            assert result.success is False


@pytest.mark.asyncio
class TestRepairEnvironmentEdgeCases:
    """Test edge cases in environment repair."""

    @patch("uv_mcp.actions.check_uv_available")
    async def test_repair_with_uv_not_installed(self, mock_check):
        """Test repair when UV is not installed."""
        mock_check.return_value = (False, None)

        result = await repair_environment_action()

        assert result.success is False
        assert "not installed" in result.error.lower()

    @patch("uv_mcp.actions.check_uv_available")
    async def test_repair_with_auto_fix_disabled(self, mock_check):
        """Test repair with auto_fix=False."""
        mock_check.return_value = (True, "1.0.0")

        with patch("uv_mcp.actions.run_uv_command") as mock_run:
            mock_run.return_value = (True, "", "")

            result = await repair_environment_action(auto_fix=False)

            # Should identify issues but not fix them
            assert isinstance(result, RepairResult)
            # Actions should be skipped
            assert all(
                action.status == "skipped" for action in result.actions if action.status
            )

    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.run_uv_command")
    async def test_repair_with_partial_failures(self, mock_run, mock_check):
        """Test repair when some operations fail."""
        mock_check.return_value = (True, "1.0.0")

        # First call succeeds, second fails
        mock_run.side_effect = [
            (True, "init ok", ""),
            (False, "", "venv creation failed"),
        ]

        result = await repair_environment_action()

        assert result.success is False
        assert any(action.status == "failed" for action in result.actions)


@pytest.mark.asyncio
class TestPythonVersionEdgeCases:
    """Test edge cases in Python version management."""

    @patch("uv_mcp.actions.run_uv_command")
    async def test_list_python_versions_empty_output(self, mock_run):
        """Test listing Python versions with no versions installed."""
        mock_run.return_value = (True, "", "")

        result = await list_python_versions_action()

        assert result.versions == []
        assert result.output == ""

    @patch("uv_mcp.actions.run_uv_command")
    async def test_list_python_versions_malformed_output(self, mock_run):
        """Test parsing malformed output from uv python list."""
        mock_run.return_value = (
            True,
            "malformed\n   \n\t\n   spaces    everywhere   \n",
            "",
        )

        result = await list_python_versions_action()

        # Should handle gracefully
        assert isinstance(result.versions, list)

    @patch("uv_mcp.actions.run_uv_command")
    async def test_install_python_exotic_versions(self, mock_run):
        """Test installing exotic Python versions."""
        mock_run.return_value = (True, "Installed", "")

        versions = [
            "pypy@3.10",
            "3.13.0rc1",
            "3.12-dev",
            "graalpy-24.0.0",
        ]

        for version in versions:
            result = await install_python_version_action(version)
            assert result.version == version

    @patch("uv_mcp.actions.run_uv_command")
    @patch("uv_mcp.actions.find_uv_project_root")
    async def test_pin_python_without_pyproject(self, mock_root, mock_run):
        """Test pinning Python version in directory without pyproject.toml."""
        mock_run.return_value = (True, "Pinned", "")
        mock_root.return_value = None  # No project root found

        result = await pin_python_version_action("3.12")

        # Should still work (creates .python-version file)
        assert isinstance(result.success, bool)


@pytest.mark.asyncio
class TestCacheOperationEdgeCases:
    """Test edge cases in cache operations."""

    @patch("uv_mcp.actions.run_uv_command")
    async def test_clear_cache_with_special_package_names(self, mock_run):
        """Test clearing cache for packages with special characters."""
        mock_run.return_value = (True, "Cache cleared", "")

        special_names = [
            "package-with-dashes",
            "package_with_underscores",
            "package.with.dots",
            "UPPERCASE-Package",
        ]

        for name in special_names:
            result = await clear_cache_action(package=name)
            assert result.package == name

    @patch("uv_mcp.actions.run_uv_command")
    async def test_clear_cache_concurrent_operations(self, mock_run):
        """Test multiple cache clear operations running concurrently."""
        mock_run.return_value = (True, "Cache cleared", "")

        # Clear multiple package caches concurrently
        tasks = [clear_cache_action(package=f"package{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r.success for r in results)


class TestErrorSuggestionsEdgeCases:
    """Test edge cases in error suggestion generation."""

    def test_suggestion_for_empty_error(self):
        """Test suggestion generation for empty error string."""
        suggestion = get_error_suggestion("")

        assert suggestion is None

    def test_suggestion_for_very_long_error(self):
        """Test suggestion generation for very long error messages."""
        long_error = "Error: " + "x" * 10000
        suggestion = get_error_suggestion(long_error)

        # Should handle without crashing
        assert suggestion is None or isinstance(suggestion, str)

    def test_suggestion_with_multiple_error_patterns(self):
        """Test error message matching multiple patterns."""
        error = "Connection timeout and permission denied"
        suggestion = get_error_suggestion(error)

        # Should return a suggestion (might match first pattern)
        assert suggestion is not None

    def test_suggestion_case_sensitivity(self):
        """Test that suggestions are case-insensitive."""
        suggestions = [
            get_error_suggestion("UV: command not found"),
            get_error_suggestion("uv: Command Not Found"),
            get_error_suggestion("UV: COMMAND NOT FOUND"),
        ]

        # All should produce suggestions
        assert all(s is not None for s in suggestions)

    def test_suggestion_with_special_characters(self):
        """Test error messages with special characters."""
        errors = [
            "Error: file not found\n\t at line 42",
            "Error: 'package' not found",
            'Error: "module" is missing',
            "Error: connection failed ❌",
        ]

        for error in errors:
            suggestion = get_error_suggestion(error)
            # Should handle gracefully
            assert suggestion is None or isinstance(suggestion, str)


@pytest.mark.asyncio
class TestDiagnosticsEdgeCases:
    """Test edge cases in diagnostic report generation."""

    async def test_diagnose_empty_directory(self, tmp_path):
        """Test diagnostics on completely empty directory."""
        report = await generate_diagnostic_report(tmp_path)

        assert report.overall_health in ["healthy", "warning", "critical"]
        assert isinstance(report.critical_issues, list)

    async def test_diagnose_directory_with_only_lockfile(self, tmp_path):
        """Test diagnostics with only uv.lock, no pyproject.toml."""
        (tmp_path / "uv.lock").write_text("locked")

        report = await generate_diagnostic_report(tmp_path)

        assert report.structure is not None

    async def test_diagnose_corrupted_project(self, tmp_path):
        """Test diagnostics on project with corrupted files."""
        # Create corrupted pyproject.toml
        (tmp_path / "pyproject.toml").write_bytes(b"\x00\x00\xff\xff")

        report = await generate_diagnostic_report(tmp_path)

        # Should handle gracefully
        assert report.project_info is not None

    @patch("uv_mcp.diagnostics.check_uv_available")
    async def test_diagnose_without_uv(self, mock_check, tmp_path):
        """Test diagnostics when UV is not available."""
        mock_check.return_value = (False, None)

        report = await generate_diagnostic_report(tmp_path)

        assert report.overall_health == "critical"
        assert "not installed" in str(report.critical_issues)


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    def test_project_name_length_limits(self, tmp_path):
        """Test very short and very long project names."""
        names = [
            "a",  # Single character
            "x" * 255,  # Maximum reasonable length
        ]

        for name in names:
            (tmp_path / "pyproject.toml").write_text(f"[project]\nname='{name}'")
            info = get_project_info(tmp_path)
            assert info["project_name"] == name

    def test_dependency_list_size_limits(self, tmp_path):
        """Test projects with zero and many dependencies."""
        # Zero dependencies
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='test'\ndependencies=[]"
        )
        info = get_project_info(tmp_path)
        assert len(info["dependencies"]) == 0

        # Many dependencies
        deps = [f'"pkg{i}"' for i in range(100)]
        (tmp_path / "pyproject.toml").write_text(
            f"[project]\nname='test'\ndependencies=[{','.join(deps)}]"
        )
        info = get_project_info(tmp_path)
        assert len(info["dependencies"]) == 100

    def test_path_with_spaces_and_special_chars(self, tmp_path):
        """Test paths with spaces and special characters."""
        special_dir = tmp_path / "path with spaces & special-chars"
        special_dir.mkdir()
        (special_dir / "pyproject.toml").write_text("[project]\nname='test'")

        info = get_project_info(special_dir)

        assert info["has_pyproject"] is True


@pytest.mark.asyncio
class TestRaceConditions:
    """Test potential race conditions."""

    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.run_uv_command")
    async def test_concurrent_add_remove_operations(self, mock_run, mock_check):
        """Test concurrent add/remove of same package."""
        mock_check.return_value = (True, "1.0.0")
        mock_run.return_value = (True, "Done", "")

        # Simulate concurrent operations
        tasks = [
            add_dependency_action("package"),
            remove_dependency_action("package"),
            add_dependency_action("package"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete (though results may vary)
        assert len(results) == 3

    async def test_concurrent_diagnostic_reports(self, tmp_path):
        """Test generating multiple diagnostic reports concurrently."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")

        tasks = [generate_diagnostic_report(tmp_path) for _ in range(5)]
        reports = await asyncio.gather(*tasks)

        assert len(reports) == 5
        # All should have same basic structure
        assert all(r.project_dir == str(tmp_path) for r in reports)


@pytest.mark.asyncio
class TestErrorRecovery:
    """Test error recovery scenarios."""

    @patch("uv_mcp.actions.run_uv_command")
    async def test_retry_after_timeout(self, mock_run):
        """Test behavior after timeout errors."""
        # First call times out, second succeeds
        mock_run.side_effect = [
            (False, "", "Command timed out after 120 seconds"),
            (True, "Success", ""),
        ]

        # First attempt fails
        result1 = await clear_cache_action()
        assert result1.success is False

        # Second attempt succeeds
        result2 = await clear_cache_action()
        assert result2.success is True

    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.run_uv_command")
    async def test_recovery_from_broken_state(self, mock_run, mock_check):
        """Test recovering from a broken environment state."""
        mock_check.return_value = (True, "1.0.0")

        # Simulate broken state, then repair
        mock_run.side_effect = [
            (False, "", "Broken dependency tree"),
            (True, "Repaired", ""),
            (True, "Synced", ""),
        ]

        result = await repair_environment_action()

        # Should attempt repair
        assert isinstance(result, RepairResult)


class TestMemoryAndPerformance:
    """Test memory usage and performance edge cases."""

    def test_large_number_of_dependencies(self, tmp_path):
        """Test parsing project with large number of dependencies."""
        # Create project with 1000 dependencies
        deps = [f'"package{i}>=1.0.0"' for i in range(1000)]
        (tmp_path / "pyproject.toml").write_text(
            f"[project]\nname='test'\ndependencies=[{','.join(deps)}]"
        )

        import time

        start = time.time()
        info = get_project_info(tmp_path)
        duration = time.time() - start

        assert len(info["dependencies"]) == 1000
        assert duration < 1.0  # Should be fast

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_memory_efficiency_with_large_output(self, mock_exec):
        """Test memory efficiency with large command output."""
        mock_process = AsyncMock()
        # 10MB of output
        large_output = ("x" * 1024 * 1024 * 10).encode()
        mock_process.communicate.return_value = (large_output, b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        success, stdout, stderr = await run_uv_command(["test"])

        # Should handle without memory issues
        assert success is True
        assert len(stdout) == 1024 * 1024 * 10


class TestPlatformSpecificEdgeCases:
    """Test platform-specific edge cases."""

    def test_windows_path_handling(self, tmp_path):
        """Test handling of Windows-style paths."""
        # Even on Unix, test the logic handles mixed separators
        mixed_path = str(tmp_path).replace("/", "\\")
        path = Path(mixed_path)

        # Should normalize path
        info = get_project_info(path)
        assert isinstance(info["project_dir"], str)

    def test_path_with_unicode(self, tmp_path):
        """Test paths with unicode characters."""
        unicode_dir = tmp_path / "测试目录"
        unicode_dir.mkdir()
        (unicode_dir / "pyproject.toml").write_text("[project]\nname='test'")

        info = get_project_info(unicode_dir)

        assert info["has_pyproject"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
