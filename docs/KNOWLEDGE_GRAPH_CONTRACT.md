# AI Bodhi Knowledge 2.0 — Unified Knowledge Graph Contract

## Goal

The Graph Contract is the stable read-only boundary between Semantic Engine,
Bodhi Service and any graph storage implementation.

## Compatibility strategy

Existing persisted names (`KnowledgeEntity`, `EntityType`) remain supported.
Knowledge 2.0 introduces domain aliases (`KnowledgeAspect`, `AspectType`) and a
protocol instead of duplicating graph data or replacing loaders in one step.

## Contract operations

- resolve one aspect by canonical id;
- list and filter aspects by type;
- resolve aspects by canonical name or alias;
- read typed incoming and outgoing relations;
- obtain a deterministic one-hop neighborhood.

## Migration rule

New consumers depend on `KnowledgeGraphContract`. Existing consumers may keep
using the legacy repository methods until their own isolated migration stage.
Both APIs operate on the same repository and the same graph data.
