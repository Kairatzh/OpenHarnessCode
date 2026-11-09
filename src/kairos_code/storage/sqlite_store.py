"""SQLite-based local-first storage for tasks, sessions, and events."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from kairos_code.core.models import SessionInfo, Task


class SQLiteStore:
    """Local-first storage engine using SQLite."""

    def __init__(self, db_path: str | Path = ".harness/kairos.db") -> None:
        self.db_path = Path(db_path)
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self.db_path))
        await self._db.executescript('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                session_id TEXT,
                data TEXT DEFAULT '{}',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                state TEXT DEFAULT 'active',
                task_id TEXT,
                workflow TEXT DEFAULT 'feature_development',
                data TEXT DEFAULT '{}',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                source TEXT,
                session_id TEXT,
                task_id TEXT,
                data TEXT DEFAULT '{}',
                created_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);
            CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
        ''')
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def save_task(self, task: Task) -> None:
        assert self._db is not None
        data = task.model_dump_json()
        await self._db.execute(
            '''INSERT OR REPLACE INTO tasks (id, title, description, status, priority, session_id, data, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                task.id, task.title, task.description,
                task.status.value, task.priority.value,
                task.session_id, data,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
            ),
        )
        await self._db.commit()

    async def get_task(self, task_id: str) -> Task | None:
        assert self._db is not None
        async with self._db.execute(
            "SELECT data FROM tasks WHERE id = ?", (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Task.model_validate_json(row[0])
        return None

    async def list_tasks(
        self, status: str | None = None, limit: int = 50
    ) -> list[Task]:
        assert self._db is not None
        if status:
            query = "SELECT data FROM tasks WHERE status = ? ORDER BY updated_at DESC LIMIT ?"
            params = (status, limit)
        else:
            query = "SELECT data FROM tasks ORDER BY updated_at DESC LIMIT ?"
            params = (limit,)

        tasks = []
        async with self._db.execute(query, params) as cursor:
            async for row in cursor:
                tasks.append(Task.model_validate_json(row[0]))
        return tasks

    async def save_session(self, session: SessionInfo) -> None:
        assert self._db is not None
        data = session.model_dump_json()
        await self._db.execute(
            '''INSERT OR REPLACE INTO sessions (id, state, task_id, workflow, data, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                session.id, session.state.value,
                session.task_id, session.workflow,
                data,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
            ),
        )
        await self._db.commit()

    async def get_session(self, session_id: str) -> SessionInfo | None:
        assert self._db is not None
        async with self._db.execute(
            "SELECT data FROM sessions WHERE id = ?", (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return SessionInfo.model_validate_json(row[0])
        return None

    async def log_event(
        self,
        event_type: str,
        source: str = "",
        session_id: str = "",
        task_id: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        assert self._db is not None
        await self._db.execute(
            '''INSERT INTO events (type, source, session_id, task_id, data, created_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                event_type, source, session_id, task_id,
                json.dumps(data or {}),
                datetime.utcnow().isoformat(),
            ),
        )
        await self._db.commit()

    async def get_events(
        self,
        session_id: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        assert self._db is not None
        if session_id:
            query = "SELECT type, source, data, created_at FROM events WHERE session_id = ? ORDER BY id DESC LIMIT ?"
            params = (session_id, limit)
        else:
            query = "SELECT type, source, data, created_at FROM events ORDER BY id DESC LIMIT ?"
            params = (limit,)

        events = []
        async with self._db.execute(query, params) as cursor:
            async for row in cursor:
                events.append({
                    "type": row[0],
                    "source": row[1],
                    "data": json.loads(row[2]),
                    "created_at": row[3],
                })
        return events
