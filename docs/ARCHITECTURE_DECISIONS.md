# Architecture Decisions

## ADR-001 — Semantic Engine is a fallback

Business handlers have priority.

## ADR-002 — Aspect Registry owns canonical wording

Russian case forms and aliases resolve through the registry.

## ADR-003 — Legacy and typed graph coexist temporarily

Migration is incremental.

## ADR-004 — Runtime graph does not overwrite stable JSON

Current products and tours are attached at runtime.

## ADR-005 — Aspect type differs from product type

White Tara remains a Bodhisattva whether represented as a statue or
thangka.

## ADR-006 — Vajra and Phurba are practice items

They are not classified as abstract symbols.

## ADR-007 — No test-specific hacks

Tests document domain rules; code must remain general.

## ADR-008 — Small architecture stages

Each stage requires architecture, code, tests, diagnostics, smoke and Git.

## ADR-005: Additive Knowledge Graph Contract

Knowledge 2.0 introduces `KnowledgeGraphContract` as a read-only protocol and
uses aspect-oriented domain aliases over the existing persisted graph models.
The repository implements both legacy and Knowledge 2.0 methods against one
storage collection. This avoids a flag-day migration and prevents duplicated
graph state.
