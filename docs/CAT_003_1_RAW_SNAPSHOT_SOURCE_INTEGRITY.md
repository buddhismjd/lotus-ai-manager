# CAT-003.1 — Raw Snapshot Source Integrity

## Goal

Prove that `product_raw_snapshots.raw_json` preserves the complete Tilda
`var product = {...}` object and identify whether a field was lost during
capture or whether the published page changed after the snapshot was stored.

## Architecture

The integrity layer compares two independent values:

1. the current `product` object extracted from the published product page;
2. the stored raw JSON for the same `product_uid`.

The comparison is recursive and schema-independent. Unknown future fields are
therefore covered automatically and are not removed by a whitelist.

## Source metadata

Each new raw snapshot records:

- `source_kind = product_page_script`;
- `extractor_version = 2.1`;
- source page URL;
- HTML SHA-256;
- normalized product-object SHA-256;
- capture timestamp.

Existing databases are upgraded additively during `initialize_database()`.

## Difference kinds

- `lost_from_snapshot`: present on the current page, absent in storage;
- `stored_only`: present in storage, absent on the current page;
- `value_changed`: present in both but changed since capture.

A changed value is not automatically a capture defect. It may represent a
legitimate catalog update between snapshot time and integrity inspection.

## Operation

```powershell
.\RUN_RAW_SNAPSHOT_INTEGRITY.bat
```

The command performs read-only comparison. It does not overwrite snapshots or
normalized catalog records.
