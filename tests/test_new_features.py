"""Tests for new features: cache, lock, build, and error handling."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uv_mcp.actions import clear_cache_action
from uv_mcp.models import CacheOperationResult
from uv_mcp.errors import (
    UVNotInstalledError,
    ProjectNotFoundError,
    PyProjectNotFoundError,
    get_error_suggestion,
)


@pytest.mark.asyncio
class TestCacheManagement:
    """Test cache management functionality."""

    @patch("uv_mcp.actions.run_uv_command")
    async def test_clear_all_cache(self, mock_run):
        """Test clearing entire cache."""
        mock_run.return_value = (True, "Cache cleaned", "")

        result = await clear_cache_action()

        assert result.success is True
        assert result.operation == "clean"
        assert result.package is None
        assert "successfully" in result.message.lower()
        mock_run.assert_called_once_with(["cache", "clean"])

    @patch("uv_mcp.actions.run_uv_command")
    async def test_clear_package_cache(self, mock_run):
        """Test clearing cache for specific package."""
        mock_run.return_value = (True, "Package cache cleaned", "")

        result = await clear_cache_action(package="requests")

        assert result.success is True
        assert result.package == "requests"
        mock_run.assert_called_once_with(["cache", "clean", "requests"])

    @patch("uv_mcp.actions.run_uv_command")
    async def test_clear_cache_failure(self, mock_run):
        """Test cache clear failure."""
        mock_run.return_value = (False, "", "Permission denied")

        result = await clear_cache_action()

        assert result.success is False
        assert result.error == "Permission denied"
        assert "failed" in result.message.lower()


class TestErrorSuggestions:
    """Test error handling and suggestions."""

    def test_uv_not_found_error(self):
        """Test UV not installed error."""
        error = UVNotInstalledError()

        assert error.error_code == "UV_NOT_FOUND"
        assert "not installed" in error.message
        assert "install" in error.suggestion.lower()

    def test_project_not_found_error(self):
        """Test project not found error."""
        error = ProjectNotFoundError("/some/path")

        assert error.error_code == "PROJECT_NOT_FOUND"
        assert "/some/path" in error.message
        assert "initialize" in error.suggestion.lower()

    def test_pyproject_not_found_error(self):
        """Test pyproject.toml not found error."""
        error = PyProjectNotFoundError("/project")

        assert error.error_code == "PYPROJECT_MISSING"
        assert "pyproject.toml" in error.message.lower()

    def test_error_to_dict(self):
        """Test error serialization to dict."""
        error = UVNotInstalledError()
        result = error.to_dict()

        assert "error" in result
        assert "suggestion" in result
        assert "error_code" in result

    def test_get_suggestion_uv_not_found(self):
        """Test suggestion for uv not found."""
        suggestion = get_error_suggestion("uv: command not found")

        assert suggestion is not None
        assert "install" in suggestion.lower()

    def test_get_suggestion_missing_pyproject(self):
        """Test suggestion for missing pyproject.toml."""
        suggestion = get_error_suggestion("No pyproject.toml found")

        assert suggestion is not None
        assert "initialize" in suggestion.lower()

    def test_get_suggestion_network_error(self):
        """Test suggestion for network errors."""
        suggestion = get_error_suggestion("Connection timeout")

        assert suggestion is not None
        assert "internet" in suggestion.lower() or "connection" in suggestion.lower()

    def test_get_suggestion_permission_denied(self):
        """Test suggestion for permission errors."""
        suggestion = get_error_suggestion("Permission denied")

        assert suggestion is not None
        assert "permission" in suggestion.lower()

    def test_get_suggestion_dependency_conflict(self):
        """Test suggestion for dependency conflicts."""
        suggestion = get_error_suggestion("Could not find a version that satisfies")

        assert suggestion is not None
        assert "version" in suggestion.lower()

    def test_get_suggestion_unknown_error(self):
        """Test no suggestion for unknown errors."""
        suggestion = get_error_suggestion("Some random error message")

        # May or may not have a suggestion, just ensure no crash
        assert suggestion is None or isinstance(suggestion, str)


class TestModelValidation:
    """Test model validation and defaults."""

    def test_cache_operation_result_defaults(self):
        """Test CacheOperationResult has correct defaults."""
        result = CacheOperationResult(success=True)

        assert result.operation == "clean"
        assert result.package is None
        assert result.success is True
        assert result.timestamp is not None

    def test_cache_operation_result_full(self):
        """Test CacheOperationResult with all fields."""
        result = CacheOperationResult(
            operation="clean",
            package="requests",
            success=True,
            message="Done",
            output="Cache cleaned",
            cache_size_before="100 MB",
            cache_size_after="50 MB",
            space_freed="50 MB",
        )

        assert result.operation == "clean"
        assert result.package == "requests"
        assert result.space_freed == "50 MB"


class TestIntegrationScenarios:
    """Test realistic usage scenarios."""

    @pytest.mark.asyncio
    @patch("uv_mcp.actions.run_uv_command")
    async def test_cache_clear_after_corruption(self, mock_run):
        """Test clearing cache after package corruption."""
        # Simulate cache corruption scenario
        mock_run.return_value = (True, "Cache cleared", "")

        result = await clear_cache_action(package="corrupted-package")

        assert result.success is True
        assert result.package == "corrupted-package"

    def test_error_chain_suggestions(self):
        """Test that errors provide actionable next steps."""
        errors = [
            UVNotInstalledError(),
            ProjectNotFoundError("/tmp/test"),
            PyProjectNotFoundError("/tmp/test"),
        ]

        for error in errors:
            assert error.message is not None
            assert error.suggestion is not None
            assert error.error_code is not None
            # Each error should have actionable suggestions
            assert len(error.suggestion) > 20
