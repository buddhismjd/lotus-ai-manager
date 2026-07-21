# CB-0.9.8 — Verified Product Catalog Synchronization

## Goal

Use the published Tilda product page as the authoritative commercial source for images, stock status, material and price.

## Source precedence

1. Product page JSON-LD Product/Offer data.
2. Product page Open Graph image and visible published status.
3. Tilda Store API only for values absent from the published page.

The synchronizer never converts document availability into product stock and never invents a status.

## Persistence

Verified commercial fields are stored in `product_catalog_items`. The existing `documents` table remains the searchable knowledge layer. `ProductRepository` joins both layers so current search and selection mechanisms remain compatible.
