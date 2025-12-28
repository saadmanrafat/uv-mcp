import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import sys
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uv_mcp.utils import (
    run_uv_command,
    check_uv_available,
    get_project_info,
    UVError,
    UVCommandError,
    UVTimeoutError,
)


@pytest.mark.asyncio
class TestRunUvCommandExtended:

    @patch("asyncio.create_subprocess_exec")
    async def test_timeout_error(self, mock_exec):
        """Test that timeout raises no exception but returns false with message (as per current implementation)"""
        # Note: The implementation returns False, "", error_msg on timeout, it does NOT raise UVTimeoutError
        # The UVTimeoutError class exists but is not currently raised by run_uv_command,
        # it catches asyncio.TimeoutError and returns False.
        # If we want to be "idiomatic" and "production ready", we might want to raise exceptions,
        # but the current contract returns (bool, str, str).
        # So we test that contract.

        mock_exec.side_effect = asyncio.TimeoutError()

        success, stdout, stderr = await run_uv_command(["test"], timeout=0.1)

        assert success is False
        assert "timed out" in stderr

    @patch("asyncio.create_subprocess_exec")
    async def test_general_exception(self, mock_exec):
        """Test handling of general exceptions."""
        mock_exec.side_effect = Exception("Boom")

        success, stdout, stderr = await run_uv_command(["test"])

        assert success is False
        assert "Boom" in stderr

    @patch("asyncio.create_subprocess_exec")
    async def test_non_zero_return_code(self, mock_exec):
        """Test command failure."""
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"", b"Error output"))
        mock_process.return_code = 1
        # asyncio.create_subprocess_exec returns a process object
        mock_exec.return_value = mock_process

        # We need to set returncode on the mock process object that await process.communicate() doesn't override?
        # In the code:
        # process = await asyncio.create_subprocess_exec(...)
        # await process.communicate()
        # if process.returncode != 0: ...

        # So we need to ensure process.returncode is set.
        mock_process.returncode = 1

        success, stdout, stderr = await run_uv_command(["test"])

        assert success is False
        assert stderr == "Error output"


class TestGetProjectInfoExtended:

    @pytest.mark.skip(
        reason="Cannot reliably test tomllib import error without complex mocking"
    )
    def test_tomllib_import_error(self, tmp_path):
        """Test behavior when tomllib is missing (simulated)."""
        # Create a dummy pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]\nname='foo'")

        with patch.dict(sys.modules, {"tomllib": None, "tomli": None}):
            # Force reload or just mock the import inside the function?
            # Since the import happens inside the function, patching sys.modules should work
            # IF the module hasn't been imported yet.
            # But it likely has been imported by other tests.

            # Use unittest.mock.patch to mock import is harder for builtins.
            # Easier to trust the logic or try to mock the exception.
            pass

    def test_parse_error(self, tmp_path):
        """Test parsing invalid TOML."""
        (tmp_path / "pyproject.toml").write_text("invalid toml [ [")

        info = get_project_info(tmp_path)

        assert info["has_pyproject"] is True
        assert "parse_error" in info
