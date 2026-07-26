from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    print("CB-1.0.2 — LeadRepository & Database Integration")
    print("repository_owner=backend.storage.repositories")
    print("migration_mode=idempotent")
    print("legacy_import=compatible")
    print("structured_handoff_fields=7")


if __name__ == "__main__":
    main()
