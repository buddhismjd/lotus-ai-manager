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
DATABASE_FILE = DATA_DIR / "lotus_ai.db"

def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

CORS_ALLOWED_ORIGINS = tuple(
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "https://svet-lotosa.tilda.ws,https://svet-lotosa.ru",
    ).split(",")
    if origin.strip()
)
CORS_ALLOW_LOCALHOST = _env_bool("CORS_ALLOW_LOCALHOST", True)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
CHAT_RATE_LIMIT_PER_MINUTE = _env_int("CHAT_RATE_LIMIT_PER_MINUTE", 30)
RESET_RATE_LIMIT_PER_MINUTE = _env_int("RESET_RATE_LIMIT_PER_MINUTE", 10)
SQLITE_BUSY_TIMEOUT_MS = _env_int("SQLITE_BUSY_TIMEOUT_MS", 5000)
SECURITY_LOG_FILE = Path(os.getenv("SECURITY_LOG_FILE", str(LOGS_DIR / "security.jsonl")))
