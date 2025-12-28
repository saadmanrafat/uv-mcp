import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import sys
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uv_mcp.diagnostics import check_python_version
from uv_mcp.models import PythonCheck


@pytest.mark.asyncio
class TestCheckPythonVersionContext:

    @patch("uv_mcp.diagnostics.check_project_venv")
    @patch("uv_mcp.diagnostics.get_project_info")
    @patch("uv_mcp.diagnostics.run_uv_command")
    async def test_uses_venv_python_version(
        self, mock_run_uv, mock_project_info, mock_check_venv, tmp_path
    ):
        """Test that it uses the python version from the virtual environment."""

        # Mock virtual env existence
        mock_check_venv.return_value = (True, str(tmp_path / ".venv"))

        # Mock project info
        mock_project_info.return_value = {"python_version": "unknown"}

        # Mock run_uv_command to return specific python version
        # It returns (success, stdout, stderr)
        mock_run_uv.return_value = (True, "Python 3.9.5\n", "")

        result = await check_python_version(tmp_path)

        assert isinstance(result, PythonCheck)
        assert result.current_version == "3.9.5"
        assert result.source == "virtual_env"

        # Verify run_uv_command was called with correct args
        args, kwargs = mock_run_uv.call_args
        assert args[0] == ["run", "python", "--version"]
        assert kwargs["cwd"] == tmp_path

    @patch("uv_mcp.diagnostics.check_project_venv")
    @patch("uv_mcp.diagnostics.get_project_info")
    async def test_fallback_to_system_python(
        self, mock_project_info, mock_check_venv, tmp_path
    ):
        """Test fallback to system python when no venv exists or uv run fails."""

        # Mock no virtual env
        mock_check_venv.return_value = (False, None)

        # Mock project info
        mock_project_info.return_value = {"python_version": "unknown"}

        # We need to mock run_uv_command to fail
        with patch("uv_mcp.diagnostics.run_uv_command") as mock_run_uv:
            mock_run_uv.return_value = (False, "", "some error")

            result = await check_python_version(tmp_path)

            assert isinstance(result, PythonCheck)
            assert result.source == "system_fallback"
            assert len(result.warnings) > 0
            assert "Using system Python" in result.warnings[1]

    @patch("uv_mcp.diagnostics.check_project_venv")
    @patch("uv_mcp.diagnostics.get_project_info")
    @patch("uv_mcp.diagnostics.run_uv_command")
    async def test_version_mismatch(
        self, mock_run_uv, mock_project_info, mock_check_venv, tmp_path
    ):
        """Test detection of version mismatch."""

        mock_check_venv.return_value = (True, str(tmp_path / ".venv"))
        mock_project_info.return_value = {"python_version": "==3.10.0"}

        # Mock venv has 3.9.0
        mock_run_uv.return_value = (True, "Python 3.9.0\n", "")

        result = await check_python_version(tmp_path)

        assert isinstance(result, PythonCheck)
        assert result.compatible is False
        assert "mismatch" in result.issues[0]
        assert "need 3.10.0" in result.issues[0]
        assert "have 3.9.0" in result.issues[0]
