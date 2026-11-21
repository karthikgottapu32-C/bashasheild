import json
import os
import re
from collections import Counter
from typing import Dict, Any

def audit_benchmark_v3():
    v3_path = "backend/data/bhashashield_benchmark_v3.json"
    audit_out = "backend/data/benchmark_v3_audit.json"

    with open(v3_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_samples = len(data)
    raw_texts = [d["text"] for d in data]
    unique_raw_texts = len(set(raw_texts))

    # Normalized keys
    def normalize_str(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r'[\s\W_]+', ' ', s)
        return s.strip()

    normalized_keys = [normalize_str(t) for t in raw_texts]
    unique_norm_keys = len(set(normalized_keys))

    exact_duplicates = total_samples - unique_raw_texts
    normalized_duplicates = total_samples - unique_norm_keys

    classes = Counter(d["label"] for d in data)
    languages = Counter(d["language"] for d in data)
    scripts = Counter(d["script"] for d in data)
    threat_cats = Counter(d["threat_category"] for d in data)
    def get_prov(p):
        if isinstance(p, dict):
            return p.get("provenance_type", "unknown")
        return str(p)

    provenances = Counter(get_prov(d.get("provenance")) for d in data)
    attack_families = Counter(d.get("attack_family", "unknown") for d in data)

    # Verification of corrected samples
    corrected_ids = ["BS23-01051", "BS23-01052", "BS23-01053", "BS23-01054", "BS23-01055"]
    corrected_verified = all(
        any(d["id"] == cid and d["label"] == "BENIGN" for d in data)
        for cid in corrected_ids
    )

    audit_result = {
        "benchmark_version": "v3.0.0",
        "total_samples": total_samples,
        "unique_raw_texts": unique_raw_texts,
        "unique_normalized_keys": unique_norm_keys,
        "exact_duplicates": exact_duplicates,
        "normalized_duplicates": normalized_duplicates,
        "v2_corrected_samples_verified": corrected_verified,
        "class_distribution": dict(classes),
        "threat_category_distribution": dict(threat_cats),
        "language_distribution": dict(languages),
        "script_distribution": dict(scripts),
        "provenance_distribution": dict(provenances),
        "total_attack_families": len(attack_families)
    }

    with open(audit_out, "w", encoding="utf-8") as f:
        json.dump(audit_result, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print("BHASHASHIELD BENCHMARK V3 INTEGRITY AUDIT")
    print("=" * 60)
    print(f"Total Samples:            {total_samples}")
    print(f"Unique Raw Texts:         {unique_raw_texts}")
    print(f"Exact Duplicates:         {exact_duplicates}")
    print(f"Normalized Duplicates:    {normalized_duplicates}")
    print(f"V2 Corrections Verified:  {corrected_verified}")
    print(f"Total Attack Families:    {len(attack_families)}")
    print("\nClass Distribution:")
    for k, v in classes.items():
        print(f"  {k:12}: {v:5} ({v/total_samples*100:.2f}%)")
    print("\nLanguage Distribution:")
    for k, v in languages.items():
        print(f"  {k:12}: {v:5} ({v/total_samples*100:.2f}%)")
    print("=" * 60)

if __name__ == "__main__":
    audit_benchmark_v3()
