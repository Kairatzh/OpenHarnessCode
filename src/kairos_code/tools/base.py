"""Base tool interface and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Tool(ABC):
    """Abstract base class for all tools."""

    name: str = "base_tool"
    description: str = "Base tool"
    required_capability: str = ""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""
        ...

    def get_schema(self) -> dict[str, Any]:
        """Return OpenAI-compatible function schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._get_parameters_schema(),
            },
        }

    def _get_parameters_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}


class ToolRegistry:
    """Registry for managing available tools with capability control."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_tools_for_capabilities(
        self, capabilities: list[str]
    ) -> list[Tool]:
        result = []
        for tool in self._tools.values():
            if not tool.required_capability:
                result.append(tool)
            elif tool.required_capability in capabilities:
                result.append(tool)
        return result

    def get_schemas(self, capabilities: list[str] | None = None) -> list[dict[str, Any]]:
        if capabilities is not None:
            tools = self.get_tools_for_capabilities(capabilities)
        else:
            tools = list(self._tools.values())
        return [t.get_schema() for t in tools]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def register_defaults(self, project_root: str = ".") -> None:
        from kairos_code.tools.filesystem import FileReadTool, FileWriteTool, FileSearchTool
        from kairos_code.tools.terminal import TerminalTool
        from kairos_code.tools.git import GitTool

        self.register(FileReadTool(project_root=project_root))
        self.register(FileWriteTool(project_root=project_root))
        self.register(FileSearchTool(project_root=project_root))
        self.register(TerminalTool(project_root=project_root))
        self.register(GitTool(project_root=project_root))
