
import pytest
from uv_mcp.actions import (
    add_dependency_action,
    repair_environment_action,
    list_dependencies_action,
)
from uv_mcp.utils import validate_project_path, ProjectNotFoundError

@pytest.mark.asyncio
async def test_validate_project_path_missing():
    """Test that validate_project_path raises ProjectNotFoundError for missing paths."""
    with pytest.raises(ProjectNotFoundError):
        validate_project_path("/non/existent/path/12345")

@pytest.mark.asyncio
async def test_add_dependency_missing_project(tmp_path):
    """Test add_dependency with a missing project directory."""
    # Pass a non-existent path
    result = await add_dependency_action(
        "requests",
        project_path=str(tmp_path / "missing"),
    )
    assert not result.success
    assert "directory does not exist" in result.error

@pytest.mark.asyncio
async def test_add_dependency_no_pyproject(tmp_path):
    """Test add_dependency where directory exists but no pyproject.toml."""
    # tmp_path exists but is empty
    result = await add_dependency_action(
        "requests",
        project_path=str(tmp_path),
    )
    assert not result.success
    assert "No pyproject.toml found" in result.error

@pytest.mark.asyncio
async def test_repair_environment_missing_dir():
    """Test repair_environment with missing directory."""
    result = await repair_environment_action(
        project_path="/non/existent/path/99999"
    )
    assert not result.success
    assert "directory does not exist" in result.error

@pytest.mark.asyncio
async def test_list_dependencies_missing_dir():
    """Test list_dependencies with missing directory."""
    result = await list_dependencies_action(
        project_path="/non/existent/path/88888"
    )
    assert not result.success
    assert "directory does not exist" in result.error
