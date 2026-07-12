from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.storage.database import get_connection, initialize_database


@dataclass(frozen=True, slots=True)
class SavedLead:
    id: int
    name: str
    contact_method: str
    contact_value: str
    interest: str | None


class LeadRepository:
    """Persist completed sales leads in the existing SQLite schema."""

    def save(
        self,
        *,
        name: str,
        contact_method: str,
        contact_value: str,
        interest: str | None,
        comment: str | None = None,
    ) -> SavedLead:
        initialize_database()
        phone = contact_value if contact_method in {"phone", "whatsapp"} else None
        email = contact_value if contact_method == "email" else None
        telegram = contact_value if contact_method == "telegram" else None
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    name, phone, email, telegram, interest, comment, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
                """,
                (name, phone, email, telegram, interest, comment, now),
            )
            lead_id = int(cursor.lastrowid)
        return SavedLead(lead_id, name, contact_method, contact_value, interest)

    def count(self) -> int:
        initialize_database()
        with get_connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM leads").fetchone()[0])


__all__ = ["LeadRepository", "SavedLead"]
