from __future__ import annotations

import sqlite3
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MemoryEntry:
    role: str
    content: str


class NanoBotAgent:
    """Minimal runtime adapter with intent routing and session memory."""

    def __init__(self, sqlite_path: str | None = None) -> None:
        self._memory: dict[str, list[MemoryEntry]] = {}
        self._lock = threading.Lock()
        self._sqlite_path = sqlite_path
        if sqlite_path:
            self._init_sqlite(Path(sqlite_path))

    def _init_sqlite(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def _route_intent(self, query: str) -> str:
        lowered = query.lower()
        tool_keywords = {
            "calculate",
            "compute",
            "tool",
            "lookup",
            "search",
            "weather",
            "stock",
            "price",
        }
        return "tool" if any(keyword in lowered for keyword in tool_keywords) else "skill"

    def _append_memory(self, session_id: str, role: str, content: str) -> None:
        entry = MemoryEntry(role=role, content=content)
        with self._lock:
            self._memory.setdefault(session_id, []).append(entry)

        if self._sqlite_path:
            with sqlite3.connect(self._sqlite_path) as conn:
                conn.execute(
                    "INSERT INTO conversation_memory(session_id, role, content) VALUES(?, ?, ?)",
                    (session_id, role, content),
                )
                conn.commit()

    def _read_memory(self, session_id: str) -> list[MemoryEntry]:
        with self._lock:
            in_memory = list(self._memory.get(session_id, []))

        if not in_memory and self._sqlite_path:
            with sqlite3.connect(self._sqlite_path) as conn:
                rows = conn.execute(
                    "SELECT role, content FROM conversation_memory WHERE session_id = ? ORDER BY created_at ASC",
                    (session_id,),
                ).fetchall()
            return [MemoryEntry(role=row[0], content=row[1]) for row in rows]

        return in_memory

    def handle_query(self, query: str, session_id: str | None = None) -> dict[str, Any]:
        normalized_query = query.strip()
        active_session = session_id or str(uuid.uuid4())
        intent = self._route_intent(normalized_query)

        self._append_memory(active_session, "user", normalized_query)

        if intent == "tool":
            answer = f"Tool intent detected. Routed query: {normalized_query}"
        else:
            answer = f"Skill intent detected. Routed query: {normalized_query}"

        self._append_memory(active_session, "assistant", answer)
        memory = self._read_memory(active_session)

        return {
            "session_id": active_session,
            "intent": intent,
            "answer": answer,
            "memory": [{"role": item.role, "content": item.content} for item in memory],
        }
