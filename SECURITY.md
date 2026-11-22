# BhashaShield Security Policy & Hardening Guidelines

## 1. Security Architecture & Principles

BhashaShield is designed under the **Defense-in-Depth** and **Zero-Trust Input** paradigms:
1. **Never Trust Raw Input**: All incoming bytes pass through Unicode NFKC canonicalization, homoglyph mapping, and spacing sanitization prior to inspection.
2. **Transparent Decisioning**: When models or rules detect a threat, exact matching evidence, highlighted offsets, and risk scores are delivered back to the operator.
3. **Fail-Closed Policy**: If an unhandled anomaly occurs during analysis, the system reports HIGH risk with explicit diagnostic information rather than silently letting traffic pass.
4. **Privacy-First Operations**: Scans executed via `/v1/decision` or with `save_to_history: false` are analyzed strictly in-memory without persistent disk logging.

---

## 2. API Hardening & Rate Limiting

- **API Keys**: Clients authenticate using the `X-API-Key` header.
- **Rate Limiting**: Configured for 120 requests per client IP per minute on API endpoints to prevent brute-force probing and DoS attacks.
- **Input Bounds**: Maximum string length enforced at 10,000 characters by default (`settings.MAX_INPUT_LENGTH`) to protect against regex denial of service (ReDoS) and memory exhaustion.
- **CORS Restrictions**: Configurable via `CORS_ORIGINS` in `.env` to restrict cross-origin access in production environments.

---

## 3. Vulnerability Reporting

If you identify a security issue in BhashaShield or discover a novel bypass technique:
1. Please submit a private vulnerability report via [GitHub Security Advisories](https://github.com/karthikgottapu32-C/bashasheild/security/advisories) with a reproducible proof-of-concept.
2. If private reporting is unavailable, submit a report via GitHub Issues.
3. Notice: Direct telephone and email inboxes are inactive; all security reporting is handled via the official GitHub repository.
