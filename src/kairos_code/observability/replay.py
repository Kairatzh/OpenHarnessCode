"""Session Replay — inspect and replay session events step-by-step."""

from __future__ import annotations

from typing import Any
from kairos_code.storage.sqlite_store import SQLiteStore


class SessionReplayer:
    """Replays and formats historical session execution events."""

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    async def get_session_timeline(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve chronologically ordered events for a session."""
        raw_events = await self.store.get_events(session_id=session_id, limit=500)
        # Reverse to get chronological order (get_events returns DESC)
        events = list(reversed(raw_events))

        timeline: list[dict[str, Any]] = []
        for e in events:
            timeline.append({
                "timestamp": e.get("created_at"),
                "type": e.get("type"),
                "source": e.get("source"),
                "data": e.get("data", {}),
            })
        return timeline

    async def format_replay_summary(self, session_id: str) -> str:
        """Format an execution timeline into a human-readable trace."""
        timeline = await self.get_session_timeline(session_id)
        if not timeline:
            return f"No recorded events for session {session_id}."

        lines = [f"=== Session Replay Trace: {session_id} ==="]
        for step in timeline:
            ts = step["timestamp"]
            stype = step["type"]
            src = step["source"]
            data = step["data"]

            if "started" in stype:
                lines.append(f"[{ts}] ▶ START: {src} -> {data.get('step_name', data.get('workflow', ''))}")
            elif "completed" in stype:
                lines.append(f"[{ts}] ✓ COMPLETED: {src} (tokens: {data.get('tokens', 'N/A')})")
            elif "failed" in stype or "error" in stype:
                lines.append(f"[{ts}] ✗ ERROR: {src} -> {data.get('error', 'unknown error')}")
            elif "checkpoint" in stype:
                lines.append(f"[{ts}] 💾 CHECKPOINT: {data.get('checkpoint', '')}")
            else:
                lines.append(f"[{ts}] • {stype} ({src})")

        return "\n".join(lines)
