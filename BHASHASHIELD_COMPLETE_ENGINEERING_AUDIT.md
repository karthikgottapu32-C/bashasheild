# BHASHASHIELD — COMPLETE ENGINEERING & ARCHITECTURAL AUDIT

**Audit Date:** November 21, 2026  
**Auditor:** Senior AI Security, ML, and Backend Systems Architect  
**Target Repository:** `karthikgottapu32-C/bashasheild` (Branch: `main`)  
**Deployment URL:** `https://bhashashield-api.onrender.com`  

---

## 1. Executive Summary

A comprehensive, end-to-end audit was conducted across the entire BhashaShield codebase, encompassing:
1. Backend architecture and FastAPI routers
2. ML classification engine and feature extractors
3. Synthetic and benchmark dataset pipelines
4. Normalization and character offset mapping
5. Language and script identification
6. Rule catalog and regex patterns
7. Risk calculation and decision engine
8. Explanation and actionable recommendation generation
9. Database persistence, privacy controls, and schema design
10. Security headers, rate limiting, and administrative authorization
11. Python and TypeScript client SDKs
12. Docker container configuration and Render deployment limits
13. Frontend UI-API contracts and telemetry displays

The audit confirmed the root causes for the reported production failures:
- **Test 1 (`string`)** was misclassified as `PROMPT_INJECTION` (Risk: 92.165, CRITICAL) because the single token `"string"` appeared exclusively inside Base64 evasion attack templates (`"Decode this base64 string..."`) in the synthetic training corpus and was absent from the sparse benign dataset. Consequently, the linear classifier assigned a disproportionately large positive weight to the token `string`. Combined with the lack of out-of-distribution (OOD) detection, the uncalibrated engine amplified this into a critical alert.
- **Test 2 (`Hello, how are you today? I hope you are having a wonderful day.`)** was misclassified as `JAILBREAK` (Probability: 0.501 vs BENIGN: 0.455, Risk: 72.545, HIGH) because the benign training set contained zero conversational greetings or everyday dialogues. When evaluated on unseen conversational English, the model's raw probability hovered at a coin-flip (0.501). The risk synthesis formula in `detector.py` unconditionally elevated any prediction with `is_malicious=True` into a high risk score (`50.0 + prob * 45.0 = 72.545`), while default fallback logic overwrote the primary threat to `PROMPT_INJECTION`, creating internal contradiction.

Below is the complete inventory of all architectural defects, their root causes, impacts, required remediations, and verification tests.

---

## 2. Comprehensive Inventory of Architectural Defects

### Issue 1: Sparse Benign Training Distribution Causing False Positives on Common Words
- **File & Function:** [`backend/app/dataset/generator.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/dataset/generator.py) — `TEMPLATE_FAMILIES`, [`backend/app/ml/train.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/ml/train.py) — `train_model`
- **Root Cause:** The benign dataset contained only 7 specialized families (mostly academic questions about prompt injection, UPI bills, and order status). Standard conversational English, Telugu, and Hindi greetings, technical questions, common vocabulary (including words like `"string"`, `"hello"`, `"system"`, `"function"`), and diverse everyday dialogue were completely absent from training.
- **Impact:** Any unseen harmless token that happened to co-occur with an attack template (e.g. `"string"` in Base64 evasion templates) or lacked sufficient benign weight was falsely classified as malicious with high confidence.
- **Required Correction:** Expand the dataset with comprehensive benign distributions: conversational greetings, general inquiries, technical programming queries, cultural discussions, and multi-domain texts across English, Telugu, Hindi, and Romanized forms.
- **Verification Test:** Unit regression test verifying that generic words (`"string"`, `"array"`, `"boolean"`) and everyday greetings (`"Hello, how are you today?"`) classify as `BENIGN` with Risk Score < 15.0.

---

### Issue 2: Arbitrary Additive Risk Score Synthesis Formula
- **File & Function:** [`backend/app/core/detector.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/core/detector.py) — lines 40–46 in `analyze_text`
- **Root Cause:** Risk score calculation used hardcoded heuristic jumps:
  ```python
  if model_finding and model_finding.is_malicious:
      combined_score = min(100.0, max(combined_score, 50.0 + (model_finding.probability * 45.0)))
  ```
  Even if the model predicted malicious with a marginal probability of 0.501 (a coin flip), the risk score immediately jumped to `50.0 + 22.545 = 72.545` (HIGH risk).
- **Impact:** Low-confidence ML predictions triggered severe alarms, generating unacceptable false positive rates on benign user inputs.
- **Required Correction:** Implement a calibrated decision engine where ML probability contributes proportionally to risk only when confidence exceeds calibrated validation thresholds (e.g. margin $\ge 0.25$ over second class, probability $\ge 0.70$, or confirmed by deterministic rule matches). If confidence is marginal, the engine should abstain or mark the finding as `UNCERTAIN` / `LOW`.
- **Verification Test:** Test with inputs yielding marginal model probabilities ($0.48 - 0.52$) ensuring they do not trigger HIGH or CRITICAL risk scores without corroborating rule evidence.

---

### Issue 3: Inconsistent Threat Category Fallback
- **File & Function:** [`backend/app/core/detector.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/core/detector.py) — lines 59–65 in `analyze_text`
- **Root Cause:** When no rule matched (`categories` was empty), but the risk score was elevated by the ML model, the code unconditionally defaulted:
  ```python
  if not cat_names:
      if risk_level != RiskLevel.LOW:
          cat_names = [ThreatCategory.PROMPT_INJECTION.value]
  ```
- **Impact:** Even when the ML model explicitly predicted `JAILBREAK` or `SOCIAL_ENGINEERING`, `cat_names` was overwritten to `PROMPT_INJECTION`, causing direct contradiction between `model_finding.predicted_class` and `primary_threat`.
- **Required Correction:** When rule categories are empty, propagate the ML model's predicted class if malicious, or `BENIGN` / `UNCERTAIN` if confidence is low. Ensure 100% agreement between primary threat, categories, and model finding.
- **Verification Test:** Assert `primary_threat == model_finding.predicted_class` for all ML-driven detections where rules do not fire.

---

### Issue 4: Absence of Out-of-Distribution (OOD) and Low-Information Abstention
- **File & Function:** [`backend/app/ml/classifier.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/ml/classifier.py), [`backend/app/core/model_service.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/core/model_service.py)
- **Root Cause:** The classifier calculated probabilities using softmax over linear model outputs without checking the magnitude of feature activations. A single isolated word or gibberish input produced non-zero sparse activations that forced an arbitrary top-1 classification.
- **Impact:** Single words, random strings, or out-of-domain sentences triggered high-confidence predictions on classes with slight bias.
- **Required Correction:** Calculate feature activation norm or entropy across prediction probabilities. If total TF-IDF vector norm is below threshold, or entropy is high (no clear winner), output `UNCERTAIN` / `BENIGN` with confidence penalty.
- **Verification Test:** Test single-word placeholders (`"string"`, `"test"`, `"hello"`, `"foo"`) and verify no malicious classification occurs.

---

### Issue 5: Hard Negatives & Quotation Context Disregard
- **File & Function:** [`backend/app/core/rule_engine.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/core/rule_engine.py) — `evaluate_rules`
- **Root Cause:** While an educational pattern check existed, it only matched specific prefix regexes (`"can you explain prompt injection"`). Contexts discussing attacks in technical papers, quoting an attack for incident reporting, or using programming terms (`"override"`, `"system"`, `"ignore"`) in harmless sentences lacked robust contextual gating.
- **Impact:** Legitimate technical discussions, research questions, and harmless code snippets could trigger false positive regex alerts.
- **Required Correction:** Enhance contextual filtering for quotations, security research inquiries, programming contexts (Python/Java/SQL keywords), and benign conversational markers.
- **Verification Test:** Benchmark suite on 15+ hard negative samples including security research abstracts, programming queries, and customer support inquiries.

---

### Issue 6: Language Detection Over-Confidence on Unknown Latin Input
- **File & Function:** [`backend/app/core/language_detector.py`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/app/core/language_detector.py) — `detect_language`
- **Root Cause:** If an input was in Latin script and contained zero Telugu, Hindi, or English dictionary matches, the fallback defaulted to:
  ```python
  detected_lang = "English"
  lang_code = "en"
  conf = min(0.98, 0.75 + (en_total * 0.03)) # = 0.75 even with 0 matches!
  ```
- **Impact:** Unknown strings, random characters, or unsupported European languages were reported as English with 75% confidence.
- **Required Correction:** If English, Telugu, and Hindi token hits are zero, report `"Undetermined (Latin)"` or `"Unknown"` with low confidence ($0.30 - 0.50$).
- **Verification Test:** Verify input `"xyzqwerty 1234"` yields `Undetermined` or low confidence ($< 0.50$).

---

### Issue 7: RAM Budget & Deployment Architecture Reality
- **File & Function:** [`backend/Dockerfile`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/Dockerfile), [`render.yaml`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/render.yaml)
- **Root Cause:** Render's free/starter tier provides **512 MB RAM**. Full HuggingFace transformer models (e.g. `google/muril-base-cased` at ~950MB weights + PyTorch runtime ~600MB) require $>1.5\text{ GB}$ resident RAM, causing an instant OOM crash (`SIGKILL` exit code 137) on container boot.
- **Impact:** Claiming to run full PyTorch MuRIL in production on a 512MB container results in immediate deployment failure.
- **Required Correction:** 
  1. Maintain a high-performance, calibrated multilingual n-gram classifier combined with robust deterministic normalization and rules that executes in $< 140\text{ MB}$ RAM, satisfying Render constraints with zero risk of OOM.
  2. Implement an optional transformer pipeline with clear hardware/memory requirement guards and transparent reporting in `/v1/health` (`"model_status"`).
  3. Benchmark both architectures and document memory and latency profiles transparently.
- **Verification Test:** Execute memory profiling script measuring process RSS during inference to ensure resident memory remains $< 250\text{ MB}$.

---

## 3. Action Plan & Roadmap

1. **Phase 2 & 3 (Data & ML Engine Overhaul):**
   - Re-engineer dataset generator with 500+ curated multilingual samples spanning 12 attack categories, 10 hard negative categories, and rich benign dialogue across English, Telugu, Hindi, and Romanized forms.
   - Re-train calibrated classifier with class balancing, sub-word character + word n-grams, and probability calibration.
   - Implement OOD activation thresholding and entropy-based confidence scoring.
2. **Phase 5 & 6 (Decision, Rules & Explainer):**
   - Eliminate arbitrary risk score formulas; establish unified decision pipeline.
   - Enforce 100% categorical consistency across model findings, primary threat, and explanations.
   - Refine offset mapping and contextual rules for hard negatives.
3. **Phase 8 & 9 (API & Security):**
   - Audit all endpoints (`/v1/health`, `/v1/analyze`, `/v1/decision`, `/stats`, `/scans`, `/evaluation/report`).
   - Validate rate limiting, security headers, and PII masking.
4. **Phase 10 & 11 (Automated Testing & Deployment):**
   - Expand automated test suite covering all regression cases, hard negatives, and multilingual vectors.
   - Verify Docker compatibility, commit, and push.
