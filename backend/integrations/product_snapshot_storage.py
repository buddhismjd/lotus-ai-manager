from __future__ import annotations

import json
from typing import Any

from backend.integrations.product_raw_snapshot import RawProductSnapshot
from backend.integrations.product_snapshot_normalizer import NormalizedProductSnapshot
from backend.storage.database import get_connection


def save_raw_snapshot(snapshot: RawProductSnapshot) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO product_raw_snapshots (
                product_uid, page_url, raw_json, html_sha256,
                snapshot_sha256, captured_at, source_kind, extractor_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_uid) DO UPDATE SET
                page_url = excluded.page_url,
                raw_json = excluded.raw_json,
                html_sha256 = excluded.html_sha256,
                snapshot_sha256 = excluded.snapshot_sha256,
                captured_at = excluded.captured_at,
                source_kind = excluded.source_kind,
                extractor_version = excluded.extractor_version
            """,
            (
                snapshot.product_uid,
                snapshot.page_url,
                snapshot.raw_json,
                snapshot.html_sha256,
                snapshot.snapshot_sha256,
                snapshot.captured_at,
                snapshot.source_kind,
                snapshot.extractor_version,
            ),
        )


def save_normalized_snapshot(product: NormalizedProductSnapshot) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO product_snapshot_items (
                product_uid, url, title, description, brand, sku,
                price, currency, gallery_json, primary_image, quantity,
                characteristics_json, properties_json, partuids_json,
                source_hash, captured_at, category, material,
                height_cm, width_cm, depth_cm, availability_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_uid) DO UPDATE SET
                url = excluded.url,
                title = excluded.title,
                description = excluded.description,
                brand = excluded.brand,
                sku = excluded.sku,
                price = excluded.price,
                currency = excluded.currency,
                gallery_json = excluded.gallery_json,
                primary_image = excluded.primary_image,
                quantity = excluded.quantity,
                characteristics_json = excluded.characteristics_json,
                properties_json = excluded.properties_json,
                partuids_json = excluded.partuids_json,
                source_hash = excluded.source_hash,
                captured_at = excluded.captured_at,
                category = excluded.category,
                material = excluded.material,
                height_cm = excluded.height_cm,
                width_cm = excluded.width_cm,
                depth_cm = excluded.depth_cm,
                availability_status = excluded.availability_status
            """,
            (
                product.product_uid,
                product.url,
                product.title,
                product.description,
                product.brand,
                product.sku,
                str(product.price) if product.price is not None else None,
                product.currency,
                json.dumps(product.gallery, ensure_ascii=False),
                product.primary_image,
                str(product.quantity) if product.quantity is not None else None,
                json.dumps(product.characteristics, ensure_ascii=False),
                json.dumps(product.properties, ensure_ascii=False),
                json.dumps(product.partuids, ensure_ascii=False),
                product.source_hash,
                product.captured_at,
                product.category,
                product.material,
                str(product.height_cm) if product.height_cm is not None else None,
                str(product.width_cm) if product.width_cm is not None else None,
                str(product.depth_cm) if product.depth_cm is not None else None,
                product.availability_status,
            ),
        )


def snapshot_quality_counts() -> dict[str, int]:
    fields = (
        "title", "description", "brand", "sku", "price", "primary_image",
        "quantity", "category", "material", "height_cm", "availability_status",
    )
    with get_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS count FROM product_snapshot_items"
        ).fetchone()["count"]
        result = {"total": total}
        for field in fields:
            row = connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM product_snapshot_items
                WHERE {field} IS NOT NULL AND TRIM(CAST({field} AS TEXT)) != ''
                """
            ).fetchone()
            result[field] = row["count"]
    return result


__all__ = [
    "save_raw_snapshot",
    "save_normalized_snapshot",
    "snapshot_quality_counts",
]
