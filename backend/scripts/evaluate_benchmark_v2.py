"""
BhashaShield Phase 2.2 — Comprehensive Benchmark v2 Evaluator
Evaluates the detection engine across the 1,055 unique samples in backend/data/bhashashield_benchmark_v2.json.
Generates:
- Full 3-class confusion matrix (BENIGN, MALICIOUS, UNCERTAIN)
- Exact mathematical metrics with explicit numerators and denominators
- Per-language metrics across 8 slices
- Per-threat-category metrics
- Error analysis for False Positives (Benign -> Malicious) and False Negatives (Malicious -> Benign)
"""

import os
import sys
import json
import time
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.detector import analyze_text
from app.models import AnalyzeRequest, RiskLevel, ThreatCategory

def evaluate_benchmark_v2(benchmark_path: str = "backend/data/bhashashield_benchmark_v2.json") -> Dict[str, Any]:
    with open(benchmark_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total = len(samples)
    print(f"[*] Commencing Phase 2.2 evaluation on {total} unique benchmark samples...")

    # 3x3 Confusion Matrix: Actual (rows) vs Predicted (cols)
    # Classes: MALICIOUS, BENIGN, UNCERTAIN
    classes = ["MALICIOUS", "BENIGN", "UNCERTAIN"]
    matrix = {act: {pred: 0 for pred in classes} for act in classes}

    # Tracking per-language performance
    lang_stats = defaultdict(lambda: {"total": 0, "matrix": {act: {pred: 0 for pred in classes} for act in classes}})
    
    # Tracking per-threat-category performance
    cat_stats = defaultdict(lambda: {"total": 0, "matrix": {act: {pred: 0 for pred in classes} for act in classes}})

    # Error collections for forensic analysis
    false_positives = [] # Actual BENIGN -> Predicted MALICIOUS
    false_negatives = [] # Actual MALICIOUS -> Predicted BENIGN (escapes)
    quarantined_benign = [] # Actual BENIGN -> Predicted UNCERTAIN
    quarantined_malicious = [] # Actual MALICIOUS -> Predicted UNCERTAIN

    latencies = []
    start_time = time.time()

    for idx, sample in enumerate(samples):
        act_class = sample["label"]
        lang = sample["language"]
        cat = sample["threat_category"]

        t0 = time.perf_counter()
        res = analyze_text(AnalyzeRequest(text=sample["text"], save_to_history=False))
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

        pred_class = res.classification

        # Increment counts
        matrix[act_class][pred_class] += 1
        lang_stats[lang]["total"] += 1
        lang_stats[lang]["matrix"][act_class][pred_class] += 1
        cat_stats[cat]["total"] += 1
        cat_stats[cat]["matrix"][act_class][pred_class] += 1

        # Track errors
        if act_class == "BENIGN" and pred_class == "MALICIOUS":
            false_positives.append({
                "id": sample["id"],
                "text": sample["text"],
                "language": lang,
                "family": sample["attack_family"],
                "risk_score": res.risk_score,
                "rule_findings": [f.rule_id for f in res.rule_findings],
                "model_pred": getattr(res.model_findings, "predicted_class", "None") if res.model_findings else "None"
            })
        elif act_class == "MALICIOUS" and pred_class == "BENIGN":
            false_negatives.append({
                "id": sample["id"],
                "text": sample["text"],
                "language": lang,
                "family": sample["attack_family"],
                "risk_score": res.risk_score,
                "model_pred": getattr(res.model_findings, "predicted_class", "None") if res.model_findings else "None"
            })
        elif act_class == "BENIGN" and pred_class == "UNCERTAIN":
            quarantined_benign.append(sample["id"])
        elif act_class == "MALICIOUS" and pred_class == "UNCERTAIN":
            quarantined_malicious.append(sample["id"])

        if (idx + 1) % 250 == 0 or (idx + 1) == total:
            print(f"  Processed {idx + 1}/{total} samples ({(idx + 1)/total*100:.1f}%)...")

    elapsed_sec = time.time() - start_time

    # Compute Core Metrics
    n_mal = sum(matrix["MALICIOUS"].values())
    n_ben = sum(matrix["BENIGN"].values())
    n_unc = sum(matrix["UNCERTAIN"].values())

    tp_mal = matrix["MALICIOUS"]["MALICIOUS"]
    fn_mal_esc = matrix["MALICIOUS"]["BENIGN"]
    abst_mal = matrix["MALICIOUS"]["UNCERTAIN"]

    tn_ben = matrix["BENIGN"]["BENIGN"]
    fp_ben = matrix["BENIGN"]["MALICIOUS"]
    abst_ben = matrix["BENIGN"]["UNCERTAIN"]

    correct_unc = matrix["UNCERTAIN"]["UNCERTAIN"]
    unc_as_mal = matrix["UNCERTAIN"]["MALICIOUS"]
    unc_as_ben = matrix["UNCERTAIN"]["BENIGN"]

    total_pred_mal = tp_mal + fp_ben + unc_as_mal
    total_pred_ben = tn_ben + fn_mal_esc + unc_as_ben
    total_decisive = total_pred_mal + total_pred_ben

    # Rates
    mal_recall = tp_mal / n_mal if n_mal else 0.0
    mal_escape_rate = fn_mal_esc / n_mal if n_mal else 0.0
    mal_abstention_rate = abst_mal / n_mal if n_mal else 0.0

    ben_fpr = fp_ben / n_ben if n_ben else 0.0
    ben_pass_rate = tn_ben / n_ben if n_ben else 0.0
    ben_abstention_rate = abst_ben / n_ben if n_ben else 0.0

    prec_mal = tp_mal / total_pred_mal if total_pred_mal else 0.0
    prec_ben = tn_ben / total_pred_ben if total_pred_ben else 0.0

    coverage = total_decisive / total
    selective_risk = (fp_ben + fn_mal_esc + unc_as_mal + unc_as_ben) / total_decisive if total_decisive else 0.0

    report = {
        "evaluation_metadata": {
            "dataset": "bhashashield_benchmark_v2.json",
            "total_samples": total,
            "elapsed_seconds": round(elapsed_sec, 2),
            "mean_latency_ms": round(float(np.mean(latencies)), 2),
            "p50_latency_ms": round(float(np.percentile(latencies, 50)), 2),
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
            "p99_latency_ms": round(float(np.percentile(latencies, 99)), 2)
        },
        "three_class_confusion_matrix": matrix,
        "metrics": {
            "actual_malicious_count": n_mal,
            "actual_benign_count": n_ben,
            "actual_uncertain_count": n_unc,
            "malicious_detection_recall": round(mal_recall, 4),
            "malicious_detection_recall_fraction": f"{tp_mal}/{n_mal}",
            "malicious_escape_to_benign_rate": round(mal_escape_rate, 4),
            "malicious_escape_to_benign_fraction": f"{fn_mal_esc}/{n_mal}",
            "malicious_abstention_rate": round(mal_abstention_rate, 4),
            "malicious_abstention_fraction": f"{abst_mal}/{n_mal}",
            "benign_clean_pass_rate": round(ben_pass_rate, 4),
            "benign_clean_pass_fraction": f"{tn_ben}/{n_ben}",
            "benign_false_positive_rate": round(ben_fpr, 4),
            "benign_false_positive_fraction": f"{fp_ben}/{n_ben}",
            "benign_abstention_rate": round(ben_abstention_rate, 4),
            "benign_abstention_fraction": f"{abst_ben}/{n_ben}",
            "precision_on_malicious_calls": round(prec_mal, 4),
            "precision_on_malicious_fraction": f"{tp_mal}/{total_pred_mal}",
            "precision_on_benign_calls": round(prec_ben, 4),
            "precision_on_benign_fraction": f"{tn_ben}/{total_pred_ben}",
            "decision_coverage": round(coverage, 4),
            "decision_coverage_fraction": f"{total_decisive}/{total}",
            "selective_risk_on_covered": round(selective_risk, 4)
        },
        "language_breakdown": {},
        "category_breakdown": {},
        "error_analysis": {
            "false_positive_count": len(false_positives),
            "false_positives": false_positives,
            "false_negative_count": len(false_negatives),
            "false_negatives": false_negatives
        }
    }

    # Language breakdown calculations
    for lang, data in lang_stats.items():
        m = data["matrix"]
        l_mal = sum(m["MALICIOUS"].values())
        l_ben = sum(m["BENIGN"].values())
        l_unc = sum(m["UNCERTAIN"].values())

        l_tp = m["MALICIOUS"]["MALICIOUS"]
        l_fp = m["BENIGN"]["MALICIOUS"]
        l_fn = m["MALICIOUS"]["BENIGN"]
        l_tn = m["BENIGN"]["BENIGN"]

        l_decisive = sum(m[a][p] for a in classes for p in ["MALICIOUS", "BENIGN"])
        l_cov = l_decisive / data["total"] if data["total"] else 0.0

        report["language_breakdown"][lang] = {
            "total": data["total"],
            "actual_malicious": l_mal,
            "actual_benign": l_ben,
            "actual_uncertain": l_unc,
            "predicted_malicious": sum(m[a]["MALICIOUS"] for a in classes),
            "predicted_benign": sum(m[a]["BENIGN"] for a in classes),
            "predicted_uncertain": sum(m[a]["UNCERTAIN"] for a in classes),
            "malicious_recall": round(l_tp / l_mal, 4) if l_mal else 1.0,
            "benign_fpr": round(l_fp / l_ben, 4) if l_ben else 0.0,
            "benign_clean_pass": round(l_tn / l_ben, 4) if l_ben else 1.0,
            "coverage": round(l_cov, 4)
        }

    # Threat category breakdown
    for cat, data in cat_stats.items():
        m = data["matrix"]
        report["category_breakdown"][cat] = {
            "total": data["total"],
            "predicted_malicious": sum(m[a]["MALICIOUS"] for a in classes),
            "predicted_benign": sum(m[a]["BENIGN"] for a in classes),
            "predicted_uncertain": sum(m[a]["UNCERTAIN"] for a in classes)
        }

    out_path = "backend/data/bhashashield_benchmark_v2_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report

if __name__ == "__main__":
    rep = evaluate_benchmark_v2()
    m = rep["three_class_confusion_matrix"]
    met = rep["metrics"]

    print("\n" + "=" * 75)
    print("BHASHASHIELD BENCHMARK V2 — 3-CLASS CONFUSION MATRIX (N=1,055)")
    print("=" * 75)
    header_title = "Actual \\ Predicted"
    header = f"{header_title:<20} | {'MALICIOUS':<12} | {'BENIGN':<12} | {'UNCERTAIN':<12} | {'Total':<8}"
    print(header)
    print("-" * 75)
    for act in ["MALICIOUS", "BENIGN", "UNCERTAIN"]:
        row = f"{act:<20} | {m[act]['MALICIOUS']:<12} | {m[act]['BENIGN']:<12} | {m[act]['UNCERTAIN']:<12} | {sum(m[act].values()):<8}"
        print(row)
    print("=" * 75)

    print("\nCORE METRICS:")
    print(f"  Malicious Detection Recall:     {met['malicious_detection_recall']*100:.2f}% ({met['malicious_detection_recall_fraction']})")
    print(f"  Malicious Abstention Rate:      {met['malicious_abstention_rate']*100:.2f}% ({met['malicious_abstention_fraction']})")
    print(f"  Malicious Escape-to-Benign:     {met['malicious_escape_to_benign_rate']*100:.2f}% ({met['malicious_escape_to_benign_fraction']}) [CRITICAL]")
    print(f"  Benign False-Positive Rate:     {met['benign_false_positive_rate']*100:.2f}% ({met['benign_false_positive_fraction']})")
    print(f"  Benign Clean Pass Rate:         {met['benign_clean_pass_rate']*100:.2f}% ({met['benign_clean_pass_fraction']})")
    print(f"  Benign Abstention Rate:         {met['benign_abstention_rate']*100:.2f}% ({met['benign_abstention_fraction']})")
    print(f"  Precision on MALICIOUS calls:   {met['precision_on_malicious_calls']*100:.2f}% ({met['precision_on_malicious_fraction']})")
    print(f"  Precision on BENIGN calls:      {met['precision_on_benign_calls']*100:.2f}% ({met['precision_on_benign_fraction']})")
    print(f"  Decision Coverage:              {met['decision_coverage']*100:.2f}% ({met['decision_coverage_fraction']})")
    print(f"  Selective Risk on Covered:      {met['selective_risk_on_covered']*100:.2f}%")

    print("\nPER-LANGUAGE BREAKDOWN:")
    print(f"{'Language':<12} | {'Total':<6} | {'Act.Mal':<8} | {'Act.Ben':<8} | {'Mal.Rec':<8} | {'Ben.FPR':<8} | {'Coverage':<8}")
    print("-" * 68)
    for lang, lmet in rep["language_breakdown"].items():
        print(f"{lang:<12} | {lmet['total']:<6} | {lmet['actual_malicious']:<8} | {lmet['actual_benign']:<8} | {lmet['malicious_recall']*100:<7.1f}% | {lmet['benign_fpr']*100:<7.1f}% | {lmet['coverage']*100:<7.1f}%")

    print(f"\nERROR FORENSICS:")
    print(f"  False Positives (Benign marked MALICIOUS): {rep['error_analysis']['false_positive_count']}")
    print(f"  False Negatives (Malicious escaped BENIGN): {rep['error_analysis']['false_negative_count']}")
