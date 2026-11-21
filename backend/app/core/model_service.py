import os
import logging
import joblib
import numpy as np
from typing import Optional, Dict, Any
from app.models import ModelFinding
from app.config import settings

logger = logging.getLogger("bhashashield.model")

class ModelService:
    """
    Multilingual Model Service.
    Transparently reports whether a genuine MuRIL/XLM-R transformer model or
    scikit-learn multilingual n-gram classifier is loaded, or explicitly falls back
    to RULES-ONLY MODE. Never fabricates predictions.
    """
    def __init__(self):
        self.model_path = settings.MODEL_PATH
        self.model = None
        self.tokenizer = None
        self.model_backend = None # 'transformer' or 'sklearn'
        self.status = "MODEL NOT LOADED — RULES-ONLY MODE"
        self._load_model()

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def _verify_genuine_transformer_model(self) -> bool:
        """
        Verify whether genuine Hugging Face MuRIL / transformer weights and dependencies exist.
        """
        try:
            import torch
            import transformers
        except ImportError:
            return False

        if not os.path.exists(self.model_path):
            return False

        if os.path.isdir(self.model_path):
            has_config = os.path.exists(os.path.join(self.model_path, "config.json"))
            has_weights = (
                os.path.exists(os.path.join(self.model_path, "model.safetensors")) or
                os.path.exists(os.path.join(self.model_path, "pytorch_model.bin"))
            )
            return has_config and has_weights

        return False

    def _verify_genuine_sklearn_model(self) -> bool:
        """
        Verify whether a trained scikit-learn multilingual classifier exists.
        """
        if not os.path.exists(self.model_path):
            return False
        return self.model_path.endswith(".joblib") or self.model_path.endswith(".pkl")

    def _load_model(self):
        if not settings.USE_ML_MODEL:
            self.status = "MODEL DISABLED — RULES-ONLY MODE"
            self.model = None
            self.model_backend = None
            return

        # 1. Try PyTorch / HuggingFace Transformer
        if self._verify_genuine_transformer_model():
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
                self.model.eval()
                self.model_backend = "transformer"
                self.status = "ACTIVE: MuRIL Transformer (PyTorch)"
                logger.info("Successfully loaded genuine MuRIL transformer model.")
                return
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")

        # 2. Try Scikit-Learn Multilingual Security Classifier
        if self._verify_genuine_sklearn_model():
            try:
                loaded = joblib.load(self.model_path)
                if hasattr(loaded, "predict") and hasattr(loaded, "predict_proba"):
                    self.model = loaded
                    self.tokenizer = None
                    self.model_backend = "sklearn"
                    model_title = getattr(loaded, "name", "Multilingual N-Gram Classifier")
                    self.status = f"ACTIVE: {model_title} (scikit-learn)"
                    logger.info(f"Successfully loaded genuine {model_title}.")
                    return
            except Exception as e:
                logger.warning(f"Failed to load scikit-learn model: {e}")

        # 3. Explicit fallback
        self.status = "MODEL NOT LOADED — RULES-ONLY MODE"
        self.model = None
        self.tokenizer = None
        self.model_backend = None
        logger.info("Operating in RULES-ONLY MODE.")

    def reload(self):
        self._load_model()

    def predict(self, text: str) -> Optional[ModelFinding]:
        if not self.is_loaded:
            return None

        # Transformer Inference
        if self.model_backend == "transformer" and self.tokenizer is not None:
            try:
                import torch
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = torch.softmax(outputs.logits, dim=-1)[0].tolist()

                classes = ["BENIGN", "PROMPT_INJECTION"]
                pred_idx = int(torch.argmax(outputs.logits, dim=-1)[0])
                pred_class = classes[pred_idx] if pred_idx < len(classes) else str(pred_idx)
                max_prob = float(probs[pred_idx])

                return ModelFinding(
                    predicted_class=pred_class,
                    probability=round(max_prob, 3),
                    is_malicious=(pred_class != "BENIGN"),
                    model_name="MuRIL-Transformer",
                    probabilities_by_class={c: round(p, 3) for c, p in zip(classes, probs)}
                )
            except Exception as e:
                logger.warning(f"Transformer inference error: {e}")
                return None

        # Scikit-Learn Inference
        if self.model_backend == "sklearn":
            try:
                probs = self.model.predict_proba([text])[0]
                classes = list(getattr(self.model, "classes_", ["BENIGN", "PROMPT_INJECTION"]))
                sorted_idx = np.argsort(probs)[::-1]
                top_idx = int(sorted_idx[0])
                pred_class = classes[top_idx]
                max_prob = float(probs[top_idx])

                second_prob = float(probs[sorted_idx[1]]) if len(sorted_idx) > 1 else 0.0
                margin = float(max_prob - second_prob)

                p_safe = np.clip(probs, 1e-9, 1.0)
                entropy = float(-np.sum(p_safe * np.log2(p_safe)) / np.log2(max(2, len(probs))))
                is_ambiguous = (margin < 0.20 or entropy > 0.75)

                # Determine if malicious
                is_malicious = (pred_class not in ("BENIGN", "0", 0, "UNKNOWN"))

                return ModelFinding(
                    predicted_class=str(pred_class),
                    probability=round(max_prob, 3),
                    is_malicious=is_malicious,
                    model_name=getattr(self.model, "name", "BhashaShield-ML-v1"),
                    probabilities_by_class={str(c): round(float(p), 3) for c, p in zip(classes, probs)},
                    margin=round(margin, 3),
                    entropy=round(entropy, 3),
                    is_ambiguous=is_ambiguous
                )
            except Exception as e:
                logger.warning(f"Scikit-learn inference error: {e}")
                return None

        return None

# Singleton instance
model_service = ModelService()
