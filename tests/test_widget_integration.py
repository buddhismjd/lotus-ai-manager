from fastapi.testclient import TestClient

import backend.main as main_module

client = TestClient(main_module.app)


def test_widget_assets_are_served_by_backend() -> None:
    js = client.get('/widget/widget.js')
    css = client.get('/widget/widget.css')
    assert js.status_code == 200
    assert css.status_code == 200
    assert '/api/sales/chat' in js.text
    assert 'ai-bodhi__suggestions' in css.text


def test_tilda_embed_uses_sales_api_and_single_backend_domain() -> None:
    response = client.get('/widget/embed')
    assert response.status_code == 200
    assert 'https://YOUR-API-DOMAIN/api/sales/chat' in response.text
    assert 'https://YOUR-API-DOMAIN/widget/widget.js' in response.text
    assert 'https://YOUR-API-DOMAIN/widget/widget.css' in response.text
