@echo off
chcp 65001 > nul
call .venv\Scripts\activate.bat
python -c "import json; from backend.config import KNOWLEDGE_FILE; d=json.loads(KNOWLEDGE_FILE.read_text(encoding='utf-8')); p=[x for x in d.get('pages',[]) if x.get('page_type')=='product']; print('PRODUCTS:',len(p)); [print('-',x.get('title'),'|',x.get('price'),x.get('currency'),'|',x.get('url')) for x in p]"
pause
