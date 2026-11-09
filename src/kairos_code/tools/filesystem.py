"""Filesystem tools — read, write, and search files."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any

from kairos_code.tools.base import Tool, ToolResult


class FileReadTool(Tool):
    """Read file content safely."""

    name = "file_read"
    description = "Read the contents of a file. Returns text content."
    required_capability = "filesystem.read"

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root).resolve()

    async def execute(self, path: str = "", **kwargs: Any) -> ToolResult:
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
            if not file_path.is_file():
                return ToolResult(success=False, error=f"Not a file: {path}")

            content = file_path.read_text(encoding="utf-8", errors="replace")

            max_size = 100_000
            truncated = False
            if len(content) > max_size:
                content = content[:max_size]
                truncated = True

            return ToolResult(
                success=True,
                output=content,
                metadata={
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "truncated": truncated,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.project_root / p
        return p.resolve()

    def _get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read.",
                },
            },
            "required": ["path"],
        }


class FileWriteTool(Tool):
    """Write content to a file with directory creation and boundary check."""

    name = "file_write"
    description = "Write content to a file. Creates or overwrites."
    required_capability = "filesystem.write"

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root).resolve()

    async def execute(
        self, path: str = "", content: str = "", create_dirs: bool = True, **kwargs: Any
    ) -> ToolResult:
        try:
            file_path = self._resolve_path(path)

            try:
                file_path.relative_to(self.project_root)
            except ValueError:
                return ToolResult(
                    success=False,
                    error=f"Cannot write outside project root: {path}",
                )

            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding="utf-8")

            return ToolResult(
                success=True,
                output=f"Written {len(content)} bytes to {file_path}",
                metadata={"path": str(file_path), "bytes_written": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.project_root / p
        return p.resolve()

    def _get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write.",
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if needed.",
                    "default": True,
                },
            },
            "required": ["path", "content"],
        }


class FileSearchTool(Tool):
    """Search files by pattern or query text."""

    name = "file_search"
    description = "Search for files by glob pattern or search file contents."
    required_capability = "filesystem.search"

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root).resolve()

    _skip_dirs = {
        ".git", ".venv", "venv", "__pycache__", "node_modules",
        ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
        "dist", "build",
    }

    async def execute(
        self,
        pattern: str = "",
        query: str = "",
        max_results: int = 50,
        **kwargs: Any,
    ) -> ToolResult:
        try:
            results: list[str] = []

            if pattern:
                for root, dirs, files in os.walk(self.project_root):
                    dirs[:] = [d for d in dirs if d not in self._skip_dirs]
                    for f in files:
                        if fnmatch.fnmatch(f, pattern):
                            rel = os.path.relpath(os.path.join(root, f), self.project_root)
                            results.append(rel)
                            if len(results) >= max_results:
                                break
                    if len(results) >= max_results:
                        break

            elif query:
                query_lower = query.lower()
                for root, dirs, files in os.walk(self.project_root):
                    dirs[:] = [d for d in dirs if d not in self._skip_dirs]
                    for f in files:
                        fpath = os.path.join(root, f)
                        try:
                            with open(fpath, encoding="utf-8", errors="ignore") as fh:
                                for line_num, line in enumerate(fh, 1):
                                    if query_lower in line.lower():
                                        rel = os.path.relpath(fpath, self.project_root)
                                        results.append(f"{rel}:{line_num}: {line.rstrip()}")
                                        if len(results) >= max_results:
                                            break
                        except Exception:
                            continue
                    if len(results) >= max_results:
                        break

            return ToolResult(
                success=True,
                output="\n".join(results) if results else "No matches found.",
                metadata={"count": len(results), "truncated": len(results) >= max_results},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g. '*.py').",
                },
                "query": {
                    "type": "string",
                    "description": "Text to search in file contents.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max results.",
                    "default": 50,
                },
            },
        }
