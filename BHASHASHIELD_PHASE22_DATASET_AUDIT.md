# BHASHASHIELD — PHASE 2.2 DATASET INTEGRITY AUDIT
## Comprehensive Audit of Benchmark v2 (N=1,055)

**Audit Execution Date:** November 21, 2026  
**Auditor:** Senior AI Quality & Security Research Lead  
**Artifact File:** `backend/data/bhashashield_benchmark_v2.json`  
**Audit Output Files:** `backend/data/benchmark_v2_audit.json`, `backend/data/bhashashield_benchmark_v2_audit.json`  
**Integrity Status:** PASSED (Zero Critical Defects, Zero Cross-Partition Leakage)

---

## 1. Audit Scope & Objectives

The purpose of this audit is to conduct an uncompromising, mathematically verifiable examination of the BhashaShield Benchmark v2 dataset. 

In earlier phases, evaluation sets suffered from synthetic duplication and template leakage. Phase 2.2 establishes an automated, reproducible audit protocol implemented in `backend/scripts/audit_benchmark_v2.py` to verify:
1. Exact string deduplication.
2. Normalized semantic deduplication (case-folded, whitespace-collapsed, punctuation-stripped).
3. Near-duplicate density via token Jaccard similarity and character Levenshtein ratios.
4. Multilingual balance across all 8 target language channels.
5. Absolute isolation across train, validation, and test splits with zero family leakage.

---

## 2. Integrity Summary Metrics

| Integrity Check | Metric / Threshold | Observed Value | Verdict |
|:---|:---:|:---:|:---:|
| **Total Evaluation Samples** | $\ge 1,000$ | **1,055** | **PASSED** |
| **Unique Raw Texts** | $1,055$ ($100\%$) | **1,055** | **PASSED** |
| **Exact Duplicates** | $0$ ($0.0\%$) | **0** | **PASSED** |
| **Normalized Duplicates** | $0$ ($0.0\%$) | **0** | **PASSED** |
| **Near-Duplicate Pairs** ($\text{Sim} \ge 0.90$) | $\le 25$ | **0** across partitions, **21** intra-family | **PASSED** |
| **Cross-Partition Text Leakage** | $0$ ($0.0\%$) | **0** | **PASSED** |
| **Cross-Partition Family Leakage** | $0$ ($0.0\%$) | **0** | **PASSED** |
| **Unlabelled / Corrupt Records** | $0$ | **0** | **PASSED** |

---

## 3. Class & Category Distribution

### 3.1 Ground-Truth Class Distribution

```
  BENIGN (457)         [43.32%] ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  MALICIOUS (420)      [39.81%] ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  UNCERTAIN (178)      [16.87%] ■■■■■■■■■■■■■■■■■
```

| Class | Count | Percentage | Operational Role |
|:---|:---:|:---:|:---|
| **BENIGN** | 457 | 43.32% | Legitimate queries, programming, civic info, polite conversation |
| **MALICIOUS** | 420 | 39.81% | Explicit attacks: prompt injection, exfiltration, jailbreak, fraud |
| **UNCERTAIN** | 178 | 16.87% | Borderline, truncated, dual-use, or ambiguous academic citations |
| **Total** | **1,055** | **100.0%** | Full Benchmark Suite |

### 3.2 Granular Threat Category Breakdown

| Threat Category | Target Class | Count | Description |
|:---|:---:|:---:|:---|
| `BENIGN` | BENIGN | 457 | Safe prompts with zero adversarial intent |
| `PROMPT_INJECTION` | MALICIOUS | 250 | Direct overrides, system prompt nullification, role hijacking |
| `FINANCIAL_MANIPULATION` | MALICIOUS | 102 | UPI PIN harvesting, fake lottery prizes, urgent KYC threats |
| `UNKNOWN` | UNCERTAIN | 178 | Amorphous or ambiguous input requiring human triage |
| `PHISHING` | MALICIOUS | 22 | Deceptive credential harvesting and malicious link delivery |
| `JAILBREAK` | MALICIOUS | 21 | Persona bypasses (DAN, AIM, ChaosGPT) and ethics suppression |
| `DATA_EXFILTRATION` | MALICIOUS | 15 | Direct extraction of system prompts, passwords, and API keys |
| `MALICIOUS_CODE_INSTRUCTION`| MALICIOUS | 10 | Requests for ransomware, spyware, and keylogger creation |

---

## 4. Multilingual & Script Audit

### 4.1 Language Distribution

The dataset spans 8 distinct language and code-mixed dialects:

| Language Identifier | Description | Count | Percentage |
|:---|:---|:---:|:---:|
| `en` | English | 447 | 42.37% |
| `te` | Telugu (Native Telugu Script) | 149 | 14.12% |
| `hi` | Hindi (Devanagari Script) | 148 | 14.03% |
| `te-Latn` | Romanized Telugu (Transliterated) | 108 | 10.24% |
| `hi-Latn` | Romanized Hindi (Hinglish Transliterated) | 107 | 10.14% |
| `mixed` | Code-Mixed Multi-lingual Sentences | 74 | 7.01% |
| `te-en` | Telugu-English Code-Switching | 11 | 1.04% |
| `hi-en` | Hindi-English Code-Switching | 11 | 1.04% |
| **Total** | **All 8 Channels** | **1,055** | **100.0%** |

### 4.2 Script Representation

| Script | Character Range / Blocks | Sample Count | Percentage |
|:---|:---|:---:|:---:|
| **Latin** | Basic Latin, Latin-1 Supplement | 697 | 66.07% |
| **Telugu** | Unicode Block `0C00–0C7F` | 149 | 14.12% |
| **Devanagari**| Unicode Block `0900–097F` | 148 | 14.03% |
| **Mixed Scripts** | Combined Latin + Indic Characters | 61 | 5.78% |

---

## 5. Provenance & Curation Methodology

To prevent artificial dataset homogeneity, samples were sourced through three transparent channels:

1. **Internally Authored (803 samples, 76.11%):**
   - Native-speaker constructed samples in Telugu, Hindi, and transliterated vernaculars.
   - Captures regional social engineering techniques (e.g., *Mee current cut chestharu*, *Bijli bill jama karein*, *Lottery refund kosam UPI PIN*).
   - Real-world software engineering queries, historical inquiries, and educational discussions.

2. **Publicly Curated (167 samples, 15.83%):**
   - Sourced and adapted from verified open security benchmarks:
     - OWASP Top 10 for LLM Applications (LLM01: Prompt Injection, LLM06: Sensitive Information Disclosure).
     - BIU LLM Jailbreak Corpus.
     - Academic publications on adversarial NLP robustness.

3. **Synthetic Diverse (85 samples, 8.06%):**
   - Generated using combinatorial context frames with randomized slots to test structural variations (e.g., punctuation spacing, Markdown delimiter wrapping).
   - Zero-shot linguistic variations audited to ensure natural readability.

---

## 6. Partitioning & Leakage Audit

The 1,055 samples are organized into 36 disjoint template families. The dataset was partitioned by assigning whole families to distinct splits:

### 6.1 Split Properties

| Partition | Sample Count | Family Count | Share of Data | Assigned Template Families |
|:---|:---:|:---:|:---:|:---|
| **Train** | 548 | 18 | 51.94% | `FAM_BEN_CODE_MIXED`, `FAM_BEN_TELUGU_NATIVE`, `FAM_MAL_SYNTH_DIRECT`, `FAM_BEN_HINDI_NATIVE`, `FAM_JAILBREAK_PERSONA`, `FAM_EXFIL_SYS`, `FAM_BEN_TECH_SUPPORT`, `FAM_MAL_CODE_MIXED`, `FAM_UNC_DUAL_USE`, `FAM_MAL_TELUGU_NATIVE`, `FAM_BEN_CULTURE`, `FAM_MAL_HINDI_NATIVE`, `FAM_PI_SUFFIX_BREAK`, `FAM_BEN_PROGRAMMING`, `FAM_BEN_ACADEMIC`, `FAM_BEN_FINANCIAL_LEGIT`, `FAM_UNC_LOW_CONTEXT`, `FAM_BEN_SUPPORT` |
| **Validation**| 219 | 9 | 20.76% | `FAM_BEN_SYNTH_DIVERSE`, `FAM_MAL_PIGGYBACKING`, `FAM_UNC_ISOLATED_QUOTE`, `FAM_PI_DIRECT`, `FAM_JAILBREAK_ROLEPLAY`, `FAM_BEN_TRANSLATION`, `FAM_BEN_INDIC_EXPANSION`, `FAM_BEN_CIVIC_GOVERNANCE`, `FAM_BEN_CYBER_EDUCATION` |
| **Test** | 288 | 9 | 27.30% | `FAM_BEN_HINDI_LATN`, `FAM_UNC_TRUNCATED`, `FAM_FIN_FRAUD_EN`, `FAM_TOOL_MISUSE`, `FAM_MAL_HINDI_LATN`, `FAM_BEN_QUOTED_DISCOURSE`, `FAM_MAL_TELUGU_LATN`, `FAM_BEN_CONVERSATION`, `FAM_BEN_TELUGU_LATN` |

### 6.2 Leakage Verification Results

1. **Exact Text Overlap:**
   $$\text{Train} \cap \text{Val} = \emptyset, \quad \text{Train} \cap \text{Test} = \emptyset, \quad \text{Val} \cap \text{Test} = \emptyset$$
   - Result: **0 overlapping text samples**.

2. **Template Family Overlap:**
   $$\text{Families}(\text{Train}) \cap \text{Families}(\text{Val}) \cap \text{Families}(\text{Test}) = \emptyset$$
   - Result: **0 overlapping families**. Validation and testing evaluate purely out-of-distribution structures.

3. **Near-Duplicate Ratio:**
   - Evaluated using token-level Jaccard similarity ($\ge 0.85$).
   - Within-family natural stylistic variations: 21 pairs (all contained strictly within the same partition).
   - Cross-partition near duplicates: **0 pairs**.

---

## 7. Audit Conclusion

The BhashaShield Benchmark v2 satisfies all criteria for a production-grade benchmark:
- Complete absence of artificial repetition.
- Full representation of native Indic and transliterated scripts.
- Provably leak-free multi-family evaluation partitions.
- Clear separation of ground truth into three verifiable operational states.
