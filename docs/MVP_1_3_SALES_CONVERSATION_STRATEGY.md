# MVP-1.3 — Sales Conversation Strategy Engine

## Goal

Answer according to the user's sales goal instead of applying one response template to every tour question.

## Strategies

- `tour_list` — plural/list requests, optionally filtered by month.
- `tour_details` — a card for one named journey.
- `tour_price` — price-focused follow-up.
- `tour_date` — date-focused follow-up.
- product, service, contacts and fallback strategies remain compatible with the existing sales assistant.

## Architecture

`Dynamic Query Router → Strategy Engine → Repository → Formatter → SalesReply`

The strategy layer does not duplicate catalog search. It decides the response shape and delegates data access to existing repositories.
