from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.integrations.tilda_knowledge_sync import synchronize_tilda_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize AI Bodhi with Svet Lotosa Tilda site")
    parser.add_argument("--force", action="store_true", help="Download every Tilda page")
    args = parser.parse_args()
    result = synchronize_tilda_project(force=args.force)
    print("CB-1.4.0 — Tilda Knowledge Synchronization")
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status in {"completed", "completed_with_errors"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
