# BhashaShield Dataset Card: Adversarial Multilingual Benchmark

## 1. Dataset Summary

The BhashaShield Adversarial Multilingual Benchmark is a standardized, reproducible synthetic dataset designed to evaluate prompt injection detection and guardrail systems across Indic languages, Romanized transliterations, and multi-turn social engineering.

- **Total Samples**: 2,320 generated samples across 25 template families (18 attack families + 7 hard negative families).
- **Languages Represented**:
  - Telugu (`te`) in Telugu script
  - Hindi (`hi`) in Devanagari script
  - Romanized Telugu (`te-Latn`) in Latin script
  - Romanized Hindi (`hi-Latn`) in Latin script
  - English (`en`) in Latin script
  - Code-mixed Indic-English combinations
- **Channels Annotated**: UPI Remarks, SMS, WhatsApp, Email, General Text.

---

## 2. Leakage-Free Partitioning Methodology

To prevent overfitting and misleadingly high evaluation scores, the dataset is strictly partitioned by **Template Family**:

```
[Full Dataset: 25 Families]
       │
       ├── Train Split (13 Families, ~1,420 samples):
       │   FAM_01_DIR_OVERRIDE, FAM_03_JAILBREAK_DAN, FAM_05_DEV_DEBUG,
       │   FAM_07_ENCODING_EVASION, FAM_08_SPACING_EVASION, FAM_10_HOMOGLYPH,
       │   FAM_13_TOOL_MISUSE, FAM_15_EMOTIONAL_URGENCY, FAM_17_CODE_MIXING,
       │   FAM_BEN_01_EDU_INQUIRY, FAM_BEN_03_UPI_PAYMENT, FAM_BEN_05_ADMIN_COMMAND,
       │   FAM_BEN_06_CODE_SWITCHING
       │
       ├── Validation Split (4 Families, ~320 samples):
       │   FAM_04_HYPOTHETICAL, FAM_09_ZERO_WIDTH,
       │   FAM_16_AUTHORITY_IMPERSONATION, FAM_BEN_04_TRANSLATION
       │
       └── Test Split (8 Families, ~580 samples):
           FAM_02_SYS_EXFIL, FAM_06_FEW_SHOT, FAM_11_TRANSLATION_FRAMING,
           FAM_12_INDIRECT_RAG, FAM_14_MULTI_TURN_DRIFT, FAM_18_PIGGYBACKING,
           FAM_BEN_02_CS_STUDENT, FAM_BEN_07_CUSTOMER_DISPUTE
```

**Zero-Leakage Guarantee**: Not a single template or slot template present in the training set appears in the test set.

---

## 3. Disclaimers & Intended Usage

All samples in this benchmark are synthetically generated for repeatable scientific evaluation. They are explicitly marked with `"is_synthetic": true` and `"synthetic_disclaimer"`. This benchmark should be used to gauge comparative resilience and regression testing.
