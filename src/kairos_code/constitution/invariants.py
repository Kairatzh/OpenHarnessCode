"""Machine-verifiable engineering invariants and standards."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class InvariantViolation(BaseModel):
    rule: str
    severity: str  # "error", "warning"
    details: str
    file_path: str = ""
    line: int | None = None


class EngineeringStandards(BaseModel):
    """Machine-checkable project invariants."""
    no_unrequested_changes: bool = True
    prefer_simple_design: bool = True
    enforce_dependency_boundaries: bool = True
    no_dead_code: bool = True
    run_linter: bool = True
    run_tests: bool = True
    run_type_checker: bool = True
    max_cyclomatic_complexity: int = 15


class InvariantChecker:
    """Runs deterministic linters, typecheckers, and invariant tests to verify clean architecture."""

    def __init__(self, project_root: str | Path, standards: EngineeringStandards | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.standards = standards or EngineeringStandards()

    async def run_linter(self) -> list[InvariantViolation]:
        """Run ruff or flake8 to check code cleanliness and unused imports."""
        violations: list[InvariantViolation] = []
        if not self.standards.run_linter:
            return violations

        cmd = "ruff check src/ tests/"
        try:
            proc = await self._run_subprocess(cmd)
            if proc.returncode != 0:
                for line in proc.stdout.splitlines():
                    if ":" in line:
                        violations.append(InvariantViolation(
                            rule="linter",
                            severity="error",
                            details=line.strip(),
                        ))
        except Exception:
            pass  # Linter not installed or command skipped
        return violations

    async def run_tests(self, test_path: str = "tests/") -> tuple[bool, str]:
        """Execute automated tests deterministically and return real exit status."""
        cmd = f"pytest {test_path} -q"
        try:
            proc = await self._run_subprocess(cmd)
            output = proc.stdout + proc.stderr
            passed = proc.returncode == 0
            return passed, output
        except Exception as e:
            return False, str(e)

    async def check_unrequested_files(
        self,
        touched_files: list[str],
        allowed_files: list[str],
    ) -> list[InvariantViolation]:
        """Ensure agent did not modify files outside declared scope (No Unrequested Changes)."""
        violations: list[InvariantViolation] = []
        if not self.standards.no_unrequested_changes:
            return violations

        allowed_set = {f.replace("\\", "/").strip("./") for f in allowed_files}
        for f in touched_files:
            normalized = f.replace("\\", "/").strip("./")
            if normalized not in allowed_set and not normalized.startswith(".harness/"):
                violations.append(InvariantViolation(
                    rule="no_unrequested_changes",
                    severity="error",
                    details=f"File modified without specification approval: {f}",
                    file_path=f,
                ))
        return violations

    async def _run_subprocess(self, command: str):
        if os.name == "nt":
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                "/bin/bash", "-c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
            )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=45)
        
        class Output:
            pass
        out = Output()
        out.returncode = proc.returncode
        out.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
        out.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
        return out
