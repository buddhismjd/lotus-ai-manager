from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import backend.main as main_module

client = TestClient(main_module.app)
css = client.get("/widget/widget.css")
js = client.get("/widget/widget.js")
embed = client.get("/widget/embed")

assert css.status_code == 200
assert js.status_code == 200
assert embed.status_code == 200
assert "#123456" in css.text
assert "/api/sales/session" in embed.text
assert "/api/sales/reset" in embed.text
assert "https://YOUR-API-DOMAIN/" not in embed.text

print("live_widget_assets=OK")
print("responsive_brand_theme=OK")
print("runtime_embed_urls=OK")
