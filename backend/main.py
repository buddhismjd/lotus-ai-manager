from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from backend.config import SITE_URL, EMAIL_TO, AI_PROVIDER, OLLAMA_MODEL
from backend.services.knowledge_service import rebuild_knowledge, load_knowledge, search_knowledge
from backend.services.ai_service import chat
from backend.services.llm_service import ollama_available

app = FastAPI(title='Lotus AI Manager', version='0.5.0')

@app.get('/')
def home():
    return {'project':'Lotus AI Manager','status':'running','version':'0.5.0','site':SITE_URL,'email_to':EMAIL_TO,'ai_provider':AI_PROVIDER,'admin':'http://127.0.0.1:8000/admin','chat':'http://127.0.0.1:8000/chat-ui'}

@app.get('/admin', response_class=HTMLResponse)
def admin_page():
    k = load_knowledge()
    ollama_status = 'доступна' if ollama_available() else 'не подключена'
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Lotus AI Manager</title><style>body{{font-family:Arial,sans-serif;max-width:980px;margin:40px auto;line-height:1.5;background:#faf8ff}}.card{{background:white;border:1px solid #e5defa;border-radius:18px;padding:22px;margin:16px 0;box-shadow:0 5px 20px rgba(80,50,130,.06)}}a.button,button{{display:inline-block;padding:12px 18px;border-radius:12px;background:#6d4aff;color:white;text-decoration:none;border:0;cursor:pointer}}input{{padding:12px;width:70%;border:1px solid #ccc;border-radius:10px}}code{{background:#f1ecff;padding:2px 6px;border-radius:6px}}</style></head><body><h1>Lotus AI Manager v0.5</h1><div class="card"><h2>База знаний</h2><p><b>Сайт:</b> {SITE_URL}</p><p><b>Email заявок:</b> {EMAIL_TO}</p><p><b>Страниц:</b> {k.get('pages_count',0)}</p><p><b>Фрагментов:</b> {k.get('chunks_count',0)}</p><p><b>Последнее обновление:</b> {k.get('updated_at') or 'ещё не обновлялась'}</p><p><a class="button" href="/admin/rebuild">Обновить сайт</a></p></div><div class="card"><h2>AI</h2><p><b>Режим:</b> <code>{AI_PROVIDER}</code></p><p><b>Ollama:</b> {ollama_status}</p><p><b>Модель:</b> <code>{OLLAMA_MODEL}</code></p><p>Если Ollama не подключена, система работает в безопасном локальном режиме.</p></div><div class="card"><h2>Тест AI-менеджера</h2><p><a class="button" href="/chat-ui">Открыть чат</a></p></div><div class="card"><h2>Тест поиска</h2><form action="/admin/search" method="get"><input name="q" placeholder="Например: Кайлас, консультации, ретрит"><button type="submit">Искать</button></form></div></body></html>'''

@app.get('/admin/rebuild', response_class=HTMLResponse)
def admin_rebuild():
    k = rebuild_knowledge()
    return f'''<html><body style="font-family:Arial;max-width:800px;margin:40px auto"><h1>База знаний обновлена</h1><p>Страниц: <b>{k.get('pages_count',0)}</b></p><p>Фрагментов: <b>{k.get('chunks_count',0)}</b></p><p>Ошибок: <b>{k.get('errors_count',0)}</b></p><p><a href="/admin">Вернуться в админку</a></p></body></html>'''

@app.get('/admin/search', response_class=HTMLResponse)
def admin_search(q: str = Query(...)):
    results = search_knowledge(q)
    items = ''
    for item in results:
        items += f'''<div style="background:white;border:1px solid #ddd;border-radius:12px;padding:14px;margin:12px 0"><h3>{item['title']}</h3><p><b>Score:</b> {item['score']}</p><p><a href="{item['url']}" target="_blank">{item['url']}</a></p><p>{item['snippet']}</p></div>'''
    if not items:
        items = '<p>Ничего не найдено.</p>'
    return f'''<html><body style="font-family:Arial;max-width:900px;margin:40px auto"><h1>Результаты поиска: {q}</h1>{items}<p><a href="/admin">Назад</a></p></body></html>'''

@app.post('/api/chat')
async def api_chat(payload: dict):
    message = (payload.get('message') or '').strip()
    if not message:
        return JSONResponse({'answer':'Напишите вопрос.','status':'empty'})
    return JSONResponse(chat(message))

@app.get('/chat-ui', response_class=HTMLResponse)
def chat_ui():
    return '''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>AI-менеджер Свет Лотоса</title><style>body{font-family:Arial,sans-serif;background:#f7f2ff;margin:0;padding:0}.wrap{max-width:780px;margin:40px auto;background:white;border-radius:22px;padding:24px;box-shadow:0 10px 35px rgba(60,30,120,.12)}h1{margin-top:0}#messages{min-height:390px;border:1px solid #eee;border-radius:16px;padding:16px;background:#fff;overflow:auto}.msg{padding:12px 14px;border-radius:14px;margin:10px 0;white-space:pre-wrap;line-height:1.45}.user{background:#ede7ff;margin-left:80px}.bot{background:#f5f5f5;margin-right:80px}.row{display:flex;gap:10px;margin-top:14px}input{flex:1;padding:14px;border:1px solid #ccc;border-radius:12px;font-size:16px}button{padding:14px 18px;border:0;border-radius:12px;background:#6d4aff;color:white;font-size:16px;cursor:pointer}a{color:#6d4aff}.hint{color:#666;font-size:14px}</style></head><body><div class="wrap"><h1>AI-менеджер «Свет Лотоса»</h1><p><a href="/admin">← Админка</a></p><p class="hint">Попробуйте: «Есть консультации?», «Расскажите про Кайлас», «Хочу записаться».</p><div id="messages"><div class="msg bot">Здравствуйте! Я AI-менеджер студии «Свет Лотоса». Задайте вопрос по услугам, турам или практикам.</div></div><div class="row"><input id="message" placeholder="Ваш вопрос..." onkeydown="if(event.key==='Enter') sendMessage()"><button onclick="sendMessage()">Отправить</button></div></div><script>async function sendMessage(){const input=document.getElementById('message');const text=input.value.trim();if(!text)return;addMessage(text,'user');input.value='';addMessage('Думаю...','bot');const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});const data=await response.json();const messages=document.getElementById('messages');messages.lastChild.textContent=data.answer;messages.scrollTop=messages.scrollHeight}function addMessage(text,cls){const box=document.getElementById('messages');const div=document.createElement('div');div.className='msg '+cls;div.textContent=text;box.appendChild(div);box.scrollTop=box.scrollHeight}</script></body></html>'''
