# Unified Catalog Contract

## Purpose

The Unified Catalog Contract gives AI Bodhi one read-only commercial catalog
for three supported directions only:

1. products;
2. tours;
3. psychologist-buddhologist consultations.

The contract is intentionally closed. Practices, books, teachings, rituals and
other non-catalog knowledge cannot be returned as catalog items or sales
recommendations.

## Contract

`CatalogItem` contains common fields:

- `id`;
- `item_type`;
- `title`;
- `url`;
- `summary`;
- `status`;
- `tags`;
- `price` and `currency`;
- type-specific `attributes`.

Allowed values of `item_type` are:

- `product`;
- `tour`;
- `psychologist_service`.

`UnifiedCatalogRepository` adapts the existing Product, Structured Tour and
Consultation repositories. Existing repositories remain the source of truth.
No catalog data is duplicated.

## Recommendation boundary

Recommendation candidates are always selected from the same supported
commercial type. A product can recommend other real products; a tour can
recommend other tours; a consultation can recommend consultation options.
The contract cannot produce practices, books or teachings as recommendations.
