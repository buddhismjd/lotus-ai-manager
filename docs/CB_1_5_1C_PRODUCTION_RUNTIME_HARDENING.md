# CB-1.5.1C — Production Runtime Hardening

This stage hardens the public runtime boundary without changing catalogue, knowledge, dialogue, handoff or widget behaviour.

## Runtime controls

- CORS uses an explicit environment-controlled allowlist.
- SQLite connections enable WAL and a configurable busy timeout.
- Public sales chat and reset endpoints have per-IP rate limits.
- Administrative pages require `X-Admin-Token` or the `admin_token` query parameter.
- Knowledge rebuilding is a protected `POST /admin/rebuild` operation.
- Security events are appended as JSON Lines to `logs/security.jsonl` by default.

For production, set a long random `ADMIN_TOKEN`, disable localhost CORS, and retain only the real public site origins.
