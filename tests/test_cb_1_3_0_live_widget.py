from pathlib import Path

from backend.config import BASE_DIR


WIDGET_DIR = Path(BASE_DIR) / "widget"


def _read(name: str) -> str:
    return (WIDGET_DIR / name).read_text(encoding="utf-8")


def test_widget_visual_contract_matches_svet_lotosa_brand() -> None:
    css = _read("widget.css")
    assert "--bodhi-navy: #123456" in css
    assert '"TildaSans"' in css
    assert "--bodhi-ivory" in css
    assert "@media (max-width: 520px)" in css


def test_widget_supports_live_session_reset_and_restore() -> None:
    js = _read("widget.js")
    assert "AI_BODHI_SESSION_URL" in js
    assert "AI_BODHI_RESET_URL" in js
    assert "restoreConversation" in js
    assert "resetConversation" in js
    assert "localStorage" in js


def test_widget_renders_rich_cards_and_quick_actions() -> None:
    js = _read("widget.js")
    html = _read("widget.html")
    assert "appendCollection" in js
    assert "appendSuggestions" in js
    assert "data-bodhi-quick-actions" in html
    assert "Путешествия" in html
    assert "Магазин" in html
    assert "Консультация" in html


def test_tilda_embed_contains_all_production_endpoint_placeholders() -> None:
    embed = _read("tilda_embed.html")
    assert "https://YOUR-API-DOMAIN/api/sales/chat" in embed
    assert "https://YOUR-API-DOMAIN/api/sales/session" in embed
    assert "https://YOUR-API-DOMAIN/api/sales/reset" in embed
    assert "https://YOUR-API-DOMAIN/widget/widget.css" in embed
    assert "https://YOUR-API-DOMAIN/widget/widget.js" in embed
