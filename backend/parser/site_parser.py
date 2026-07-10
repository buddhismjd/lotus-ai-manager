from __future__ import annotations
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'LotusAIManager/0.5'}
TOUR_MARKERS = ['тур','путешествие','поездка','паломнич','маршрут','кайлас','лапчи','милареп','тибет','непал','бутан','ретрит','катманду','гимала','kailas','kailash','lapchi','milarepa']
BAD_TEXT_PARTS = ['tilda','li_ph','li_req','li_nm','recaptcha','window.','function(','document.','jquery','prototype']

def normalize_url(url: str) -> str:
    return url.split('#')[0].rstrip('/')

def is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc == urlparse(base_url).netloc

def clean_text(text: str) -> str:
    lines = []
    seen = set()
    for raw in text.splitlines():
        line = re.sub(r'\s{2,}', ' ', raw.strip())
        if len(line) < 3:
            continue
        if any(bad in line.lower() for bad in BAD_TEXT_PARTS):
            continue
        if line.count('{') + line.count('}') + line.count('[') + line.count(']') > 2:
            continue
        if re.search(r'\\u[0-9a-fA-F]{4}', line):
            continue
        key = line.lower()
        if key in seen and len(line) < 80:
            continue
        seen.add(key)
        lines.append(line)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()

def classify_page(url: str, title: str, text: str) -> str:
    hay = (url + ' ' + title + ' ' + text).lower()
    hits = sum(1 for marker in TOUR_MARKERS if marker in hay)
    if hits >= 2 or any(marker in url.lower() for marker in ['tour','tur','kailas','kailash','lapchi','tibet','nepal','milarepa']):
        return 'tour'
    if 'консультац' in hay or 'психолог' in hay or 'буддолог' in hay:
        return 'consultation'
    if 'магазин' in hay or 'товар' in hay or 'купить' in hay:
        return 'shop'
    return 'general'

def extract_page(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    for tag in soup(['script','style','noscript','svg','iframe']):
        tag.decompose()
    for tag in soup.select('[aria-hidden="true"], [style*="display:none"], [style*="display: none"]'):
        tag.decompose()
    title = soup.title.get_text(strip=True) if soup.title else url
    text = clean_text(soup.get_text('\n', strip=True))
    return {'url': url, 'title': title, 'text': text, 'chars': len(text), 'page_type': classify_page(url, title, text)}

def discover_links(base_url: str, limit: int = 50) -> list[str]:
    base_url = normalize_url(base_url)
    response = requests.get(base_url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    links = {base_url}
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith(('mailto:', 'tel:', 'javascript:', 'whatsapp:', 'tg:')):
            continue
        full_url = normalize_url(urljoin(base_url + '/', href))
        if is_same_domain(full_url, base_url):
            links.add(full_url)
        if len(links) >= limit:
            break
    return sorted(links)

def chunk_text(text: str, chunk_size: int = 1100, overlap: int = 150) -> list[str]:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    chunks = []
    current = ''
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= chunk_size:
            current += ('\n' if current else '') + paragraph
        else:
            if len(current) > 100:
                chunks.append(current.strip())
            current = paragraph
    if len(current) > 100:
        chunks.append(current.strip())
    final = []
    for chunk in chunks:
        if len(chunk) <= chunk_size + 200:
            final.append(chunk)
        else:
            start = 0
            while start < len(chunk):
                part = chunk[start:start + chunk_size].strip()
                if len(part) > 100:
                    final.append(part)
                start += chunk_size - overlap
    return final

def parse_site(base_url: str, limit: int = 50) -> dict:
    pages = []
    chunks = []
    errors = []
    for url in discover_links(base_url, limit=limit):
        try:
            page = extract_page(url)
            if page['chars'] > 100:
                page_chunks = chunk_text(page['text'])
                page['chunks_count'] = len(page_chunks)
                pages.append(page)
                for i, chunk in enumerate(page_chunks):
                    chunks.append({'id': f'{len(chunks)+1}', 'page_url': page['url'], 'page_title': page['title'], 'page_type': page.get('page_type', 'general'), 'chunk_index': i, 'text': chunk})
        except Exception as exc:
            errors.append({'url': url, 'error': str(exc)})
    return {'site': base_url, 'updated_at': datetime.now().isoformat(timespec='seconds'), 'pages_count': len(pages), 'chunks_count': len(chunks), 'tour_pages_count': len([p for p in pages if p.get('page_type') == 'tour']), 'errors_count': len(errors), 'pages': pages, 'chunks': chunks, 'errors': errors}
