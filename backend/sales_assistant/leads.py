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


    def save_artisan_selection(
        self,
        *,
        social_channel: str,
        social_contact: str,
        email: str,
        interest: str | None,
        selection_category: str | None,
        selection_aspect: str | None,
        requested_height_min_cm: float | None,
        requested_height_max_cm: float | None,
        consent_text: str,
        conversation_summary: str | None = None,
    ) -> SavedLead:
        initialize_database()
        phone = social_contact if social_channel == "whatsapp" else None
        telegram = social_contact if social_channel == "telegram" else None
        details = [
            "workflow=artisan_selection",
            f"social_channel={social_channel}",
            f"social_contact={social_contact}",
            f"selection_category={selection_category or 'не указана'}",
            f"selection_aspect={selection_aspect or 'не указан'}",
            f"requested_height_min_cm={requested_height_min_cm if requested_height_min_cm is not None else 'не указана'}",
            f"requested_height_max_cm={requested_height_max_cm if requested_height_max_cm is not None else 'не указана'}",
            f"consent_text={consent_text}",
            f"context={conversation_summary or 'не указан'}",
        ]
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    name, phone, email, telegram, interest, comment, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
                """,
                (
                    "Посетитель сайта",
                    phone,
                    email,
                    telegram,
                    interest,
                    "; ".join(details),
                    now,
                ),
            )
            lead_id = int(cursor.lastrowid)
        return SavedLead(lead_id, "Посетитель сайта", social_channel, social_contact, interest)

    def count(self) -> int:
        initialize_database()
        with get_connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM leads").fetchone()[0])


__all__ = ["LeadRepository", "SavedLead"]
