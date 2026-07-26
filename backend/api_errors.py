from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def validation_error_response(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a stable, non-internal validation error contract."""

    fields: list[str] = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", ()) if part not in {"body", "path", "query"}]
        field = ".".join(location)
        if field and field not in fields:
            fields.append(field)

    return JSONResponse(
        status_code=422,
        content={
            "status": "invalid_request",
            "error": {
                "code": "validation_error",
                "message": "Некорректные данные запроса.",
                "fields": fields,
            },
        },
    )
