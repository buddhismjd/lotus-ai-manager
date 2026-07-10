from __future__ import annotations
from datetime import datetime
import json, re
from backend.config import DIALOGS_FILE, EMAIL_TO, MIN_SEARCH_SCORE
from backend.services.knowledge_service import search_knowledge, load_knowledge, is_tour_query, get_tour_pages
from backend.services.llm_service import llm_answer

HUMAN_TRIGGERS = ['менеджер','человек','оператор','администратор','свяжитесь','позвоните','напишите мне','живой']
CONTACT_TRIGGERS = ['@','+7','+371','whatsapp','telegram','телеграм']

def wants_human(message: str) -> bool:
    return any(t in message.lower() for t in HUMAN_TRIGGERS)

def looks_like_contact(message: str) -> bool:
    return bool(re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', message)) or any(t in message.lower() for t in CONTACT_TRIGGERS)

def save_dialog(user_message: str, answer: str, status: str, sources: list[dict]) -> None:
    DIALOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {'created_at': datetime.now().isoformat(timespec='seconds'), 'user_message': user_message, 'answer': answer, 'status': status, 'sources': [{'title': s.get('title'), 'url': s.get('url'), 'score': s.get('score'), 'page_type': s.get('page_type')} for s in sources]}
    with DIALOGS_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

def unique_sources(sources: list[dict]) -> list[dict]:
    seen = set(); out = []
    for s in sources:
        url = s.get('url')
        if url and url not in seen:
            seen.add(url); out.append(s)
    return out

def tour_answer(sources: list[dict]) -> str:
    unique = unique_sources(sources)
    if not unique:
        pages = get_tour_pages()
        if pages:
            answer = 'Я не нашёл точного совпадения по этому направлению, но на сайте есть страницы с турами:\n\n'
            for p in pages[:5]:
                answer += f"• {p.get('title')}\n  {p.get('url')}\n"
            return answer + '\nМогу передать ваш вопрос менеджеру, чтобы уточнить подходящее направление.'
        return f'Я не нашёл на сайте страницу тура по этому направлению. Лучше передать вопрос менеджеру: {EMAIL_TO}'
    answer = 'По этому направлению я нашёл страницу тура на сайте «Свет Лотоса»:\n\n'
    for s in unique[:3]:
        short = s.get('text', '').replace('\n', ' ')[:260].strip()
        if len(s.get('text', '')) > 260: short += '...'
        answer += f"• {s.get('title') or 'Тур'}\n  {s.get('url')}\n"
        if short: answer += f"  {short}\n"
        answer += '\n'
    return answer + 'Если хотите, я помогу оставить заявку по этому туру.'

def smart_local_answer(message: str, sources: list[dict]) -> str:
    text = '\n'.join([s.get('text', '') for s in sources[:2]])
    lowq = message.lower(); lowt = text.lower(); bullets = []
    if 'консульта' in lowq:
        if 'евгения драй' in lowt or 'буддолог' in lowt or 'психолог' in lowt:
            bullets.append('На сайте указаны консультации буддолога-психолога с Евгенией Драй.')
        if '30 минут' in lowt: bullets.append('Первая консультация 30 минут — бесплатно.')
        if 'стресс' in lowt: bullets.append('Среди тем указаны снижение стресса, осознанность и работа с эмоциями.')
        if 'записаться' in lowt: bullets.append('Можно оставить контактные данные для записи на консультацию.')
    if not bullets:
        bullets = [line.strip() for line in text.splitlines() if 25 <= len(line.strip()) <= 180][:4]
    if not bullets:
        return f'Я нашёл информацию на сайте, но не смог сформулировать точный короткий ответ. Лучше передать вопрос менеджеру: {EMAIL_TO}'
    answer = 'Да, по информации с сайта «Свет Лотоса»:\n\n' + ''.join([f'• {b}\n' for b in bullets[:5]])
    answer += '\nЕсли хотите, я помогу оставить заявку для менеджера.'
    if sources: answer += f"\n\nИсточник: {sources[0].get('url')}"
    return answer

def build_context(sources: list[dict]) -> str:
    return '\n\n---\n\n'.join([f"[Источник {i}: {s.get('title')} | {s.get('url')}]\n{s.get('text', '')}" for i, s in enumerate(sources[:3], 1)])

def chat(message: str) -> dict:
    knowledge = load_knowledge()
    if knowledge.get('chunks_count', 0) == 0:
        answer = 'База знаний пока пустая. Нажмите в админке «Обновить сайт», затем повторите вопрос.'
        save_dialog(message, answer, 'knowledge_empty', [])
        return {'answer': answer, 'status': 'knowledge_empty', 'sources': [], 'handoff': False}
    if wants_human(message):
        answer = f'Хорошо, я передам ваш запрос менеджеру. Заявки отправляются на: {EMAIL_TO}'
        save_dialog(message, answer, 'handoff_requested', [])
        return {'answer': answer, 'status': 'handoff_requested', 'sources': [], 'handoff': True}
    if looks_like_contact(message):
        answer = f'Спасибо, я зафиксировал ваши контактные данные и передам обращение менеджеру на {EMAIL_TO}.'
        save_dialog(message, answer, 'lead_collected', [])
        return {'answer': answer, 'status': 'lead_collected', 'sources': [], 'handoff': True}

    # v0.5: вопросы про направления/туры ищем только среди страниц туров.
    if is_tour_query(message):
        sources = search_knowledge(message, limit=5, page_type='tour')
        if not sources or sources[0]['score'] < MIN_SEARCH_SCORE:
            answer = tour_answer([])
            save_dialog(message, answer, 'tour_no_exact_match', sources)
            return {'answer': answer, 'status': 'tour_no_exact_match', 'sources': sources, 'handoff': True}
        generated, provider_status = llm_answer(message, build_context(sources))
        if generated:
            answer = generated
            uniq = unique_sources(sources)
            if uniq and uniq[0].get('url') not in answer:
                answer += f"\n\nСтраница тура: {uniq[0].get('url')}"
            status = 'tour_answer_with_llm'
        else:
            answer = tour_answer(sources)
            status = f'tour_answer_local ({provider_status})'
        save_dialog(message, answer, status, sources)
        return {'answer': answer, 'status': status, 'sources': sources, 'handoff': False}

    sources = search_knowledge(message, limit=4)
    if not sources or sources[0]['score'] < MIN_SEARCH_SCORE:
        answer = f'Я не нашёл точной информации об этом в базе знаний сайта. Лучше передать вопрос менеджеру. Уведомление будет отправлено на {EMAIL_TO}.'
        save_dialog(message, answer, 'no_context_handoff', sources)
        return {'answer': answer, 'status': 'no_context_handoff', 'sources': sources, 'handoff': True}
    generated, provider_status = llm_answer(message, build_context(sources))
    if generated:
        answer = generated
        if sources and 'Источник:' not in answer:
            answer += f"\n\nИсточник: {sources[0].get('url')}"
        status = 'answered_with_llm'
    else:
        answer = smart_local_answer(message, sources)
        status = f'answered_local_fallback ({provider_status})'
    save_dialog(message, answer, status, sources)
    return {'answer': answer, 'status': status, 'sources': sources, 'handoff': False}
