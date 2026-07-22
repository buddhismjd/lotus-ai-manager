from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
scenarios = ['Непал', 'Кайлас', 'Белая Тара', 'Хочу записаться на консультацию']
for index, message in enumerate(scenarios, 1):
    response = client.post('/api/sales/chat', json={'message': message, 'session_id': f'cb10-{index}'})
    payload = response.json()
    ok = response.status_code == 200 and bool(payload.get('answer')) and 'items' in payload
    print(f'{message}: {"OK" if ok else "FAIL"} ({payload.get("kind")})')
    if not ok:
        raise SystemExit(1)
