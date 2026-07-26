from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from backend.config import DATA_DIR, DATABASE_FILE


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    page_type TEXT NOT NULL DEFAULT 'general',
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    priority INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    state_json TEXT NOT NULL DEFAULT '{}',
    handoff_status TEXT NOT NULL DEFAULT 'none'
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS dialogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dialog_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (dialog_id)
        REFERENCES dialogs(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dialog_id INTEGER,
    name TEXT,
    phone TEXT,
    email TEXT,
    telegram TEXT,
    interest TEXT,
    comment TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    contact_channel TEXT,
    contact_value TEXT,
    session_id TEXT,
    handoff_reason TEXT,
    handoff_priority TEXT,
    manager_summary TEXT,
    FOREIGN KEY (dialog_id)
        REFERENCES dialogs(id)
        ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS product_catalog_items (
    product_uid TEXT PRIMARY KEY,
    document_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category TEXT,
    description TEXT NOT NULL DEFAULT '',
    price TEXT,
    currency TEXT,
    sku TEXT,
    image_url TEXT,
    availability_status TEXT,
    material TEXT,
    source_hash TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE
);



CREATE TABLE IF NOT EXISTS product_raw_snapshots (
    product_uid TEXT PRIMARY KEY,
    page_url TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    html_sha256 TEXT NOT NULL,
    snapshot_sha256 TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    source_kind TEXT NOT NULL DEFAULT 'product_page_script',
    extractor_version TEXT NOT NULL DEFAULT '2.1'
);

CREATE TABLE IF NOT EXISTS product_snapshot_items (
    product_uid TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    brand TEXT,
    sku TEXT,
    price TEXT,
    currency TEXT,
    gallery_json TEXT NOT NULL DEFAULT '[]',
    primary_image TEXT,
    quantity TEXT,
    characteristics_json TEXT NOT NULL DEFAULT '[]',
    properties_json TEXT NOT NULL DEFAULT '[]',
    partuids_json TEXT NOT NULL DEFAULT '[]',
    source_hash TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    category TEXT,
    material TEXT,
    height_cm TEXT,
    width_cm TEXT,
    depth_cm TEXT,
    availability_status TEXT
);

CREATE INDEX IF NOT EXISTS idx_product_snapshot_title
ON product_snapshot_items(title);

CREATE INDEX IF NOT EXISTS idx_product_snapshot_sku
ON product_snapshot_items(sku);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_page_type
ON documents(page_type);

CREATE INDEX IF NOT EXISTS idx_documents_enabled
ON documents(enabled);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id
ON document_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_messages_dialog_id
ON messages(dialog_id);

CREATE INDEX IF NOT EXISTS idx_dialogs_session_status
ON dialogs(session_id, status);

CREATE INDEX IF NOT EXISTS idx_leads_status
ON leads(status);

CREATE INDEX IF NOT EXISTS idx_product_catalog_status
ON product_catalog_items(availability_status);

CREATE INDEX IF NOT EXISTS idx_product_catalog_category
ON product_catalog_items(category);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def initialize_database() -> Path:
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        _ensure_column(
            connection,
            "product_raw_snapshots",
            "source_kind",
            "TEXT NOT NULL DEFAULT 'product_page_script'",
        )
        _ensure_column(
            connection,
            "product_raw_snapshots",
            "extractor_version",
            "TEXT NOT NULL DEFAULT '2.1'",
        )
        dialog_columns = {
            "state_json": "TEXT NOT NULL DEFAULT '{}'",
            "handoff_status": "TEXT NOT NULL DEFAULT 'none'",
        }
        for column_name, definition in dialog_columns.items():
            _ensure_column(connection, "dialogs", column_name, definition)

        lead_columns = {
            "updated_at": "TEXT",
            "contact_channel": "TEXT",
            "contact_value": "TEXT",
            "session_id": "TEXT",
            "handoff_reason": "TEXT",
            "handoff_priority": "TEXT",
            "manager_summary": "TEXT",
        }
        for column_name, definition in lead_columns.items():
            _ensure_column(connection, "leads", column_name, definition)

        connection.execute(
            """
            UPDATE leads
            SET updated_at = COALESCE(updated_at, created_at),
                contact_channel = COALESCE(
                    contact_channel,
                    CASE
                        WHEN telegram IS NOT NULL AND telegram != '' THEN 'telegram'
                        WHEN phone IS NOT NULL AND phone != '' THEN 'phone'
                        WHEN email IS NOT NULL AND email != '' THEN 'email'
                        ELSE NULL
                    END
                ),
                contact_value = COALESCE(
                    contact_value, telegram, phone, email
                )
            """
        )

    return DATABASE_FILE


def clear_knowledge_documents() -> None:
    """
    Clears only generated knowledge documents and chunks.

    Dialogs, messages, leads and settings are preserved.
    """
    with get_connection() as connection:
        connection.execute("DELETE FROM document_chunks")
        connection.execute("DELETE FROM documents")


def get_table_names() -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

    return [row["name"] for row in rows]


def save_document(document: dict) -> None:
    """
    Creates or updates one document and replaces its chunks.

    A URL is unique. If an older document has the same URL but another ID,
    the older record is removed before saving the current document.
    """
    now = datetime.now().isoformat(timespec="seconds")
    document_id = document["id"]
    document_url = document.get("url", "")
    chunks = document.get("chunks", [])

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM documents WHERE url = ?",
            (document_url,),
        ).fetchone()

        if existing and existing["id"] != document_id:
            connection.execute(
                "DELETE FROM documents WHERE id = ?",
                (existing["id"],),
            )

        connection.execute(
            """
            INSERT INTO documents (
                id,
                source_type,
                page_type,
                title,
                url,
                summary,
                content,
                enabled,
                priority,
                content_hash,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source_type = excluded.source_type,
                page_type = excluded.page_type,
                title = excluded.title,
                url = excluded.url,
                summary = excluded.summary,
                content = excluded.content,
                enabled = excluded.enabled,
                priority = excluded.priority,
                content_hash = excluded.content_hash,
                updated_at = excluded.updated_at
            """,
            (
                document_id,
                document.get("source_type", "tilda"),
                document.get("type", "general"),
                document.get("title", ""),
                document_url,
                document.get("summary", ""),
                document.get("content", ""),
                1 if document.get("enabled", True) else 0,
                int(document.get("priority", 0)),
                document.get("content_hash"),
                now,
                now,
            ),
        )

        connection.execute(
            "DELETE FROM document_chunks WHERE document_id = ?",
            (document_id,),
        )

        for chunk_index, chunk_content in enumerate(chunks):
            chunk_content = chunk_content.strip()

            if not chunk_content:
                continue

            connection.execute(
                """
                INSERT INTO document_chunks (
                    document_id,
                    chunk_index,
                    content,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    document_id,
                    chunk_index,
                    chunk_content,
                    now,
                ),
            )


def get_database_stats() -> dict[str, int]:
    with get_connection() as connection:
        documents_count = connection.execute(
            "SELECT COUNT(*) AS count FROM documents"
        ).fetchone()["count"]

        chunks_count = connection.execute(
            "SELECT COUNT(*) AS count FROM document_chunks"
        ).fetchone()["count"]

        tours_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM documents
            WHERE page_type = 'tour'
            """
        ).fetchone()["count"]

        psychologist_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM documents
            WHERE page_type = 'psychologist'
            """
        ).fetchone()["count"]

        products_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM documents
            WHERE page_type = 'product'
            """
        ).fetchone()["count"]

    return {
        "documents": documents_count,
        "chunks": chunks_count,
        "tours": tours_count,
        "psychologist": psychologist_count,
        "products": products_count,
    }


def set_setting(key: str, value: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, now),
        )


def get_setting(key: str) -> str | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        ).fetchone()

    return row["value"] if row else None


if __name__ == "__main__":
    database_path = initialize_database()

    print(f"Database initialized: {database_path}")
    print("Tables:")

    for table_name in get_table_names():
        print(f"  - {table_name}")
