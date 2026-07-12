# Developer Onboarding

## 1. Read before changing code

Read in this order:

1. `CURRENT_STATE.md`
2. `ARCHITECTURE.md`
3. `MODULE_MAP.md`
4. `QUERY_FLOW.md`
5. `TESTING.md`
6. `ARCHITECTURE_DECISIONS.md`

## 2. Environment

Supported setup:

- Windows 11;
- Python 3.12;
- SQLite;
- FastAPI/Uvicorn;
- local development without Docker.

Activate the environment with:

```cmd
.venv\Scripts\activate.bat
```

## 3. Configuration

Copy `.env.example` to `.env`.

Never commit:

- `.env`;
- API tokens;
- credentials;
- local database snapshots;
- exported customer data.

## 4. Run the project

```cmd
setup.bat
run.bat
```

## 5. First checks

```cmd
python -m pytest tests\test_bodhi_service.py
python -m pytest tests\test_bodhi_api.py
python -m pytest tests\test_knowledge_answers.py
python -m pytest tests\test_semantic_engine.py
```

## 6. Architecture discipline

Never:

- add a special `if` only to satisfy one test;
- duplicate an existing registry, router or graph;
- let Semantic Engine bypass business routing;
- hard-code a product category for one specific product;
- replace reliable structured data with generated assumptions.

Always:

- reuse the existing repository/profile/registry layers;
- add regression coverage;
- keep legacy compatibility until migration is complete;
- update documentation with architecture changes.

## 7. Git workflow

```cmd
git status --short
git add <exact files>
git commit -m "Describe the architecture stage"
git push
```
