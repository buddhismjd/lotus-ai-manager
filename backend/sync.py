from __future__ import annotations

import subprocess
import sys
from pathlib import Path


STEPS = (
    ("Tilda API", "backend.integrations.tilda_sync"),
    ("Knowledge Builder", "backend.rag.knowledge_builder"),
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print("AI Bodhi Site Sync")
    print("=" * 70)
    for label, module in STEPS:
        print(f"\n[{label}]")
        result = subprocess.run(
            [sys.executable, "-m", module],
            cwd=root,
            check=False,
        )
        if result.returncode != 0:
            print(f"\nSync stopped: {label} failed with code {result.returncode}.")
            return result.returncode
    print("\n" + "=" * 70)
    print("Sync completed. New, changed and removed site entries are reflected in the database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
