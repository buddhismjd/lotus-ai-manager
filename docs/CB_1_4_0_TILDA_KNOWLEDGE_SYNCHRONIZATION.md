# CB-1.4.0 — Tilda Knowledge Synchronization

AI Bodhi uses one knowledge source: `https://svet-lotosa.tilda.ws/`.

## Guarantees

- New and changed Tilda pages are downloaded and normalized.
- Unchanged pages are reused from the local mirror.
- Removed Tilda pages are removed from the mirror and knowledge database.
- A page that temporarily fails to download remains available from the last successful mirror.
- `data/knowledge.json` is replaced atomically only after a consistent candidate mirror is built.
- SQLite documents and chunks are updated incrementally by semantic content hash.
- Each run is recorded in `tilda_sync_runs`; page fingerprints are stored in `tilda_page_snapshots`.

## Manual synchronization

```bat
python tools\sync_tilda.py
```

Force a full page download:

```bat
python tools\sync_tilda.py --force
```

The existing `.env` must contain `TILDA_PROJECT_ID`, `TILDA_PUBLIC_KEY`, and `TILDA_SECRET_KEY`.
