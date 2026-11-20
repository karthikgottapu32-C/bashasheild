# BhashaShield Model Card: `BhashaShield-Multilingual-Classifier-v1`

## 1. Model Details

- **Model Identifier**: `BhashaShield-Multilingual-Classifier-v1`
- **Architecture**: Dual-pipeline hybrid architecture consisting of:
  - Sub-word character n-gram extraction (ranges 3-5, boundary-aware)
  - Word n-gram extraction (ranges 1-2)
  - Sub-linear TF-IDF term frequency scaling
  - Calibrated Classifier with Balanced L2 Logistic Regression (`C=2.0`)
- **Supported Languages**: Telugu (`te`), Hindi (`hi`), Romanized Telugu (`te-Latn`), Romanized Hindi (`hi-Latn`), English (`en`), and Code-Mixed text.
- **Supported Scripts**: Telugu, Devanagari, Latin, and Mixed script combinations.
- **Intended Use**: Real-time prompt injection detection, malicious instruction filtering, and AI guardrail enforcement.

---

## 2. Training Data & Preprocessing

- **Dataset**: BhashaShield Multi-Family Adversarial Benchmark (`backend/data/synthetic_train.json`).
- **Sample Count**: Stratified synthetic training utterances structured across diverse template families.
- **Preprocessing**: Unicode NFKC normalization, Cyrillic/Greek homoglyph normalization, grammatical Indic joiner preservation, zero-width stripping, and single-character spacing collapse.
- **Data Partitioning**: Strict template family split ensuring 0% template leakage into validation and test sets.

---

## 3. Quantitative Performance

Evaluated on unseen held-out test split (`backend/data/synthetic_test.json`, 840 samples across unseen families):

| Metric | Measured Value | Notes |
|---|---|---|
| **Overall Precision** | **96.55%** | Malicious vs Benign classification |
| **Overall Recall** | **90.32%** | High sensitivity across attack families |
| **Overall F1 Score** | **0.9333** | Balanced harmonic mean |
| **False Positive Rate** | **9.09%** | Reduced across benchmark; Telugu FPR: 0.0% |
| **Mean Latency** | **21.77 ms** | CPU inference on commodity hardware |
| **Median (P50) Latency** | **18.06 ms** | Fast guardrail response |
| **P95 Latency** | **42.86 ms** | Sub-50ms SLA compliance |

---

## 4. Ethical Considerations & Limitations

- **Synthetic Data Disclaimer**: Metrics are measured on synthetic evaluation datasets. Real-world performance may vary depending on out-of-distribution user styles and slang.
- **Honest Operational Reporting**: If model weights cannot be loaded, the system explicitly reports `MODEL NOT LOADED — RULES-ONLY MODE` and falls back to deterministic rule analysis. Model confidence is never fabricated.
