"""Developer-controlled policy engine — permissions, paths, commands, and secrets."""

from __future__ import annotations

import re
from pathlib import Path
from pydantic import BaseModel

from kairos_code.core.config import SecurityConfig
from kairos_code.core.exceptions import SecurityError


class Permission(BaseModel):
    action: str
    resource: str = "*"
    allowed: bool = True
    reason: str = ""


class PolicyEngine:
    """Enforces security policies defined and controlled by the developer.
    
    Philosophy: No forced harness guardrails. The developer owns permissions.
    """

    def __init__(self, config: SecurityConfig) -> None:
        self.config = config
        self._compiled_secret_patterns = [
            re.compile(p) for p in config.secret_patterns
        ]

    def check_command(self, command: str) -> Permission:
        if not self.config.enabled:
            return Permission(action="terminal.execute", resource=command, allowed=True)

        cmd_lower = command.lower().strip()
        for pattern in self.config.command_denylist:
            if pattern.lower() in cmd_lower:
                return Permission(
                    action="terminal.execute",
                    resource=command,
                    allowed=False,
                    reason=f"Command matches denylist pattern: {pattern}",
                )

        if self.config.command_allowlist:
            cmd_base = command.strip().split()[0] if command.strip() else ""
            base_name = cmd_base.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            if base_name not in self.config.command_allowlist:
                return Permission(
                    action="terminal.execute",
                    resource=command,
                    allowed=False,
                    reason=f"Command '{base_name}' not in allowlist",
                )

        return Permission(action="terminal.execute", resource=command, allowed=True)

    def check_file_access(
        self, path: str, write: bool = False, project_root: str = ""
    ) -> Permission:
        if not self.config.enabled:
            return Permission(
                action="filesystem.write" if write else "filesystem.read",
                resource=path,
                allowed=True,
            )

        if self.config.filesystem_access == "project_only" and project_root:
            try:
                Path(path).resolve().relative_to(Path(project_root).resolve())
            except ValueError:
                return Permission(
                    action="filesystem.write" if write else "filesystem.read",
                    resource=path,
                    allowed=False,
                    reason="Access outside project root is not permitted in 'project_only' mode",
                )

        return Permission(
            action="filesystem.write" if write else "filesystem.read",
            resource=path,
            allowed=True,
        )

    def check_network_access(self, url: str = "") -> Permission:
        if not self.config.network_access:
            return Permission(
                action="network.access",
                resource=url,
                allowed=False,
                reason="Network access is disabled in configuration",
            )
        return Permission(action="network.access", resource=url, allowed=True)

    def redact_secrets(self, text: str) -> str:
        for pattern in self._compiled_secret_patterns:
            text = pattern.sub("[REDACTED]", text)
        return text

    def enforce(self, permission: Permission) -> None:
        if not permission.allowed:
            raise SecurityError(
                f"Policy check failed: {permission.action} on {permission.resource}. "
                f"Reason: {permission.reason}"
            )
