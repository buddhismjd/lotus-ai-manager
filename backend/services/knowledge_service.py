from __future__ import annotations
import json, re
from backend.config import DATA_DIR, KNOWLEDGE_FILE, SITE_URL
from backend.parser.site_parser import parse_site

STOPWORDS = {'что','как','где','когда','это','или','для','про','мне','меня','есть','можно','хочу','нужно','ваш','ваша','ваши','какой','какая','какие','сколько','будет','если','подскажите','расскажите','направление','направления','поехать','ехать','the','and','for','with'}
SYNONYMS = {
    'консультации': ['консультация','психолог','буддолог','записаться'],
    'консультация': ['консультации','психолог','буддолог','записаться'],
    'кайлас': ['кора','тибет','гора','паломничество','kailas','kailash'],
    'лапчи': ['миларепа','milarepa','lapchi','непал'],
    'миларепа': ['лапчи','milarepa','lapchi','непал'],
    'тибет': ['кайлас','кора','гималаи'],
    'непал': ['катманду','лапчи','гималаи'],
    'бутан': ['bhutan','гималаи'],
    'тур': ['путешествие','поездка','ретрит','маршрут'],
    'туры': ['путешествие','поездка','ретрит','маршрут'],
    'ретрит': ['практика','медитация','путешествие'],
}
DIRECTION_WORDS = {'кайлас','kailas','kailash','тибет','лапчи','lapchi','миларепа','milarepa','непал','nepal','бутан','bhutan','индия','india','гималаи','катманду','гора','кора','паломничество'}
TRAVEL_INTENT_WORDS = {'тур','туры','поездка','поехать','ехать','путешествие','маршрут','ретрит','направление','направления','паломничество','даты','стоимость'}

def tokenize(text: str) -> list[str]:
    words = re.findall(r'[a-zA-Zа-яА-ЯёЁ0-9]{3,}', text.lower())
    base = [w for w in words if w not in STOPWORDS]
    expanded = []
    for word in base:
        expanded.append(word)
        expanded.extend(SYNONYMS.get(word, []))
    return expanded

def is_tour_query(query: str) -> bool:
    words = set(re.findall(r'[a-zA-Zа-яА-ЯёЁ0-9]{3,}', query.lower()))
    return bool(words & DIRECTION_WORDS) or bool(words & TRAVEL_INTENT_WORDS)

def rebuild_knowledge() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    knowledge = parse_site(SITE_URL)
    KNOWLEDGE_FILE.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2), encoding='utf-8')
    return knowledge

def load_knowledge() -> dict:
    if not KNOWLEDGE_FILE.exists():
        return {'site': SITE_URL, 'updated_at': None, 'pages_count': 0, 'chunks_count': 0, 'tour_pages_count': 0, 'errors_count': 0, 'pages': [], 'chunks': [], 'errors': []}
    return json.loads(KNOWLEDGE_FILE.read_text(encoding='utf-8'))

def search_knowledge(query: str, limit: int = 5, page_type: str | None = None) -> list[dict]:
    knowledge = load_knowledge()
    query_words = tokenize(query)
    results = []
    for chunk in knowledge.get('chunks', []):
        if page_type and chunk.get('page_type') != page_type:
            continue
        text = chunk.get('text', '')
        low = text.lower()
        title = (chunk.get('page_title') or '').lower()
        url = (chunk.get('page_url') or '').lower()
        score = 0
        for word in query_words:
            if word in url: score += 7
            if word in title: score += 6
            if word in low: score += 3
            score += low.count(word)
        if page_type == 'tour': score += 2
        if score > 0:
            results.append({'score': score, 'title': chunk.get('page_title'), 'url': chunk.get('page_url'), 'page_type': chunk.get('page_type'), 'snippet': text[:900], 'text': text})
    results.sort(key=lambda item: item['score'], reverse=True)
    return results[:limit]

def get_tour_pages() -> list[dict]:
    return [p for p in load_knowledge().get('pages', []) if p.get('page_type') == 'tour']
