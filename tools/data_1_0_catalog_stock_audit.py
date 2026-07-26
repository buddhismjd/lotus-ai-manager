from __future__ import annotations

import argparse
import sys
import csv
import json
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import DATABASE_FILE
from backend.integrations.product_stock_status import resolve_stock_status


@dataclass(frozen=True, slots=True)
class AuditRow:
    product_uid: str
    title: str
    url: str
    raw_quantity: str | None
    raw_explicit_status: str | None
    snapshot_status: str | None
    catalog_status: str | None
    expected_status: str | None
    result: str


def _raw_fields(raw_json: str | None) -> tuple[str | None, str | None]:
    if not raw_json:
        return None, None
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return None, None
    quantity = data.get("quantity")
    explicit = data.get("availability_status") or data.get("availability") or data.get("stock_status")
    return (None if quantity is None else str(quantity), None if explicit is None else str(explicit))


def build_audit_rows(db_path: Path) -> list[AuditRow]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT c.product_uid, c.title, c.url,
               c.availability_status AS catalog_status,
               s.availability_status AS snapshot_status,
               s.quantity AS snapshot_quantity,
               r.raw_json
        FROM product_catalog_items c
        LEFT JOIN product_snapshot_items s ON s.product_uid = c.product_uid
        LEFT JOIN product_raw_snapshots r ON r.product_uid = c.product_uid
        ORDER BY c.title COLLATE NOCASE
        """
    ).fetchall()
    result: list[AuditRow] = []
    for row in rows:
        raw_quantity, raw_explicit = _raw_fields(row["raw_json"])
        quantity = raw_quantity if raw_quantity is not None else row["snapshot_quantity"]
        expected = resolve_stock_status(explicit_status=raw_explicit, quantity=quantity)
        actual = row["catalog_status"]
        status = "OK" if expected == actual else "MISMATCH"
        result.append(AuditRow(
            product_uid=row["product_uid"], title=row["title"], url=row["url"],
            raw_quantity=quantity, raw_explicit_status=raw_explicit,
            snapshot_status=row["snapshot_status"], catalog_status=actual,
            expected_status=expected, result=status,
        ))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit product stock truth across AI Bodhi data layers")
    parser.add_argument("--db", type=Path, default=Path(DATABASE_FILE))
    parser.add_argument("--csv", type=Path, default=Path("data/reports/data_1_0_stock_audit.csv"))
    args = parser.parse_args()
    rows = build_audit_rows(args.db)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()) if rows else [f.name for f in AuditRow.__dataclass_fields__.values()])
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    mismatches = [row for row in rows if row.result != "OK"]
    print("=" * 72)
    print("AI BODHI DATA-1.0 PRODUCT STOCK AUDIT")
    print("=" * 72)
    print(f"Products checked: {len(rows)}")
    print(f"Mismatches:       {len(mismatches)}")
    print(f"CSV report:       {args.csv}")
    for row in mismatches[:20]:
        print(f"- {row.title}: quantity={row.raw_quantity!r}, catalog={row.catalog_status!r}, expected={row.expected_status!r}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
