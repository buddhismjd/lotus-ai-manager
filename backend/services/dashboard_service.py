from __future__ import annotations

from backend.storage.database import get_connection, initialize_database


TYPE_LABELS = {
    "tour": "Тур",
    "tour_catalog": "Каталог туров",
    "psychologist": "Психолог",
    "product": "Товар",
    "shop_catalog": "Каталог магазина",
    "reviews": "Отзывы",
    "contacts": "Контакты",
    "legal": "Политика",
    "general": "Общая страница",
}


def get_dashboard_data() -> dict:
    initialize_database()

    with get_connection() as connection:
        documents = connection.execute(
            """
            SELECT
                id,
                page_type,
                title,
                url,
                enabled,
                priority,
                updated_at
            FROM documents
            ORDER BY page_type, priority DESC, title
            """
        ).fetchall()

        count_rows = connection.execute(
            """
            SELECT page_type, COUNT(*) AS count
            FROM documents
            GROUP BY page_type
            ORDER BY page_type
            """
        ).fetchall()

        chunks_count = connection.execute(
            "SELECT COUNT(*) AS count FROM document_chunks"
        ).fetchone()["count"]

    type_counts = {row["page_type"]: row["count"] for row in count_rows}

    return {
        "documents_count": len(documents),
        "chunks_count": chunks_count,
        "type_counts": type_counts,
        "type_labels": TYPE_LABELS,
        "documents": [dict(row) for row in documents],
    }
