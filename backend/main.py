from __future__ import annotations

from html import escape
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

from backend.config import AI_PROVIDER, EMAIL_TO, OLLAMA_MODEL, SITE_URL
from backend.services.ai_service import chat
from backend.rag.dynamic_query_router import route_query
from backend.catalog.collection_builder import build_product_collection
from backend.tours.collection_builder import build_tour_collection, detect_country
from backend.services.bodhi_service import answer_query
from backend.services.dashboard_service import get_dashboard_data
from backend.services.knowledge_service import load_knowledge, rebuild_knowledge, search_knowledge
from backend.services.llm_service import ollama_available
from backend.sales_assistant.api import router as sales_router

app = FastAPI(title="Lotus AI Manager", version="0.7.0")
app.include_router(sales_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # только для локальной разработки
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STYLE = """
<style>
body{font-family:Arial,sans-serif;background:#f7f3ff;color:#2d2440;margin:0;padding:30px 18px}.container{max-width:1080px;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-bottom:18px}.card{background:#fff;border:1px solid #e7def8;border-radius:18px;padding:20px;margin-bottom:16px;box-shadow:0 7px 25px rgba(70,42,120,.06)}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}.stat{background:#faf8ff;border:1px solid #e7def8;border-radius:14px;padding:16px}.num{font-size:28px;font-weight:bold;color:#6847d9}.button{display:inline-block;padding:11px 16px;border-radius:11px;background:#6847d9;color:#fff;text-decoration:none;border:0;cursor:pointer}.secondary{background:#ede7ff;color:#4b358d}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:11px 9px;border-bottom:1px solid #eee8f8;vertical-align:top}.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#eee8ff;color:#503b9d;font-size:12px;font-weight:bold}input{width:72%;padding:12px;border:1px solid #d8cdec;border-radius:10px;font-size:15px}.muted{color:#786f88}.chat{min-height:360px;border:1px solid #eee8f8;border-radius:16px;padding:16px;overflow:auto}.msg{white-space:pre-wrap;padding:12px 14px;border-radius:14px;margin:10px 0;line-height:1.45}.user{background:#eee8ff;margin-left:80px}.bot{background:#f5f3f7;margin-right:80px}.row{display:flex;gap:10px;margin-top:14px}.row input{flex:1;width:auto}.suggestions{display:flex;flex-wrap:wrap;gap:8px;margin:8px 80px 14px 0}.suggestion{padding:8px 12px;border:1px solid #cfc0f1;border-radius:999px;background:#fff;color:#5639a8;cursor:pointer;font-size:13px}.suggestion:hover{background:#eee8ff}.collection{display:grid;gap:12px;margin:8px 80px 16px 0}.item-card{overflow:hidden;background:#fff;border:1px solid #e7def8;border-radius:15px}.item-card img{display:block;width:100%;max-height:260px;object-fit:cover;background:#f4effa}.item-body{padding:13px}.item-title{font-weight:700;margin-bottom:7px}.item-meta{font-size:13px;color:#786f88;margin-top:4px}.item-link{display:inline-block;margin-top:10px;padding:9px 12px;border-radius:9px;background:#6847d9;color:#fff;text-decoration:none;font-size:13px;font-weight:700}
</style>
"""


def render(title: str, body: str) -> str:
    return f"""<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{escape(title)}</title>{STYLE}</head><body><div class='container'>{body}</div></body></html>"""


@app.get("/")
def home() -> dict:
    return {
        "project": "Lotus AI Manager",
        "status": "running",
        "version": "0.6.0",
        "site": SITE_URL,
        "email_to": EMAIL_TO,
        "ai_provider": AI_PROVIDER,
        "admin": "http://127.0.0.1:8000/admin",
        "dev": "http://127.0.0.1:8000/dev",
        "chat": "http://127.0.0.1:8000/chat-ui",
    }


@app.get("/admin", response_class=HTMLResponse)
def admin_page() -> str:
    knowledge = load_knowledge()
    ollama_status = "доступна" if ollama_available() else "не подключена"
    body = f"""
    <div class='top'><div><h1>Lotus AI Manager v0.6</h1><div class='muted'>Административная панель</div></div><div><a class='button secondary' href='/dev'>Состояние системы</a> <a class='button' href='/chat-ui'>Открыть чат</a></div></div>
    <div class='card'><h2>База знаний сайта</h2><p><b>Сайт:</b> {escape(SITE_URL)}</p><p><b>Страниц:</b> {knowledge.get('pages_count',0)}</p><p><b>Фрагментов:</b> {knowledge.get('chunks_count',0)}</p><p><b>Обновлено:</b> {escape(str(knowledge.get('updated_at') or 'ещё не обновлялась'))}</p><a class='button' href='/admin/rebuild'>Обновить сайт</a></div>
    <div class='card'><h2>AI</h2><p><b>Режим:</b> {escape(AI_PROVIDER)}</p><p><b>Ollama:</b> {ollama_status}</p><p><b>Модель:</b> {escape(OLLAMA_MODEL)}</p></div>
    <div class='card'><h2>Проверить поиск</h2><form action='/admin/search' method='get'><input name='q' required placeholder='Например: Кайлас, Лапчи, консультация'> <button class='button'>Искать</button></form></div>
    """
    return render("Lotus AI Manager — админка", body)


@app.get("/dev", response_class=HTMLResponse)
def developer_dashboard() -> str:
    data = get_dashboard_data()
    stats = data["stats"]
    rows = ""
    for doc in data["documents"]:
        rows += f"<tr><td><span class='badge'>{escape(doc['page_type'])}</span></td><td>{escape(doc['title'])}</td><td><a href='{escape(doc['url'])}' target='_blank'>Открыть</a></td><td>{'Да' if doc['enabled'] else 'Нет'}</td><td>{doc['priority']}</td></tr>"
    if not rows:
        rows = "<tr><td colspan='5'>Документов пока нет.</td></tr>"
    body = f"""
    <div class='top'><div><h1>Состояние Lotus AI Manager</h1><div class='muted'>SQLite и классификация документов</div></div><div><a class='button secondary' href='/admin'>Админка</a> <a class='button' href='/chat-ui'>Чат</a></div></div>
    <div class='card'><div class='stats'>
      <div class='stat'><div class='num'>{stats['documents']}</div><div>Документов</div></div>
      <div class='stat'><div class='num'>{stats['chunks']}</div><div>Фрагментов</div></div>
      <div class='stat'><div class='num'>{stats['tours']}</div><div>Туров</div></div>
      <div class='stat'><div class='num'>{stats['consultations']}</div><div>Консультаций</div></div>
      <div class='stat'><div class='num'>{stats['shop']}</div><div>Товаров</div></div>
      <div class='stat'><div class='num'>{stats['general']}</div><div>Общих страниц</div></div>
    </div></div>
    <div class='card'><h2>Документы в SQLite</h2><table><thead><tr><th>Тип</th><th>Название</th><th>Ссылка</th><th>Активен</th><th>Приоритет</th></tr></thead><tbody>{rows}</tbody></table></div>
    """
    return render("Lotus AI Manager — состояние", body)


@app.get("/admin/rebuild", response_class=HTMLResponse)
def admin_rebuild() -> str:
    knowledge = rebuild_knowledge()
    body = f"<div class='card'><h1>Сайт обновлён</h1><p><b>Страниц:</b> {knowledge.get('pages_count',0)}</p><p><b>Фрагментов:</b> {knowledge.get('chunks_count',0)}</p><p><b>Ошибок:</b> {knowledge.get('errors_count',0)}</p><p>После этого выполните <code>python -m backend.rag.knowledge_builder</code></p><a class='button' href='/admin'>Вернуться</a></div>"
    return render("База знаний обновлена", body)


@app.get("/admin/search", response_class=HTMLResponse)
def admin_search(q: str = Query(...)) -> str:
    results = search_knowledge(q)
    items = ""
    for item in results:
        items += f"<div class='card'><h3>{escape(str(item.get('title') or 'Без названия'))}</h3><p><b>Тип:</b> {escape(str(item.get('page_type') or 'general'))}</p><p><b>Score:</b> {item.get('score',0)}</p><p><a href='{escape(str(item.get('url') or '#'))}' target='_blank'>Открыть источник</a></p><p>{escape(str(item.get('snippet') or ''))}</p></div>"
    if not items:
        items = "<div class='card'>Ничего не найдено.</div>"
    return render("Результаты поиска", f"<div class='top'><h1>Результаты поиска: {escape(q)}</h1><a class='button secondary' href='/admin'>Назад</a></div>{items}")


@app.post("/api/chat")
async def api_chat(payload: dict) -> JSONResponse:
    message = (payload.get("message") or "").strip()
    if not message:
        return JSONResponse({"answer": "Напишите вопрос.", "status": "empty"})
    return JSONResponse(chat(message))




@app.post("/api/bodhi/chat")
async def api_bodhi_chat(payload: dict) -> JSONResponse:
    message = (payload.get("message") or "").strip()

    if not message:
        return JSONResponse(
            {
                "answer": "Напишите вопрос.",
                "status": "empty",
            }
        )

    response = answer_query(message)
    items: list[dict] = []
    kind = response.kind
    answer = response.text

    try:
        route = route_query(message)
        if route.intent == "product":
            items = [item.to_dict() for item in build_product_collection(message)]
            if items:
                count = len(items)
                answer = f"Нашла {count} подходящих " + ("товар." if count == 1 else "товара." if count < 5 else "товаров.")
                kind = "product_collection"
        elif route.intent == "tour" and detect_country(message):
            items = [item.to_dict() for item in build_tour_collection(message)]
            if items:
                country = detect_country(message)
                planned_only = all(item.get("status") == "planned" for item in items)
                answer = (
                    f"По направлению «{country}» опубликованных программ пока нет, но готовится следующее путешествие:"
                    if planned_only else
                    f"Нашла путешествия по направлению «{country}»:"
                )
                kind = "tour_collection"
    except Exception:
        # The established answer remains available while catalog storage is
        # being initialized or during isolated API tests.
        items = []

    return JSONResponse(
        {
            "answer": answer,
            "status": f"bodhi_{kind}",
            "kind": kind,
            "title": response.title,
            "url": response.url,
            "items": items,
        }
    )


@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui() -> str:
    body = """
    <div class='top'><div><h1>AI-менеджер «Свет Лотоса»</h1><div class='muted'>Локальный тестовый чат</div></div><a class='button secondary' href='/admin'>Админка</a></div>
    <div class='card'><div id='messages' class='chat'><div class='msg bot'>Здравствуйте! Я AI-менеджер студии «Свет Лотоса». Спросите меня о турах, товарах или консультации буддолога-психолога.</div></div><div class='row'><input id='message' placeholder='Например: Есть тур на Кайлас?' onkeydown="if(event.key==='Enter')sendMessage()"><button class='button' onclick='sendMessage()'>Отправить</button></div></div>
    <script>
    async function sendMessage(value){const input=document.getElementById('message');const text=(value||input.value).trim();if(!text)return;clearSuggestions();addMessage(text,'user');input.value='';addMessage('Думаю...','bot');try{const r=await fetch('/api/sales/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,session_id:'local-chat-ui'})});const d=await r.json();const m=document.getElementById('messages');m.lastChild.textContent=d.answer;showItems(d.items||[]);showSuggestions(d.suggestions||[]);m.scrollTop=m.scrollHeight}catch(e){document.getElementById('messages').lastChild.textContent='Не удалось получить ответ. Проверьте сервер.'}}
    function addMessage(text,cls){const m=document.getElementById('messages');const d=document.createElement('div');d.className='msg '+cls;d.textContent=text;m.appendChild(d);m.scrollTop=m.scrollHeight}
    function showItems(items){if(!items.length)return;const m=document.getElementById('messages');const collection=document.createElement('div');collection.className='collection';items.forEach(item=>{const card=document.createElement('article');card.className='item-card';if(item.image_url){const img=document.createElement('img');img.src=item.image_url;img.alt=item.title||'Товар';img.loading='lazy';card.appendChild(img)}const body=document.createElement('div');body.className='item-body';const title=document.createElement('div');title.className='item-title';title.textContent=item.title||'Без названия';body.appendChild(title);[item.price,item.size,item.material,item.availability].filter(Boolean).forEach(value=>{const meta=document.createElement('div');meta.className='item-meta';meta.textContent=value;body.appendChild(meta)});if(item.url){const link=document.createElement('a');link.className='item-link';link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=item.status==='planned'?'Подробнее':'Открыть товар';body.appendChild(link)}card.appendChild(body);collection.appendChild(card)});m.appendChild(collection)}
    function clearSuggestions(){document.querySelectorAll('.suggestions').forEach(x=>x.remove())}
    function showSuggestions(items){if(!items.length)return;const m=document.getElementById('messages');const box=document.createElement('div');box.className='suggestions';items.forEach(item=>{const b=document.createElement('button');b.className='suggestion';b.textContent=item.label;b.onclick=()=>sendMessage(item.message);box.appendChild(b)});m.appendChild(box)}
    </script>
    """
    return render("AI-менеджер Свет Лотоса", body)
