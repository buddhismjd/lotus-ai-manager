# Архитектура AI Bodhi

```text
Tilda / Tilda Store API
        │
        ▼
Integrations & Sync
        │
        ▼
SQLite + Repositories
        │
        ├── Product Intelligence ── Product Profiles
        └── Tour Intelligence ───── Tour Profiles
        │
        ▼
Aspect Registry + Knowledge Layers
        │
        ├── Legacy Knowledge Graph
        ├── Typed Knowledge Graph
        └── Runtime Knowledge Graph
        │
        ▼
Router / Knowledge Answer / Semantic Engine
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

## Ключевые каталоги

### `backend/catalog`

Товары, репозитории, профили, классификация.

### `backend/tours`

Профили путешествий и planned tours.

### `backend/integrations`

Синхронизация внешних источников.

### `backend/rag`

Маршрутизация и поиск.

### `backend/knowledge`

Legacy-знания, Aspect Registry, Knowledge Answers, Knowledge Core.

### `backend/knowledge_graph`

Типизированный граф, loader, validator, runtime graph.

### `backend/semantic_engine`

Parser, registry adapter, semantic answer engine.

### `backend/services`

Бизнес-оркестрация и публичная точка ответа.

## Инвариант

```text
Business handlers > Semantic fallback
```

Semantic Engine не должен заменять точную карточку товара или тур.
