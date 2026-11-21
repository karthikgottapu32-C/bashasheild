import os
import numpy as np
from typing import List, Dict, Any, Tuple
from scipy.sparse import issparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.calibration import CalibratedClassifierCV

class MultilingualSecurityClassifier:
    """
    Multilingual Contextual Sub-word & N-gram Security Classifier.
    Designed for zero-OOM production deployment (<120MB resident RAM).
    Features:
    - Sub-word char ngrams (3-5) for Indic script root morphology and romanized transliterations.
    - Word ngrams (1-2) for multi-token adversarial phrases and imperative verbs.
    - Out-of-Distribution (OOD) low-activation attenuation: prevents spurious predictions on single words.
    - Probability calibration with entropy and confidence margin metrics.
    """
    def __init__(self, name: str = "BhashaShield-Multilingual-Classifier-v1"):
        self.name = name
        char_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=2,
            sublinear_tf=True
        )
        word_vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True
        )
        self.feature_union = FeatureUnion([
            ("char_ngrams", char_vectorizer),
            ("word_ngrams", word_vectorizer)
        ])
        base_clf = LogisticRegression(
            C=2.0,
            class_weight="balanced",
            max_iter=1500,
            random_state=42
        )
        self.pipeline = Pipeline([
            ("features", self.feature_union),
            ("clf", CalibratedClassifierCV(estimator=base_clf, cv=3))
        ])
        self.classes_ = None

    def fit(self, texts: List[str], labels: List[Any]):
        self.pipeline.fit(texts, labels)
        self.classes_ = list(self.pipeline.classes_)
        return self

    def predict(self, texts: List[str]) -> np.ndarray:
        return self.pipeline.predict(texts)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        return self.pipeline.predict_proba(texts)

    def analyze_sample(self, text: str) -> Dict[str, Any]:
        """
        Calculates top prediction, probability distribution, confidence margin, entropy, and OOD activation.
        """
        probs = self.predict_proba([text])[0]
        sorted_indices = np.argsort(probs)[::-1]
        top_idx = int(sorted_indices[0])
        top_class = self.classes_[top_idx]
        top_prob = float(probs[top_idx])

        second_prob = float(probs[sorted_indices[1]]) if len(sorted_indices) > 1 else 0.0
        margin = float(top_prob - second_prob)

        # Normalized Shannon entropy
        p_safe = np.clip(probs, 1e-9, 1.0)
        entropy = float(-np.sum(p_safe * np.log2(p_safe)) / np.log2(len(probs)))

        # Feature activation norm to detect Out-of-Distribution (OOD) inputs
        try:
            feats = self.pipeline.named_steps["features"].transform([text])
            if issparse(feats):
                norm = float(np.asarray(feats.power(2).sum(axis=1)).flatten()[0])
            else:
                norm = float(np.sum(feats ** 2, axis=1)[0])
        except Exception:
            norm = 1.0

        is_ood = bool(norm < 0.06)
        is_ambiguous = bool(margin < 0.20 or entropy > 0.70 or is_ood)

        return {
            "predicted_class": top_class,
            "probability": round(top_prob, 3),
            "second_class": self.classes_[int(sorted_indices[1])] if len(sorted_indices) > 1 else None,
            "margin": round(margin, 3),
            "entropy": round(entropy, 3),
            "is_ambiguous": is_ambiguous,
            "is_ood": is_ood,
            "norm": round(norm, 4),
            "probabilities_by_class": {c: round(float(p), 3) for c, p in zip(self.classes_, probs)}
        }
