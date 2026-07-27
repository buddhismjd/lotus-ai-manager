from fastapi.testclient import TestClient

from backend.main import app


def main() -> None:
    client = TestClient(app)
    health = client.get("/widget/health")
    embed = client.get("/widget/embed")
    js = client.get("/widget/widget.js")
    css = client.get("/widget/widget.css")
    assert health.status_code == 200 and health.json()["status"] == "ok"
    assert embed.status_code == 200 and "/api/sales/chat" in embed.text
    assert js.status_code == 200 and css.status_code == 200
    print("W-1.0 smoke: OK")
    print("health_endpoint=OK")
    print("tilda_embed=OK")
    print("assets=OK")


if __name__ == "__main__":
    main()
