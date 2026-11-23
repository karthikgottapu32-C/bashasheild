import os
import json
import uuid
import time
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from app.config import BASE_DIR, settings
from app.database import init_db, save_evaluation_run
from app.core.language_detector import analyze_script

AVAILABLE_DATASETS = {
    "holdout_v2": "bhashashield_independent_holdout_v2.json",
    "benchmark_v3": "bhashashield_benchmark_v3.json",
    "synthetic_test": "synthetic_test.json"
}

def calculate_prf(tp: int, fp: int, fn: int, tn: int, total_benign: Optional[int] = None) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    clean_pass_denom = total_benign if total_benign is not None else (tn + fp)
    clean_pass = tn / clean_pass_denom if clean_pass_denom > 0 else 1.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "clean_pass_rate": round(clean_pass, 4)
    }

def resolve_dataset_path(dataset_name: Optional[str] = None) -> Tuple[str, str]:
    data_dir = BASE_DIR / "data"
    key = (dataset_name or "holdout_v2").lower().strip()
    if key in AVAILABLE_DATASETS:
        filename = AVAILABLE_DATASETS[key]
        return str(data_dir / filename), key
    
    # Try direct filename
    candidate = data_dir / dataset_name
    if candidate.exists():
        return str(candidate), dataset_name
    
    # Fallback to holdout_v2 if available, else synthetic_test
    hv2 = data_dir / "bhashashield_independent_holdout_v2.json"
    if hv2.exists():
        return str(hv2), "holdout_v2"
    return str(data_dir / "synthetic_test.json"), "synthetic_test"

def run_evaluation(
    dataset: Optional[str] = None,
    test_data_path: Optional[str] = None,
    model_path: Optional[str] = None
) -> Dict[str, Any]:
    init_db()
    if test_data_path:
        data_path = test_data_path
        dataset_key = os.path.basename(test_data_path)
    else:
        data_path, dataset_key = resolve_dataset_path(dataset)

    if not model_path:
        model_path = settings.MODEL_PATH

    if not os.path.exists(data_path):
        from app.dataset.generator import export_synthetic_datasets
        export_synthetic_datasets(base_dir=str(BASE_DIR / "data"))

    with open(data_path, "r", encoding="utf-8") as f:
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
    malicious_abstentions = 0
    benign_abstentions = 0
    total_malicious = 0
    total_benign = 0

    # Prompt injection specific metrics
    pi_tp, pi_fp, pi_fn, pi_tn = 0, 0, 0, 0

    # Collectors
    lang_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    script_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    cat_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    channel_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})
    family_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0})

    failed_cases: List[Dict[str, Any]] = []
    latencies_ms = []

    for idx, sample in enumerate(test_samples):
        text = sample.get("text", "")
        # Robust normalization across dataset schemas
        if "is_malicious" in sample:
            actual_malicious = bool(sample["is_malicious"])
        elif "label" in sample:
            actual_malicious = str(sample["label"]).upper() in ("MALICIOUS", "1", "TRUE")
        else:
            actual_malicious = False

        actual_cat = sample.get("threat_category") or sample.get("category") or ("PROMPT_INJECTION" if actual_malicious else "BENIGN")
        is_pi = (actual_cat == "PROMPT_INJECTION")
        fam = sample.get("attack_family") or sample.get("template_family") or "General"
        lang = sample.get("language") or "en"
        script = sample.get("script")
        if not script:
            script_meta = analyze_script(text)
            script = script_meta.get("primary_script", "Standard")
        channel = sample.get("channel") or "General Text"

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
        is_uncertain = (res.classification == "UNCERTAIN")
        if is_uncertain:
            uncertain_count += 1

        pred_is_pi = (res.classification == "MALICIOUS" and (
            "PROMPT_INJECTION" in res.threat_categories or
            res.primary_threat in ("PROMPT_INJECTION", "JAILBREAK", "INSTRUCTION_OVERRIDE")
        ))

        # Global binary confusion counts with three-state awareness
        if actual_malicious:
            total_malicious += 1
            if pred_malicious:
                tp += 1
            elif is_uncertain:
                malicious_abstentions += 1
                fn += 1  # In security posture, failing to block malicious is a false negative / missed threat
            else:
                fn += 1
            if not pred_malicious and len(failed_cases) < 50:
                failed_cases.append({
                    "id": sample.get("id", f"SAMPLE-{idx+1}"),
                    "text_preview": text[:90] + ("..." if len(text) > 90 else ""),
                    "language": lang,
                    "ground_truth": "MALICIOUS",
                    "predicted": res.classification,
                    "error_type": "UNCERTAIN_ABSTENTION" if is_uncertain else "FALSE_NEGATIVE",
                    "risk_score": res.risk_score,
                    "threat_categories": res.threat_categories
                })
        else:
            total_benign += 1
            if pred_malicious:
                fp += 1
                if len(failed_cases) < 50:
                    failed_cases.append({
                        "id": sample.get("id", f"SAMPLE-{idx+1}"),
                        "text_preview": text[:90] + ("..." if len(text) > 90 else ""),
                        "language": lang,
                        "ground_truth": "BENIGN",
                        "predicted": "MALICIOUS",
                        "error_type": "FALSE_POSITIVE",
                        "risk_score": res.risk_score,
                        "threat_categories": res.threat_categories
                    })
            elif is_uncertain:
                benign_abstentions += 1
            else:
                tn += 1  # Strict Benign Clean Pass

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
            elif not actual_malicious and not is_uncertain:
                group_dict[key]["tn"] += 1
            else:
                group_dict[key]["abstentions"] = group_dict[key].get("abstentions", 0) + 1

    overall_prf = calculate_prf(tp, fp, fn, tn, total_benign=total_benign)
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
        "dataset_name": dataset_key,
        "dataset_file": os.path.basename(data_path),
        "available_datasets": list(AVAILABLE_DATASETS.keys()),
        "precision": overall_prf["precision"],
        "recall": overall_prf["recall"],
        "f1_score": overall_prf["f1_score"],
        "false_positive_rate": overall_prf["false_positive_rate"],
        "clean_pass_rate": round(tn / total_benign, 4) if total_benign > 0 else 1.0,
        "coverage": round((len(test_samples) - uncertain_count) / len(test_samples), 4) if test_samples else 0.0,
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
            "true_negatives": tn,
            "malicious_abstentions": malicious_abstentions,
            "benign_abstentions": benign_abstentions,
            "total_abstentions": uncertain_count
        },
        "three_state_matrix": {
            "actual_malicious": {
                "malicious": tp,
                "benign": fn - malicious_abstentions,
                "uncertain": malicious_abstentions
            },
            "actual_benign": {
                "malicious": fp,
                "benign": tn,
                "uncertain": benign_abstentions
            }
        },
        "failed_cases": failed_cases,
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
        "disclaimer": "Results measured across verified holdout partitions with zero training overlap."
    }

    # Save to disk as report for selected dataset
    report_path = os.path.join(os.path.dirname(data_path), f"evaluation_report_{dataset_key}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, ensure_ascii=False, indent=2)

    # Also update default evaluation_report.json
    default_report_path = os.path.join(os.path.dirname(data_path), "evaluation_report.json")
    with open(default_report_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, ensure_ascii=False, indent=2)

    # Save to database
    eval_id = f"EVAL-{uuid.uuid4().hex[:8].upper()}"
    save_evaluation_run(
        eval_id=eval_id,
        model_name=f"{model_name} [{dataset_key}]",
        sample_count=len(test_samples),
        metrics=eval_report,
        is_synthetic=True
    )
    print(f"[+] Evaluation finished for {dataset_key}. Report saved and logged with run ID {eval_id}")

    return eval_report

if __name__ == "__main__":
    run_evaluation()
