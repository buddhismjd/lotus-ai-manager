# API

## FastAPI application

The project exposes its public API through FastAPI.

The exact route set must be verified against the current branch before
changing this document.

## Expected public concerns

- health/status endpoint;
- chat/query endpoint;
- admin interface;
- website synchronization actions;
- lead/contact handling.

## API change rules

Any API change must include:

- request/response test;
- backward compatibility note;
- updated widget integration if required;
- updated API documentation;
- smoke test through the real service.

## Verification commands

```cmd
python -m pytest tests\test_bodhi_api.py
python -m py_compile backend\main.py
```

## Do not expose

Never return:

- internal IDs unless required;
- filesystem paths;
- stack traces;
- credentials;
- raw database errors;
- private configuration.
