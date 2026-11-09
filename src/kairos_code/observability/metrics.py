"""Metrics collection for performance, token usage, and evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SessionMetrics:
    """Execution metrics for a task session."""
    session_id: str = ""
    task_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    total_tokens: int = 0
    agent_calls: int = 0
    tool_calls: int = 0
    iterations: int = 0
    errors: int = 0
    final_status: str = ""


class MetricsCollector:
    """Aggregates metrics across sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionMetrics] = {}

    def start_session(self, session_id: str, task_id: str = "") -> SessionMetrics:
        metrics = SessionMetrics(session_id=session_id, task_id=task_id)
        self._sessions[session_id] = metrics
        return metrics

    def record_tokens(self, session_id: str, tokens: int) -> None:
        m = self._sessions.get(session_id)
        if m:
            m.total_tokens += tokens

    def record_agent_call(self, session_id: str) -> None:
        m = self._sessions.get(session_id)
        if m:
            m.agent_calls += 1

    def record_tool_call(self, session_id: str) -> None:
        m = self._sessions.get(session_id)
        if m:
            m.tool_calls += 1

    def record_error(self, session_id: str) -> None:
        m = self._sessions.get(session_id)
        if m:
            m.errors += 1

    def end_session(self, session_id: str, status: str = "") -> SessionMetrics | None:
        m = self._sessions.get(session_id)
        if m:
            m.ended_at = datetime.utcnow()
            m.final_status = status
        return m

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_sessions": len(self._sessions),
            "total_tokens": sum(m.total_tokens for m in self._sessions.values()),
            "total_agent_calls": sum(m.agent_calls for m in self._sessions.values()),
            "total_errors": sum(m.errors for m in self._sessions.values()),
        }
