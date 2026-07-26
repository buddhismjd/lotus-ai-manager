from uuid import uuid4

from fastapi.testclient import TestClient
import backend.main as main_module

client = TestClient(main_module.app)


def test_sales_api_answers_psychologist_question() -> None:
    session_id = f"test-psychologist-{uuid4().hex}"
    response = client.post(
        '/api/sales/chat',
        json={'message': 'Хочу консультацию буддолога', 'session_id': session_id},
    )
    payload=response.json()
    assert response.status_code == 200
    assert payload['topic'] == 'psychologist'
    assert payload['session_id'] == session_id


def test_sales_api_rejects_empty_message() -> None:
    response = client.post('/api/sales/chat', json={'message':'  '})
    assert response.json()['status'] == 'sales_empty'
