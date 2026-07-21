from __future__ import annotations

import argparse
from pathlib import Path

from backend.integrations.tilda_script_inspector import inspect_script_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect inline Tilda JavaScript without executing it or modifying the catalog."
    )
    parser.add_argument("url", help="Published Tilda product page URL")
    parser.add_argument("--output", default="data/tilda_script_inspections")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)
    bundle = inspect_script_url(args.url, args.output, args.timeout)
    print("=" * 78)
    print("AI BODHI TILDA SCRIPT INSPECTOR")
    print("=" * 78)
    print(f"Inspection bundle: {bundle.resolve()}")
    print(f"Text report:       {(bundle / 'script_inspection.txt').resolve()}")
    print(f"JSON report:       {(bundle / 'script_inspection.json').resolve()}")
    print(f"Raw scripts:       {(bundle / 'scripts').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
