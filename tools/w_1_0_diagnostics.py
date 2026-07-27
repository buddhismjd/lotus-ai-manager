from pathlib import Path

from backend.config import BASE_DIR, CORS_ALLOWED_ORIGINS


def main() -> None:
    widget = Path(BASE_DIR) / "widget"
    required = ["widget.js", "widget.css", "tilda_embed.html"]
    missing = [name for name in required if not (widget / name).is_file()]
    assert not missing, f"Missing widget files: {missing}"
    assert "https://svet-lotosa.tilda.ws" in CORS_ALLOWED_ORIGINS
    js = (widget / "widget.js").read_text(encoding="utf-8")
    assert "AbortController" in js
    assert "AI_BODHI_HEALTH_URL" in js
    print("W-1.0 diagnostics: OK")
    print("tilda_origin=OK")
    print("widget_assets=OK")
    print("timeout_retry=OK")


if __name__ == "__main__":
    main()
