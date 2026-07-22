# CB-0.9.12 — Intelligent tour and product collections

## Goal

Ensure country requests return only tours for the requested country, while exact product selection immediately returns every matching product as a complete UI card.

## Architecture

- Country collection intent is resolved before generic product routing when the country itself is explicitly named.
- Destination requests such as `Кайлас` remain exact-tour requests and do not become country collections.
- `build_product_items()` is the shared product-to-card adapter used by both semantic product collections and exact statue/thangka selections.
- The dialogue decorator preserves structured `items` instead of dropping them.

## UI contract

Each product card may contain:

- image URL;
- title;
- product URL;
- price;
- availability;
- material;
- size.

No artificial result limit is applied to exact product selection.

## Verification

```bat
python -m pytest -q
python -m tools.cb_0_9_12_diagnostics
python -m tools.cb_0_9_12_smoke
python -m tools.cb_0_9_12_report
```
