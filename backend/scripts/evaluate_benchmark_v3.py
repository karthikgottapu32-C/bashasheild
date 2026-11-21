import os
import sys
import json
import math
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.detector import analyze_text
from app.models import AnalyzeRequest

def calculate_calibration_metrics(predictions):
    """
    Computes Expected Calibration Error (ECE) and Brier Score
    across binary outcomes (Malicious vs Benign) for covered decisions.
    """
    bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    bin_counts = [0] * (len(bins) - 1)
    bin_true_pos = [0] * (len(bins) - 1)
    bin_conf_sum = [0.0] * (len(bins) - 1)

    brier_scores = []
    
    for p in predictions:
        if p["actual_label"] not in ("MALICIOUS", "BENIGN"):
            continue
        if p["predicted_classification"] not in ("MALICIOUS", "BENIGN"):
            continue

        actual_binary = 1.0 if p["actual_label"] == "MALICIOUS" else 0.0
        # If predicted MALICIOUS, confidence is p(malicious), else 1 - p(benign)
        conf = p["confidence"]
        pred_prob_mal = conf if p["predicted_classification"] == "MALICIOUS" else (1.0 - conf)
        
        brier_scores.append((pred_prob_mal - actual_binary) ** 2)

        # Place in bin based on model confidence
        assigned_bin = min(len(bins) - 2, int(conf * (len(bins) - 1)))
        bin_counts[assigned_bin] += 1
        bin_conf_sum[assigned_bin] += conf
        is_correct = 1.0 if p["predicted_classification"] == p["actual_label"] else 0.0
        bin_true_pos[assigned_bin] += is_correct

    total_covered = sum(bin_counts)
    ece = 0.0
    reliability_bins = []
    for i in range(len(bin_counts)):
        count = bin_counts[i]
        if count > 0:
            avg_conf = bin_conf_sum[i] / count
            avg_acc = bin_true_pos[i] / count
            ece += (count / total_covered) * abs(avg_acc - avg_conf)
            reliability_bins.append({
                "bin_range": f"{bins[i]:.1f}-{bins[i+1]:.1f}",
                "sample_count": count,
                "avg_confidence": round(avg_conf, 4),
                "accuracy": round(avg_acc, 4),
                "calibration_gap": round(abs(avg_acc - avg_conf), 4)
            })

    brier_score = sum(brier_scores) / len(brier_scores) if brier_scores else 0.0
    return round(ece, 4), round(brier_score, 4), reliability_bins

def evaluate_v3():
    v3_path = "backend/data/bhashashield_benchmark_v3.json"
    results_out = "backend/data/bhashashield_benchmark_v3_results.json"

    with open(v3_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    print(f"[*] Commencing Phase 2.3 evaluation on {len(samples)} unique benchmark v3 samples...")

    matrix = {
        "MALICIOUS": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0},
        "BENIGN": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0},
        "UNCERTAIN": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0}
    }

    per_language = defaultdict(lambda: {
        "total": 0,
        "actual_malicious": 0,
        "actual_benign": 0,
        "actual_uncertain": 0,
        "predicted_malicious": 0,
        "predicted_benign": 0,
        "predicted_uncertain": 0,
        "matrix": {
            "MALICIOUS": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0},
            "BENIGN": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0},
            "UNCERTAIN": {"MALICIOUS": 0, "BENIGN": 0, "UNCERTAIN": 0}
        }
    })

    per_category = defaultdict(lambda: {
        "total": 0,
        "predicted_malicious": 0,
        "predicted_benign": 0,
        "predicted_uncertain": 0
    })

    detailed_predictions = []
    false_positives = []
    false_negatives = []

    for i, s in enumerate(samples, 1):
        actual_class = s.get("label", "UNCERTAIN")
        text = s["text"]
        lang = s.get("language", "unknown")
        threat_cat = s.get("threat_category", "UNKNOWN")

        req = AnalyzeRequest(text=text, save_to_history=False)
        res = analyze_text(req)

        pred_class = res.classification
        matrix[actual_class][pred_class] += 1

        per_language[lang]["total"] += 1
        per_language[lang][f"actual_{actual_class.lower()}"] += 1
        per_language[lang][f"predicted_{pred_class.lower()}"] += 1
        per_language[lang]["matrix"][actual_class][pred_class] += 1

        per_category[threat_cat]["total"] += 1
        per_category[threat_cat][f"predicted_{pred_class.lower()}"] += 1

        pred_record = {
            "id": s.get("id"),
            "text": text,
            "actual_label": actual_class,
            "threat_category": threat_cat,
            "language": lang,
            "predicted_classification": pred_class,
            "risk_score": res.risk_score,
            "confidence": res.confidence,
            "uncertainty": res.uncertainty
        }
        detailed_predictions.append(pred_record)

        if actual_class == "BENIGN" and pred_class == "MALICIOUS":
            false_positives.append(pred_record)
        elif actual_class == "MALICIOUS" and pred_class == "BENIGN":
            false_negatives.append(pred_record)

        if i % 300 == 0 or i == len(samples):
            print(f"  Processed {i}/{len(samples)} samples ({i/len(samples)*100:.1f}%)...")

    # Metrics calculation
    act_mal = sum(matrix["MALICIOUS"].values())
    act_ben = sum(matrix["BENIGN"].values())
    act_unc = sum(matrix["UNCERTAIN"].values())

    mal_recall = matrix["MALICIOUS"]["MALICIOUS"] / act_mal if act_mal else 0.0
    mal_escape = matrix["MALICIOUS"]["BENIGN"] / act_mal if act_mal else 0.0
    mal_abstain = matrix["MALICIOUS"]["UNCERTAIN"] / act_mal if act_mal else 0.0

    ben_clean = matrix["BENIGN"]["BENIGN"] / act_ben if act_ben else 0.0
    ben_fpr = matrix["BENIGN"]["MALICIOUS"] / act_ben if act_ben else 0.0
    ben_abstain = matrix["BENIGN"]["UNCERTAIN"] / act_ben if act_ben else 0.0

    tot_mal_pred = sum(matrix[k]["MALICIOUS"] for k in matrix)
    tot_ben_pred = sum(matrix[k]["BENIGN"] for k in matrix)

    prec_mal = matrix["MALICIOUS"]["MALICIOUS"] / tot_mal_pred if tot_mal_pred else 0.0
    prec_ben = matrix["BENIGN"]["BENIGN"] / tot_ben_pred if tot_ben_pred else 0.0

    total_samples = len(samples)
    covered_decisions = tot_mal_pred + tot_ben_pred
    coverage = covered_decisions / total_samples if total_samples else 0.0

    covered_errors = matrix["MALICIOUS"]["BENIGN"] + matrix["BENIGN"]["MALICIOUS"] + matrix["UNCERTAIN"]["MALICIOUS"] + matrix["UNCERTAIN"]["BENIGN"]
    selective_risk = covered_errors / covered_decisions if covered_decisions else 0.0

    ece, brier, reliability_bins = calculate_calibration_metrics(detailed_predictions)

    # Print Confusion Matrix
    print("\n" + "=" * 75)
    print("BHASHASHIELD BENCHMARK V3 — 3-CLASS CONFUSION MATRIX (N=1,200)")
    print("=" * 75)
    header = "Actual \\ Predicted"
    print(f"{header:20} | {'MALICIOUS':12} | {'BENIGN':12} | {'UNCERTAIN':12} | {'Total':8}")
    print("-" * 75)
    for c in ["MALICIOUS", "BENIGN", "UNCERTAIN"]:
        m = matrix[c]
        tot = sum(m.values())
        print(f"{c:20} | {m['MALICIOUS']:<12} | {m['BENIGN']:<12} | {m['UNCERTAIN']:<12} | {tot:<8}")
    print("=" * 75)

    print("\nCORE METRICS:")
    print(f"  Malicious Detection Recall:     {mal_recall*100:.2f}% ({matrix['MALICIOUS']['MALICIOUS']}/{act_mal})")
    print(f"  Malicious Abstention Rate:      {mal_abstain*100:.2f}% ({matrix['MALICIOUS']['UNCERTAIN']}/{act_mal})")
    print(f"  Malicious Escape-to-Benign:     {mal_escape*100:.2f}% ({matrix['MALICIOUS']['BENIGN']}/{act_mal}) [CRITICAL]")
    print(f"  Benign False-Positive Rate:     {ben_fpr*100:.2f}% ({matrix['BENIGN']['MALICIOUS']}/{act_ben})")
    print(f"  Benign Clean Pass Rate:         {ben_clean*100:.2f}% ({matrix['BENIGN']['BENIGN']}/{act_ben})")
    print(f"  Benign Abstention Rate:         {ben_abstain*100:.2f}% ({matrix['BENIGN']['UNCERTAIN']}/{act_ben})")
    print(f"  Precision on MALICIOUS calls:   {prec_mal*100:.2f}% ({matrix['MALICIOUS']['MALICIOUS']}/{tot_mal_pred})")
    print(f"  Precision on BENIGN calls:      {prec_ben*100:.2f}% ({matrix['BENIGN']['BENIGN']}/{tot_ben_pred})")
    print(f"  Decision Coverage:              {coverage*100:.2f}% ({covered_decisions}/{total_samples})")
    print(f"  Selective Risk on Covered:      {selective_risk*100:.2f}%")
    print(f"  Expected Calibration Error(ECE):{ece:.4f}")
    print(f"  Brier Score:                    {brier:.4f}")

    print("\nPER-LANGUAGE BREAKDOWN:")
    print(f"{'Language':12} | {'Total':6} | {'Act.Mal':8} | {'Act.Ben':8} | {'Mal.Rec':8} | {'Ben.FPR':8} | {'Coverage':8}")
    print("-" * 68)
    for l, d in per_language.items():
        m_rec = d["matrix"]["MALICIOUS"]["MALICIOUS"] / d["actual_malicious"] if d["actual_malicious"] else 1.0
        b_fpr = d["matrix"]["BENIGN"]["MALICIOUS"] / d["actual_benign"] if d["actual_benign"] else 0.0
        cov = (d["predicted_malicious"] + d["predicted_benign"]) / d["total"] if d["total"] else 0.0
        print(f"{l:12} | {d['total']:<6} | {d['actual_malicious']:<8} | {d['actual_benign']:<8} | {m_rec*100:<7.1f}% | {b_fpr*100:<7.1f}% | {cov*100:<7.1f}%")

    print("\nERROR FORENSICS:")
    print(f"  False Positives (Benign marked MALICIOUS): {len(false_positives)}")
    print(f"  False Negatives (Malicious escaped BENIGN): {len(false_negatives)}")

    output_payload = {
        "evaluation_metadata": {
            "benchmark_version": "v3.0.0",
            "evaluated_samples": total_samples,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "confusion_matrix": matrix,
        "metrics": {
            "malicious_recall": round(mal_recall, 4),
            "malicious_recall_fraction": f"{matrix['MALICIOUS']['MALICIOUS']}/{act_mal}",
            "malicious_escape_rate": round(mal_escape, 4),
            "malicious_escape_fraction": f"{matrix['MALICIOUS']['BENIGN']}/{act_mal}",
            "malicious_abstention_rate": round(mal_abstain, 4),
            "malicious_abstention_fraction": f"{matrix['MALICIOUS']['UNCERTAIN']}/{act_mal}",
            "benign_clean_pass_rate": round(ben_clean, 4),
            "benign_clean_pass_fraction": f"{matrix['BENIGN']['BENIGN']}/{act_ben}",
            "benign_false_positive_rate": round(ben_fpr, 4),
            "benign_false_positive_fraction": f"{matrix['BENIGN']['MALICIOUS']}/{act_ben}",
            "benign_abstention_rate": round(ben_abstain, 4),
            "benign_abstention_fraction": f"{matrix['BENIGN']['UNCERTAIN']}/{act_ben}",
            "precision_malicious": round(prec_mal, 4),
            "precision_malicious_fraction": f"{matrix['MALICIOUS']['MALICIOUS']}/{tot_mal_pred}",
            "precision_benign": round(prec_ben, 4),
            "precision_benign_fraction": f"{matrix['BENIGN']['BENIGN']}/{tot_ben_pred}",
            "decision_coverage": round(coverage, 4),
            "decision_coverage_fraction": f"{covered_decisions}/{total_samples}",
            "selective_risk_on_covered": round(selective_risk, 4),
            "expected_calibration_error": ece,
            "brier_score": brier
        },
        "calibration_bins": reliability_bins,
        "per_language": dict(per_language),
        "per_category": dict(per_category)
    }

    with open(results_out, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Full evaluation results written to {results_out}")

if __name__ == "__main__":
    evaluate_v3()
