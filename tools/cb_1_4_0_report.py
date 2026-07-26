from __future__ import annotations


def main() -> int:
    print("CB-1.4.0 — Tilda Knowledge Synchronization")
    print("source=https://svet-lotosa.tilda.ws/")
    print("mode=incremental Tilda mirror")
    print("change_detection=page metadata and semantic content hashes")
    print("failure_policy=retain last successful page")
    print("write_policy=atomic knowledge.json replacement")
    print("database=incremental documents and chunks update")
    print("journal=tilda_sync_runs")
    print("manual_command=python tools\\sync_tilda.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
