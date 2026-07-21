# CB-0.9.9 — Tilda Discovery 2.0

## Goal

Prevent product catalog synchronization from silently finishing with zero store blocks when the published Tilda page no longer exposes store identifiers in its HTML.

## Architecture

Discovery now combines two independent sources:

1. Dynamic identifiers extracted from the current published shop HTML.
2. Versioned configured store identifiers used as a safe operational fallback.

HTML data has higher precedence. The fallback is not test-specific logic: it is an explicit source configuration for the commercial site and can contain multiple sites and multiple store blocks.

## Diagnostics

The synchronizer reports whether HTML was loaded, how many candidates were found dynamically, how many came from configuration, which blocks were queried, how many products were received, and the exact error for every failed block.

A zero-result run is no longer silent: the report identifies whether discovery or the Store API failed.
