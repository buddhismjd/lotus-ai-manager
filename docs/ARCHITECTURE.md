# Architecture

## Data flow

```text
External source
    │
    ▼
Integration
    │
    ▼
Repository
    │
    ▼
Structured profile
    │
    ▼
Registry / Graph / Router
    │
    ▼
Bodhi Orchestrator
    │
    ▼
BuiltResponse
    │
    ▼
FastAPI / Widget
```

## Layer responsibilities

### Integration layer

Reads external data and converts it into internal repository records.

It must not contain final user-response logic.

### Repository layer

Stores and retrieves products, tours, messages, leads and settings.

### Intelligence layer

Converts raw records into structured profiles.

Examples:

- type;
- aspect;
- material;
- use;
- country;
- destination;
- practice;
- duration;
- altitude.

### Registry layer

Normalizes wording to canonical IDs.

Example:

```text
Белой Таре
→ white_tara
→ Белая Тара
```

### Knowledge layer

Stores stable facts and typed relations.

### Runtime graph

Combines stable graph data with current products and tours.

### Routing layer

Determines which business domain owns the question.

### Semantic layer

Handles unresolved knowledge-style questions only.

### Orchestrator

Preserves priority and prevents regressions.

## Core invariant

```text
Product/Tour/Planned/Aspect/Legacy Knowledge
before
Semantic fallback
```
