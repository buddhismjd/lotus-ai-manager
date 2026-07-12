# Repository Baseline — K2.0-00.5

## Goal

Create a clean, reproducible Git baseline before AI Bodhi Knowledge 2.0.

## Included

- repository hygiene rules;
- pytest discovery configuration;
- repository health diagnostic and regression tests;
- architecture/developer documentation index;
- operational synchronization launchers;
- terminology correction in product profile tests.

## Excluded

- generated `data/` and root `knowledge/`;
- Python caches;
- temporary patch/install files;
- wildcard CORS configuration in `backend/main.py`;
- obsolete stage-specific installation notes.

## Invariant

One archive represents one architectural stage and one Git commit.
