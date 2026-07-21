# CB-0.9.1 — Natural Tour Discovery

AI Bodhi shows tours according to the user's natural request and does not force a questionnaire.

## Product rules

- `Какие туры есть?` returns every published tour with known dates.
- A named direction such as Nepal returns every matching scheduled tour.
- A named place such as Kailas returns every matching scheduled tour.
- Results are not truncated to the first three or five items.
- Programs without dates are not mixed into the published-tour list.
- AI Bodhi does not ask about month, season, trekking, or route difficulty.
- Conditions are applied only when the user explicitly includes them in the request.

## Architecture

`TourDiscoveryQuery` extracts explicit destination conditions. `StructuredTourRepository.search()` applies those conditions to the structured catalog. The formatter renders the full result set in compact cards.
