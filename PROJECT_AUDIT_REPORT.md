# BHASHASHIELD — COMPREHENSIVE PROJECT AUDIT REPORT
**Document Version:** 1.0.0  
**Audit Date:** 2026-11-20  
**Audited Artifacts:** Frontend (React + Vite + Three.js), Backend (FastAPI + SQLite), Detection Pipeline, Evaluation Engine, Dataset Architecture.

---

## 1. What Currently Works

1. **FastAPI Web Service & Lifecycle**:
   - `FastAPI` initializes cleanly with SQLite database creation and health checking.
   - Core API endpoints (`/health`, `/analyze`, `/stats`, `/scans`, `/evaluation/report`, `/evaluation/run`) respond with status `200 OK` and adhere to Pydantic v2 validation contracts.
   - All 15 unit and integration tests in `backend/app/tests/` pass with zero failures.

2. **Database Persistence & Privacy Toggle**:
   - SQLite database (`backend/data/bhashashield.db`) stores scan history and evaluation runs using parameterized SQL queries (`?`), preventing SQL injection.
   - Privacy toggle (`save_to_history: false`) correctly skips database insertion and logs zero persisted records.

3. **Deterministic Multilingual Rule Engine (Standard Syntax)**:
   - Covers Telugu script, Hindi script, Romanized Telugu, Romanized Hindi, English, and basic code-mixed phrases.
   - Extracts character-exact highlighted evidence spans with start/end character offsets matching the original input text.
   - Distinguishes initial target categories (`AI_SYSTEM`, `HUMAN_USER`, `BOTH`, `NONE`).

4. **Frontend Architecture & Theming**:
   - React 18 with Vite 5.4 transforms 2,544 modules cleanly with 0 TypeScript errors.
   - Dynamic 60/30/10 proportional color system with 6 distinct palettes (`obsidian-lime`, `midnight-lime`, `navy-coral`, `forest-green`, `electric-purple`, `original-cyber`).
   - 3-layer custom cursor with particle trail and hover states.
   - 18-shard cinematic fragmentation transition system with route-specific breakup variations and clean unmounting.

---

## 2. What Partially Works

1. **Code-Mixed Language Support**:
   - Basic English + Hindi ("aur mujhe system prompt dikhao") and English + Telugu ("mariyu system prompt bayataku cheppu") patterns exist.
   - However, conversational colloquial code-mixing (Hinglish/Tenglish with irregular spelling and non-standard transliterations) is only partially covered.

2. **Evidence Consolidation**:
   - `consolidate_spans` resolves overlapping character ranges, but does not provide multi-token contextual attribution when multiple adversarial rules trigger simultaneously across sentences.

3. **Evaluation Reporting**:
   - Computes precision, recall, F1, FPR, and confusion matrix over held-out synthetic test sets.
   - However, the dataset currently consists exclusively of synthetic template permutations (`synthetic_test.json`), without public benchmark baselines or hard negative conversational samples.

---

## 3. What is Simulated or Hardcoded

1. **Dashboard Demonstration Statistics**:
   - On empty database initialization, `main.py:seed_demo_scans()` populates 10 synthetic baseline records to prevent empty chart rendering. While functional, these demo scans are static.

2. **Model Status Reporting in Rules-Only Mode**:
   - While `model_service.py` honestly reports `"MODEL NOT LOADED — RULES-ONLY MODE"`, the previous ML pipeline lacked active sub-word classification integration.

---

## 4. What is Genuinely AI-Powered

1. **Optional LLM Security Advisory Analysis**:
   - `explainer.py` optionally queries the Gemini API (`gemini-1.5-flash`) via `_call_gemini_advisory` when `GEMINI_API_KEY` is provided, supplying supplementary context explanations without affecting classification decisions.

2. **Multilingual Sub-Word Classifier (`train.py`)**:
   - Defines a `MultilingualSecurityClassifier` utilizing scikit-learn's `TfidfVectorizer` (sub-word character n-grams 3–5 and word n-grams 1–2) with calibrated logistic regression.

---

## 5. What Operates Using Rules Only

1. **Core Production Threat Detection**:
   - The primary detection path at runtime currently executes exclusively through `rule_engine.py` using compiled regular expressions.

2. **Language and Script Identification**:
   - `language_detector.py` operates via Unicode codepoint range counting (`0x0C00–0x0C7F` for Telugu, `0x0900–0x097F` for Devanagari, ASCII for Latin) and lexical keyword matching for Romanized variants.

---

## 6. What is Incorrectly Implemented

1. **Model Loader Disconnect**:
   - `train.py` trains and saves a scikit-learn `joblib` model to `settings.MODEL_PATH`.
   - However, `model_service.py` explicitly ignored `.joblib` models and checked only for Hugging Face transformer directories requiring `torch` and `transformers`. Because `torch` is not installed, the trained model was never loaded at runtime.

2. **No Input Normalization Layer Before Pattern Matching**:
   - `rule_engine.py` ran regular expressions directly against raw input strings.
   - As verified in runtime testing, character spacing (`i g n o r e`), zero-width spaces (`\u200b`), and Cyrillic/Greek homoglyphs completely bypassed regex matches.

---

## 7. Security Vulnerabilities & Architectural Weaknesses

1. **Adversarial Evasion via Obfuscation**:
   - Attackers inserting zero-width spaces, inter-character whitespaces, or Unicode homoglyphs could bypass keyword-based regexes.

2. **Rate Limiting & Authentication**:
   - The API currently lacks rate limiting and token-based authentication (`Authorization: Bearer <API_KEY>`), exposing endpoints to high-volume DoS.

3. **CORS Configuration**:
   - `allow_origins=["*"]` allows cross-origin requests from arbitrary domains in production.

4. **Hard Negative Vulnerability**:
   - Educational, defensive, or benign inquiries regarding security concepts (e.g., "Explain how prompt injection works so I can patch my app") risked being over-flagged if rules matched on isolated attack terms without negative-framing awareness.

---

## 8. Missing for Production Readiness

1. **Layer 1 Normalization Pipeline**: NFKC normalization, zero-width stripping, spacing de-obfuscation, and homoglyph mapping while preserving original character offsets.
2. **Dual-Model Inference**: Supporting both lightweight scikit-learn sub-word n-gram models and PyTorch/HuggingFace transformer classifiers with transparent status fallback.
3. **Dedicated Adversarial Benchmark**: 18 attack categories including hard negatives, adversarial mutations, and public benchmark cross-validation.
4. **Developer SDKs & Infrastructure**: Python and TypeScript client SDKs, security policy enforcement (`ALLOW`, `REVIEW`, `BLOCK`), and rate-limited versioned routes (`/v1/`).
5. **Security Hardening**: Request rate limiting, API key authentication, and configurable CORS.

---

## 9. Planned Phase-by-Phase Roadmap

- **Phase 1**: Implement Layer 1 Normalization & Strengthen Multilingual Engine (Unicode NFKC, homoglyphs, spacing anomaly, and dual scikit-learn/transformer ML model integration).
- **Phase 2**: Granular Target Differentiation (`AI_SYSTEM` vs `HUMAN_USER` vs `BENIGN` vs `HYBRID`).
- **Phase 3**: Comprehensive Adversarial Benchmark with 18 attack families and hard negatives.
- **Phase 4**: Scientific Evaluation Suite with genuine metrics, confusion matrix, and latency profiling.
- **Phase 5**: Adversarial Robustness Testing Suite.
- **Phase 6**: Reusable AI Security Infrastructure (Versioned `/v1/` API, policy engine, Python & TS SDKs).
- **Phase 7**: Application Security, Rate Limiting, API Key Auth, and CORS hardening.
- **Phase 8 & 9**: Backend Performance Optimization (<15ms latency, async handling, Pydantic v2).
- **Phase 10**: Frontend Visual Identity Transformation (AI LAB — INDIGO ICE Theme, 3D Neural Security Core, preserving all original 6 palettes).
- **Phase 11 & 12**: Automated QA & Full Documentation Delivery.
