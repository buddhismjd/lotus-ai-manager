from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
checks = {
    'health': client.get('/').status_code == 200,
    'widget_js': client.get('/widget/widget.js').status_code == 200,
    'widget_css': client.get('/widget/widget.css').status_code == 200,
    'tilda_embed': '/api/sales/chat' in client.get('/widget/embed').text,
}
for name, ok in checks.items():
    print(f'{name}: {"OK" if ok else "FAIL"}')
if not all(checks.values()):
    raise SystemExit(1)
