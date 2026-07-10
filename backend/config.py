from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
SITE_URL = os.getenv('SITE_URL', 'https://svet-lotosa.tilda.ws/')
EMAIL_TO = os.getenv('EMAIL_TO', 'buddhismjd@gmail.com')
MIN_SEARCH_SCORE = int(os.getenv('MIN_SEARCH_SCORE', '2'))
AI_PROVIDER = os.getenv('AI_PROVIDER', 'local').lower()
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:3b')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
KNOWLEDGE_FILE = DATA_DIR / 'knowledge.json'
DIALOGS_FILE = DATA_DIR / 'dialogs.jsonl'
