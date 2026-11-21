import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import json
import joblib
from datetime import datetime
from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.calibration import CalibratedClassifierCV
from app.dataset.generator import export_synthetic_datasets
from app.config import BASE_DIR, settings
from app.ml.classifier import MultilingualSecurityClassifier

def train_model(data_dir: str = None, model_out_path: str = None) -> Dict[str, Any]:
    if not data_dir:
        data_dir = str(BASE_DIR / "data")
    if not model_out_path:
        model_out_path = settings.MODEL_PATH

    os.makedirs(os.path.dirname(model_out_path), exist_ok=True)

    # 1. Load foundational balanced dataset and diverse benchmark v2 training data
    paths = export_synthetic_datasets(base_dir=data_dir)
    with open(paths["train"], "r", encoding="utf-8") as f:
        synth_train = json.load(f)

    train_texts = [d["text"] for d in synth_train]
    train_labels = [str(d["threat_category"]) if d["is_malicious"] else "BENIGN" for d in synth_train]

    v2_train_path = os.path.join(data_dir, "benchmark_v2_train.json")
    v2_val_path = os.path.join(data_dir, "benchmark_v2_val.json")

    seen_train_texts = set(train_texts)
    if os.path.exists(v2_train_path):
        with open(v2_train_path, "r", encoding="utf-8") as f:
            v2_train = json.load(f)
        for d in v2_train:
            t = d["text"]
            lbl = d.get("label")
            if lbl in ("BENIGN", "MALICIOUS") and t not in seen_train_texts:
                train_texts.append(t)
                train_labels.append(d["threat_category"] if lbl == "MALICIOUS" else "BENIGN")
                seen_train_texts.add(t)

    if os.path.exists(v2_val_path):
        with open(v2_val_path, "r", encoding="utf-8") as f:
            val_raw = json.load(f)
        val_texts = [d["text"] for d in val_raw if d.get("label") in ("BENIGN", "MALICIOUS")]
        val_labels = [d["threat_category"] if d.get("label") == "MALICIOUS" else "BENIGN" for d in val_raw if d.get("label") in ("BENIGN", "MALICIOUS")]
    else:
        with open(paths["val"], "r", encoding="utf-8") as f:
            val_data = json.load(f)
        val_texts = [d["text"] for d in val_data]
        val_labels = [str(d["threat_category"]) if d["is_malicious"] else "BENIGN" for d in val_data]

    print(f"[*] Training Multilingual Security Classifier on {len(train_texts)} samples across template families...")
    model = MultilingualSecurityClassifier(name="BhashaShield-Multilingual-Classifier-v1")
    model.fit(train_texts, train_labels)

    # 2. Evaluate on validation set
    val_preds = model.predict(val_texts)

    correct = sum(1 for p, y in zip(val_preds, val_labels) if p == y)
    val_acc = correct / len(val_labels) if val_labels else 0.0
    print(f"[+] Validation Accuracy on unseen template family: {val_acc:.4f}")

    # 3. Save model
    joblib.dump(model, model_out_path)
    print(f"[+] Model saved successfully to {model_out_path}")

    return {
        "status": "success",
        "model_name": model.name,
        "model_path": model_out_path,
        "train_samples": len(train_texts),
        "val_samples": len(val_texts),
        "val_accuracy": round(val_acc, 4),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    train_model()
