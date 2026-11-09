"""Terminal tool — controlled command execution with developer policies."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from kairos_code.tools.base import Tool, ToolResult


class TerminalTool(Tool):
    """Execute shell commands with safety checks."""

    name = "terminal"
    description = "Execute a shell command in the project directory."
    required_capability = "terminal.execute"

    _blocked_patterns = [
        "rm -rf /",
        "rm -rf /*",
        "sudo rm",
        "mkfs",
        "chmod -R 777 /",
    ]

    def __init__(
        self,
        project_root: str = ".",
        timeout: int = 60,
        allowed_commands: list[str] | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.timeout = timeout
        self.allowed_commands = allowed_commands

    async def execute(
        self,
        command: str = "",
        timeout: int | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        if not command.strip():
            return ToolResult(success=False, error="No command provided.")

        cmd_lower = command.lower().strip()
        for pattern in self._blocked_patterns:
            if pattern in cmd_lower:
                return ToolResult(
                    success=False,
                    error=f"Blocked dangerous command pattern: {pattern}",
                )

        if self.allowed_commands is not None:
            cmd_base = command.strip().split()[0]
            base_name = cmd_base.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            if base_name not in self.allowed_commands:
                return ToolResult(
                    success=False,
                    error=f"Command '{base_name}' not in developer allowlist.",
                )

        effective_timeout = timeout or self.timeout

        try:
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

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=effective_timeout
            )

            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            output = stdout_text
            if stderr_text:
                output += f"\n--- stderr ---\n{stderr_text}"

            return ToolResult(
                success=proc.returncode == 0,
                output=output,
                error=stderr_text if proc.returncode != 0 else "",
                metadata={
                    "return_code": proc.returncode,
                    "command": command,
                },
            )
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Command timed out after {effective_timeout}s: {command}",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Command failed: {e}")

    def _get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to run.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds.",
                    "default": 60,
                },
            },
            "required": ["command"],
        }
