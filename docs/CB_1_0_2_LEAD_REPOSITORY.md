# CB-1.0.2 — LeadRepository & Database Integration

## Goal

Move lead persistence into the storage repository layer and extend the existing
SQLite `leads` table for structured manager handoff without losing legacy data.

## Architecture

- `backend.storage.repositories.LeadRepository` owns lead database access.
- `backend.sales_assistant.leads` remains a compatibility import.
- `initialize_database()` performs an idempotent additive migration.
- Existing lead capture and artisan-selection workflows remain supported.
- Structured handoff persistence stores channel, contact value, session,
  reason, priority and deterministic manager summary.

## Migration safety

The migration adds nullable columns and backfills legacy rows from the existing
`telegram`, `phone`, `email`, `created_at` fields. It does not delete or rename
legacy columns.

## Verification

```bat
python -m pytest -q
python tools\cb_1_0_2_diagnostics.py
python tools\cb_1_0_2_smoke.py
python tools\cb_1_0_2_report.py
```
