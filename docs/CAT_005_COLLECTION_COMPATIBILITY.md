# CAT-005 — Collection Compatibility Layer

## Purpose

Preserve the new product and country collection UX without allowing collection
responses to replace exact tour details, price, date, dialogue state, or legacy
Bodhi responses.

## Routing rule

A country collection is built only for a broad request that explicitly names a
country and asks whether journeys are available. Destination requests such as
"Кайлас" remain exact-tour requests and continue through the established Bodhi
response pipeline.

Tour price and date strategies always take precedence over collection output.

## Verification

```cmd
python -m pytest tests\test_collection_compatibility_layer.py tests\test_sales_assistant.py tests\test_sales_dialogue_manager.py tests\test_catalog_collection_builder.py
python -m tools.catalog_compatibility_report
```
