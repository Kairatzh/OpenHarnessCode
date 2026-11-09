"""Plugin system interfaces and registry."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HarnessPlugin(Protocol):
    """Protocol for KAIROS Code plugins."""

    name: str
    version: str
    description: str

    def register(self, registry: "PluginRegistry") -> None:
        """Register plugin components with the harness."""
        ...

    async def initialize(self, context: dict[str, Any]) -> None:
        """Initialize the plugin."""
        ...

    async def shutdown(self) -> None:
        """Cleanup upon unloading."""
        ...


class PluginRegistry:
    """Manages plugin discovery, loading, and registration."""

    def __init__(self) -> None:
        self._plugins: dict[str, HarnessPlugin] = {}
        self._agent_factories: dict[str, Any] = {}
        self._provider_factories: dict[str, Any] = {}
        self._tool_factories: dict[str, Any] = {}
        self._workflow_factories: dict[str, Any] = {}

    def register_plugin(self, plugin: HarnessPlugin) -> None:
        self._plugins[plugin.name] = plugin
        plugin.register(self)

    def register_agent(self, name: str, factory: Any) -> None:
        self._agent_factories[name] = factory

    def register_provider(self, name: str, factory: Any) -> None:
        self._provider_factories[name] = factory

    def register_tool(self, name: str, factory: Any) -> None:
        self._tool_factories[name] = factory

    def register_workflow(self, name: str, factory: Any) -> None:
        self._workflow_factories[name] = factory

    async def initialize_all(self, context: dict[str, Any] | None = None) -> None:
        for plugin in self._plugins.values():
            await plugin.initialize(context or {})

    async def shutdown_all(self) -> None:
        for plugin in self._plugins.values():
            await plugin.shutdown()

    def list_plugins(self) -> list[dict[str, str]]:
        return [
            {"name": p.name, "version": p.version, "description": p.description}
            for p in self._plugins.values()
        ]
