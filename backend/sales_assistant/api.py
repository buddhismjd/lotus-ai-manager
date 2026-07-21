from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.sales_assistant.service import get_sales_assistant
from backend.sales_assistant.selection_page import router as selection_router

router = APIRouter(prefix="/api/sales", tags=["sales-assistant"])
router.include_router(selection_router)


@router.post("/chat")
async def sales_chat(payload: dict) -> JSONResponse:
    message = str(payload.get("message") or "").strip()
    session_id = str(payload.get("session_id") or "default").strip() or "default"
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
        "session_id": session_id,
        "items": list(reply.items),
    })


@router.post("/reset")
async def reset_sales_chat(payload: dict) -> JSONResponse:
    session_id = str(payload.get("session_id") or "default").strip() or "default"
    get_sales_assistant().reset(session_id)
    return JSONResponse({"status": "reset", "session_id": session_id})
