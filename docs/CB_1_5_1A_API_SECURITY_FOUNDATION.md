# CB-1.5.1A — API Security Foundation

This stage hardens the public sales API input boundary without changing the
sales assistant's internal dialogue behavior.

## Contracts

- `/api/sales/chat` accepts only `message` and `session_id`.
- `/api/sales/reset` accepts only `session_id`.
- `message` is trimmed and limited to 4000 characters.
- `session_id` is limited to 128 characters and may contain Latin letters,
  digits, `.`, `_`, `:`, and `-`.
- Unknown fields and malformed values return HTTP 422 using a stable safe JSON
  error format.
- Empty messages remain a normal `sales_empty` response for compatibility with
  the current widget and existing dialogue tests.

Session ownership tokens, rate limiting, CORS restrictions, and admin
protection are intentionally reserved for the following hardening stages.
