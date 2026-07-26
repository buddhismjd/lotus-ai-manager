from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Path, Query
from fastapi.responses import JSONResponse

from backend.sales_assistant.api_models import (
    MAX_SESSION_ID_LENGTH,
    SESSION_ID_PATTERN,
    SalesChatRequest,
    SalesResetRequest,
    SalesRotateTokenRequest,
    normalize_session_token,
)
from backend.sales_assistant.service import get_sales_assistant
from backend.sales_assistant.selection_page import router as selection_router
from backend.sales_assistant.product_media import router as product_media_router
from backend.storage.repositories.session_repository import (
    SessionAccessDeniedError,
    SessionRepository,
)

router = APIRouter(prefix="/api/sales", tags=["sales-assistant"])
router.include_router(selection_router)
router.include_router(product_media_router)


def _access_denied() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "status": "session_access_denied",
            "error": {
                "code": "session_access_denied",
                "message": "Доступ к этой сессии не подтверждён.",
            },
        },
    )


def _request_token(header_token: str | None, query_token: str | None = None) -> str | None:
    value = header_token or query_token
    return normalize_session_token(value)


@router.post("/chat")
async def sales_chat(payload: SalesChatRequest) -> JSONResponse:
    if not payload.message:
        reply = get_sales_assistant().reply(payload.message, payload.session_id)
        return JSONResponse({
            "answer": reply.answer,
            "status": f"sales_{reply.kind}",
            "kind": reply.kind,
            "topic": reply.topic,
            "title": reply.title,
            "url": reply.url,
            "needs_manager": reply.needs_manager,
            "next_action": reply.next_action.value,
            "suggestions": [],
            "dialogue_stage": reply.dialogue_stage,
            "lead_id": reply.lead_id,
            "handoff_reason": reply.handoff_reason,
            "handoff_priority": reply.handoff_priority,
            "session_id": payload.session_id,
            "session_token": payload.session_token,
            "items": [],
        })

    repository = SessionRepository()
    try:
        access = repository.establish_access(payload.session_id, payload.session_token)
    except SessionAccessDeniedError:
        return _access_denied()

    reply = get_sales_assistant().reply(payload.message, payload.session_id)
    return JSONResponse({
        "answer": reply.answer,
        "status": f"sales_{reply.kind}",
        "kind": reply.kind,
        "topic": reply.topic,
        "title": reply.title,
        "url": reply.url,
        "needs_manager": reply.needs_manager,
        "next_action": reply.next_action.value,
        "suggestions": [
            {
                "action": suggestion.action.value,
                "label": suggestion.label,
                "message": suggestion.message,
                "url": suggestion.url,
            }
            for suggestion in reply.suggestions
        ],
        "dialogue_stage": reply.dialogue_stage,
        "lead_id": reply.lead_id,
        "handoff_reason": reply.handoff_reason,
        "handoff_priority": reply.handoff_priority,
        "session_id": payload.session_id,
        "session_token": access.token,
        "items": list(reply.items),
    })


@router.get("/session/{session_id}")
async def sales_session(
    session_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=MAX_SESSION_ID_LENGTH,
            pattern=SESSION_ID_PATTERN,
        ),
    ],
    x_session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
    session_token: Annotated[str | None, Query()] = None,
) -> JSONResponse:
    try:
        token = _request_token(x_session_token, session_token)
        SessionRepository().verify_access(session_id, token)
    except (SessionAccessDeniedError, ValueError):
        return _access_denied()

    session = get_sales_assistant().session(session_id)
    return JSONResponse({
        "session_id": session.session_id,
        "status": session.status,
        "handoff_status": session.handoff_status,
        "dialogue_stage": session.state.get("stage", "discovery"),
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in session.messages
        ],
    })


@router.post("/reset")
async def reset_sales_chat(payload: SalesResetRequest) -> JSONResponse:
    repository = SessionRepository()
    try:
        repository.verify_access(payload.session_id, payload.session_token)
    except SessionAccessDeniedError:
        return _access_denied()
    get_sales_assistant().reset(payload.session_id)
    return JSONResponse({"status": "reset", "session_id": payload.session_id})


@router.post("/session/rotate-token")
async def rotate_sales_session_token(payload: SalesRotateTokenRequest) -> JSONResponse:
    try:
        replacement = SessionRepository().rotate_token(
            payload.session_id,
            payload.session_token or "",
        )
    except SessionAccessDeniedError:
        return _access_denied()
    return JSONResponse({
        "status": "session_token_rotated",
        "session_id": payload.session_id,
        "session_token": replacement,
    })
