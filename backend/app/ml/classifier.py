import os
from typing import List, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.calibration import CalibratedClassifierCV

class MultilingualSecurityClassifier:
    """
    Multilingual sub-word & n-gram classifier optimized for Indian scripts and romanized text.
    Handles Telugu, Hindi, Romanized Telugu, Romanized Hindi, and English.
    """
    def __init__(self, name: str = "BhashaShield-MuRIL-v1"):
        self.name = name
        # Sub-word char ngrams (3-5) capture morphological roots in Telugu/Hindi script and romanized transliterations
        char_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=2,
            sublinear_tf=True
        )
        # Word ngrams (1-2) capture phrase combinations and injection tokens
        word_vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True
        )
        union = FeatureUnion([
            ("char_ngrams", char_vectorizer),
            ("word_ngrams", word_vectorizer)
        ])
        base_clf = LogisticRegression(C=2.5, class_weight="balanced", max_iter=1000, random_state=42)
        self.pipeline = Pipeline([
            ("features", union),
            ("clf", CalibratedClassifierCV(base_clf, cv=3))
        ])
        self.classes_ = None

    def fit(self, texts: List[str], labels: List[Any]):
        self.pipeline.fit(texts, labels)
        self.classes_ = self.pipeline.classes_
        return self

    def predict(self, texts: List[str]):
        return self.pipeline.predict(texts)

    def predict_proba(self, texts: List[str]):
        return self.pipeline.predict_proba(texts)
