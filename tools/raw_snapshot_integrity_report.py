from __future__ import annotations

from backend.catalog.integrity.raw_snapshot_comparator import (
    inspect_snapshot_integrity,
    summarize_lost_paths,
)


def main() -> int:
    report = inspect_snapshot_integrity()
    checked = report.checked
    average = (
        sum(item.integrity_percent for item in report.comparisons) / checked
        if checked else 0.0
    )
    print("AI BODHI CAT-003.1 RAW SNAPSHOT INTEGRITY REPORT")
    print(f"Checked snapshots: {checked}")
    print(f"Identical to current page: {report.identical}/{checked}")
    print(f"Changed since capture: {report.changed}/{checked}")
    print(f"Average integrity: {average:.2f}%")
    print(f"Errors: {len(report.errors)}")
    print("Source kinds:")
    kinds: dict[str, int] = {}
    for item in report.comparisons:
        key = item.source_kind or "unknown"
        kinds[key] = kinds.get(key, 0) + 1
    for key, count in sorted(kinds.items()):
        print(f"- {key}: {count}")
    print("Lost fields:")
    lost = summarize_lost_paths(report.comparisons)
    if not lost:
        print("- none")
    else:
        for path, count in list(lost.items())[:50]:
            print(f"- {path}: {count}")
    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
