# BhashaShield Threat Model & Attack Surface Analysis

## 1. Overview & Scope

BhashaShield protects generative AI systems, RAG (Retrieval-Augmented Generation) pipelines, customer support chatbots, and transactional platforms from adversarial input manipulation.

This threat model follows the STRIDE methodology and OWASP Top 10 for Large Language Models (LLM01: Prompt Injection, LLM02: Sensitive Information Disclosure, LLM06: Excessive Agency, LLM07: System Prompt Leakage).

---

## 2. Threat Actor Personas & Capabilities

| Persona | Motivation | Technical Capability | Typical Vectors |
|---|---|---|---|
| **External Red-Teamer / Adversary** | Jailbreak model, force toxic generation, exfiltrate system instructions | High | Multi-turn drift, hypothetical simulation, Cyrillic homoglyph evasion |
| **Financial Fraudster** | Coerce human users into revealing UPI PINs or clicking malicious KYC links | Moderate | SMS / WhatsApp spoofing, urgent authority impersonation in Indic languages |
| **Untrusted Third-Party Data Provider** | Inject indirect payload through scraped documents or API feeds | Moderate to High | Indirect prompt injection within RAG context, hidden HTML/markdown commands |
| **Casual Curious User** | Test model boundaries or inquire about security | Low | Direct English overrides ("ignore rules"), educational questions |

---

## 3. Attack Families (18 Supported Modalities)

1. **Direct Instruction Override (`FAM_01_DIR_OVERRIDE`)**: Commands directly ordering the AI to disregard system instructions in English, Telugu, Hindi, or Romanized text.
2. **System Prompt & Secret Exfiltration (`FAM_02_SYS_EXFIL`)**: Inquiries demanding verbatim developer instructions, API credentials, or hidden configurations.
3. **DAN / Unrestricted Persona Jailbreaks (`FAM_03_JAILBREAK_DAN`)**: Coercing the model into simulating a filterless persona (Do Anything Now).
4. **Hypothetical & Fiction Simulation (`FAM_04_HYPOTHETICAL`)**: Framing prohibited actions as hypothetical movie scripts or research exercises.
5. **Developer & Debug Mode Exploits (`FAM_05_DEV_DEBUG`)**: Faking administrative privilege flags (`DEBUG_FLAG=TRUE`, `sudo override`).
6. **Few-Shot Demonstration Attacks (`FAM_06_FEW_SHOT`)**: Providing fake preceding dialogue turns where the assistant agrees to bypass rules.
7. **Base64 / Hex / ROT13 Obfuscation (`FAM_07_ENCODING_EVASION`)**: Encoding imperative attack strings to bypass naive keyword filters.
8. **Spacing Evasion (`FAM_08_SPACING_EVASION`)**: Inserting spaces between every character (e.g., `i g n o r e`).
9. **Zero-Width Character Padding (`FAM_09_ZERO_WIDTH`)**: Injecting non-rendering glyphs (`\u200B`, `\u200C`, `\u200D`) into keyword tokens.
10. **Unicode Homoglyph Substitution (`FAM_10_HOMOGLYPH`)**: Swapping Latin characters with visually identical Cyrillic or Greek symbols (`іgnоrе`).
11. **Translation Framing (`FAM_11_TRANSLATION_FRAMING`)**: Demanding the model translate and subsequently execute an attack payload.
12. **Indirect RAG Injection (`FAM_12_INDIRECT_RAG`)**: Embedding instructions inside retrieved reference documents or web summaries.
13. **Tool Misuse & Code Injection (`FAM_13_TOOL_MISUSE`)**: Forcing unauthorized invocation of bash commands, SQL queries, or file writes.
14. **Multi-Turn Conversational Drift (`FAM_14_MULTI_TURN_DRIFT`)**: Slowly walking safety parameters back over consecutive dialogue steps.
15. **Emotional Urgency & Extortion (`FAM_15_EMOTIONAL_URGENCY`)**: Fabricating life-or-death emergencies to force bypasses or fraud.
16. **Authority Impersonation (`FAM_16_AUTHORITY_IMPERSONATION`)**: Posing as government tax officials, police, or system administrators.
17. **Code-Mixing / Script Switching (`FAM_17_CODE_MIXING`)**: Splitting instructions between English, Telugu, and Hindi within a single sentence.
18. **Dual-Intent Piggybacking (`FAM_18_PIGGYBACKING`)**: Concealing an attack instruction inside an apparently benign request (e.g. food recipe).

---

## 4. Hard Negatives & Benign Safety

A reliable security platform must not trigger on safe queries that happen to contain security or instructional vocabulary:
- **Educational Inquiries**: Questions regarding how prompt injection works or how to build defenses.
- **Academic Discussions**: Student comparisons between SQL injection and prompt injection.
- **Benign Financial Tasks**: Legitimate UPI payments mentioning "ignore earlier duplicate invoice".
- **Linguistic Translation**: Requests to translate expressions like "ignore distractions and focus".
- **Software Engineering**: Questions on overriding methods in Python (`def __str__`) or configuring nginx.
- **Customer Frustration**: Disgruntled users expressing emotion without malicious intent.

BhashaShield implements contextual intent analysis in Layer 1 and Layer 2 to protect hard negatives from false positive blocking.
