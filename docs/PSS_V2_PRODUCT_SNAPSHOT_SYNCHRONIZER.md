# Product Snapshot Synchronizer v2

## Purpose

The synchronizer captures the confirmed `var product = {...}` object published
on every Tilda product page. It separates raw capture, normalization, storage,
and sales use.

## Confirmed fields

- uid
- title and description
- brand
- SKU
- price
- gallery and primary image
- raw quantity
- characteristics and properties
- partuids
- URL

## Deliberately unconfirmed

Category, material, dimensions, and customer-facing availability are not
derived until a separate authoritative source is proven. In particular,
`quantity=0` is stored as raw data and is not automatically translated into
a customer-facing status.

## Storage

`product_raw_snapshots` preserves source JSON and hashes.
`product_snapshot_items` stores normalized values for downstream consumers.
