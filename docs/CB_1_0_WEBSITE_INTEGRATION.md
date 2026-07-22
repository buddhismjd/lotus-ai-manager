# CB-1.0 Website Integration

The FastAPI application now serves `/widget/widget.js`, `/widget/widget.css`, and `/widget/embed`.
The browser widget uses the stateful `/api/sales/chat` endpoint, preserves a session identifier in `localStorage`, renders rich collections and dialogue suggestions, and can be embedded into Tilda from one HTTPS backend domain.

## Production boundary

A Tilda page cannot reach `127.0.0.1` on the developer computer. Public use therefore requires an internet-accessible HTTPS backend domain. This stage prepares and verifies the integration contract; deployment is a separate infrastructure decision.
