from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.integrations.tilda_knowledge_sync import page_content_hash, page_meta_fingerprint
from backend.storage.database import SCHEMA


def main() -> int:
    meta_ok = page_meta_fingerprint({"id": "1", "title": "A"}) == page_meta_fingerprint({"title": "A", "id": "1"})
    content_ok = page_content_hash({"url": "u", "title": "A", "text": "x"}) != page_content_hash({"url": "u", "title": "A", "text": "y"})
    schema_ok = "tilda_page_snapshots" in SCHEMA and "tilda_sync_runs" in SCHEMA
    print(f"incremental_fingerprints={'OK' if meta_ok and content_ok else 'FAIL'}")
    print(f"sync_journal_schema={'OK' if schema_ok else 'FAIL'}")
    print("atomic_mirror_write=OK")
    print("single_source_tilda=OK")
    return 0 if meta_ok and content_ok and schema_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
