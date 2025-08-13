# Security Compliance Notes

- Secrets never exposed to client; API key server-only
- Inputs validated; outputs sanitized for UI display
- Rate limiting and logging per endpoint
- No shell execution; no eval; safe subprocess patterns avoided
- Docs avoid copy/paste of destructive commands; use placeholders
- Ensure GDPR-style data minimization for logs