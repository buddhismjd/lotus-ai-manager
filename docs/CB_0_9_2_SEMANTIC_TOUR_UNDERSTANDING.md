# CB-0.9.2 — Semantic Tour Understanding

## Goal

Resolve natural tour requests by meaning before catalog lookup.

The assistant remains within the commercial tour domain and does not offer
practices, books, teachings, or rituals.

## Supported semantics

- travel language such as `возите`, `поехать`, `путешествие` selects tours;
- named aspects such as **Гуру Ринпоче** and **Миларепа** constrain tour search;
- natural time expressions are interpreted only when the user writes them;
- no month, season, trekking, or difficulty questionnaire is imposed.

## Natural time expressions

The first contract includes:

- New Year holidays: 25 December through 10 January;
- May holidays: 28 April through 12 May.

If no published scheduled tour intersects the requested period, the result is
empty. The assistant must not replace it with the complete catalog.

## Query flow

```text
User request
→ commercial domain resolution
→ aspect/place/time extraction
→ structured tour catalog
→ all matching scheduled tours
→ sales response
```
