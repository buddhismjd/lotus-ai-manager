# Knowledge Migration Plan

## Goal

Move public knowledge answers from the legacy layer to the typed Knowledge
Graph without breaking existing behaviour.

## Current state

```text
backend/knowledge
    ├── aspect_registry
    ├── graph
    ├── answering
    └── knowledge_core

backend/knowledge_graph
    ├── typed models
    ├── repository
    ├── loader
    ├── validator
    └── runtime graph
```

## Migration stages

### Stage 1 — canonical IDs

All aspect wording resolves through Aspect Registry.

### Stage 2 — typed nodes

Every stable aspect, teacher, place, country, practice and practice item
exists as a typed graph node.

### Stage 3 — product and tour adapters

Runtime graph links repository objects to typed nodes.

### Stage 4 — answer parity

For each legacy answer scenario, add an equivalent typed-graph test.

### Stage 5 — orchestrator switch

Switch one intent at a time to the typed graph.

### Stage 6 — deprecation

Mark legacy APIs deprecated only after full parity.

### Stage 7 — removal

Remove legacy code only when:

- no production imports remain;
- no tests depend on it;
- reports and tools use the typed graph;
- release notes document the migration.

## Non-goals

Do not perform a big-bang rewrite.
