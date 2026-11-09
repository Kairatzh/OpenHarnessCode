"""Event system for inter-component communication and hooks."""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events in the harness."""
    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # Agent events & hooks
    BEFORE_AGENT = "before_agent"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_MESSAGE = "agent.message"
    AFTER_AGENT = "after_agent"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Approval events
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"

    # Tool events & hooks
    BEFORE_TOOL = "before_tool"
    TOOL_INVOKED = "tool.invoked"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    AFTER_TOOL = "after_tool"

    # Checkpoint & Git
    CHECKPOINT_CREATED = "checkpoint.created"
    CHECKPOINT_RESTORED = "checkpoint.restored"

    # System events
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    CONFIG_CHANGED = "config.changed"
    ERROR = "error"
    LOG = "log"


class Event(BaseModel):
    """An event in the harness system."""
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    task_id: Optional[str] = None


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Async event bus for publishing, subscribing, and executing hooks."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._global_handlers: list[EventHandler] = []
        self._history: list[Event] = []
        self._max_history: int = 2000

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to all events."""
        self._global_handlers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from a specific event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        """Publish an event to all matching subscribers."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        handlers = list(self._global_handlers)
        if event.type in self._handlers:
            handlers.extend(self._handlers[event.type])

        if handlers:
            await asyncio.gather(
                *(handler(event) for handler in handlers),
                return_exceptions=True,
            )

    async def emit(
        self,
        event_type: EventType,
        source: str = "",
        data: dict[str, Any] | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
    ) -> Event:
        """Convenience method to create and publish an event."""
        event = Event(
            type=event_type,
            source=source,
            data=data or {},
            session_id=session_id,
            task_id=task_id,
        )
        await self.publish(event)
        return event

    def get_history(
        self,
        event_type: EventType | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get recent event history, optionally filtered."""
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        return events[-limit:]
