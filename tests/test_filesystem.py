"""
Unit tests for JARVIS Filesystem Tools & Security Guardrails.
Verifies real folder creation, nested subfolders, file writing, reading, and security path rejection.
"""

import os
import shutil
from pathlib import Path
from app.tools.filesystem_tools import (
    CreateFolderTool, CreateFileTool, ReadFileTool, ListDirectoryTool, CreateProjectStructureTool
)
from app.security.guardrails import SecurityGuardrails
from app.config import DESKTOP_DIR


def test_create_folder_and_nested_subfolders():
    tool = CreateFolderTool()
    test_dir = DESKTOP_DIR / "TestJarvisFolder"

    try:
        # Test creating folder with subfolders
        result = tool.execute(path=str(test_dir), subfolders=["Clients", "Projects", "Finance"])
        assert result.success is True
        assert test_dir.exists()
        assert (test_dir / "Clients").exists()
        assert (test_dir / "Projects").exists()
        assert (test_dir / "Finance").exists()
    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


def test_create_and_read_file():
    create_tool = CreateFileTool()
    read_tool = ReadFileTool()
    test_file = DESKTOP_DIR / "jarvis_test_note.txt"
    content = "Hello from JARVIS. Automated computer control verified."

    try:
        res = create_tool.execute(path=str(test_file), content=content)
        assert res.success is True
        assert test_file.exists()

        # Read back
        read_res = read_tool.execute(path=str(test_file))
        assert read_res.success is True
        assert content in read_res.data["content"]
    finally:
        if test_file.exists():
            test_file.unlink()


def test_reject_unauthorized_paths():
    tool = CreateFolderTool()
    # Try forbidden system paths
    res_win = tool.execute(path="C:\\Windows\\System32\\MaliciousDir")
    assert res_win.success is False
    assert "Access denied" in res_win.message

    res_prog = tool.execute(path="C:\\Program Files\\UnauthorizedDir")
    assert res_prog.success is False
    assert "Access denied" in res_prog.message


def test_create_project_structure():
    tool = CreateProjectStructureTool()
    proj_name = "JarvisAutomatedProject"
    target_dir = DESKTOP_DIR / proj_name

    try:
        res = tool.execute(project_name=proj_name, folders=["frontend", "backend", "docs"], readme_title="Automated Test")
        assert res.success is True
        assert (target_dir / "frontend").exists()
        assert (target_dir / "backend").exists()
        assert (target_dir / "docs").exists()
        assert (target_dir / "README.md").exists()
    finally:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
