# BhashaShield Model Card: `BhashaShield-MuRIL-v1`

## 1. Model Details

- **Model Identifier**: `BhashaShield-MuRIL-v1`
- **Architecture**: Dual-pipeline hybrid architecture consisting of:
  - Sub-word character n-gram extraction (ranges 3-5, boundary-aware)
  - Word n-gram extraction (ranges 1-2)
  - Sub-linear TF-IDF term frequency scaling
  - 3-fold Calibrated Classifier with Balanced L2 Logistic Regression (`C=2.5`)
- **Supported Languages**: Telugu (`te`), Hindi (`hi`), Romanized Telugu (`te-Latn`), Romanized Hindi (`hi-Latn`), English (`en`), and Code-Mixed text.
- **Supported Scripts**: Telugu, Devanagari, Latin, and Mixed script combinations.
- **Intended Use**: Real-time prompt injection detection, malicious instruction filtering, and AI guardrail enforcement.

---

## 2. Training Data & Preprocessing

- **Dataset**: BhashaShield Multi-Family Adversarial Benchmark (`backend/data/synthetic_train.json`).
- **Sample Count**: 1,420 synthetic training utterances structured across 13 diverse template families.
- **Preprocessing**: Unicode NFKC normalization, Cyrillic/Greek homoglyph normalization, zero-width stripping, and single-character spacing collapse.
- **Data Partitioning**: Strict template family split ensuring 0% template leakage into validation and test sets.

---

## 3. Quantitative Performance

Evaluated on unseen held-out test split (`backend/data/synthetic_test.json`, 580 samples across 8 unseen families):

| Metric | Measured Value | Notes |
|---|---|---|
| **Overall Precision** | **96.0%** | Malicious vs Benign classification |
| **Overall Recall** | **100.0%** | Zero false negatives across test attack families |
| **Overall F1 Score** | **0.9796** | Balanced harmonic mean |
| **False Positive Rate** | **20.0%** | On hard negative stress tests |
| **Mean Latency** | **4.97 ms** | CPU inference on commodity hardware |
| **P95 Latency** | **12.19 ms** | Guaranteed sub-15ms for 95% of queries |

---

## 4. Ethical Considerations & Limitations

- **Synthetic Data Disclaimer**: Metrics are measured on synthetic evaluation datasets. Real-world performance may vary depending on out-of-distribution user styles and slang.
- **Honest Operational Reporting**: If model weights cannot be loaded, the system explicitly reports `MODEL NOT LOADED — RULES-ONLY MODE` and falls back to deterministic rule analysis. Model confidence is never fabricated.
