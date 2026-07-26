from __future__ import annotations

import re
import sqlite3
from decimal import Decimal, InvalidOperation
from typing import Generic, TypeVar

from backend.catalog.models import Consultation, Product, Tour
from backend.storage.database import get_connection
from backend.tours.price_parser import parse_tour_price


CatalogItem = TypeVar("CatalogItem", Product, Tour, Consultation)


def _row_value(row: sqlite3.Row, key: str, default=None):
    return row[key] if key in row.keys() else default


def _description_from_row(row: sqlite3.Row) -> str:
    summary = (_row_value(row, "summary", "") or "").strip()
    content = (_row_value(row, "content", "") or "").strip()
    return summary or content


def _metadata_from_row(row: sqlite3.Row) -> dict:
    return {
        "source_type": _row_value(row, "source_type"),
        "page_type": _row_value(row, "page_type"),
        "priority": _row_value(row, "priority", 0),
        "content_hash": _row_value(row, "content_hash"),
        "created_at": _row_value(row, "created_at"),
        "updated_at": _row_value(row, "updated_at"),
    }


_FIELD_PATTERNS = {
    "image_url": re.compile(r"^Изображение:\s*(?P<value>https?://\S+)$", re.MULTILINE),
    "availability_status": re.compile(r"^Статус:\s*(?P<value>.+)$", re.MULTILINE),
    "material": re.compile(r"^Материал:\s*(?P<value>.+)$", re.MULTILINE),
}


def _content_field(content: str, field: str) -> str | None:
    pattern = _FIELD_PATTERNS[field]
    match = pattern.search(content or "")
    return match.group("value").strip() if match else None


def _decimal_value(value) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except (InvalidOperation, ValueError):
        return None


def _row_to_product(row: sqlite3.Row) -> Product:
    description = (_row_value(row, "catalog_description", "") or "").strip()
    if not description:
        description = _description_from_row(row)
    content = (_row_value(row, "content", "") or "").strip()
    availability_status = (
        _row_value(row, "catalog_availability_status")
        or _content_field(content, "availability_status")
    )
    return Product(
        id=row["id"],
        title=_row_value(row, "catalog_title") or row["title"],
        url=_row_value(row, "catalog_url") or row["url"],
        category=_row_value(row, "catalog_category"),
        description=description,
        price=_decimal_value(_row_value(row, "catalog_price")),
        currency=_row_value(row, "catalog_currency") or "RUR",
        available=(availability_status != "Нет в наличии") and bool(_row_value(row, "enabled", 1)),
        availability_status=availability_status,
        material=(
            _row_value(row, "catalog_material")
            or _content_field(content, "material")
        ),
        image_url=(
            _row_value(row, "catalog_image_url")
            or _content_field(content, "image_url")
        ),
        metadata={
            **_metadata_from_row(row),
            "catalog_synced_at": _row_value(row, "catalog_synced_at"),
            "catalog_source_hash": _row_value(row, "catalog_source_hash"),
        },
    )


def _row_to_tour(row: sqlite3.Row) -> Tour:
    description = _description_from_row(row)
    content = (_row_value(row, "content", "") or "").strip()
    parsed_price = parse_tour_price(content or description)
    metadata = _metadata_from_row(row)
    if parsed_price is not None:
        metadata["price_source_text"] = parsed_price.source_text
        metadata["price_is_from"] = parsed_price.is_from
    return Tour(
        id=row["id"],
        title=row["title"],
        url=row["url"],
        description=description,
        price=parsed_price.amount if parsed_price else None,
        currency=parsed_price.currency if parsed_price else "RUR",
        metadata=metadata,
    )


def _row_to_consultation(row: sqlite3.Row) -> Consultation:
    return Consultation(
        id=row["id"],
        title=row["title"],
        url=row["url"],
        description=_description_from_row(row),
        metadata=_metadata_from_row(row),
    )


class _BaseRepository(Generic[CatalogItem]):
    page_type: str
    mapper = None

    def get_by_id(self, item_id: str) -> CatalogItem | None:
        with get_connection() as connection:
            row = connection.execute(
                '''
                SELECT *
                FROM documents
                WHERE id = ?
                  AND page_type = ?
                LIMIT 1
                ''',
                (item_id, self.page_type),
            ).fetchone()
        return self.mapper(row) if row else None

    def list_all(self, enabled_only: bool = True) -> list[CatalogItem]:
        sql = '''
            SELECT *
            FROM documents
            WHERE page_type = ?
        '''
        params: list[object] = [self.page_type]

        if enabled_only:
            sql += " AND enabled = 1"

        sql += " ORDER BY priority DESC, title ASC"

        with get_connection() as connection:
            rows = connection.execute(sql, params).fetchall()

        return [self.mapper(row) for row in rows]

    def search(
        self,
        query: str,
        limit: int = 20,
        enabled_only: bool = True,
    ) -> list[CatalogItem]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        safe_limit = max(1, min(int(limit), 100))
        search_term = f"%{normalized_query}%"

        sql = '''
            SELECT *
            FROM documents
            WHERE page_type = ?
              AND (
                    title LIKE ? COLLATE NOCASE
                 OR summary LIKE ? COLLATE NOCASE
                 OR content LIKE ? COLLATE NOCASE
              )
        '''
        params: list[object] = [
            self.page_type,
            search_term,
            search_term,
            search_term,
        ]

        if enabled_only:
            sql += " AND enabled = 1"

        sql += " ORDER BY priority DESC, title ASC LIMIT ?"
        params.append(safe_limit)

        with get_connection() as connection:
            rows = connection.execute(sql, params).fetchall()

        return [self.mapper(row) for row in rows]


class ProductRepository(_BaseRepository[Product]):
    page_type = "product"
    mapper = staticmethod(_row_to_product)

    _select = """
        SELECT d.*,
               p.title AS catalog_title,
               p.url AS catalog_url,
               p.category AS catalog_category,
               p.description AS catalog_description,
               p.price AS catalog_price,
               p.currency AS catalog_currency,
               p.image_url AS catalog_image_url,
               p.availability_status AS catalog_availability_status,
               p.material AS catalog_material,
               p.source_hash AS catalog_source_hash,
               p.synced_at AS catalog_synced_at
        FROM documents d
        LEFT JOIN product_catalog_items p ON p.document_id = d.id
    """

    def get_by_id(self, item_id: str) -> Product | None:
        with get_connection() as connection:
            row = connection.execute(
                self._select + " WHERE d.id = ? AND d.page_type = 'product' LIMIT 1",
                (item_id,),
            ).fetchone()
        return self.mapper(row) if row else None

    def list_all(self, enabled_only: bool = True) -> list[Product]:
        sql = self._select + " WHERE d.page_type = 'product'"
        if enabled_only:
            sql += " AND d.enabled = 1"
        sql += " ORDER BY d.priority DESC, d.title ASC"
        with get_connection() as connection:
            rows = connection.execute(sql).fetchall()
        return [self.mapper(row) for row in rows]

    def search(
        self, query: str, limit: int = 20, enabled_only: bool = True
    ) -> list[Product]:
        normalized_query = query.strip()
        if not normalized_query:
            return []
        safe_limit = max(1, min(int(limit), 100))
        term = f"%{normalized_query}%"
        sql = self._select + """
            WHERE d.page_type = 'product'
              AND (
                    d.title LIKE ? COLLATE NOCASE
                 OR d.summary LIKE ? COLLATE NOCASE
                 OR d.content LIKE ? COLLATE NOCASE
                 OR p.title LIKE ? COLLATE NOCASE
                 OR p.description LIKE ? COLLATE NOCASE
              )
        """
        params: list[object] = [term, term, term, term, term]
        if enabled_only:
            sql += " AND d.enabled = 1"
        sql += " ORDER BY d.priority DESC, d.title ASC LIMIT ?"
        params.append(safe_limit)
        with get_connection() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self.mapper(row) for row in rows]


class TourRepository(_BaseRepository[Tour]):
    page_type = "tour"
    mapper = staticmethod(_row_to_tour)


class ConsultationRepository(_BaseRepository[Consultation]):
    page_type = "psychologist"
    mapper = staticmethod(_row_to_consultation)


__all__ = [
    "ProductRepository",
    "TourRepository",
    "ConsultationRepository",
]
