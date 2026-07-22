from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from backend.config import BASE_DIR

router = APIRouter(prefix="/widget", tags=["widget"])
WIDGET_DIR = BASE_DIR / "widget"


def _asset(name: str) -> Path:
    path = (WIDGET_DIR / name).resolve()
    if path.parent != WIDGET_DIR.resolve() or not path.is_file():
        raise HTTPException(status_code=404, detail="Widget asset not found")
    return path


@router.get("/widget.js", response_class=FileResponse)
def widget_js() -> FileResponse:
    return FileResponse(_asset("widget.js"), media_type="application/javascript")


@router.get("/widget.css", response_class=FileResponse)
def widget_css() -> FileResponse:
    return FileResponse(_asset("widget.css"), media_type="text/css")


@router.get("/embed", response_class=HTMLResponse)
def widget_embed() -> HTMLResponse:
    return HTMLResponse(_asset("tilda_embed.html").read_text(encoding="utf-8"))
