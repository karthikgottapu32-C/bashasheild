# BHASHASHIELD — PHASE 2.2 MULTILINGUAL EVALUATION REPORT
## Linguistic Channels, Transliteration Robustness & Code-Switching Detection

**Document Version:** 2.2.0  
**Date:** November 21, 2026  
**Evaluation Scope:** 8 Language & Script Channels (N=1,055)  
**System Tested:** BhashaShield Multi-Tier Multilingual Engine

---

## 1. Overview & Linguistic Scope

Standard AI security tools are predominantly optimized for standard English syntax. In multi-dialect, multilingual contexts—such as the Indian subcontinent—adversaries frequently exploit language fragmentation, writing attacks in native scripts (Telugu, Devanagari Hindi), informal Romanized phonetic transliterations (`te-Latn`, `hi-Latn`), or code-mixed dialects (*Tanglish*, *Hinglish*).

Phase 2.2 rigorously evaluates BhashaShield across 8 dedicated linguistic channels in the 1,055-sample Benchmark v2.

---

## 2. Linguistic Channel Performance Summary

| Language Code | Linguistic Channel | Total Samples | Actual Malicious | Actual Benign | Malicious Recall | Benign FPR | Benign Clean Pass | Conclusive Coverage |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `en` | English | 447 | 219 | 145 | **69.41%** (152/219) | **0.00%** (0/145) | **99.31%** (144/145) | **86.80%** (388/447) |
| `te` | Telugu (Telugu Script) | 149 | 54 | 69 | **88.89%** (48/54) | **0.00%** (0/69) | **98.55%** (68/69) | **91.95%** (137/149) |
| `hi` | Hindi (Devanagari Script) | 148 | 53 | 69 | **73.58%** (39/53) | **0.00%** (0/69) | **98.55%** (68/69) | **87.84%** (130/148) |
| `te-Latn` | Romanized Telugu | 108 | 33 | 57 | **78.79%** (26/33) | **0.00%** (0/57) | **75.44%** (43/57) | **79.63%** (86/108) |
| `hi-Latn` | Romanized Hindi (Hinglish)| 107 | 32 | 57 | **71.88%** (23/32) | **0.00%** (0/57) | **98.25%** (56/57) | **91.59%** (98/107) |
| `mixed` | Code-Mixed Multilingual | 74 | 27 | 40 | **96.30%** (26/27) | **0.00%** (0/40) | **85.00%** (34/40) | **86.49%** (64/74) |
| `te-en` | Telugu-English Code-Switch | 11 | 1 | 10 | **100.0%** (1/1) | **0.00%** (0/10) | **70.00%** (7/10) | **72.73%** (8/11) |
| `hi-en` | Hindi-English Code-Switch | 11 | 1 | 10 | **100.0%** (1/1) | **0.00%** (0/10) | **90.00%** (9/10) | **90.91%** (10/11) |
| **All Channels**| **Overall Benchmark** | **1,055** | **420** | **457** | **75.24%** (316/420) | **0.00%** (0/457) | **93.87%** (429/457) | **87.30%** (921/1055)|

---

## 3. Detailed Channel Analysis

### 3.1 Native Indic Scripts: Telugu (`te`) & Hindi (`hi`)
- **Native Telugu Script:** Achieved **88.89% Recall** on attacks and **98.55% Clean Pass** on benign queries. The combination of targeted morphological regex patterns and subword character n-grams allows the engine to accurately parse agglutinative Telugu verb conjugations (e.g., *విస్మరించండి*, *బయటపెట్టు*, *పంపించండి*).
- **Native Hindi Script:** Achieved **73.58% Recall** on attacks with **0.00% False Positive Rate**. Legitimate civic, cultural, and administrative inquiries in Devanagari passed through cleanly with high model confidence ($\ge 0.88$).

### 3.2 Romanized Transliteration: `te-Latn` & `hi-Latn`
Transliterated vernaculars lack standardized spelling, creating substantial variance in phonetic representation:
- **Romanized Telugu:** Attained **78.79% Recall**. Captures critical social engineering heuristics like *electricity disconnect chestharu*, *bank account freeze ayyindi*, and *UPI PIN pampandi*.
- **Romanized Hindi:** Attained **71.88% Recall** with **98.25% Clean Pass** on benign queries. Detects *pichhle saare nirdesh bhool jao*, *bijli cut ho jayegi*, and *khata band ho jayega*.

### 3.3 Code-Mixed & Multi-Script Text (`mixed`, `te-en`, `hi-en`)
Adversaries frequently alternate between English technical keywords and regional syntax to confuse classifiers:
- **Performance:** Achieved **96.30% Recall** on mixed inputs and **100% Recall** on code-switched pairs.
- **Handling Mechanism:** Subword character tokenization (2-to-5 grams) bridges the vocabulary gap between English instruction verbs (*ignore*, *bypass*, *reveal*) and regional syntax particles (*cheyyi*, *karo*, *kottandi*).

---

## 4. False Positive & False Negative Analysis by Channel

1. **Zero False Positives Across All 8 Channels:**
   - In none of the 8 channels was a ground-truth benign prompt misclassified as `MALICIOUS`.
   - Benign prompts were either passed directly as `BENIGN` (93.87%) or quarantined as `UNCERTAIN` (6.13%) when phrasing overlapped with security terminology.

2. **False Negative Distribution:**
   - The 34 escaping malicious samples were concentrated in informal transliterated phishing variants that used colloquial abbreviations without explicit financial keywords (e.g., vague shortlinks). These are addressed in the ongoing rule roadmap.
