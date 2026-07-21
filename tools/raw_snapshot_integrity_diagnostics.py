from __future__ import annotations

import argparse

from backend.catalog.integrity.raw_snapshot_comparator import (
    inspect_snapshot_integrity,
    summarize_lost_paths,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check live Tilda product objects against stored raw snapshots.")
    parser.add_argument("--limit", type=int, default=None, help="Check only the first N snapshots.")
    args = parser.parse_args()

    report = inspect_snapshot_integrity(limit=args.limit)
    print("=" * 72)
    print("AI BODHI CAT-003.1 RAW SNAPSHOT SOURCE INTEGRITY")
    print("=" * 72)
    print(f"Checked:   {report.checked}")
    print(f"Identical: {report.identical}")
    print(f"Changed:   {report.changed}")
    print(f"Errors:    {len(report.errors)}")

    lost = summarize_lost_paths(report.comparisons)
    print("\nLost fields:")
    if not lost:
        print("- none")
    else:
        for path, count in list(lost.items())[:30]:
            print(f"- {path}: {count}")

    print("\nChanged snapshots:")
    changed = [item for item in report.comparisons if not item.is_identical]
    if not changed:
        print("- none")
    else:
        for item in changed[:20]:
            print(
                f"- {item.product_uid}: integrity={item.integrity_percent:.2f}% "
                f"differences={len(item.differences)} url={item.page_url}"
            )

    if report.errors:
        print("\nErrors:")
        for error in report.errors:
            print(f"- {error.product_uid}: {error.error}")

    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
