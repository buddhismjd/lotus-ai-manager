from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.storage.database import get_connection, initialize_database


class SessionAccessDeniedError(PermissionError):
    """Raised when a protected widget session is accessed without ownership proof."""


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


@dataclass(frozen=True, slots=True)
class SessionAccess:
    session_id: str
    token: str
    created: bool


class SessionRepository:
    """SQLite owner for persistent widget sessions and conversation history."""

    TOKEN_BYTES = 32

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def _new_token(cls) -> str:
        return secrets.token_urlsafe(cls.TOKEN_BYTES)

    def establish_access(self, session_id: str, token: str | None = None) -> SessionAccess:
        """Create or validate ownership for an API-backed active session.

        Old rows created before CB-1.5.1B have no token hash. The first API chat
        claims such a row by assigning a newly generated token. New rows are
        protected from creation.
        """
        initialize_database()
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, ownership_token_hash
                FROM dialogs
                WHERE session_id = ? AND status = 'active'
                ORDER BY id DESC LIMIT 1
                """,
                (session_id,),
            ).fetchone()

            if row is None:
                issued = self._new_token()
                connection.execute(
                    """
                    INSERT INTO dialogs (
                        session_id, status, started_at, updated_at,
                        state_json, handoff_status, ownership_token_hash
                    ) VALUES (?, 'active', ?, ?, '{}', 'none', ?)
                    """,
                    (session_id, now, now, self._token_hash(issued)),
                )
                return SessionAccess(session_id, issued, True)

            stored_hash = row["ownership_token_hash"] or ""
            if stored_hash:
                if not token or not hmac.compare_digest(stored_hash, self._token_hash(token)):
                    raise SessionAccessDeniedError("Session ownership could not be verified.")
                return SessionAccess(session_id, token, False)

            issued = self._new_token()
            connection.execute(
                """
                UPDATE dialogs
                SET ownership_token_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (self._token_hash(issued), now, row["id"]),
            )
            return SessionAccess(session_id, issued, False)

    def verify_access(self, session_id: str, token: str | None) -> None:
        """Verify access to history/reset while retaining read compatibility for legacy rows."""
        initialize_database()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT ownership_token_hash
                FROM dialogs
                WHERE session_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return
        stored_hash = row["ownership_token_hash"] or ""
        if not stored_hash:
            return
        if not token or not hmac.compare_digest(stored_hash, self._token_hash(token)):
            raise SessionAccessDeniedError("Session ownership could not be verified.")

    def rotate_token(self, session_id: str, token: str) -> str:
        self.verify_access(session_id, token)
        replacement = self._new_token()
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE dialogs
                SET ownership_token_hash = ?, updated_at = ?
                WHERE session_id = ? AND status = 'active'
                """,
                (self._token_hash(replacement), now, session_id),
            )
            if cursor.rowcount == 0:
                raise SessionAccessDeniedError("Active session was not found.")
        return replacement

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


__all__ = [
    "ConversationMessage",
    "ConversationSession",
    "SessionAccess",
    "SessionAccessDeniedError",
    "SessionRepository",
]
