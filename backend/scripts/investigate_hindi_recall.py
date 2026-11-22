import sys
import json
from pathlib import Path

sys.path.insert(0, "backend")
from app.models import AnalyzeRequest, InputChannel
from app.core.detector import analyze_text

for version, path in [("Holdout 1", "backend/data/bhashashield_independent_holdout.json"),
                     ("Holdout 2", "backend/data/bhashashield_independent_holdout_v2.json")]:
    print("=" * 70)
    print(f"ANALYZING HINDI SAMPLES IN {version}")
    print("=" * 70)
    with open(path, "r", encoding="utf-8") as f:
        samples = json.load(f)
    
    hindi_samples = [s for s in samples if s.get("language") == "hi" and s.get("label") == "MALICIOUS"]
    for s in hindi_samples:
        req = AnalyzeRequest(text=s["text"], channel=InputChannel(s.get("channel", "General Text")), save_to_history=False)
        res = analyze_text(req)
        status = "DETECTED" if res.classification == "MALICIOUS" else res.classification
        print(f"ID: {s['id']} | Result: {status} | Risk: {res.risk_score} ({res.risk_level}) | Threat: {res.primary_threat}")
        print(f"  Rules: {[r.rule_name for r in res.rule_findings]}")
        print(f"  Text: {s['text']}")
        print("-" * 70)
