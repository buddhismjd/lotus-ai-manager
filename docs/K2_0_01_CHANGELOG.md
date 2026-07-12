# K2.0-01 — Unified Knowledge Graph Contract

## Added

- read-only `KnowledgeGraphContract` protocol;
- Knowledge 2.0 domain names `KnowledgeAspect`, `AspectType`, `AspectRelation`;
- deterministic `GraphNeighborhood` traversal result;
- compatibility methods on the existing repository without duplicated state;
- contract regression tests;
- diagnostic, smoke and report tools;
- architecture decision and contract documentation.

## Compatibility

No persisted JSON format, loader or existing public method was removed. Existing
Semantic Engine and Runtime Graph behavior remains unchanged.

## Verification baseline

- full regression: 189 passed;
- unresolved relation endpoints: 0;
- runtime graph: 221 aspects, 54 relations.
