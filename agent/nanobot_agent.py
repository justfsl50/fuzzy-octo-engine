from __future__ import annotations

import json
import os
import shlex
import sqlite3
import subprocess
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MemoryEntry:
    role: str
    content: str


class SessionMemoryStore:
    """Session memory with in-memory storage and optional SQLite persistence."""

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

    def append(self, session_id: str, role: str, content: str) -> None:
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

    def read(self, session_id: str) -> list[MemoryEntry]:
        with self._lock:
            buffered = list(self._memory.get(session_id, []))

        if buffered:
            return buffered

        if self._sqlite_path:
            with sqlite3.connect(self._sqlite_path) as conn:
                rows = conn.execute(
                    "SELECT role, content FROM conversation_memory WHERE session_id = ? ORDER BY created_at ASC",
                    (session_id,),
                ).fetchall()
            return [MemoryEntry(role=row[0], content=row[1]) for row in rows]

        return []


class NanoBotRuntimeAdapter:
    """Adapter for HKUDS/nanobot runtime via configurable command execution.

    Configure integration using one of the environment variables:
      - NANOBOT_COMMAND: full command with placeholders {query} {session_id} {intent} {history_json}
      - NANOBOT_REPO_PATH + NANOBOT_ENTRYPOINT: python entrypoint invocation

    If neither is configured, a deterministic local fallback is used.
    """

    def __init__(self, command_template: str | None = None, timeout_s: int = 60) -> None:
        self._command_template = command_template or os.getenv("NANOBOT_COMMAND")
        self._timeout_s = timeout_s

    def invoke(self, query: str, session_id: str, intent: str, history: list[dict[str, str]]) -> dict[str, Any]:
        history_json = json.dumps(history)

        if self._command_template:
            command = self._command_template.format(
                query=shlex.quote(query),
                session_id=shlex.quote(session_id),
                intent=shlex.quote(intent),
                history_json=shlex.quote(history_json),
            )
            return self._run_shell(command)

        repo_path = os.getenv("NANOBOT_REPO_PATH")
        entrypoint = os.getenv("NANOBOT_ENTRYPOINT", "main.py")
        if repo_path:
            cmd = [
                "python",
                str(Path(repo_path) / entrypoint),
                "--query",
                query,
                "--session-id",
                session_id,
                "--intent",
                intent,
                "--history-json",
                history_json,
            ]
            return self._run_list(cmd)

        return {
            "provider": "local-fallback",
            "answer": f"{intent.title()} route selected for: {query}",
            "raw": {"note": "Set NANOBOT_COMMAND or NANOBOT_REPO_PATH to use HKUDS/nanobot runtime."},
        }

    def _run_shell(self, command: str) -> dict[str, Any]:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=self._timeout_s)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"NanoBot command failed ({proc.returncode})")
        return self._parse_output(proc.stdout)

    def _run_list(self, command: list[str]) -> dict[str, Any]:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=self._timeout_s)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"NanoBot process failed ({proc.returncode})")
        return self._parse_output(proc.stdout)

    def _parse_output(self, stdout: str) -> dict[str, Any]:
        payload = stdout.strip()
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                return {
                    "provider": data.get("provider", "nanobot"),
                    "answer": data.get("answer") or data.get("response") or payload,
                    "raw": data,
                }
        except json.JSONDecodeError:
            pass

        return {"provider": "nanobot", "answer": payload, "raw": {"stdout": payload}}


class NanoBotAgent:
    """Runtime adapter with intent routing and session-aware memory."""

    def __init__(
        self,
        sqlite_path: str | None = None,
        runtime_adapter: NanoBotRuntimeAdapter | None = None,
    ) -> None:
        self._memory = SessionMemoryStore(sqlite_path=sqlite_path)
        self._runtime = runtime_adapter or NanoBotRuntimeAdapter()

    def _route_intent(self, query: str) -> str:
        lowered = query.lower()
        tool_keywords = {"calculate", "compute", "tool", "lookup", "search", "weather", "stock", "price"}
        return "tool" if any(keyword in lowered for keyword in tool_keywords) else "skill"

    def handle_query(self, query: str, session_id: str | None = None) -> dict[str, Any]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")

        active_session = session_id or str(uuid.uuid4())
        intent = self._route_intent(normalized_query)

        self._memory.append(active_session, "user", normalized_query)
        history = [{"role": item.role, "content": item.content} for item in self._memory.read(active_session)]

        runtime_result = self._runtime.invoke(
            query=normalized_query,
            session_id=active_session,
            intent=intent,
            history=history,
        )
        answer = runtime_result["answer"]

        self._memory.append(active_session, "assistant", answer)
        full_history = [{"role": item.role, "content": item.content} for item in self._memory.read(active_session)]

        return {
            "session_id": active_session,
            "intent": intent,
            "answer": answer,
            "provider": runtime_result.get("provider", "nanobot"),
            "memory": full_history,
            "raw": runtime_result.get("raw", {}),
        }
