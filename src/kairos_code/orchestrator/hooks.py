"""Event Hooks — user-defined callbacks executed during lifecycle events."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Coroutine

from kairos_code.core.events import Event, EventBus, EventType


HookCallable = Callable[[Event], Coroutine[Any, Any, None] | None]


class HookManager:
    """Manages custom lifecycle hooks.
    
    Supported hook points:
    - before_agent: Invoked prior to agent LLM call
    - after_agent: Invoked after agent finishes
    - before_tool: Invoked before tool execution
    - after_tool: Invoked after tool returns
    - on_task_complete: Invoked when a task completes
    - on_error: Invoked on any error
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._hooks: dict[str, list[HookCallable]] = {
            "before_agent": [],
            "after_agent": [],
            "before_tool": [],
            "after_tool": [],
            "on_task_complete": [],
            "on_error": [],
        }
        self._wire_event_bus()

    def register(self, hook_name: str, callback: HookCallable) -> None:
        """Register a callback for a lifecycle hook."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def _wire_event_bus(self) -> None:
        """Wire event bus notifications to registered hooks."""
        mapping = {
            EventType.BEFORE_AGENT: "before_agent",
            EventType.AFTER_AGENT: "after_agent",
            EventType.BEFORE_TOOL: "before_tool",
            EventType.AFTER_TOOL: "after_tool",
            EventType.TASK_COMPLETED: "on_task_complete",
            EventType.ERROR: "on_error",
            EventType.WORKFLOW_FAILED: "on_error",
        }
        for etype, hook_name in mapping.items():
            self.event_bus.subscribe(etype, self._create_dispatcher(hook_name))

    def _create_dispatcher(self, hook_name: str):
        async def dispatcher(event: Event) -> None:
            callbacks = self._hooks.get(hook_name, [])
            for cb in callbacks:
                try:
                    if inspect.iscoroutinefunction(cb):
                        await cb(event)
                    else:
                        cb(event)
                except Exception:
                    pass
        return dispatcher
