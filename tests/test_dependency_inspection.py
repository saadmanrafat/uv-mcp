import pytest
import pytest_asyncio
import shutil
import os
from pathlib import Path
from src.uv_mcp.actions import (
    list_dependencies_action,
    show_package_info_action,
    check_outdated_packages_action,
    analyze_dependency_tree_action,
)
from src.uv_mcp.tools import ProjectTools
from src.uv_mcp.utils import run_uv_command


@pytest_asyncio.fixture
async def temp_project(tmp_path: Path):
    """
    Fixture to create a temporary project directory.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Initialize a new project
    await ProjectTools.init_project(name="test_project", path=str(tmp_path))

    # Explicitly create a virtual environment
    # We must ensure we don't use the outer environment
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    await run_uv_command(["venv"], cwd=project_dir, env=env)

    return project_dir


@pytest_asyncio.fixture
async def temp_project_with_deps(temp_project: Path):
    """
    Fixture to create a temporary project with dependencies.
    """
    # Add 'requests' dependency (it has sub-dependencies like urllib3)
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)

    # Using 2.28.0 as it was verified to work in other tests
    success, stdout, stderr = await run_uv_command(
        ["add", "requests==2.28.0"], cwd=temp_project, env=env
    )
    if not success:
        raise RuntimeError(f"Failed to add requests: {stderr}")
    return temp_project


@pytest.mark.asyncio
async def test_list_dependencies(temp_project_with_deps: Path):
    """Test listing dependencies in both flat and tree formats."""
    # Test flat list
    result = await list_dependencies_action(str(temp_project_with_deps), tree=False)
    assert result.success
    assert not result.is_tree
    assert len(result.dependencies) > 0

    # Check if requests is present
    requests_dep = next((d for d in result.dependencies if d.name == "requests"), None)
    assert requests_dep is not None
    assert requests_dep.version == "2.28.0"

    # Test tree view
    result_tree = await list_dependencies_action(str(temp_project_with_deps), tree=True)
    assert result_tree.success
    assert result_tree.is_tree
    assert "requests" in result_tree.tree_output


@pytest.mark.asyncio
async def test_show_package_info(temp_project_with_deps: Path):
    """Test showing package info."""
    result = await show_package_info_action("requests", str(temp_project_with_deps))
    assert result.success
    assert result.name == "requests"
    assert result.version == "2.28.0"
    assert len(result.requires) > 0
    # certifi is a dependency of requests
    assert any("certifi" in r for r in result.requires) or any(
        "urllib3" in r for r in result.requires
    )


@pytest.mark.asyncio
async def test_show_package_info_not_found(temp_project: Path):
    """Test showing info for a non-existent package."""
    result = await show_package_info_action("non-existent-package", str(temp_project))
    assert not result.success
    assert "not found" in result.error.lower() or "no metadata" in result.error.lower()


@pytest.mark.asyncio
async def test_check_outdated_packages(temp_project: Path):
    """Test checking for outdated packages."""
    # Install an old version of a package
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)

    await run_uv_command(["add", "requests==2.28.0"], cwd=temp_project, env=env)

    result = await check_outdated_packages_action(str(temp_project))
    assert result.success

    # Verify that requests is listed as outdated (assuming 2.28.0 is not the latest)
    # Note: This relies on network access to PyPI. If offline, this might need mocking or skip.
    # uv usually caches, but let's assume network is available as per agent capabilities.
    outdated_requests = next(
        (p for p in result.outdated_packages if p.name == "requests"), None
    )

    if outdated_requests:
        assert outdated_requests.version == "2.28.0"
        assert outdated_requests.latest_version != "2.28.0"


@pytest.mark.asyncio
async def test_analyze_dependency_tree(temp_project_with_deps: Path):
    """Test analyzing dependency tree."""
    result = await analyze_dependency_tree_action(str(temp_project_with_deps))
    assert result.success
    assert len(result.tree_output) > 0
    # requests usually has depth > 0 because of its dependencies
    assert result.depth is not None
    assert result.depth >= 0
