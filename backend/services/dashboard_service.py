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
    """
    Returns dashboard data in the format expected by backend.main.

    The nested `stats` dictionary is kept for compatibility with the
    current /dev page, while type_counts and type_labels are also returned
    for future dashboard improvements.
    """
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
            ORDER BY
                CASE page_type
                    WHEN 'tour' THEN 1
                    WHEN 'tour_catalog' THEN 2
                    WHEN 'psychologist' THEN 3
                    WHEN 'product' THEN 4
                    WHEN 'shop_catalog' THEN 5
                    WHEN 'reviews' THEN 6
                    WHEN 'contacts' THEN 7
                    WHEN 'legal' THEN 8
                    ELSE 9
                END,
                priority DESC,
                title
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

    type_counts = {
        row["page_type"]: row["count"]
        for row in count_rows
    }

    stats = {
        "documents": len(documents),
        "chunks": chunks_count,
        "tours": type_counts.get("tour", 0),
        "consultations": type_counts.get("psychologist", 0),
        "shop": (
            type_counts.get("product", 0)
            + type_counts.get("shop_catalog", 0)
        ),
        "general": (
            type_counts.get("general", 0)
            + type_counts.get("tour_catalog", 0)
            + type_counts.get("reviews", 0)
            + type_counts.get("contacts", 0)
            + type_counts.get("legal", 0)
        ),
    }

    return {
        "stats": stats,
        "documents_count": len(documents),
        "chunks_count": chunks_count,
        "type_counts": type_counts,
        "type_labels": TYPE_LABELS,
        "documents": [dict(row) for row in documents],
    }
