import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uv_mcp.models import DependencyOperationResult


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


class TestRemoveDependency:
    """Tests for remove_dependency_action."""

    @patch("uv_mcp.actions.run_uv_command")
    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.find_uv_project_root")
    @pytest.mark.asyncio
    async def test_remove_dependency_success(
        self, mock_find_root, mock_check_uv, mock_run_uv, temp_project_with_pyproject
    ):
        """Test successful removal of dependency."""
        mock_check_uv.return_value = (True, "0.5.0")
        mock_find_root.return_value = temp_project_with_pyproject
        mock_run_uv.return_value = (True, "Removed requests", "")

        from uv_mcp.actions import remove_dependency_action

        result = await remove_dependency_action(
            "requests", str(temp_project_with_pyproject)
        )

        assert isinstance(result, DependencyOperationResult)
        assert result.success is True
        assert "requests" in result.message
        mock_run_uv.assert_called_with(
            ["remove", "requests"], cwd=temp_project_with_pyproject
        )

    @patch("uv_mcp.actions.run_uv_command")
    @patch("uv_mcp.actions.check_uv_available")
    @patch("uv_mcp.actions.find_uv_project_root")
    @pytest.mark.asyncio
    async def test_remove_dev_dependency(
        self, mock_find_root, mock_check_uv, mock_run_uv, temp_project_with_pyproject
    ):
        """Test removal of dev dependency."""
        mock_check_uv.return_value = (True, "0.5.0")
        mock_find_root.return_value = temp_project_with_pyproject
        mock_run_uv.return_value = (True, "Removed pytest", "")

        from uv_mcp.actions import remove_dependency_action

        result = await remove_dependency_action(
            "pytest", str(temp_project_with_pyproject), dev=True
        )

        assert isinstance(result, DependencyOperationResult)
        assert result.success is True
        # Check command args
        args = mock_run_uv.call_args[0][0]
        assert "remove" in args
        assert "--dev" in args
        assert "pytest" in args
