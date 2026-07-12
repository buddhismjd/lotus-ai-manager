# UCC-1 Changelog

## Added

- Unified commercial `CatalogItem` contract.
- Closed `CatalogItemType` set.
- Unified read-only repository over products, tours and consultations.
- Boundary-safe recommendation candidates.
- Regression tests, diagnostics, smoke and report tools.

## Compatibility

Existing Product, Tour, Consultation and Structured Tour models are preserved.
The new layer is additive and delegates to existing repositories.
