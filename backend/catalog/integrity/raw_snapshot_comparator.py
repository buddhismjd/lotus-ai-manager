from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from backend.integrations.product_raw_snapshot import load_raw_snapshot
from backend.storage.database import get_connection, initialize_database


_MISSING = object()


def _path_join(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Return deterministic leaf/container paths for structural comparison."""
    result: dict[str, Any] = {}

    if isinstance(value, dict):
        result[prefix or "$root"] = {"type": "object", "size": len(value)}
        for key in sorted(value):
            result.update(_flatten(value[key], _path_join(prefix, str(key))))
        return result

    if isinstance(value, list):
        result[prefix or "$root"] = {"type": "array", "size": len(value)}
        for index, item in enumerate(value):
            result.update(_flatten(item, f"{prefix}[{index}]"))
        return result

    result[prefix or "$root"] = value
    return result


@dataclass(frozen=True, slots=True)
class FieldDifference:
    path: str
    page_value: Any
    stored_value: Any
    kind: str


@dataclass(frozen=True, slots=True)
class ProductSnapshotComparison:
    product_uid: str
    page_url: str
    page_fields: int
    stored_fields: int
    matching_fields: int
    integrity_percent: float
    differences: tuple[FieldDifference, ...]
    page_snapshot_sha256: str
    stored_snapshot_sha256: str
    source_kind: str | None
    extractor_version: str | None

    @property
    def is_identical(self) -> bool:
        return not self.differences


@dataclass(frozen=True, slots=True)
class SnapshotIntegrityError:
    product_uid: str
    page_url: str
    error: str


@dataclass(frozen=True, slots=True)
class SnapshotIntegrityReport:
    checked: int
    identical: int
    changed: int
    errors: tuple[SnapshotIntegrityError, ...]
    comparisons: tuple[ProductSnapshotComparison, ...]

    @property
    def success(self) -> bool:
        return self.checked > 0 and not self.errors


def compare_product_objects(
    *,
    product_uid: str,
    page_url: str,
    page_data: dict[str, Any],
    stored_data: dict[str, Any],
    page_snapshot_sha256: str = "",
    stored_snapshot_sha256: str = "",
    source_kind: str | None = None,
    extractor_version: str | None = None,
) -> ProductSnapshotComparison:
    page_fields = _flatten(page_data)
    stored_fields = _flatten(stored_data)
    paths = sorted(set(page_fields) | set(stored_fields))
    differences: list[FieldDifference] = []
    matching = 0

    for path in paths:
        page_value = page_fields.get(path, _MISSING)
        stored_value = stored_fields.get(path, _MISSING)
        if page_value is _MISSING:
            differences.append(FieldDifference(path, None, stored_value, "stored_only"))
        elif stored_value is _MISSING:
            differences.append(FieldDifference(path, page_value, None, "lost_from_snapshot"))
        elif page_value != stored_value:
            differences.append(FieldDifference(path, page_value, stored_value, "value_changed"))
        else:
            matching += 1

    total_page = len(page_fields)
    integrity = 100.0 if total_page == 0 else round(matching / total_page * 100, 2)
    return ProductSnapshotComparison(
        product_uid=product_uid,
        page_url=page_url,
        page_fields=total_page,
        stored_fields=len(stored_fields),
        matching_fields=matching,
        integrity_percent=integrity,
        differences=tuple(differences),
        page_snapshot_sha256=page_snapshot_sha256,
        stored_snapshot_sha256=stored_snapshot_sha256,
        source_kind=source_kind,
        extractor_version=extractor_version,
    )


def _load_stored_row(product_uid: str) -> dict[str, Any]:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT product_uid, page_url, raw_json, snapshot_sha256,
                   source_kind, extractor_version
            FROM product_raw_snapshots
            WHERE product_uid = ?
            """,
            (product_uid,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Raw snapshot для товара {product_uid} не найден")
    return dict(row)


def compare_stored_snapshot(
    product_uid: str,
    *,
    loader: Callable[[str], Any] = load_raw_snapshot,
) -> ProductSnapshotComparison:
    row = _load_stored_row(product_uid)
    stored_data = json.loads(row["raw_json"])
    page_snapshot = loader(row["page_url"])
    return compare_product_objects(
        product_uid=product_uid,
        page_url=row["page_url"],
        page_data=page_snapshot.product_data,
        stored_data=stored_data,
        page_snapshot_sha256=page_snapshot.snapshot_sha256,
        stored_snapshot_sha256=row["snapshot_sha256"],
        source_kind=row.get("source_kind"),
        extractor_version=row.get("extractor_version"),
    )


def inspect_snapshot_integrity(
    *,
    limit: int | None = None,
    loader: Callable[[str], Any] = load_raw_snapshot,
) -> SnapshotIntegrityReport:
    initialize_database()
    query = "SELECT product_uid, page_url FROM product_raw_snapshots ORDER BY product_uid"
    params: tuple[Any, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (max(0, int(limit)),)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    comparisons: list[ProductSnapshotComparison] = []
    errors: list[SnapshotIntegrityError] = []
    for row in rows:
        try:
            comparisons.append(compare_stored_snapshot(row["product_uid"], loader=loader))
        except Exception as exc:
            errors.append(
                SnapshotIntegrityError(
                    product_uid=row["product_uid"],
                    page_url=row["page_url"],
                    error=str(exc),
                )
            )

    identical = sum(1 for item in comparisons if item.is_identical)
    return SnapshotIntegrityReport(
        checked=len(comparisons),
        identical=identical,
        changed=len(comparisons) - identical,
        errors=tuple(errors),
        comparisons=tuple(comparisons),
    )


def summarize_lost_paths(comparisons: Iterable[ProductSnapshotComparison]) -> dict[str, int]:
    result: dict[str, int] = {}
    for comparison in comparisons:
        for difference in comparison.differences:
            if difference.kind == "lost_from_snapshot":
                result[difference.path] = result.get(difference.path, 0) + 1
    return dict(sorted(result.items(), key=lambda item: (-item[1], item[0])))


__all__ = [
    "FieldDifference",
    "ProductSnapshotComparison",
    "SnapshotIntegrityError",
    "SnapshotIntegrityReport",
    "compare_product_objects",
    "compare_stored_snapshot",
    "inspect_snapshot_integrity",
    "summarize_lost_paths",
]
