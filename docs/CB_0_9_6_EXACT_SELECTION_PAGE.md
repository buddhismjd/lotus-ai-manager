# CB-0.9.6 — Exact Product Selection Page

AI Bodhi no longer prints dozens of matching statues or thangkas inside the chat.
For a structured request, the chat returns one button that opens a dedicated page.
The page repeats the exact selection criteria and lists only matching products.

Supported criteria:

- category: statue or thangka;
- Buddhist aspect/name;
- exact height;
- height range;
- approximate height as normalized by the existing parser.

The page is generated from the product repository at request time and does not
create a second catalog or copy product data.
