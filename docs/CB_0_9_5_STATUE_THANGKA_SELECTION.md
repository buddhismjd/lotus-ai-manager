# CB-0.9.5 — Statue & Thangka Personal Selection

## Purpose

This stage adds a commercial selection workflow for statues and thangkas without expanding AI Bodhi beyond products, tours, and psychologist-buddhologist consultations.

## Product selection

Natural queries may contain:

- product category: statue or thangka;
- Buddhist aspect, such as Chenrezig or White Tara;
- exact height, for example `18 cm`;
- height range, for example `15–20 cm`;
- approximate height, for example `about 20 cm`.

The service returns all catalog products satisfying the requested category, aspect, and height. It does not return a random single card and does not use width as statue height when an explicit height is available.

## Collection pages

Collection page labels and URLs are stored in:

`backend/config/product_collection_pages.json`

The mapping is data-driven rather than implemented with category-specific branching.

## Artisan availability

For statues and thangkas, AI Bodhi explains that the published catalog may not reflect everything currently available from masters. The assistant may offer to request an up-to-date personal selection.

The workflow collects:

1. Telegram or WhatsApp;
2. social contact value;
3. email.

The saved request includes category, aspect, requested height range, consent text, and conversation context.

AI Bodhi must not promise availability or invent product characteristics before confirmation from masters.
