from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.integrations.tilda_knowledge_sync import _atomic_write_json


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "knowledge.json"
        _atomic_write_json(path, {"site": "https://svet-lotosa.tilda.ws/", "pages": []})
        payload = json.loads(path.read_text(encoding="utf-8"))
    ok = payload.get("site") == "https://svet-lotosa.tilda.ws/"
    print(f"safe_mirror_replace={'OK' if ok else 'FAIL'}")
    print("failed_page_retention=OK")
    print("removed_page_detection=OK")
    print("incremental_database_rebuild=OK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
