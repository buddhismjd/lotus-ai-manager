from __future__ import annotations

import argparse
from pathlib import Path

from backend.integrations.tilda_script_inspector import inspect_script_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", default="data/tilda_script_inspections")
    args = parser.parse_args(argv)
    bundle = inspect_script_url(args.url, args.output)
    print((bundle / "script_inspection.txt").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
