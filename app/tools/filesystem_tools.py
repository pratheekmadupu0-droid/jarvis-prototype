"""
JARVIS Filesystem Tools
Safely performs directory and file operations with path validation, verification,
and error handling.
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.tools.base import BaseTool, ToolResult
from app.security.guardrails import SecurityGuardrails
from app.config import DESKTOP_DIR


class CreateFolderTool(BaseTool):
    name = "create_folder"
    description = "Create a directory or nested subdirectories in an approved location (Desktop, Documents, etc.)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Folder name or path (e.g. 'Desktop/Gromighty' or 'Gromighty')"},
            "subfolders": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of subfolders to create inside it (e.g. ['Clients', 'Projects', 'Finance'])"
            }
        },
        "required": ["path"]
    }

    def execute(self, path: str, subfolders: Optional[List[str]] = None) -> ToolResult:
        valid, resolved, msg = SecurityGuardrails.validate_path(path)
        if not valid or not resolved:
            return ToolResult(success=False, message=msg)

        try:
            resolved.mkdir(parents=True, exist_ok=True)
            created_subs = []
            if subfolders:
                for sub in subfolders:
                    sub_path = resolved / sub.strip()
                    sub_path.mkdir(parents=True, exist_ok=True)
                    created_subs.append(sub.strip())

            # Verification
            if not resolved.exists() or not resolved.is_dir():
                return ToolResult(success=False, message=f"Verification failed: Directory {resolved} was not created.")

            # Automatically reveal created folder on user's screen in File Explorer
            try:
                os.startfile(str(resolved))
            except Exception:
                try:
                    subprocess.Popen(["explorer.exe", str(resolved)])
                except Exception:
                    pass

            details = f"Created directory '{resolved.name}' at {resolved}."
            if created_subs:
                details += f" Created subfolders: {', '.join(created_subs)}."
            return ToolResult(success=True, message=details, data={"path": str(resolved), "subfolders": created_subs})
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to create directory: {str(e)}")


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create a new text or code file with specified content in an approved location."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file path or filename"},
            "content": {"type": "string", "description": "Text or code content to write"}
        },
        "required": ["path", "content"]
    }

    def execute(self, path: str, content: str) -> ToolResult:
        valid, resolved, msg = SecurityGuardrails.validate_path(path)
        if not valid or not resolved:
            return ToolResult(success=False, message=msg)

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)

            # Verification
            if not resolved.exists() or resolved.stat().st_size == 0 and len(content) > 0:
                return ToolResult(success=False, message="Verification failed: File was not created properly.")

            return ToolResult(
                success=True,
                message=f"Created file '{resolved.name}' ({len(content)} bytes) at {resolved}.",
                data={"path": str(resolved), "size": resolved.stat().st_size}
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to write file: {str(e)}")


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a supported text or code document in an approved directory."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to read"}
        },
        "required": ["path"]
    }

    def execute(self, path: str) -> ToolResult:
        valid, resolved, msg = SecurityGuardrails.validate_path(path)
        if not valid or not resolved:
            return ToolResult(success=False, message=msg)

        if not resolved.exists() or not resolved.is_file():
            return ToolResult(success=False, message=f"File not found: '{resolved}'.")

        try:
            with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(50000)  # limit 50KB
            return ToolResult(success=True, message=f"Read {len(content)} characters from '{resolved.name}'.", data={"content": content})
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to read file: {str(e)}")


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and subdirectories within a folder."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Folder path to inspect (defaults to Desktop)"}
        }
    }

    def execute(self, path: Optional[str] = None) -> ToolResult:
        target_path = path or str(DESKTOP_DIR)
        valid, resolved, msg = SecurityGuardrails.validate_path(target_path)
        if not valid or not resolved:
            return ToolResult(success=False, message=msg)

        if not resolved.exists() or not resolved.is_dir():
            return ToolResult(success=False, message=f"Directory does not exist: {resolved}")

        try:
            items = []
            for item in resolved.iterdir():
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })
            summary = f"Found {len(items)} items in '{resolved.name}': " + ", ".join([it["name"] for it in items[:15]])
            return ToolResult(success=True, message=summary, data={"items": items, "path": str(resolved)})
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to list directory: {str(e)}")


class CreateProjectStructureTool(BaseTool):
    name = "create_project_structure"
    description = "Create a complete development project workspace with subdirectories and initial files (e.g. frontend, backend, README.md)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "Project folder name"},
            "folders": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Subdirectories to create (e.g. ['frontend', 'backend', 'docs'])"
            },
            "readme_title": {"type": "string", "description": "Project title for README.md"}
        },
        "required": ["project_name"]
    }

    def execute(self, project_name: str, folders: Optional[List[str]] = None, readme_title: Optional[str] = None) -> ToolResult:
        target_dir = DESKTOP_DIR / project_name.strip()
        valid, resolved, msg = SecurityGuardrails.validate_path(str(target_dir))
        if not valid or not resolved:
            return ToolResult(success=False, message=msg)

        try:
            resolved.mkdir(parents=True, exist_ok=True)
            folder_list = folders or ["frontend", "backend", "docs"]
            for f in folder_list:
                (resolved / f.strip()).mkdir(parents=True, exist_ok=True)

            readme_file = resolved / "README.md"
            title = readme_title or project_name.strip()
            readme_content = f"# {title}\n\nProject initialized by JARVIS AI Assistant.\n\n## Structure\n"
            for f in folder_list:
                readme_content += f"- `{f}/`\n"

            with open(readme_file, "w", encoding="utf-8") as rf:
                rf.write(readme_content)

            # Verification
            if not resolved.exists() or not readme_file.exists():
                return ToolResult(success=False, message="Project verification failed.")

            msg = f"Project '{project_name}' created on Desktop with folders {folder_list} and README.md."
            return ToolResult(success=True, message=msg, data={"path": str(resolved), "folders": folder_list})
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to create project: {str(e)}")


class OpenFolderTool(BaseTool):
    name = "open_folder"
    description = "Open a folder or directory in Windows File Explorer (e.g. 'Gromighty', 'Desktop', 'Downloads', 'Documents')."
    parameters_schema = {
        "type": "object",
        "properties": {
            "folder_name": {"type": "string", "description": "Folder name or path (e.g. 'Gromighty', 'Desktop', 'Downloads')"}
        },
        "required": ["folder_name"]
    }

    def execute(self, folder_name: str) -> ToolResult:
        import subprocess
        fn = folder_name.strip()
        from app.config import DOWNLOADS_DIR, DOCUMENTS_DIR

        if fn.lower() in ("desktop", "my desktop"):
            target = DESKTOP_DIR
        elif fn.lower() in ("downloads", "my downloads"):
            target = DOWNLOADS_DIR
        elif fn.lower() in ("documents", "my documents"):
            target = DOCUMENTS_DIR
        else:
            valid, resolved, msg = SecurityGuardrails.validate_path(fn)
            if not valid or not resolved or not resolved.exists():
                cand = DESKTOP_DIR / fn
                if cand.exists():
                    target = cand
                else:
                    return ToolResult(success=False, message=f"Folder '{fn}' does not exist on your computer.")
            else:
                target = resolved

        if not target.exists():
            return ToolResult(success=False, message=f"Folder '{target.name}' not found at {target}.")

        try:
            try:
                os.startfile(str(target))
            except Exception:
                subprocess.Popen(["explorer.exe", str(target)])
            return ToolResult(
                success=True,
                message=f"Opened folder '{target.name}' in File Explorer on your screen.",
                data={"path": str(target)}
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to open folder: {str(e)}")
