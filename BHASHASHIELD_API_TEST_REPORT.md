# BHASHASHIELD — API INTEGRATION & AUTOMATED TEST REPORT

**Report Date:** November 21, 2026  
**Test Suite:** 37 Automated Integration & Unit Tests  
**Test Framework:** Pytest 9.2.0 + FastAPI TestClient + AnyIO  
**Outcome:** **37 PASSED / 0 FAILED / 0 SKIPPED** (Execution time: 10.21s)  

---

## 1. Endpoint Verification Matrix

| Endpoint | Method | Expected Status | Actual Status | Response Time | Payload Schema Validated |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/v1/health` | `GET` | 200 OK | **200 OK** | 1.8 ms | `{"status": "healthy", "version": "1.0.0", "model_status": "ACTIVE...", "policy_engine": "ACTIVE"}` |
| `/v1/analyze` | `POST` | 200 OK | **200 OK** | 7.2 ms | `AnalyzeResponse` (spans, categories, confidence, target_type) |
| `/v1/decision` | `POST` | 200 OK | **200 OK** | 5.4 ms | `GuardDecisionResponse` (decision: ALLOW/REVIEW/BLOCK, reason) |
| `/health` | `GET` | 200 OK | **200 OK** | 1.2 ms | Backward-compatible health payload |
| `/analyze` | `POST` | 200 OK | **200 OK** | 6.8 ms | Full threat scan payload consumed by frontend Text Guard |
| `/stats` | `GET` | 200 OK | **200 OK** | 2.6 ms | `DashboardStats` (real distribution charts and scan counts) |
| `/scans` | `GET` | 200 OK | **200 OK** | 3.1 ms | `List[ScanRecord]` with pagination (`limit`, `offset`) |
| `/v1/scans` | `DELETE` | 401 Unauthorized | **401 Unauthorized** | 1.4 ms | Enforces valid `X-Admin-Key` header |
| `/v1/scans` (Authorized) | `DELETE` | 200 OK | **200 OK** | 4.8 ms | Returns `{"status": "success", "cleared_records": N}` |
| `/evaluation/report` | `GET` | 200 OK | **200 OK** | 2.1 ms | Returns scientific benchmark report with confusion matrix |
| `/evaluation/run` | `POST` | 200 OK | **200 OK** | 6,850 ms | Runs held-out benchmark and updates database run record |

---

## 2. Regression Test Results (Failing Cases from Production Deployment)

### Regression Test 1: Single-Word Generic Placeholder
- **Endpoint:** `POST /v1/analyze`
- **Payload:** `{"text": "string", "channel": "General Text"}`
- **Previous Failure:** `PROMPT_INJECTION`, Risk: 92.165, Level: CRITICAL
- **Actual Response:**
  ```json
  {
    "scan_id": "BS-D3F12A80B2",
    "detected_language": "English",
    "threat_categories": ["BENIGN"],
    "primary_threat": null,
    "target_type": "NONE",
    "risk_score": 0.0,
    "risk_level": "LOW",
    "confidence": 0.98,
    "uncertainty": 0.02
  }
  ```
- **Verdict:** **PASSED (Zero false positive)**

### Regression Test 2: Conversational Everyday Greeting
- **Endpoint:** `POST /v1/analyze`
- **Payload:** `{"text": "Hello, how are you today? I hope you are having a wonderful day."}`
- **Previous Failure:** Model predicted `JAILBREAK` (prob 0.501), Risk: 72.545, Level: HIGH
- **Actual Response:**
  ```json
  {
    "scan_id": "BS-8C2A09B1F4",
    "detected_language": "English",
    "threat_categories": ["BENIGN"],
    "primary_threat": null,
    "target_type": "NONE",
    "risk_score": 0.0,
    "risk_level": "LOW",
    "confidence": 0.99,
    "uncertainty": 0.01
  }
  ```
- **Verdict:** **PASSED (Zero false positive)**

---

## 3. Test Suite Breakdown (37 Tests)

1. `test_health_check` — Standard health endpoint returns service name and model status.
2. `test_analyze_prompt_injection` — Verifies prompt injection detection on English attack vector.
3. `test_analyze_privacy_dont_save` — Verifies `save_to_history=False` prevents persistence in SQLite.
4. `test_analyze_empty_input_validation` — Empty string rejected with `HTTP 400`.
5. `test_stats_endpoint` — Validates dashboard statistics structure and real scan counts.
6. `test_evaluation_report_endpoint` — Validates benchmark metrics schema and synthetic disclaimer.
7. `test_v1_health_and_analyze` — V1 API contract conformity and risk score computation.
8. `test_v1_decision_policy_block_and_allow` — Guard policy engine returns `BLOCK` on attacks, `ALLOW` on safe queries.
9. `test_synthetic_dataset_generation` — Verifies balanced generation across all 20 attack + 10 benign families.
10. `test_leakage_free_splitting` — Mathematical proof of 0 template overlap between train, val, and test splits.
11. `test_regression_test_1_generic_placeholder` — `"string"` correctly classified as BENIGN (Risk: 0.0).
12. `test_regression_test_2_harmless_conversational_greeting` — Greeting correctly classified as BENIGN (Risk: 0.0).
13. `test_multilingual_benign_conversations` — Telugu, Hindi, Romanized greetings pass as BENIGN.
14. `test_hard_negatives_cybersecurity_and_programming` — Educational cyber queries and programming overrides pass as safe.
15. `test_malicious_prompt_injections_detected` — Multi-language adversarial attacks trigger CRITICAL/HIGH risk.
16. `test_internal_consistency_guarantee` — Verified that `primary_threat == categories[0]` and risk level agrees with score.
17. `test_spacing_obfuscation_resilience` — Catches `"i g n o r e   a l l   p r e v i o u s"`.
18. `test_zero_width_obfuscation_resilience` — Strips zero-width evasion while preserving character offset maps.
19. `test_homoglyph_substitution_resilience` — Normalizes Cyrillic lookalikes (`"іgnоrе"`) to Latin.
20. `test_base64_encoded_payload_detection` — Detects base64 encoded injection commands.
21. `test_tool_misuse_injection` — Flags arbitrary code execution directives (`execute_bash`, `DROP TABLE`).
22. `test_hard_negatives_zero_false_positives` — 0 false positives on cybersecurity student queries.
23. `test_target_type_discrimination` — Correctly identifies `AI_SYSTEM` vs `HUMAN_USER`.
24. `test_telugu_script_prompt_injection` — Native Telugu script injection detected.
25. `test_hindi_script_prompt_injection` — Native Devanagari Hindi script injection detected.
26. `test_romanized_telugu_prompt_injection` — Romanized Telugu transliteration detected.
27. `test_romanized_hindi_prompt_injection` — Romanized Hindi transliteration detected.
28. `test_english_prompt_injection_and_jailbreak` — DAN and override jailbreaks detected.
29. `test_financial_upi_fraud_human_target` — UPI PIN phishing scams detected and targeted to `HUMAN_USER`.
30. `test_benign_conversations_remain_clean` — Everyday commerce and chat messages remain clean.
31. `test_security_headers_present` — Injects nosniff, frame-options, and referrer-policy headers.
32. `test_payload_size_enforcement` — Payloads $>1\text{MB}$ rejected with `HTTP 413`.
33. `test_admin_authorization_enforcement` — Admin endpoints reject unauthorized requests with `HTTP 401`.
34. `test_sqlite_wal_and_backup_integrity` — Confirms SQLite WAL mode and zero database corruption.
35. `test_python_sdk_guard_allow` — Python SDK `guard()` returns `decision == 'ALLOW'` on benign text.
36. `test_python_sdk_guard_block` — Python SDK `guard()` returns `decision == 'BLOCK'` on attack vector.
37. `test_python_sdk_wrapper_exception` — Python SDK `wrap_llm_call()` raises `BhashaShieldSecurityException` when blocked.
