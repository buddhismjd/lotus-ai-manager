# RDI-1 — Product Page Inspector

## Purpose

`Product Page Inspector` investigates one published Tilda product page without changing the catalog, database, or user-facing chat.

It saves an immutable research bundle:

- `page.html` — raw published HTML;
- `inspection.json` — machine-readable structural inventory;
- `inspection.txt` — human-readable data provenance report.

## Sources inspected

- HTML title, canonical link, language and metadata;
- Open Graph and other meta tags;
- every JSON-LD document, including `Product`, `Offer` and `BreadcrumbList`;
- DOM breadcrumb candidates;
- image sources and lazy-loading attributes;
- visible characteristics and availability labels;
- all `data-*` attributes;
- script inventory, hashes and known Tilda tokens.

## Safety

The inspector is read-only. It does not update SQLite, Knowledge Graph, Product Repository, or synchronized catalog records.

## Run

```powershell
python -m tools.product_page_inspector "https://published-product-url"
```

The generated path is printed at the end. By default bundles are written under:

```text
data/product_page_inspections/
```

## Architectural use

The resulting evidence map is the required input for `Product Snapshot Synchronizer v2`. Production extraction rules must use confirmed sources from an inspection report rather than assumptions about Tilda markup.
