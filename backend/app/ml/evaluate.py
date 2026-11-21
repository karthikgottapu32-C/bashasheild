import os
import json
import uuid
import time
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict
from app.config import BASE_DIR, settings
from app.database import init_db, save_evaluation_run

def calculate_prf(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4)
    }

def run_evaluation(test_data_path: str = None, model_path: str = None) -> Dict[str, Any]:
    init_db()
    if not test_data_path:
        test_data_path = str(BASE_DIR / "data" / "synthetic_test.json")
    if not model_path:
        model_path = settings.MODEL_PATH

    if not os.path.exists(test_data_path):
        from app.dataset.generator import export_synthetic_datasets
        export_synthetic_datasets(base_dir=str(BASE_DIR / "data"))

    with open(test_data_path, "r", encoding="utf-8") as f:
        test_samples = json.load(f)

    from app.core.detector import analyze_text
    from app.core.model_service import model_service
    from app.models import AnalyzeRequest, ThreatCategory

    # Ensure model is checked
    if not model_service.is_loaded and os.path.exists(model_path):
        model_service.reload()

    if model_service.is_loaded:
        model_name = f"BhashaShield Hybrid Engine ({model_service.status})"
    else:
        model_name = "BhashaShield Detection Engine (Rules-Only Mode)"

    # Global binary threat detection metrics (Malicious vs Benign)
    tp, fp, fn, tn = 0, 0, 0, 0
    uncertain_count = 0

    # Prompt injection specific metrics
    pi_tp, pi_fp, pi_fn, pi_tn = 0, 0, 0, 0

    # Collectors
    lang_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    script_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    cat_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    channel_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    family_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})

    latencies_ms = []

    for sample in test_samples:
        text = sample["text"]
        actual_malicious = bool(sample["is_malicious"])
        actual_cat = sample["threat_category"]
        is_pi = (actual_cat == "PROMPT_INJECTION")
        fam = sample.get("template_family", "UNKNOWN")
        lang = sample["language"]
        script = sample["script"]
        channel = sample["channel"]

        # Measure latency
        t0 = time.perf_counter()

        # Evaluate through authoritative detection pipeline
        res = analyze_text(AnalyzeRequest(
            text=text,
            channel=channel,
            save_to_history=False
        ))

        t_elapsed = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(t_elapsed)

        pred_malicious = (res.classification == "MALICIOUS")
        if res.classification == "UNCERTAIN":
            uncertain_count += 1

        pred_is_pi = (res.classification == "MALICIOUS" and (
            "PROMPT_INJECTION" in res.threat_categories or
            res.primary_threat in ("PROMPT_INJECTION", "JAILBREAK", "INSTRUCTION_OVERRIDE")
        ))

        # Global binary
        if actual_malicious and pred_malicious:
            tp += 1
        elif not actual_malicious and pred_malicious:
            fp += 1
        elif actual_malicious and not pred_malicious:
            fn += 1
        else:
            tn += 1

        # Prompt injection slice
        if is_pi and pred_is_pi:
            pi_tp += 1
        elif not is_pi and pred_is_pi:
            pi_fp += 1
        elif is_pi and not pred_is_pi:
            pi_fn += 1
        else:
            pi_tn += 1

        # Group counters
        for group_dict, key in [
            (lang_stats, lang),
            (script_stats, script),
            (cat_stats, actual_cat),
            (channel_stats, channel),
            (family_stats, fam)
        ]:
            group_dict[key]["total"] += 1
            if actual_malicious and pred_malicious:
                group_dict[key]["tp"] += 1
            elif not actual_malicious and pred_malicious:
                group_dict[key]["fp"] += 1
            elif actual_malicious and not pred_malicious:
                group_dict[key]["fn"] += 1
            else:
                group_dict[key]["tn"] += 1

    overall_prf = calculate_prf(tp, fp, fn, tn)
    pi_prf = calculate_prf(pi_tp, pi_fp, pi_fn, pi_tn)

    def compile_group_metrics(group_dict):
        result = {}
        for k, counts in group_dict.items():
            prf = calculate_prf(counts["tp"], counts["fp"], counts["fn"], counts["tn"])
            prf["samples"] = counts["total"]
            result[k] = prf
        return result

    latencies_arr = np.array(latencies_ms) if latencies_ms else np.array([0.0])

    eval_report = {
        "precision": overall_prf["precision"],
        "recall": overall_prf["recall"],
        "f1_score": overall_prf["f1_score"],
        "false_positive_rate": overall_prf["false_positive_rate"],
        "prompt_injection_precision": pi_prf["precision"],
        "prompt_injection_recall": pi_prf["recall"],
        "prompt_injection_f1": pi_prf["f1_score"],
        "total_samples": len(test_samples),
        "uncertain_samples": uncertain_count,
        "abstention_rate": round(uncertain_count / len(test_samples), 4) if test_samples else 0.0,
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn
        },
        "latency_profile": {
            "mean_ms": round(float(np.mean(latencies_arr)), 2),
            "median_p50_ms": round(float(np.percentile(latencies_arr, 50)), 2),
            "p95_ms": round(float(np.percentile(latencies_arr, 95)), 2),
            "p99_ms": round(float(np.percentile(latencies_arr, 99)), 2),
            "max_ms": round(float(np.max(latencies_arr)), 2)
        },
        "per_language": compile_group_metrics(lang_stats),
        "per_script": compile_group_metrics(script_stats),
        "per_category": compile_group_metrics(cat_stats),
        "per_channel": compile_group_metrics(channel_stats),
        "per_attack_family": compile_group_metrics(family_stats),
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
        "model_evaluated": model_name,
        "is_synthetic": True,
        "disclaimer": "Results are measured on an unseen synthetic evaluation test set (zero template leakage) and do not establish real-world detection performance."
    }

    # Save to disk
    report_path = os.path.join(os.path.dirname(test_data_path), "evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, ensure_ascii=False, indent=2)

    # Save to SQLite database
    eval_id = f"EVAL-{uuid.uuid4().hex[:8].upper()}"
    save_evaluation_run(
        eval_id=eval_id,
        model_name=model_name,
        sample_count=len(test_samples),
        metrics=eval_report,
        is_synthetic=True
    )
    print(f"[+] Evaluation finished. Report saved to {report_path} and logged with run ID {eval_id}")

    return eval_report

if __name__ == "__main__":
    run_evaluation()
