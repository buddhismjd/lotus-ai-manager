from __future__ import annotations

from backend.integrations.tilda_knowledge_sync import synchronize_tilda_project


def main() -> int:
    print("AI Bodhi Tilda Knowledge Sync")
    print("=" * 70)
    result = synchronize_tilda_project()
    summary = result.as_dict()
    for key in (
        "status", "pages_count", "chunks_count", "added_count", "changed_count",
        "unchanged_count", "removed_count", "retained_after_error_count",
    ):
        print(f"{key}: {summary[key]}")
    return 0 if result.status in {"completed", "completed_with_errors"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
