# Security & Anti-Cheat Controls

- Server-only OpenWebUI calls; client never sees tags/URLs
- Rate limiting per user/IP; cooldowns on repeated failure
- Randomized seeds and parameters per attempt; per-user session binding
- Output redaction for sensitive responses; context-aware filtering
- Similarity checks vs known solutions; anomaly logging
- CSRF protection on forms; input validation; output sanitization in UI
- Minimal error leakage; structured error responses only
- Logging with privacy (no secrets); audit of bypass attempts