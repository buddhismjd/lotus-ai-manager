# AI Bodhi

AI Bodhi is the intelligent assistant platform for the **Svet Lotosa**
website. It combines structured product and tour data, a canonical aspect
registry, a typed knowledge graph, semantic search and a guarded answer
orchestrator.

The system is designed to answer only from project-owned knowledge and to
fall back safely when reliable data is unavailable.

## Current status

The active development branch is:

```text
feature/structured-catalog
```

Implemented foundations include:

- product and tour repositories;
- Product Intelligence and Tour Intelligence;
- Product Profiles and Tour Profiles;
- Dynamic Query Router;
- canonical Aspect Registry;
- legacy Knowledge Answer layer;
- typed Knowledge Graph;
- Runtime Knowledge Graph;
- Semantic Engine;
- Semantic Adapter v2;
- ordered Bodhi Orchestrator;
- planned tours;
- FastAPI API;
- Tilda widget;
- diagnostics, benchmarks, smoke tests and reports.

## Quick start on Windows 11

Requirements:

- Python 3.12;
- Windows 11;
- local SQLite database;
- no Docker required.

```cmd
setup.bat
run.bat
```

Then open:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/admin
```

## Architecture at a glance

```text
Tilda / Tilda Store API
        │
        ▼
Integrations and sync
        │
        ▼
SQLite repositories
        │
        ├── Product Intelligence ── Product Profiles
        └── Tour Intelligence ───── Tour Profiles
        │
        ▼
Aspect Registry + Knowledge Layers
        │
        ├── Legacy Knowledge
        ├── Typed Knowledge Graph
        └── Runtime Knowledge Graph
        │
        ▼
Routing / Knowledge Answers / Semantic Engine
        │
        ▼
Bodhi Orchestrator
        │
        ▼
FastAPI
        │
        ▼
Tilda Widget
```

## Critical routing rule

```text
Business handlers > Semantic fallback
```

The Semantic Engine must not replace:

- exact product cards;
- active tour cards;
- planned-tour responses;
- aspect grouping logic;
- content-quality recommendations.

It is used only after the established business handlers return a fallback.

## Documentation

Start here:

1. [Developer Onboarding](docs/DEVELOPER_ONBOARDING.md)
2. [Current State](docs/CURRENT_STATE.md)
3. [Architecture](docs/ARCHITECTURE.md)
4. [Module Map](docs/MODULE_MAP.md)
5. [Query Flow](docs/QUERY_FLOW.md)
6. [API](docs/API.md)
7. [Database](docs/DATABASE.md)
8. [Knowledge Migration Plan](docs/KNOWLEDGE_MIGRATION_PLAN.md)
9. [Testing](docs/TESTING.md)
10. [Architecture Decisions](docs/ARCHITECTURE_DECISIONS.md)

## Domain terminology

User-facing responses use **aspect**, not “entity”.

Canonical examples:

```text
White Tara      → Bodhisattva
Green Tara      → Bodhisattva
Chenrezig       → Bodhisattva
Dzambala        → Bodhisattva
Vajrasattva     → Bodhisattva
Ushnishavijaya  → Bodhisattva
Milarepa        → Teacher
Guru Rinpoche   → Teacher
Mahakala        → Protector
Garuda          → Protector
Vajra           → Practice item
Phurba          → Practice item
```

Internal names such as `KnowledgeEntity` and `entity_id` are acceptable as
technical implementation details.

## Development workflow

Every architecture stage must include:

1. architecture goal;
2. implementation;
3. pytest coverage;
4. diagnostic or report tool;
5. smoke test;
6. exact Git commands.

Before commit:

```cmd
git status --short
```

Use targeted `git add` commands. Avoid `git add .` while generated or
temporary files are present.
