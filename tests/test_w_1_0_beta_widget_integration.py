from pathlib import Path

from fastapi.testclient import TestClient

import backend.main as main_module
from backend.config import BASE_DIR

client = TestClient(main_module.app)
WIDGET_DIR = Path(BASE_DIR) / "widget"


def test_widget_health_exposes_public_chat_endpoint() -> None:
    response = client.get("/widget/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["widget"] == "ai-bodhi"
    assert payload["chat_endpoint"] == "http://testserver/api/sales/chat"


def test_widget_embed_contains_health_endpoint_and_no_store_header() -> None:
    response = client.get("/widget/embed")
    assert response.status_code == 200
    assert "http://testserver/widget/health" in response.text
    assert response.headers["cache-control"] == "no-store"


def test_widget_assets_have_short_public_cache() -> None:
    for path in ("/widget/widget.js", "/widget/widget.css"):
        response = client.get(path)
        assert response.status_code == 200
        assert "public" in response.headers["cache-control"]
        assert "max-age=300" in response.headers["cache-control"]


def test_widget_has_timeout_retry_and_commercial_card_contract() -> None:
    js = (WIDGET_DIR / "widget.js").read_text(encoding="utf-8")
    assert "AbortController" in js
    assert "Повторить отправку" in js
    assert "Открыть тур" in js
    assert "Открыть услугу" in js
    assert "item.description" not in js
    assert "AI_BODHI_HEALTH_URL" in js
