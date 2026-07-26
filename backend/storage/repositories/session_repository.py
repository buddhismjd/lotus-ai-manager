from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.storage.database import get_connection, initialize_database


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    role: str
    content: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ConversationSession:
    session_id: str
    status: str
    state: dict[str, Any]
    handoff_status: str
    messages: tuple[ConversationMessage, ...]


class SessionRepository:
    """SQLite owner for persistent widget sessions and conversation history."""

    def get_state(self, session_id: str) -> dict[str, Any] | None:
        initialize_database()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT state_json
                FROM dialogs
                WHERE session_id = ? AND status = 'active'
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        try:
            value = json.loads(row["state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def save_state(self, session_id: str, state: dict[str, Any], *, handoff_status: str) -> None:
        dialog_id = self._active_dialog_id(session_id)
        now = datetime.now().isoformat(timespec="seconds")
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True)
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE dialogs
                SET state_json = ?, handoff_status = ?, updated_at = ?
                WHERE id = ?
                """,
                (payload, handoff_status, now, dialog_id),
            )

    def append_message(self, session_id: str, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Message role must be 'user' or 'assistant'.")
        dialog_id = self._active_dialog_id(session_id)
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO messages (dialog_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (dialog_id, role, content, now),
            )
            connection.execute(
                "UPDATE dialogs SET updated_at = ? WHERE id = ?",
                (now, dialog_id),
            )

    def get_session(self, session_id: str, *, limit: int = 100) -> ConversationSession:
        initialize_database()
        with get_connection() as connection:
            dialog = connection.execute(
                """
                SELECT id, status, state_json, handoff_status
                FROM dialogs
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
            if dialog is None:
                return ConversationSession(session_id, "new", {}, "none", ())
            rows = connection.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE dialog_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (dialog["id"], max(1, min(limit, 500))),
            ).fetchall()
        try:
            state = json.loads(dialog["state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            state = {}
        return ConversationSession(
            session_id=session_id,
            status=dialog["status"],
            state=state if isinstance(state, dict) else {},
            handoff_status=dialog["handoff_status"] or "none",
            messages=tuple(
                ConversationMessage(row["role"], row["content"], row["created_at"])
                for row in rows
            ),
        )

    def reset(self, session_id: str) -> None:
        initialize_database()
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE dialogs
                SET status = 'reset', updated_at = ?
                WHERE session_id = ? AND status = 'active'
                """,
                (now, session_id),
            )

    def _active_dialog_id(self, session_id: str) -> int:
        initialize_database()
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id FROM dialogs
                WHERE session_id = ? AND status = 'active'
                ORDER BY id DESC LIMIT 1
                """,
                (session_id,),
            ).fetchone()
            if row is not None:
                return int(row["id"])
            cursor = connection.execute(
                """
                INSERT INTO dialogs (
                    session_id, status, started_at, updated_at, state_json, handoff_status
                ) VALUES (?, 'active', ?, ?, '{}', 'none')
                """,
                (session_id, now, now),
            )
            return int(cursor.lastrowid)


__all__ = ["ConversationMessage", "ConversationSession", "SessionRepository"]
