import os
import json
import joblib
from datetime import datetime
from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.calibration import CalibratedClassifierCV
from app.dataset.generator import export_synthetic_datasets
from app.config import settings
from app.ml.classifier import MultilingualSecurityClassifier
def train_model(data_dir: str = "backend/data", model_out_path: str = None) -> Dict[str, Any]:
    if not model_out_path:
        model_out_path = settings.MODEL_PATH

    os.makedirs(os.path.dirname(model_out_path), exist_ok=True)

    # 1. Ensure synthetic datasets are generated
    paths = export_synthetic_datasets(base_dir=data_dir)
    with open(paths["train"], "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(paths["val"], "r", encoding="utf-8") as f:
        val_data = json.load(f)

    train_texts = [d["text"] for d in train_data]
    train_labels = [str(d["threat_category"]) if d["is_malicious"] else "BENIGN" for d in train_data]

    print(f"[*] Training Multilingual Security Classifier on {len(train_texts)} samples across template families...")
    model = MultilingualSecurityClassifier(name="BhashaShield-Multilingual-Classifier-v1")
    model.fit(train_texts, train_labels)

    # 2. Evaluate on validation set
    val_texts = [d["text"] for d in val_data]
    val_labels = [str(d["threat_category"]) if d["is_malicious"] else "BENIGN" for d in val_data]
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
