from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse

from backend.sales_assistant.api_models import (
    MAX_SESSION_ID_LENGTH,
    SESSION_ID_PATTERN,
    SalesChatRequest,
    SalesResetRequest,
)
from backend.sales_assistant.service import get_sales_assistant
from backend.sales_assistant.selection_page import router as selection_router
from backend.sales_assistant.product_media import router as product_media_router

router = APIRouter(prefix="/api/sales", tags=["sales-assistant"])
router.include_router(selection_router)
router.include_router(product_media_router)


@router.post("/chat")
async def sales_chat(payload: SalesChatRequest) -> JSONResponse:
    message = payload.message
    session_id = payload.session_id
    reply = get_sales_assistant().reply(message, session_id)
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
        "session_id": session_id,
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
) -> JSONResponse:
    session_key = session_id
    session = get_sales_assistant().session(session_key)
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
    session_id = payload.session_id
    get_sales_assistant().reset(session_id)
    return JSONResponse({"status": "reset", "session_id": session_id})
