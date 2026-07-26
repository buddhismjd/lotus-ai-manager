from pathlib import Path

from fastapi.testclient import TestClient

import backend.main as main_module
from backend.config import BASE_DIR

client = TestClient(main_module.app)


def test_widget_assets_are_served_by_backend() -> None:
    js = client.get('/widget/widget.js')
    css = client.get('/widget/widget.css')
    assert js.status_code == 200
    assert css.status_code == 200
    assert '/api/sales/chat' in js.text
    assert 'ai-bodhi__suggestions' in css.text


def test_local_embed_resolves_assets_against_current_backend_origin() -> None:
    response = client.get('/widget/embed')
    assert response.status_code == 200
    assert 'http://testserver/api/sales/chat' in response.text
    assert 'http://testserver/widget/widget.js' in response.text
    assert 'http://testserver/widget/widget.css' in response.text
    assert 'https://YOUR-API-DOMAIN/' not in response.text


def test_tilda_source_template_keeps_production_domain_placeholder() -> None:
    template = (Path(BASE_DIR) / 'widget' / 'tilda_embed.html').read_text(encoding='utf-8')
    assert 'https://YOUR-API-DOMAIN/api/sales/chat' in template
    assert 'https://YOUR-API-DOMAIN/widget/widget.js' in template
    assert 'https://YOUR-API-DOMAIN/widget/widget.css' in template
