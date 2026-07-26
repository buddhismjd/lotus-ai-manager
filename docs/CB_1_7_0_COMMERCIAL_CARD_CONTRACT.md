# CB-1.7.0 — Commercial Card Contract

AI Bodhi uses chat cards only to identify a commercial offer and open its canonical page on the «Свет Лотоса» site.

## Product card

- image;
- title;
- price;
- availability status;
- `Открыть товар` button.

## Tour card

- image;
- title;
- tour dates;
- price;
- `Открыть тур` button.

Descriptions, material, dimensions and lead-capture buttons are not rendered in commercial cards. Full information remains on the site page.

The public card shape is produced by `backend.catalog.commercial_cards` and is deterministic. Unknown values are represented honestly as `Цена уточняется`, `Наличие уточняется` or `Даты уточняются` rather than invented.
