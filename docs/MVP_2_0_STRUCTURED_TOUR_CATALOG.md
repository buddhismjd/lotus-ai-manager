# MVP-2.0 — Structured Tour Catalog Foundation

## Goal

The sales assistant must answer tour-list questions from structured catalog facts rather than raw page-text matching.

## Architecture

```text
Tilda documents
    ↓
TourRepository
    ↓
Tour Intelligence profile
    ↓
StructuredTour builder
    ↓
StructuredTourRepository
    ↓
Sales Conversation Strategy
    ↓
Sales Response Formatter
```

The layer is additive. Existing `Tour`, `TourProfile`, `TourRepository`, Semantic Engine, and Bodhi Service remain available.

## Contract

`StructuredTour` combines:

- published title and URL;
- parsed schedule without inventing a missing year;
- duration;
- countries, regions, destinations, aspects, practices, and teachers from Tour Intelligence;
- price and status when available;
- source metadata.

`StructuredProduct` and `StructuredService` establish compatible contracts for later catalog stages, but this stage switches only tour-list queries.

## Truthfulness

A year is never inferred when it is absent from the source page. Unknown price, dates, and fields remain empty.
