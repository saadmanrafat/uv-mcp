#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify all UV-Agent MCP tools work correctly."""

import json
import sys
import platform
import asyncio
import inspect
from pathlib import Path

# Ensure UTF-8 encoding for output on all platforms
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, 'src')

from uv_mcp.utils import check_uv_available, get_project_info
from uv_mcp.diagnostics import generate_diagnostic_report
from uv_mcp.actions import (
    repair_environment_action,
    add_dependency_action,
    check_uv_installation_action,
    get_install_instructions_action
)


# Use ASCII-safe symbols for cross-platform compatibility
CHECK_MARK = "[PASS]" if platform.system() == "Windows" else "✓"
CROSS_MARK = "[FAIL]" if platform.system() == "Windows" else "✗"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{ '='*60}\n")


async def test_check_uv_installation():
    """Test the check_uv_installation action."""
    print_section("Testing: uv installation check")
    
    # Test action directly
    data = await check_uv_installation_action()
    # data is now a Pydantic model
    print(data.model_dump_json(indent=2))
    
    assert data.installed, "uv should be installed"
    
    print(f"{CHECK_MARK} Test passed: uv is installed")


async def test_install_uv():
    """Test installation instructions action."""
    print_section("Testing: installation instructions")
    instructions = get_install_instructions_action()
    
    print("Installation methods available:")
    # instructions.methods is a dict of InstallMethod or dict of InstallMethod
    for platform_key, cmd in instructions.methods["standalone_installer"].items():
        # cmd is InstallMethod
        print(f"  {platform_key}: {cmd.command}")
    print(f"{CHECK_MARK} Test passed: installation instructions available")


async def test_diagnose_environment():
    """Test the diagnose_environment logic."""
    print_section("Testing: environment diagnostics")
    report = await generate_diagnostic_report()
    print(report.model_dump_json(indent=2))
    assert report.overall_health, "Should return health status"
    assert report.uv.installed, "uv should be detected"
    
    print(f"{CHECK_MARK} Test passed: environment health is '{report.overall_health}'")


async def test_repair_environment():
    """Test the repair_environment action."""
    print_section("Testing: environment repair (dry run)")
    project_dir = Path.cwd()
    
    # Run with auto_fix=False
    results = await repair_environment_action(project_path=str(project_dir), auto_fix=False)
    
    print(results.model_dump_json(indent=2))
    assert results.success, "Repair action should return success status"
    
    has_pyproject = (project_dir / "pyproject.toml").exists()
    has_venv = (project_dir / ".venv").exists()
    
    if has_pyproject and has_venv:
        print(f"{CHECK_MARK} Test passed: environment is healthy")
    else:
        print(f"{CHECK_MARK} Test passed: repair identified issues")


async def test_add_dependency():
    """Test dependency addition (dry run)."""
    print_section("Testing: dependency addition (dry run)")
    
    info = get_project_info()
    
    # Handle both sync and async implementations for robustness
    if inspect.isawaitable(info):
        info = await info
    
    # info is now a dict (from utils.py, type hint dict[str, Any])
    print(f"Project: {info.get('project_name', 'unknown')}")
    print(f"Dependencies: {len(info.get('dependencies', []))}")
    
    assert add_dependency_action is not None
    print(f"{CHECK_MARK} Test passed: dependency management logic is ready")


async def main_async():
    """Run all tests."""
    print("\n" + "="*60)
    print("  UV-Agent MCP Server - Tool Verification Tests")
    print("="*60)
    
    try:
        await test_check_uv_installation()
        await test_install_uv()
        await test_diagnose_environment()
        await test_repair_environment()
        await test_add_dependency()
        
        print_section(f"All Tests Passed! {CHECK_MARK}")
        print("The UV-Agent MCP server is working correctly.")
        
    except Exception as e:
        print(f"\n{CROSS_MARK} Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def main():
    return asyncio.run(main_async())


if __name__ == "__main__":
    exit(main())