from __future__ import annotations
import requests
from backend.config import AI_PROVIDER, OLLAMA_MODEL, OLLAMA_URL

SYSTEM_RULES = '''Ты AI-менеджер студии «Свет Лотоса».
Отвечай на русском языке, тепло, кратко и по делу.
Используй ТОЛЬКО контекст ниже.
Не выдумывай факты, даты, цены, условия и ссылки.
Если в контексте нет ответа, скажи: «Я не нашёл точной информации на сайте и передам вопрос менеджеру».
Не цитируй огромные куски текста.'''

def ollama_available() -> bool:
    try:
        response = requests.get(OLLAMA_URL.replace('/api/generate', '/api/tags'), timeout=2)
        return response.status_code == 200
    except Exception:
        return False

def generate_with_ollama(question: str, context: str) -> str:
    prompt = f"{SYSTEM_RULES}\n\nКОНТЕКСТ С САЙТА:\n{context}\n\nВОПРОС КЛИЕНТА:\n{question}\n\nОТВЕТ:"
    response = requests.post(OLLAMA_URL, json={'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.2, 'top_p': 0.8}}, timeout=60)
    response.raise_for_status()
    return (response.json().get('response') or '').strip()

def llm_answer(question: str, context: str) -> tuple[str | None, str]:
    if AI_PROVIDER != 'ollama':
        return None, 'local'
    if not ollama_available():
        return None, 'ollama_not_available'
    try:
        answer = generate_with_ollama(question, context)
        return (answer, 'ollama') if answer else (None, 'ollama_empty')
    except Exception as exc:
        return None, f'ollama_error: {exc}'
