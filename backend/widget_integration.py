from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from backend.config import BASE_DIR, SITE_URL

router = APIRouter(prefix="/widget", tags=["widget"])
WIDGET_DIR = BASE_DIR / "widget"
_PLACEHOLDER_ORIGIN = "https://YOUR-API-DOMAIN"
_ASSET_CACHE_SECONDS = 300


def _asset(name: str) -> Path:
    path = (WIDGET_DIR / name).resolve()
    if path.parent != WIDGET_DIR.resolve() or not path.is_file():
        raise HTTPException(status_code=404, detail="Widget asset not found")
    return path


def _public_origin(request: Request) -> str:
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}".rstrip("/")
    return str(request.base_url).rstrip("/")


def _asset_response(name: str, media_type: str) -> FileResponse:
    response = FileResponse(_asset(name), media_type=media_type)
    response.headers["Cache-Control"] = f"public, max-age={_ASSET_CACHE_SECONDS}"
    return response


@router.get("/widget.js", response_class=FileResponse)
def widget_js() -> FileResponse:
    return _asset_response("widget.js", "application/javascript")


@router.get("/widget.css", response_class=FileResponse)
def widget_css() -> FileResponse:
    return _asset_response("widget.css", "text/css")


@router.get("/health", response_class=JSONResponse)
def widget_health(request: Request) -> JSONResponse:
    origin = _public_origin(request)
    return JSONResponse(
        {
            "status": "ok",
            "widget": "ai-bodhi",
            "site": SITE_URL,
            "api_origin": origin,
            "chat_endpoint": f"{origin}/api/sales/chat",
        }
    )


@router.get("/embed", response_class=HTMLResponse)
def widget_embed(request: Request) -> HTMLResponse:
    template = _asset("tilda_embed.html").read_text(encoding="utf-8")
    html = template.replace(_PLACEHOLDER_ORIGIN, _public_origin(request))
    response = HTMLResponse(html)
    response.headers["Cache-Control"] = "no-store"
    return response
