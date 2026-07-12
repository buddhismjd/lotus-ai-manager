# Module Map

## `backend/catalog`

Product models, repositories, profiles and classification.

Key concerns:

- product type;
- aspect links;
- materials;
- dimensions;
- usage;
- content completeness.

## `backend/tours`

Tour profiles and planned-tour knowledge.

Key concerns:

- country;
- destination;
- practice;
- aspect;
- duration;
- altitude;
- publication status.

## `backend/integrations`

Tilda and repository synchronization.

Do not place public answer wording here.

## `backend/rag`

Search and dynamic query routing.

## `backend/knowledge`

Legacy knowledge layer and canonical Aspect Registry.

This layer remains operational for compatibility.

## `backend/knowledge_graph`

Typed knowledge graph.

Typical files:

```text
models.py
repository.py
loader.py
validator.py
runtime.py
service.py
data/
```

## `backend/semantic_engine`

Semantic intent parsing and graph-based fallback answers.

## `backend/services`

Public business logic.

The primary public function is:

```python
backend.services.bodhi_service.answer_query()
```

## `backend/api` / `backend/main.py`

FastAPI entry points.

## `widget`

Tilda-compatible user interface.

## `tests`

Unit, regression and integration coverage.

## `tools`

Diagnostics, reports, benchmarks, smoke tests and controlled migration
utilities.
