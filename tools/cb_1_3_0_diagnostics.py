from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import BASE_DIR

widget = Path(BASE_DIR) / "widget"
css = (widget / "widget.css").read_text(encoding="utf-8")
js = (widget / "widget.js").read_text(encoding="utf-8")
embed = (widget / "tilda_embed.html").read_text(encoding="utf-8")

assert "--bodhi-navy: #123456" in css
assert "appendCollection" in js and "appendSuggestions" in js
assert "restoreConversation" in js and "resetConversation" in js
assert "AI_BODHI_RESET_URL" in embed

print("svet_lotosa_brand=OK")
print("rich_cards=OK")
print("session_restore=OK")
print("tilda_embed_contract=OK")
