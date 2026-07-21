from __future__ import annotations

from backend.storage.database import get_connection, initialize_database


def main() -> None:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT availability_status, COUNT(*) AS count
            FROM product_catalog_items
            GROUP BY availability_status
            ORDER BY count DESC
            """
        ).fetchall()
    print("AI BODHI PRODUCT CATALOG STATUS REPORT")
    for row in rows:
        print(f"- {row['availability_status'] or 'status not published'}: {row['count']}")


if __name__ == "__main__":
    main()
