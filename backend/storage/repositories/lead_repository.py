from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class _ValueEnum(Protocol):
    value: str


class _LeadContact(Protocol):
    name: str
    contact_channel: _ValueEnum
    contact_value: str
    email: str

from backend.storage.database import get_connection, initialize_database


@dataclass(frozen=True, slots=True)
class SavedLead:
    id: int
    name: str
    contact_method: str
    contact_value: str
    interest: str | None
    email: str | None = None
    status: str = "new"
    handoff_reason: str | None = None


class LeadRepository:
    """Own all SQLite persistence for completed sales leads."""

    def save(
        self,
        *,
        name: str,
        contact_method: str,
        contact_value: str,
        interest: str | None,
        comment: str | None = None,
        email: str | None = None,
        dialog_id: int | None = None,
    ) -> SavedLead:
        """Save the legacy lead-capture contract without changing its callers."""
        normalized_method = contact_method.strip().lower()
        return self._insert(
            dialog_id=dialog_id,
            name=name,
            contact_method=normalized_method,
            contact_value=contact_value,
            email=email,
            interest=interest,
            comment=comment,
        )

    def save_handoff(
        self,
        *,
        contact: _LeadContact,
        reason: _ValueEnum,
        priority: _ValueEnum,
        manager_summary: str,
        interest: str | None,
        comment: str | None = None,
        dialog_id: int | None = None,
        session_id: str | None = None,
    ) -> SavedLead:
        """Persist a validated manager-handoff lead with structured metadata."""
        return self._insert(
            dialog_id=dialog_id,
            name=contact.name,
            contact_method=contact.contact_channel.value,
            contact_value=contact.contact_value,
            email=contact.email,
            interest=interest,
            comment=comment,
            session_id=session_id,
            handoff_reason=reason.value,
            handoff_priority=priority.value,
            manager_summary=manager_summary,
        )

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
        return self._insert(
            dialog_id=None,
            name="Посетитель сайта",
            contact_method=social_channel.strip().lower(),
            contact_value=social_contact,
            email=email,
            interest=interest,
            comment="; ".join(details),
        )

    def get(self, lead_id: int) -> SavedLead | None:
        initialize_database()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, name, phone, telegram, contact_channel, contact_value, interest,
                       email, status, handoff_reason
                FROM leads
                WHERE id = ?
                """,
                (lead_id,),
            ).fetchone()
        if row is None:
            return None
        return SavedLead(
            id=int(row["id"]),
            name=row["name"] or "",
            contact_method=row["contact_channel"] or self._legacy_contact_method(row),
            contact_value=row["contact_value"] or "",
            interest=row["interest"],
            email=row["email"],
            status=row["status"],
            handoff_reason=row["handoff_reason"],
        )

    def count(self) -> int:
        initialize_database()
        with get_connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM leads").fetchone()[0])

    def _insert(
        self,
        *,
        dialog_id: int | None,
        name: str,
        contact_method: str,
        contact_value: str,
        email: str | None,
        interest: str | None,
        comment: str | None,
        session_id: str | None = None,
        handoff_reason: str | None = None,
        handoff_priority: str | None = None,
        manager_summary: str | None = None,
    ) -> SavedLead:
        initialize_database()
        phone = contact_value if contact_method in {"phone", "whatsapp"} else None
        telegram = contact_value if contact_method == "telegram" else None
        stored_email = contact_value if contact_method == "email" else email
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    dialog_id, name, phone, email, telegram, interest, comment,
                    status, created_at, updated_at, contact_channel, contact_value,
                    session_id, handoff_reason, handoff_priority, manager_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dialog_id,
                    name,
                    phone,
                    stored_email,
                    telegram,
                    interest,
                    comment,
                    now,
                    now,
                    contact_method,
                    contact_value,
                    session_id,
                    handoff_reason,
                    handoff_priority,
                    manager_summary,
                ),
            )
            lead_id = int(cursor.lastrowid)
        return SavedLead(
            id=lead_id,
            name=name,
            contact_method=contact_method,
            contact_value=contact_value,
            interest=interest,
            email=stored_email,
            status="new",
            handoff_reason=handoff_reason,
        )

    @staticmethod
    def _legacy_contact_method(row) -> str:
        if row["telegram"]:
            return "telegram"
        if row["phone"]:
            return "phone"
        if row["email"]:
            return "email"
        return ""


__all__ = ["LeadRepository", "SavedLead"]
