# BHASHASHIELD — PHASE 2.3 PRIVACY & DATA GOVERNANCE REPORT
## Zero Data Retention (ZDR), PII Redaction & Data Protection Standards

**Document Version:** 2.3.0  
**Date:** November 21, 2026  
**Compliance Frameworks:** GDPR (Art. 5, 25, 32), India Digital Personal Data Protection Act (DPDPA 2023)  
**Status:** **AUDITED & VERIFIED**

---

## 1. Privacy-by-Design Architecture

AI security platforms process inbound prompts that may contain proprietary corporate directives, personal user identities, or confidential financial details. To protect data subjects, BhashaShield operates strictly on a **Privacy-by-Design** foundation.

---

## 2. Zero Data Retention (ZDR) & Ephemeral Execution

Clients are provided with explicit programmatic control over data persistence:

1. **The `save_to_history` Parameter:**
   - Every API request supports a boolean parameter: `"save_to_history": false`.
   - When set to `false`, the backend analyzes the text entirely within transient volatile memory and immediately discards the prompt text upon sending the HTTP response.
2. **Database Verification:**
   - When `save_to_history = false`, the `scans` table writes `NULL` to the `full_text` column.
   - Only pseudonymous metadata (`scan_id`, bounded `text_preview` up to 80 chars, `risk_score`, `detected_language`) is recorded for aggregate telemetry.
3. **Automated Unit Verification:**
   - `backend/app/tests/test_api.py::test_analyze_privacy_dont_save` executes and confirms that `full_text` is `NULL` in the database.

---

## 3. PII & Sensitive Credential Handling

During analysis of phishing and financial scam inputs, user text often contains sensitive data (e.g., telephone numbers, UPI IDs, passwords, Aadhaar numbers):

1. **Log Sanitization:**
   - Server stdout/stderr logs emit only the `scan_id`, `detected_language`, and high-level `risk_score`. Raw user prompt strings are strictly excluded from logging statements.
2. **Bounded Preview Strings:**
   - Previews in audit dashboards are clamped to 80 characters followed by an ellipsis (`...`), preventing sensitive data embedded deeper in the prompt from being exposed in summary views.
3. **Zero External Cloud Telemetry:**
   - Model inference and heuristic rule matching run 100% locally on the host container. Zero customer prompt tokens are transmitted to external third-party LLM APIs or telemetry collectors.

---

## 4. Regulatory Compliance Mapping

| Legal Standard | Requirement | BhashaShield Implementation | Compliance Verdict |
|:---|:---|:---|:---:|
| **GDPR Art. 5(1)(c)** | Data Minimization | Only security metrics retained; full text discarded when requested | **COMPLIANT** |
| **GDPR Art. 5(1)(e)** | Storage Limitation | Configurable retention expiration for historical audit logs | **COMPLIANT** |
| **GDPR Art. 25** | Privacy by Design | Opt-in retention policy; default security headers on all endpoints | **COMPLIANT** |
| **India DPDPA 2023 §4** | Purpose Limitation | Scans executed exclusively for security triage, no secondary use | **COMPLIANT** |
| **India DPDPA 2023 §8** | Reasonable Safeguards | In-flight TLS 1.3 encryption, WAL SQLite storage with restricted permissions | **COMPLIANT** |

---

## 5. Privacy Conclusion

BhashaShield enables enterprise organizations and developers to deploy robust threat intelligence without introducing third-party data leakage risks or violating data residency and privacy mandates.
