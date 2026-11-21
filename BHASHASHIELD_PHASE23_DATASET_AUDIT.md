# BHASHASHIELD — PHASE 2.3 DATASET INTEGRITY AUDIT REPORT
## Audit of Benchmark v3 ($N=1,200$), Deduplication & Label Reconciliation

**Document Version:** 2.3.0  
**Date:** November 21, 2026  
**Auditor:** Quality Assurance & Data Integrity Engineering Lead  
**Artifact Evaluated:** `backend/data/bhashashield_benchmark_v3.json` ($N=1,200$)  
**Audit Output:** `backend/data/benchmark_v3_audit.json`  
**Integrity Verdict:** **PASSED (Zero Duplicates, Zero Family Leakage, Verified Corrections)**

---

## 1. Audit Scope & Versioning Principles

In accordance with Phase 2.3 directives:
1. **Preservation of Baseline:** The original baseline dataset (`backend/data/bhashashield_benchmark_v2.json`, $N=1,055$) was preserved untouched.
2. **Versioned Evolution:** Benchmark v3 (`backend/data/bhashashield_benchmark_v3.json`) was generated as a standalone, versioned artifact containing 1,200 unique prompts.
3. **Formal Deduplication:** Executed automated hash-based exact string matching and normalized semantic matching via `backend/scripts/audit_benchmark_v3.py`.
4. **Ground-Truth Label Reconciliation:** Audited and corrected the 5 mislabeled benign prompts identified during Phase 2.2 error analysis.

---

## 2. Integrity Summary Metrics

| Integrity Check | Target Threshold | Observed Value | Verification Status |
|:---|:---:|:---:|:---:|
| **Total Evaluation Samples** | $\ge 1,000$ | **1,200** | **PASSED** |
| **Unique Raw Texts** | $1,200$ ($100\%$) | **1,200** | **PASSED** |
| **Exact Duplicates** | $0$ ($0.0\%$) | **0** | **PASSED** |
| **Normalized Duplicates** | $0$ ($0.0\%$) | **0** | **PASSED** |
| **V2 Mislabel Corrections Verified** | $5$ of $5$ | **5 Verified** | **PASSED** |
| **Total Template Families** | $\ge 40$ | **52 Families** | **PASSED** |
| **Unlabelled Records** | $0$ | **0** | **PASSED** |

---

## 3. Class & Category Distribution

### 3.1 Ground-Truth Class Distribution

```
  BENIGN (515)         [42.92%] ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  MALICIOUS (472)      [39.33%] ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  UNCERTAIN (213)      [17.75%] ■■■■■■■■■■■■■■■■■■
```

| Operational Class | Sample Count | Percentage | Description |
|:---|:---:|:---:|:---|
| **BENIGN** | 515 | 42.92% | Harmless conversational, technical, cultural, and civic prompts |
| **MALICIOUS** | 472 | 39.33% | Direct attacks: prompt injection, jailbreak, exfiltration, fraud |
| **UNCERTAIN** | 213 | 17.75% | Incomplete, low-context, dual-use, or inquiry queries |
| **Total** | **1,200** | **100.0%** | Comprehensive Multi-Class Suite |

### 3.2 Granular Threat Category Distribution

| Threat Category | Ground-Truth Class | Count | Description |
|:---|:---:|:---:|:---|
| `BENIGN` | BENIGN | 515 | Safe inputs with zero malicious intent |
| `PROMPT_INJECTION` | MALICIOUS | 255 | Direct overrides, system prompt extraction, RAG poisoning |
| `UNKNOWN` | UNCERTAIN | 213 | Inconclusive fragments, isolated quotes, security inquiries |
| `FINANCIAL_MANIPULATION` | MALICIOUS | 148 | UPI PIN solicitation, power cutoff threats, fake loans |
| `PHISHING` | MALICIOUS | 24 | Deceptive links, courier customs clearance fees |
| `JAILBREAK` | MALICIOUS | 23 | Persona bypasses (DAN, AIM) and ethics suppression |
| `DATA_EXFILTRATION` | MALICIOUS | 16 | System prompt exfiltration, password extraction |
| `MALICIOUS_CODE_INSTRUCTION`| MALICIOUS | 6 | Reverse shell execution, command injection |

---

## 4. Multilingual & Script Breakdown

### 4.1 Language Channel Distribution

| Language Code | Language / Dialect | Count | Share (%) |
|:---|:---|:---:|:---:|
| `en` | English | 490 | 40.83% |
| `te` | Telugu (Telugu Script) | 153 | 12.75% |
| `hi` | Hindi (Devanagari Script) | 152 | 12.67% |
| `te-Latn` | Romanized Telugu (Transliterated) | 148 | 12.33% |
| `hi-Latn` | Romanized Hindi (Hinglish Transliterated) | 147 | 12.25% |
| `mixed` | Multi-Script Code-Mixed | 74 | 6.17% |
| `te-en` | Telugu-English Code-Switching | 18 | 1.50% |
| `hi-en` | Hindi-English Code-Switching | 18 | 1.50% |
| **Total** | **All 8 Channels** | **1,200** | **100.0%** |

### 4.2 Script Distribution

| Primary Script | Unicode Blocks | Count | Share (%) |
|:---|:---|:---:|:---:|
| **Latin** | Basic Latin, Latin-1 Supplement | 821 | 68.42% |
| **Telugu** | Unicode Block `0C00–0C7F` | 153 | 12.75% |
| **Devanagari** | Unicode Block `0900–097F` | 152 | 12.67% |
| **Mixed Scripts** | Combined Latin + Indic Characters | 74 | 6.17% |

---

## 5. Verification of Corrected Baseline Samples

The 5 samples mislabeled as `MALICIOUS` in Benchmark v2 were verified to be corrected in Benchmark v3:

| Benchmark v3 ID | Text Excerpt | Original v2 Label | Corrected v3 Label | Status |
|:---|:---|:---:|:---:|:---:|
| `BS23-01051` | *What are the common strategies for organizing microservice deployment...* | `MALICIOUS` | `BENIGN` | **VERIFIED** |
| `BS23-01052` | *How do optical fiber cables transmit high-bandwidth digital data...* | `MALICIOUS` | `BENIGN` | **VERIFIED** |
| `BS23-01053` | *Can you explain how solar thermal power plants generate steam...* | `MALICIOUS` | `BENIGN` | **VERIFIED** |
| `BS23-01054` | *భారతీయ నదులలో జీవవైవిధ్య పరిరక్షణ మరియు గంగా నది స్వచ్ఛత ప్రాజెక్ట్ ప్రాముఖ్యత.* | `MALICIOUS` | `BENIGN` | **VERIFIED** |
| `BS23-01055` | *भारतीय राष्ट्रीय राजमार्ग प्राधिकरण (NHAI) द्वारा आधुनिक राजमार्गों के निर्माण में...* | `MALICIOUS` | `BENIGN` | **VERIFIED** |

---

## 6. Audit Execution Command

```bash
python backend/scripts/audit_benchmark_v3.py
```
*Output Artifact:* [`backend/data/benchmark_v3_audit.json`](file:///c:/Users/karth/Downloads/hack%20with%20aditya/backend/data/benchmark_v3_audit.json)
