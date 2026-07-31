from pathlib import Path

from backend.config import BASE_DIR


def main() -> None:
    widget_dir = Path(BASE_DIR) / "widget"
    js = (widget_dir / "widget.js").read_text(encoding="utf-8")
    css = (widget_dir / "widget.css").read_text(encoding="utf-8")
    assert "const appendCard" in js
    assert "normalizedCardActions" in js
    assert "ai-bodhi__card-badge" in css
    assert "ai-bodhi__card-actions" in css
    print("CB-1.5 Rich Cards 2.0 smoke: OK")


if __name__ == "__main__":
    main()
