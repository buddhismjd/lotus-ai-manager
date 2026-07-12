# Database

## Storage

The project uses SQLite for local development.

Known tables from the project foundation include:

```text
dialogs
messages
leads
documents
document_chunks
settings
```

Additional catalog/profile tables may exist in the current branch and
must be verified directly from migrations and repository code.

## Ownership

Repositories own database access.

Answer builders and semantic modules must not issue ad-hoc SQL.

## Migration rules

- migrations must be idempotent;
- existing data must remain readable;
- destructive migrations require backup instructions;
- schema changes require tests;
- local database files must not be committed.

## Diagnostics

Before changing schema, inspect:

```cmd
python -m backend.storage.database
```

and the current migration/profile tests.
