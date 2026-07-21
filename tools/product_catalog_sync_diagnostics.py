from __future__ import annotations

from backend.storage.database import get_connection, initialize_database


def main() -> None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN image_url IS NOT NULL AND image_url <> '' THEN 1 ELSE 0 END) AS with_image,
                   SUM(CASE WHEN availability_status IS NOT NULL AND availability_status <> '' THEN 1 ELSE 0 END) AS with_status,
                   SUM(CASE WHEN material IS NOT NULL AND material <> '' THEN 1 ELSE 0 END) AS with_material
            FROM product_catalog_items
            """
        ).fetchone()
    print("=" * 72)
    print("AI BODHI VERIFIED PRODUCT CATALOG DIAGNOSTICS")
    print("=" * 72)
    print(f"Products:     {row['total']}")
    print(f"With image:   {row['with_image'] or 0}")
    print(f"With status:  {row['with_status'] or 0}")
    print(f"With material:{row['with_material'] or 0}")


if __name__ == "__main__":
    main()
