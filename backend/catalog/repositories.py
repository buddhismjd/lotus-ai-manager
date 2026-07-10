from __future__ import annotations

import sqlite3
from typing import Generic, TypeVar

from backend.catalog.models import Consultation, Product, Tour
from backend.storage.database import get_connection


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


def _row_to_product(row: sqlite3.Row) -> Product:
    return Product(
        id=row["id"],
        title=row["title"],
        url=row["url"],
        description=_description_from_row(row),
        available=bool(_row_value(row, "enabled", 1)),
        metadata=_metadata_from_row(row),
    )


def _row_to_tour(row: sqlite3.Row) -> Tour:
    return Tour(
        id=row["id"],
        title=row["title"],
        url=row["url"],
        description=_description_from_row(row),
        metadata=_metadata_from_row(row),
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
