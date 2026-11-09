"""Git tool — version control, checkpoints, and rollback."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from kairos_code.tools.base import Tool, ToolResult


class GitTool(Tool):
    """Git operations with checkpoint and undo support."""

    name = "git"
    description = "Git operations: status, diff, log, commit, branch, checkpoint, rollback."
    required_capability = "git.read"

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root).resolve()

    async def execute(
        self,
        operation: str = "status",
        args: str = "",
        **kwargs: Any,
    ) -> ToolResult:
        op = operation.lower().strip()

        if op == "checkpoint":
            tag = f"kairos-checkpoint-{int(time.time())}"
            msg = args or f"Checkpoint: {tag}"
            cmd = f'git add -A && git commit -m "{msg}" --allow-empty'
            res = await self._run_shell(cmd)
            res.metadata["checkpoint_tag"] = tag
            return res

        if op == "rollback":
            # Revert last commit or restore unstaged files
            cmd = "git reset --hard HEAD~1" if args == "commit" else "git checkout -- ."
            return await self._run_shell(cmd)

        op_map = {
            "status": "git status --short",
            "status_full": "git status",
            "diff": f"git diff {args}".strip(),
            "diff_staged": f"git diff --staged {args}".strip(),
            "log": f"git log --oneline -20 {args}".strip(),
            "branch": "git branch -a",
            "show": f"git show {args}".strip(),
            "add": f"git add {args}".strip(),
            "commit": f'git commit -m "{args}"' if args else "git commit",
            "checkout": f"git checkout {args}".strip(),
            "reset": f"git reset {args}".strip(),
        }

        if op not in op_map:
            return ToolResult(
                success=False,
                error=f"Unknown git operation: {op}. Available: {', '.join(op_map.keys())}, checkpoint, rollback",
            )

        return await self._run_shell(op_map[op])

    async def _run_shell(self, command: str) -> ToolResult:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            return ToolResult(
                success=proc.returncode == 0,
                output=stdout_text,
                error=stderr_text if proc.returncode != 0 else "",
                metadata={"command": command},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Git command failed: {e}")

    def _get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Git operation: status, diff, log, commit, checkout, checkpoint, rollback.",
                },
                "args": {
                    "type": "string",
                    "description": "Additional arguments or message.",
                },
            },
            "required": ["operation"],
        }
