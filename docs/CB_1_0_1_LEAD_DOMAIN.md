# CB-1.0.1 — Lead Domain Contract

This stage introduces the domain contract for manager handoff without changing the
existing dialogue flow or SQLite schema.

## Added modules

- `handoff.py`: structured handoff reason and decision.
- `lead_validator.py`: mandatory name, Telegram/MAX contact and email validation.
- `lead_summary.py`: deterministic manager-facing summary.

## Architectural boundary

The modules contain no SQL, no HTTP code and no dialogue routing. Integration with
the existing `LeadRepository`, `DialogueState` and `SalesAssistant` is deferred to
the next stages so the change remains regression-safe.
