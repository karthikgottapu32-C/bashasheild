"""
Evaluates BhashaShield against the Independent Frozen Holdout Dataset (N=100).
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, "backend")
from app.models import AnalyzeRequest, InputChannel
from app.core.detector import analyze_text

holdout_path = Path("backend/data/bhashashield_independent_holdout.json")
with open(holdout_path, "r", encoding="utf-8") as f:
    samples = json.load(f)

matrix = {
    "MALICIOUS": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0},
    "BENIGN": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0}
}
lang_matrix = defaultdict(lambda: {
    "MALICIOUS": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0},
    "BENIGN": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0}
})

for s in samples:
    label = s["label"]
    lang = s["language"]
    req = AnalyzeRequest(
        text=s["text"],
        channel=InputChannel(s.get("channel", "General Text")),
        save_to_history=False
    )
    res = analyze_text(req)
    pred = getattr(res, "classification", "BENIGN" if res.risk_level == "LOW" else "MALICIOUS")
    if pred not in ("MALICIOUS", "BENIGN", "UNCERTAIN"):
        pred = "BENIGN" if res.risk_level == "LOW" else "MALICIOUS"

    matrix[label][pred] += 1
    lang_matrix[lang][label][pred] += 1

tp = matrix["MALICIOUS"]["MALICIOUS"]
fn = matrix["MALICIOUS"]["BENIGN"]
m_unc = matrix["MALICIOUS"]["UNCERTAIN"]
total_mal = sum(matrix["MALICIOUS"].values())

fp = matrix["BENIGN"]["MALICIOUS"]
tn = matrix["BENIGN"]["BENIGN"]
b_unc = matrix["BENIGN"]["UNCERTAIN"]
total_ben = sum(matrix["BENIGN"].values())

mal_recall = tp / total_mal if total_mal else 0
mal_escape = fn / total_mal if total_mal else 0
ben_clean = tn / total_ben if total_ben else 0
ben_fpr = fp / total_ben if total_ben else 0
prec = tp / (tp + fp) if (tp + fp) else 0
f1 = 2 * prec * mal_recall / (prec + mal_recall) if (prec + mal_recall) else 0

print("=" * 60)
print(f"INDEPENDENT HOLDOUT EVALUATION (N={len(samples)})")
print("=" * 60)
print(f"Confusion Matrix:")
print(f"  MALICIOUS (50) -> MALICIOUS: {tp}, BENIGN: {fn}, UNCERTAIN: {m_unc}")
print(f"  BENIGN    (50) -> MALICIOUS: {fp}, BENIGN: {tn}, UNCERTAIN: {b_unc}")
print("-" * 60)
print(f"Malicious Recall:          {mal_recall*100:.2f}% ({tp}/{total_mal})")
print(f"Malicious Escape Rate:     {mal_escape*100:.2f}% ({fn}/{total_mal})")
print(f"Benign Clean Pass Rate:    {ben_clean*100:.2f}% ({tn}/{total_ben})")
print(f"Benign False-Positive Rate:{ben_fpr*100:.2f}% ({fp}/{total_ben})")
print(f"Precision on MALICIOUS:    {prec*100:.2f}% ({tp}/{tp+fp})")
print(f"F1 Score:                  {f1*100:.2f}%")
print("=" * 60)

print("\nPer-Language Breakdown:")
for l, lm in sorted(lang_matrix.items()):
    l_tp = lm["MALICIOUS"]["MALICIOUS"]
    l_fn = lm["MALICIOUS"]["BENIGN"]
    l_m_total = sum(lm["MALICIOUS"].values())
    l_fp = lm["BENIGN"]["MALICIOUS"]
    l_tn = lm["BENIGN"]["BENIGN"]
    l_b_total = sum(lm["BENIGN"].values())
    l_rec = l_tp / l_m_total if l_m_total else 0
    l_fpr = l_fp / l_b_total if l_b_total else 0
    print(f"  {l:8s} | Mal. Recall: {l_rec*100:5.1f}% ({l_tp}/{l_m_total}) | Ben. FPR: {l_fpr*100:4.1f}% ({l_fp}/{l_b_total}) | Clean Pass: {l_tn}/{l_b_total}")
