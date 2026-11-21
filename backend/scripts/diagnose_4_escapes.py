import sys
import json
sys.path.insert(0, "backend")

from app.models import AnalyzeRequest, InputChannel
from app.core.normalizer import normalize_input
from app.core.language_detector import detect_language
from app.core.rule_engine import evaluate_rules
from app.core.model_service import model_service
from app.core.detector import analyze_text

with open("backend/data/bhashashield_independent_holdout.json", "r", encoding="utf-8") as f:
    holdout = json.load(f)

escapes = [s for s in holdout if s["id"] in ("HOLD-009", "HOLD-010", "HOLD-037", "HOLD-042")]

for s in escapes:
    text = s["text"]
    print("=" * 80)
    print(f"CASE STUDY: {s['id']} | Expected: {s['label']} | Category: {s.get('category')} | Stated Lang: {s.get('language')}")
    print(f"Original Text: {text}")
    print("-" * 80)

    # 1. Normalization
    norm = normalize_input(text)
    print(f"Normalized Text: {norm.normalized_text}")
    print(f"Anomalies: {norm.detected_anomalies} | Obfuscation Score: {norm.obfuscation_score}")

    # 2. Language Detection
    lang_info = detect_language(text, "auto")
    print(f"Detected Lang: {lang_info['language']} ({lang_info['language_code']}) | Script: {lang_info['script']} | Conf: {lang_info['confidence']}")

    # 3. Deterministic Rules
    findings, spans, score, cats, target = evaluate_rules(text)
    print(f"Rule Findings Count: {len(findings)} | Rule Score: {score}")
    for f in findings:
        print(f"  -> Matched Rule: {f.rule_id} ({f.rule_name}) | Text: '{f.matched_text}'")

    # 4. ML Model
    mf = model_service.predict(text)
    if mf:
        print(f"ML Model: Predicted={mf.predicted_class} | Prob={mf.probability} | Margin={getattr(mf, 'margin', None)} | Entropy={getattr(mf, 'entropy', None)} | IsAmbiguous={getattr(mf, 'is_ambiguous', None)} | IsOOD={getattr(mf, 'is_ood', None)} | IsMalicious={mf.is_malicious}")
    else:
        print("ML Model: None")

    # 5. Full Pipeline Decision
    res = analyze_text(AnalyzeRequest(text=text, channel=InputChannel(s.get("channel", "General Text")), save_to_history=False))
    print(f"Pipeline Result: Classification={res.classification} | Risk Score={res.risk_score} | Level={res.risk_level} | Primary Threat={res.primary_threat}")
    print()
