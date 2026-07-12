# Current State

## Stable foundations

The project currently includes:

- Product Repository;
- Tour Repository;
- Product Intelligence;
- Tour Intelligence;
- Product Profiles;
- Tour Profiles;
- Dynamic Query Router;
- Aspect Registry;
- legacy Knowledge Answers;
- Knowledge Core;
- typed Knowledge Graph;
- Runtime Knowledge Graph;
- Semantic Engine;
- Semantic Adapter v2;
- Bodhi Orchestrator;
- planned tours;
- API and widget;
- diagnostics, benchmark and smoke tools.

## Confirmed user scenarios

```text
У вас есть Ваджра?
→ exact product response

Статуя Белой Тары
→ exact product response

Поход в Лапчи
→ planned-tour response

Есть поездка в Непал?
→ planned-tour response

Какие практики связаны с Миларепой?
→ semantic knowledge response

Расскажи про Ваджру
→ knowledge response
```

## Knowledge layers

Two knowledge layers currently coexist:

```text
backend/knowledge
backend/knowledge_graph
```

This is intentional during migration.

Do not delete the legacy layer until:

- all public handlers use the typed graph;
- all legacy tests have typed-graph equivalents;
- all reports and adapters are migrated;
- a rollback path exists.

## Current risks

- overlapping knowledge implementations;
- old documentation mixed with current documentation;
- tracked Python cache files;
- no guaranteed CI on every push;
- generated local files in the repository root;
- possible divergence between local and remote branch state.
