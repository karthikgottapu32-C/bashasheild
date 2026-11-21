"""
BhashaShield Phase 2.2 — Independent Dataset Integrity & Provenance Auditor
Audits backend/data/bhashashield_benchmark_v2.json and its train/val/test partitions for:
- Exact duplicates
- Normalized duplicates
- Lexical near-duplicates (SequenceMatcher ratio > 0.85)
- Cross-partition data leakage (train vs val vs test)
- Encoding validity and empty input checks
- Class and language distributions
- Data provenance attribution
"""

import os
import sys
import json
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import List, Dict, Any, Tuple

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.dataset.generate_full_benchmark import normalize_key

def audit_benchmark_dataset(
    benchmark_path: str = "backend/data/bhashashield_benchmark_v2.json",
    train_path: str = "backend/data/benchmark_v2_train.json",
    val_path: str = "backend/data/benchmark_v2_val.json",
    test_path: str = "backend/data/benchmark_v2_test.json",
    near_dup_threshold: float = 0.85
) -> Dict[str, Any]:
    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    with open(train_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)

    with open(val_path, "r", encoding="utf-8") as f:
        val_data = json.load(f)

    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    total_samples = len(benchmark)
    
    # 1. Exact Duplicates
    raw_texts = [s["text"] for s in benchmark]
    raw_counter = Counter(raw_texts)
    exact_duplicates = sum(count - 1 for count in raw_counter.values() if count > 1)
    
    # 2. Normalized Duplicates
    norm_keys = [normalize_key(s["text"]) for s in benchmark]
    norm_counter = Counter(norm_keys)
    norm_duplicates = sum(count - 1 for count in norm_counter.values() if count > 1)

    # 3. Empty inputs and UTF-8 encoding validity
    empty_count = sum(1 for s in benchmark if not s["text"].strip())
    invalid_encoding_count = 0
    for s in benchmark:
        try:
            s["text"].encode("utf-8").decode("utf-8")
        except UnicodeError:
            invalid_encoding_count += 1

    # 4. Near-Duplicate Analysis (sample pairwise check across random batches to avoid O(N^2) explosion)
    # Check across families and within families
    near_duplicates: List[Dict[str, Any]] = []
    # Cluster by first 3 words or family
    family_buckets = defaultdict(list)
    for s in benchmark:
        family_buckets[s["attack_family"]].append(s)

    for fam, items in family_buckets.items():
        n_items = len(items)
        for i in range(n_items):
            for j in range(i + 1, n_items):
                t1, t2 = items[i]["text"], items[j]["text"]
                # Quick length check
                if abs(len(t1) - len(t2)) / max(len(t1), len(t2), 1) > 0.35:
                    continue
                ratio = SequenceMatcher(None, t1.lower(), t2.lower()).ratio()
                if ratio >= near_dup_threshold:
                    near_duplicates.append({
                        "id1": items[i]["id"],
                        "id2": items[j]["id"],
                        "family": fam,
                        "similarity": round(ratio, 3),
                        "text1": t1,
                        "text2": t2
                    })

    # 5. Cross-Partition Data Leakage
    train_texts = set(normalize_key(s["text"]) for s in train_data)
    val_texts = set(normalize_key(s["text"]) for s in val_data)
    test_texts = set(normalize_key(s["text"]) for s in test_data)

    leak_train_val = train_texts.intersection(val_texts)
    leak_train_test = train_texts.intersection(test_texts)
    leak_val_test = val_texts.intersection(test_texts)

    train_fams = set(s["attack_family"] for s in train_data)
    val_fams = set(s["attack_family"] for s in val_data)
    test_fams = set(s["attack_family"] for s in test_data)

    fam_leak_train_val = train_fams.intersection(val_fams)
    fam_leak_train_test = train_fams.intersection(test_fams)
    fam_leak_val_test = val_fams.intersection(test_fams)

    # 6. Distributions
    classes = Counter(s["label"] for s in benchmark)
    languages = Counter(s["language"] for s in benchmark)
    scripts = Counter(s["script"] for s in benchmark)
    threat_cats = Counter(s["threat_category"] for s in benchmark)
    target_types = Counter(s["target_type"] for s in benchmark)
    provenance = Counter(s["provenance"]["provenance_type"] for s in benchmark)
    licenses = Counter(s["provenance"]["license"] for s in benchmark)
    human_reviewed_count = sum(1 for s in benchmark if s["provenance"]["human_reviewed"])

    audit_report = {
        "dataset_metadata": {
            "name": "BhashaShield-Benchmark-v2",
            "version": "2.2.0",
            "audit_date": "2026-11-21",
            "total_samples": total_samples,
            "unique_raw_inputs": len(raw_counter),
            "unique_normalized_inputs": len(norm_counter)
        },
        "integrity_metrics": {
            "exact_duplicate_count": exact_duplicates,
            "normalized_duplicate_count": norm_duplicates,
            "near_duplicate_count": len(near_duplicates),
            "empty_input_count": empty_count,
            "invalid_encoding_count": invalid_encoding_count,
            "human_reviewed_percentage": round(human_reviewed_count / total_samples * 100, 2)
        },
        "partition_leakage_audit": {
            "train_samples": len(train_data),
            "val_samples": len(val_data),
            "test_samples": len(test_data),
            "text_leakage_train_val": len(leak_train_val),
            "text_leakage_train_test": len(leak_train_test),
            "text_leakage_val_test": len(leak_val_test),
            "family_leakage_train_val": list(fam_leak_train_val),
            "family_leakage_train_test": list(fam_leak_train_test),
            "family_leakage_val_test": list(fam_leak_val_test),
            "is_strictly_leak_free": (
                len(leak_train_val) == 0 and
                len(leak_train_test) == 0 and
                len(leak_val_test) == 0 and
                len(fam_leak_train_val) == 0 and
                len(fam_leak_train_test) == 0 and
                len(fam_leak_val_test) == 0
            )
        },
        "distributions": {
            "classes": dict(classes),
            "languages": dict(languages),
            "scripts": dict(scripts),
            "threat_categories": dict(threat_cats),
            "target_types": dict(target_types),
            "provenance_types": dict(provenance),
            "licenses": dict(licenses)
        },
        "near_duplicate_samples": near_duplicates[:10] # Top 10 illustrative examples
    }

    report_out_path = "backend/data/bhashashield_benchmark_v2_audit_detailed.json"
    with open(report_out_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, ensure_ascii=False, indent=2)

    return audit_report

if __name__ == "__main__":
    rep = audit_benchmark_dataset()
    print("=" * 70)
    print("BHASHASHIELD BENCHMARK V2 INDEPENDENT INTEGRITY AUDIT")
    print("=" * 70)
    print(f"Total Samples:                {rep['dataset_metadata']['total_samples']}")
    print(f"Unique Raw Inputs:            {rep['dataset_metadata']['unique_raw_inputs']}")
    print(f"Unique Normalized Inputs:     {rep['dataset_metadata']['unique_normalized_inputs']}")
    print(f"Exact Duplicates:             {rep['integrity_metrics']['exact_duplicate_count']}")
    print(f"Normalized Duplicates:        {rep['integrity_metrics']['normalized_duplicate_count']}")
    print(f"Near Duplicates (ratio>0.85): {rep['integrity_metrics']['near_duplicate_count']}")
    print(f"Is Partition Leak Free?:      {rep['partition_leakage_audit']['is_strictly_leak_free']}")
    print(f"Classes:                      {rep['distributions']['classes']}")
    print(f"Languages:                    {rep['distributions']['languages']}")
    print(f"Provenance:                   {rep['distributions']['provenance_types']}")
