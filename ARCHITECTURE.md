# BhashaShield Architecture Specification

## 1. Executive Summary

BhashaShield is a multi-tier AI security intelligence platform engineered to protect Large Language Models (LLMs), agentic toolchains, and communication channels against multilingual prompt injection, adversarial evasion, and Indic-script obfuscation.

```
                              [ Incoming Untrusted Input ]
                                          │
                                          ▼
                ┌──────────────────────────────────────────────────┐
                │   LAYER 1: Input Normalization & De-obfuscation  │
                │   - Unicode NFKC canonical decomposition         │
                │   - Zero-width character stripping (\u200B-F)    │
                │   - Homoglyph mapping (Cyrillic/Greek -> Latin)  │
                │   - Inter-character whitespace collapse          │
                │   - Base64 / Hex / ROT13 anomaly extraction      │
                │   - Bi-directional raw-to-normalized offset map  │
                └─────────────────────────┬────────────────────────┘
                                          │
                                          ▼
                ┌──────────────────────────────────────────────────┐
                │   LAYER 2: Deterministic Rule Engine             │
                │   - Multilingual regex catalog (18 families)     │
                │   - Telugu Script (తెలుగు) patterns              │
                │   - Devanagari Hindi (हिन्दी) patterns          │
                │   - Romanized Indic (te-Latn, hi-Latn) patterns  │
                │   - Tool execution & command injection traps     │
                │   - Target differentiation (AI vs Human)         │
                │   - Hard negative defensive inquiry filtering    │
                └─────────────────────────┬────────────────────────┘
                                          │
                                          ▼
                ┌──────────────────────────────────────────────────┐
                │   LAYER 3: Multilingual Statistical ML Engine    │
                │   - Sub-word character n-grams (3-5)             │
                │   - Morphological word n-grams (1-2)             │
                │   - Calibrated probability estimation            │
                │   - Fallback transparency: ML vs Rules-Only      │
                └─────────────────────────┬────────────────────────┘
                                          │
                                          ▼
                ┌──────────────────────────────────────────────────┐
                │   LAYER 4: Guardrail Decision Policy Engine      │
                │   - Risk score thresholding (0.0 to 100.0)       │
                │   - Categorical action: ALLOW | REVIEW | BLOCK   │
                │   - Granular span highlighting for UI auditing   │
                │   - Low-latency sub-15ms response profiling      │
                └─────────────────────────┬────────────────────────┘
                                          │
                                          ▼
                             [ Policy Decision Output ]
```

---

## 2. Multi-Layer Detection Pipeline

### Layer 1: Input Normalization (`backend/app/core/normalizer.py`)
Attackers frequently exploit visual similarity and character spacing to bypass naive tokenizers and regex filters. BhashaShield passes all untrusted strings through:
1. **Unicode NFKC Normalization**: Resolves compatibility characters and full-width forms.
2. **Zero-Width Stripping**: Removes non-rendering characters including `\u200B` (ZWSP), `\u200C` (ZWNJ), `\u200D` (ZWJ), `\uFEFF` (BOM), and direction overrides.
3. **Homoglyph Normalization**: Transliterates visually identical Cyrillic and Greek glyphs (e.g., Cyrillic `а`, `е`, `о`, `р`, `і`) to standard ASCII Latin.
4. **Spacing Collapse**: Identifies single-spaced inter-character padding (e.g. `i g n o r e   a l l`) and collapses words while preserving inter-word boundaries.
5. **Coordinate Mapping**: Tracks byte offsets so that rule matches on normalized text accurately map back to character spans in the user's raw input.

### Layer 2: Deterministic Rule Engine (`backend/app/core/rule_engine.py`)
- Curated catalog covering 18 distinct threat families across Telugu, Hindi, Romanized Indic, English, and Code-Mixed text.
- Differentiates between attacks targeting the **AI System** (prompt injection, jailbreak, system prompt extraction, tool execution) and attacks targeting the **Human User** (financial fraud, UPI PIN extortion, phishing).
- Includes **Hard Negative Filtering**: Identifies educational and definitional inquiries (e.g., *"What is prompt injection?"*, *"How to override __str__ in Python?"*) to eliminate false positives.

### Layer 3: Multilingual Statistical Classifier (`backend/app/ml/classifier.py`)
- Employs a dual-pipeline architecture:
  - Primary: `MultilingualSecurityClassifier` utilizing sub-word character n-grams (ranges 3-5) to capture Indic phonetic roots and transliterations, combined with word n-grams (1-2) and Calibrated Logistic Regression.
  - Secondary / Advanced: MuRIL (Multilingual Representations for Indian Languages) / XLM-RoBERTa transformer integration.
- **Strict Transparency**: The engine dynamically reports its operational state (`ACTIVE: BhashaShield-MuRIL-v1 (scikit-learn)`, `ACTIVE: MuRIL Transformer (PyTorch)`, or `MODEL NOT LOADED — RULES-ONLY MODE`).

### Layer 4: Decision Policy Engine (`/v1/decision`)
Provides actionable security verdicts for downstream AI orchestrators:
- `BLOCK`: Risk score ≥ 60.0, or any CRITICAL severity rule match, or high-confidence AI-targeted prompt injection.
- `REVIEW`: Risk score ≥ 25.0, or HIGH severity rule match, or anomalous model probability.
- `ALLOW`: Safe query with clean baseline characteristics.

---

## 3. Technology Stack & Directory Structure

```
hack with aditya/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── normalizer.py      # Layer 1 normalization & coordinate mapping
│   │   │   ├── rule_engine.py     # Layer 2 rule engine & target differentiation
│   │   │   ├── model_service.py   # Layer 3 ML model service & loader
│   │   │   └── detector.py        # Pipeline orchestrator
│   │   ├── dataset/
│   │   │   └── generator.py       # 18-family adversarial benchmark generator
│   │   ├── ml/
│   │   │   ├── classifier.py      # Sub-word n-gram classifier architecture
│   │   │   ├── train.py           # Calibration and training pipeline
│   │   │   └── evaluate.py        # Latency profiling & scientific evaluation
│   │   ├── tests/
│   │   │   ├── test_api.py        # API endpoint verification
│   │   │   ├── test_generator.py  # Dataset integrity & zero-leakage tests
│   │   │   ├── test_robustness.py # Adversarial obfuscation resilience tests
│   │   │   └── test_rules.py      # Multilingual rule matching tests
│   │   ├── config.py              # Application settings
│   │   ├── database.py            # SQLite audit log & metrics persistence
│   │   ├── main.py                # FastAPI entrypoint (/v1/ endpoints)
│   │   └── models.py              # Pydantic data schemas
│   └── data/                      # Model weights and benchmark splits
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CyberShield3D.tsx  # Three.js WebGL reactive visualization
│   │   │   ├── CustomCursor.tsx   # GPU-accelerated canvas cursor
│   │   │   └── Navbar.tsx         # Unified navigation & theme selector
│   │   ├── theme/
│   │   │   └── palettes.ts        # 7 color palettes (Indigo Ice, Obsidian Lime, etc.)
│   │   ├── views/
│   │   │   ├── LandingPageView.tsx# Command hero & interactive scanner
│   │   │   ├── TextGuardView.tsx  # Multi-channel text analysis console
│   │   │   ├── DashboardView.tsx  # Threat intelligence & incident analytics
│   │   │   └── EvaluationView.tsx # Scientific benchmark results & latency profile
│   │   └── App.tsx                # Cinematic breakup transitions & routing
├── sdk/
│   ├── python/                    # BhashaShield Python SDK
│   └── typescript/                # BhashaShield TypeScript SDK
└── backups/                       # Complete verified design snapshots
```
