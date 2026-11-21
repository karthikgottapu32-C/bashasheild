# BHASHASHIELD — PHASE 2.2 PRIVACY & DATA GOVERNANCE REPORT
## Zero Data Retention, PII Protection & Regulatory Compliance

**Document Version:** 2.2.0  
**Date:** November 21, 2026  
**Compliance Scope:** GDPR (Art. 5, 25, 32), India DPDPA 2023, Zero Data Retention (ZDR)  
**Verification Status:** VERIFIED & ENFORCED

---

## 1. Privacy-by-Design Architecture

BhashaShield handles security-sensitive prompts that may contain proprietary source code, confidential organizational directives, or personal financial details. To protect user privacy, the platform adheres strictly to **Privacy-by-Design** principles.

---

## 2. Zero Data Retention (ZDR) & Ephemeral Processing

BhashaShield provides clients with explicit, programmatic control over whether inbound prompts are persisted to disk:

1. **The `save_to_history` Flag:**
   - Every API request supports a boolean parameter: `save_to_history: false`.
   - When set to `false`, the backend processes the text purely in transient memory for classification, scoring, and explanation generation, and immediately discards the full text upon response transmission.
2. **Database Verification:**
   - When `save_to_history = false`, the `scans` table records only operational metadata:
     - `scan_id`: Cryptographically generated pseudonymous identifier (e.g., `BS-86D16677CE`).
     - `text_preview`: Truncated, bounded preview string (maximum 80 characters).
     - `full_text`: `NULL` (never written to disk).
     - `risk_score`, `risk_level`, `detected_language`: Statistical classification output.
3. **Automated Verification Test:**
   - `backend/app/tests/test_api.py::test_analyze_privacy_dont_save` verifies that queries with `save_to_history: false` write `NULL` to the database.

---

## 3. PII & Sensitive Credential Handling

During analysis of social engineering and financial phishing attacks, raw prompts frequently contain sensitive data (e.g., telephone numbers, UPI IDs, passwords, Aadhaar numbers):

1. **Log Redaction:**
   - Server stdout/stderr logs emit only the `scan_id`, `detected_language`, and high-level `risk_score`. Raw user prompts are strictly excluded from logging statements.
2. **Bounded Preview Strings:**
   - Previews in audit dashboards are clamped to 80 characters followed by an ellipsis (`...`), preventing sensitive text embedded deeper in the prompt from being exposed in summary views.
3. **No External Cloud Telemetry:**
   - Model inference and heuristic rule matching run 100% locally on the host container. Zero customer prompt tokens are transmitted to external third-party LLM APIs or telemetry collectors.

---

## 4. Regulatory Compliance Mapping

| Regulatory Standard | Requirement | BhashaShield Implementation | Compliance Status |
|:---|:---|:---|:---:|
| **GDPR Art. 5(1)(c)** | Data Minimization | Only security metrics retained; full text discarded when requested | **COMPLIANT** |
| **GDPR Art. 5(1)(e)** | Storage Limitation | Automatic rolling expiration options for historical scan records | **COMPLIANT** |
| **GDPR Art. 25** | Privacy by Design | Opt-in retention policy; default security headers on all endpoints | **COMPLIANT** |
| **India DPDPA 2023** | Purpose Limitation | Security scans performed solely for threat detection, no secondary use | **COMPLIANT** |
| **India DPDPA 2023** | Reasonable Safeguards | In-flight TLS 1.3 encryption, WAL SQLite storage with restricted permissions | **COMPLIANT** |

---

## 5. Privacy Conclusion

BhashaShield enables enterprise organizations and developers to deploy robust threat intelligence without introducing third-party data leakage risks or violating data residency and privacy mandates.
