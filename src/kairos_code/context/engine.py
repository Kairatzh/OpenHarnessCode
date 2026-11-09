"""Context engine — gathers and assembles repository context for agents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProjectContext(BaseModel):
    """Assembled project context for agent consumption."""
    project_root: str
    project_name: str = ""
    language: str = "unknown"
    framework: str = ""
    structure: str = ""
    key_files: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    git_status: str = ""
    conventions: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_prompt_section(self) -> str:
        parts = ["# Project Context"]
        parts.append(f"\n**Project**: {self.project_name}")
        parts.append(f"**Root**: {self.project_root}")
        parts.append(f"**Language**: {self.language}")
        if self.framework:
            parts.append(f"**Framework**: {self.framework}")

        if self.structure:
            parts.append(f"\n## Project Structure\n```\n{self.structure}\n```")

        if self.key_files:
            parts.append("\n## Key Files")
            for f in self.key_files:
                parts.append(f"- {f}")

        if self.dependencies:
            parts.append("\n## Dependencies")
            for d in self.dependencies[:25]:
                parts.append(f"- {d}")

        if self.git_status:
            parts.append(f"\n## Git Status\n```\n{self.git_status}\n```")

        if self.conventions:
            parts.append(f"\n## Conventions & Rules\n{self.conventions}")

        return "\n".join(parts)


class ContextEngine:
    """Gathers and indexes project structure and knowledge."""

    _skip_dirs = {
        ".git", ".venv", "venv", "__pycache__", "node_modules",
        ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
        "dist", "build",
    }

    _language_indicators = {
        "pyproject.toml": ("python", ""),
        "setup.py": ("python", ""),
        "requirements.txt": ("python", ""),
        "package.json": ("javascript", "node"),
        "tsconfig.json": ("typescript", ""),
        "Cargo.toml": ("rust", ""),
        "go.mod": ("go", ""),
    }

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    async def gather(self) -> ProjectContext:
        ctx = ProjectContext(
            project_root=str(self.project_root),
            project_name=self.project_root.name,
        )

        ctx.language, ctx.framework = self._detect_language()
        ctx.structure = self._build_tree(max_depth=3)
        ctx.key_files = self._find_key_files()
        ctx.dependencies = self._read_dependencies()
        ctx.git_status = await self._get_git_status()
        ctx.conventions = self._read_conventions()

        return ctx

    def _detect_language(self) -> tuple[str, str]:
        for filename, (lang, fw) in self._language_indicators.items():
            if (self.project_root / filename).exists():
                return lang, fw
        return "unknown", ""

    def _build_tree(self, max_depth: int = 3) -> str:
        lines: list[str] = [self.project_root.name + "/"]
        self._walk_tree(self.project_root, "", 0, max_depth, lines)
        return "\n".join(lines[:150])

    def _walk_tree(
        self, directory: Path, prefix: str, depth: int, max_depth: int, lines: list[str]
    ) -> None:
        if depth >= max_depth:
            return

        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name))
        except (PermissionError, OSError):
            return

        entries = [
            e for e in entries
            if e.name not in self._skip_dirs and not e.name.startswith(".")
        ]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                self._walk_tree(entry, prefix + extension, depth + 1, max_depth, lines)

    def _find_key_files(self) -> list[str]:
        patterns = [
            "README.md", "pyproject.toml", "package.json", "Cargo.toml",
            "Makefile", "Dockerfile", ".env.example",
        ]
        return [p for p in patterns if (self.project_root / p).exists()]

    def _read_dependencies(self) -> list[str]:
        deps: list[str] = []
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if '"' in line or "'" in line:
                        stripped = line.strip().strip('",\'')
                        if any(stripped.startswith(prefix) for prefix in ("pydantic", "fastapi", "torch", "flask", "django")):
                            deps.append(stripped)
            except Exception:
                pass
        return deps

    async def _get_git_status(self) -> str:
        import asyncio
        if not (self.project_root / ".git").exists():
            return "No git repository initialized"
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "status", "--short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            return stdout.decode("utf-8", errors="replace").strip() or "Clean"
        except Exception:
            return "Unable to query git"

    def _read_conventions(self) -> str:
        parts: list[str] = []
        for dname in ("knowledge", "rules"):
            dir_path = self.project_root / ".harness" / dname
            if dir_path.exists():
                for f in sorted(dir_path.rglob("*.md")):
                    try:
                        parts.append(f.read_text(encoding="utf-8"))
                    except Exception:
                        pass
        return "\n\n".join(parts)
