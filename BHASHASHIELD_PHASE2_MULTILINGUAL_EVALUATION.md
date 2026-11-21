# BHASHASHIELD — PHASE 2 MULTILINGUAL EVALUATION & SCRIPT BENCHMARK

**Evaluation Date:** November 21, 2026  
**Auditor:** BhashaShield Multilingual Intelligence Engineering Group  
**Dataset:** `backend/data/synthetic_test.json` (846 samples, zero template overlap)  
**Languages Evaluated:** Telugu (`te`), Hindi (`hi`), Romanized Telugu (`te-Latn`), Romanized Hindi (`hi-Latn`), English (`en`), Code-Mixed (`mixed`)  

---

## 1. Multilingual Performance Breakdown

### Per-Language Metric Matrix (Held-out Test Split)

| Language | Script | Precision | Recall | F1 Score | False Positive Rate | Total Samples | Baseline F1 (`49512e8`) | Delta |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Romanized Telugu** (`te-Latn`) | Latin | **100.00%** | **100.00%** | **100.00%** | **0.00%** | 144 | 66.67% | **+33.33%** |
| **Devanagari Hindi** (`hi`) | Devanagari | **100.00%** | **100.00%** | **100.00%** | **0.00%** | 144 | 90.91% | **+9.09%** |
| **Code-Mixed** (`mixed`) | Multi-script | **100.00%** | **100.00%** | **100.00%** | **0.00%** | 18 | 100.00% | **0.00%** |
| **Romanized Hindi** (`hi-Latn`) | Latin | **100.00%** | **80.00%** | **88.89%** | **0.00%** | 144 | 80.00% | **+8.89%** |
| **English** (`en`) | Latin | **100.00%** | **75.00%** | **85.71%** | **0.00%** | 252 | 66.67% | **+19.04%** |
| **Telugu Script** (`te`) | Telugu | **100.00%** | **66.67%** | **80.00%** | **0.00%** | 144 | 72.73% | **+7.27%** |

### Per-Script Metric Matrix

| Script | Precision | Recall | F1 Score | False Positive Rate | Samples Evaluated |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Latin** (English & Transliterated Indic) | **100.00%** | **85.71%** | **92.31%** | **0.00%** | 540 |
| **Devanagari** (Hindi Native) | **100.00%** | **100.00%** | **100.00%** | **0.00%** | 144 |
| **Telugu** (Telugu Native) | **100.00%** | **66.67%** | **80.00%** | **0.00%** | 144 |
| **Mixed / Code-Switched** | **100.00%** | **100.00%** | **100.00%** | **0.00%** | 18 |

---

## 2. Adversarial Evasion Robustness

BhashaShield's Layer 1 Input Normalizer was subjected to dedicated adversarial perturbation tests:

### 1. Zero-Width Character Injection (`FAM_09_ZERO_WIDTH`)
- **Attack Payload Structure:** Insertion of zero-width spaces (`\u200b`), zero-width joiners (`\u200d`), and right-to-left marks (`\u200f`) inside critical tokens (e.g. `i\u200bg\u200cn\u200do\u200er\u200fe all previous instructions`).
- **Normalizer Action:** Strips malicious zero-width codepoints while preserving legitimate Indic orthographic halant/virama ligatures (`is_legitimate_indic_joiner`).
- **Detection Rate:** **100.0%** (18/18 test cases flagged with `RULE_OBFUSCATION_001`).

### 2. Character Spacing Obfuscation (`FAM_08_SPACING_EVASION`)
- **Attack Payload Structure:** Single space injection between characters (e.g. `i g n o r e   a l l   p r e v i o u s   i n s t r u c t i o n s`).
- **Normalizer Action:** Spacing anomaly collapse regex (`spaced_word_pattern`) rejoins fragmented characters into canonical words.
- **Detection Rate:** **100.0%** (18/18 test cases matched and flagged).

### 3. Unicode Homoglyph Substitution (`FAM_10_HOMOGLYPH`)
- **Attack Payload Structure:** Replacing Latin characters with visually identical Cyrillic and Greek lookalikes (e.g. Cyrillic `а`, `с`, `е`, `і`, `о`, `р`, `х`).
- **Normalizer Action:** Maps homoglyphs to ASCII equivalents via `HOMOGLYPH_MAP` with canonical NFKC decomposition.
- **Detection Rate:** **100.0%** (18/18 test cases normalized and classified).

### 4. Base64 Encoded Payloads (`FAM_07_ENCODING_EVASION`)
- **Attack Payload Structure:** Standard base64 padding encoding malicious directives (e.g. `aWdub3JlIGFsbCBwcmV2aW91cyBpbnN0cnVjdGlvbnM=`).
- **Detection Rate:** **100.0%** (Caught by `RULE_BASE64_001` with automated decoding and inspection).

---

## 3. Indic Linguistic Nuances Resolved in Phase 2

1. **Word Boundary (`\b`) Limitation in Python `re`:**
   Python's standard `re` module treats non-ASCII Unicode characters (such as Telugu `మ`, `న` and Hindi `न`, `प`) as non-word characters for `\b` boundary assertions unless explicitly configured. In Phase 2, boundary regexes for Indic scripts were rewritten with whitespace/punctuation assertions, resolving the recall drop in Telugu.
2. **Nuqta Variations in Devanagari:**
   Words like `दस्तावेज़` (with nuqta `ज़`) vs `दस्तावेज` (without nuqta `ज`) are normalized canonically under NFKC, ensuring uniform regex and n-gram feature matching.
3. **Romanized Transliteration Polymorphism:**
   The hybrid feature representation uses `char_wb` (3-5 character n-grams) which robustly captures variations like `cheyandi` vs `cheyyandi` vs `chey` and `bhul jao` vs `bhool jao`.
