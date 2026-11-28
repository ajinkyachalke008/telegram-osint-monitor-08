"""Hybrid ML and Rule-Based Classifier for Illegal Trade Detection.

Architecture:
1. Normalizer (NFKC, homoglyphs, leetspeak, Devanagari numerals, spaced words)
2. Multilingual Dense Semantic Embeddings:
   - Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dims)
   - Trained classification head (Logistic Regression) on synthetic data only
   - Fast TF-IDF (1-3 ngrams) secondary feature ensemble
3. Lexicon RuleScorer (multi-lingual slang, emojis, weighted categories)
4. Calibrated Hybrid Scoring with Hard-Negative Suppression & Explainability
"""
import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Lazy import helper for optional neural sentence embeddings (PyTorch + SentenceTransformers)
_TRANSFORMER_INSTANCE = None

def get_embedding_transformer():
    """Lazy-import and instantiate SentenceTransformer model on demand."""
    global _TRANSFORMER_INSTANCE
    if _TRANSFORMER_INSTANCE is not None:
        return _TRANSFORMER_INSTANCE
    try:
        from sentence_transformers import SentenceTransformer
        _TRANSFORMER_INSTANCE = SentenceTransformer(TRANSFORMER_MODEL_NAME)
        return _TRANSFORMER_INSTANCE
    except Exception:
        return None

def is_sentence_transformers_available() -> bool:
    """Check if sentence-transformers and PyTorch are available without downloading models."""
    try:
        import sentence_transformers
        import torch
        return True
    except ImportError:
        return False

from core.normalizer import normalize_text
from addons.scorer import RuleScorer, ScoreResult

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "classifier_weights.joblib"
EMBEDDING_HEAD_PATH = Path(__file__).resolve().parent / "embedding_head.joblib"
TRAIN_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "train_synthetic.jsonl"
TRANSFORMER_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Empirical Winner on Benchmark: TF-IDF (95.56% acc, 1.67ms latency vs 94.89% acc for Embeddings).
# Embeddings will only be made default if human-written evaluations demonstrate superior generalization.
DEFAULT_CLASSIFIER_MODE = "tfidf"


@dataclass
class ClassificationResult:
    category: str  # "drugs", "arms", "bank_account", etc. or "benign"
    confidence: float  # 0.0 to 1.0
    risk_level: str  # "High" | "Medium" | "Low" | "Clean"
    is_actionable: bool
    why_flagged: str
    matched_terms: List[Dict[str, Any]]
    ml_probabilities: Dict[str, float]
    lexicon_score: float
    normalizations_applied: List[str]
    model_architecture: str
    language: str = "EN"
    detected_scripts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "risk_level": self.risk_level,
            "is_actionable": self.is_actionable,
            "why_flagged": self.why_flagged,
            "matched_terms": self.matched_terms,
            "ml_probabilities": {k: round(v, 3) for k, v in self.ml_probabilities.items()},
            "lexicon_score": round(self.lexicon_score, 2),
            "normalizations_applied": self.normalizations_applied,
            "model_architecture": self.model_architecture,
            "language": self.language,
            "detected_scripts": self.detected_scripts,
        }


class HybridClassifier:
    """
    Hybrid OSINT classifier that combines multilingual sentence embeddings
    with TF-IDF n-grams, rule-based lexicon scoring, and hard-negative suppression.
    """

    BENIGN_SUPPRESSION_PATTERNS = [
        re.compile(r"(?i)\bnever share\b"),
        re.compile(r"(?i)\bbeware of (?:fraud|scam|fraudsters)\b"),
        re.compile(r"(?i)\bofficial notice\b"),
        re.compile(r"(?i)\bpublic awareness\b"),
        re.compile(r"(?i)\bdoctor prescription\b"),
        re.compile(r"(?i)\blicensed (?:counter|pharmacy)\b"),
        re.compile(r"(?i)\bshooting championship\b"),
        re.compile(r"(?i)\bpolice (?:busted|arrested|seized)\b"),
        re.compile(r"(?i)\bapartment for rent\b"),
        re.compile(r"(?i)\bcar for sale\b"),
        re.compile(r"(?i)\btutor available\b"),
        re.compile(r"(?i)\bzero liability\b"),
        re.compile(r"(?i)\bcybercrime helpline 1930\b"),
        re.compile(r"(?i)\bpunishable offense under pmla\b"),
        # Hindi and Hinglish public awareness & advisory patterns
        re.compile(r"(?i)\b(?:kabhi|kisi ko)\s+otp\s+(?:share\s+mat|na\s+de|mat\s+batao|kabhi\s+na)\b"),
        re.compile(r"(?i)\b(?:savdhan|satark)\s+rahe\b"),
        re.compile(r"(?i)\b(?:farzi|nakli)\s+(?:sandesh|message|call)\b"),
        re.compile(r"(?i)\bdhokhadhadi\s+se\s+bache\b"),
        re.compile(r"(?i)\bpolice\s+ne\s+(?:pakda|giraftar\s+kiya|baramad\s+kiya|raid\s+mari)\b"),
        re.compile(r"(?i)\bcyber\s*(?:crime)?\s*helpline\b"),
        re.compile(r"(?i)(?:कभी\s*किसी\s*को\s*शेयर\s*न\s*करें|ओटीपी\s*किसी\s*को\s*न\s*दें|सावधान\s*रहें|सतर्क\s*रहें)"),
        re.compile(r"(?i)(?:साइबर\s*हेल्पलाइन|साइबर\s*क्राइम\s*1930|पुलिस\s*ने\s*पकड़ा|गिरफ्तार\s*किया|बरामद\s*किया)"),
        re.compile(r"(?i)(?:फर्जी\s*संदेश|धोखाधड़ी\s*से\s*बचें|जनहित\s*में\s*जारी)"),
    ]

    def __init__(self, model_path: Optional[Path] = None, auto_load: bool = True):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.embedding_head_path = EMBEDDING_HEAD_PATH
        self.scorer = RuleScorer()
        self.tfidf_pipeline: Optional[Pipeline] = None
        self._embedding_model: Optional[Any] = None
        self.embedding_clf: Optional[LogisticRegression] = None
        self.model_name = "TF-IDF + RuleScorer"

        if auto_load:
            if self.embedding_head_path.exists():
                try:
                    self.embedding_clf = joblib.load(str(self.embedding_head_path))
                except Exception:
                    self.embedding_clf = None
            if self.model_path.exists():
                try:
                    self.tfidf_pipeline = joblib.load(str(self.model_path))
                except Exception:
                    self.tfidf_pipeline = None

    @property
    def embedding_model(self) -> Optional[Any]:
        """Lazy-loaded SentenceTransformer model."""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_transformer()
            if self._embedding_model is not None:
                self.model_name = f"paraphrase-multilingual-MiniLM-L12-v2 + RuleScorer"
        return self._embedding_model

    @property
    def embedding_available(self) -> bool:
        """True if SentenceTransformer is importable and weights are loaded."""
        return is_sentence_transformers_available() and self.embedding_clf is not None

    def train_on_synthetic(self, data_path: Optional[Path] = None) -> Dict[str, Any]:
        """Train both multilingual embeddings head and TF-IDF pipeline on synthetic JSONL dataset."""
        path = data_path or TRAIN_DATA_PATH
        if not path.exists():
            raise FileNotFoundError(f"Training data not found at {path}")

        texts = []
        labels = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                norm_text = normalize_text(record["text"])
                texts.append(norm_text)
                labels.append(record["category"])

        # 1. Train TF-IDF pipeline
        self.tfidf_pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=25000,
                sublinear_tf=True,
                strip_accents="unicode"
            )),
            ("clf", LogisticRegression(
                C=2.5,
                max_iter=1000,
                class_weight="balanced",
                random_state=42
            ))
        ])
        self.tfidf_pipeline.fit(texts, labels)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.tfidf_pipeline, str(self.model_path))

        # 2. Train Multilingual Embedding Classification Head (if sentence-transformers available)
        if self.embedding_model is not None:
            print("Encoding synthetic texts with paraphrase-multilingual-MiniLM-L12-v2...")
            embeddings = self.embedding_model.encode(texts, batch_size=64, show_progress_bar=False)
            self.embedding_clf = LogisticRegression(
                C=2.0,
                max_iter=1000,
                class_weight="balanced",
                random_state=42
            )
            self.embedding_clf.fit(embeddings, labels)
            joblib.dump(self.embedding_clf, str(self.embedding_head_path))
            print("Multilingual embedding head trained and saved.")

        return {
            "samples": len(texts),
            "classes": list(self.tfidf_pipeline.classes_),
            "multilingual_embeddings_enabled": bool(self.embedding_clf is not None)
        }

    def _check_hard_negative(self, text: str) -> bool:
        """Returns True if text contains unmistakable legitimate/warning disclaimer markers."""
        for pat in self.BENIGN_SUPPRESSION_PATTERNS:
            if pat.search(text):
                return True
        return False

    def classify(
        self,
        text: str,
        identifiers: Optional[Dict[str, Any]] = None,
        mode: str = "auto"
    ) -> ClassificationResult:
        """
        Classifies post using hybrid pipeline:
        1. Text normalization
        2. Rule-based lexicon scoring
        3. Multilingual Embedding or TF-IDF ML inference (configured via `mode`: "auto" | "embedding" | "tfidf")
        4. Calibration & hard-negative suppression
        5. Explainability generation
        """
        # Resolve effective inference mode (defaulting to empirical winner TF-IDF)
        effective_mode = DEFAULT_CLASSIFIER_MODE if mode == "auto" else mode
        active_arch = "TF-IDF + RuleScorer" if effective_mode == "tfidf" else self.model_name
        if not text or not text.strip():
            return ClassificationResult(
                category="benign",
                confidence=0.0,
                risk_level="Clean",
                is_actionable=False,
                why_flagged="Empty text.",
                matched_terms=[],
                ml_probabilities={},
                lexicon_score=0.0,
                normalizations_applied=[],
                model_architecture=active_arch,
                language="UNKNOWN",
                detected_scripts=[]
            )

        from core.multilingual import detect_language_and_script
        lang_tag, detected_scripts = detect_language_and_script(text)

        # 1. Normalize
        norm_text = normalize_text(text)

        # 2. Rule scoring on normalized text
        score_res: ScoreResult = self.scorer.score(norm_text, identifiers)

        # 3. ML inference (Embeddings vs TF-IDF selection)
        ml_probs: Dict[str, float] = {}
        top_ml_category = "benign"
        top_ml_prob = 0.0

        use_emb = (effective_mode == "embedding") and (self.embedding_model is not None and self.embedding_clf is not None)
        if use_emb:
            emb = self.embedding_model.encode([norm_text], show_progress_bar=False)
            classes = self.embedding_clf.classes_
            probs = self.embedding_clf.predict_proba(emb)[0]
            for cls_name, prob in zip(classes, probs):
                ml_probs[cls_name] = float(prob)
                if cls_name != "benign" and prob > top_ml_prob:
                    top_ml_prob = prob
                    top_ml_category = cls_name
        elif self.tfidf_pipeline is not None:
            classes = self.tfidf_pipeline.classes_
            probs = self.tfidf_pipeline.predict_proba([norm_text])[0]
            for cls_name, prob in zip(classes, probs):
                ml_probs[cls_name] = float(prob)
                if cls_name != "benign" and prob > top_ml_prob:
                    top_ml_prob = prob
                    top_ml_category = cls_name

        # 4. Calibration & Hard-Negative Suppression
        is_hard_neg = self._check_hard_negative(text) or self._check_hard_negative(norm_text) or score_res.is_awareness
        
        # Calculate aggregate illegal probability vs benign probability
        total_illegal_prob = sum(prob for cls, prob in ml_probs.items() if cls != "benign")
        benign_prob = ml_probs.get("benign", 0.0)

        # Determine dominant category
        if score_res.primary_category and score_res.total_score >= 2.5:
            category = score_res.primary_category
            cat_ml_prob = max(ml_probs.get(category, 0.0), top_ml_prob if top_ml_category != "benign" else 0.0)
        elif top_ml_prob >= 0.30 and total_illegal_prob > benign_prob:
            category = top_ml_category
            cat_ml_prob = top_ml_prob
        elif score_res.primary_category and score_res.total_score > 0:
            category = score_res.primary_category
            cat_ml_prob = max(ml_probs.get(category, 0.2), top_ml_prob if top_ml_category != "benign" else 0.2)
        else:
            category = "benign"
            cat_ml_prob = 0.0

        # Confidence calculation
        lex_norm = min(1.0, score_res.total_score / 6.0)
        if category == "benign":
            confidence = 0.0
        else:
            confidence = 0.60 * cat_ml_prob + 0.40 * lex_norm

        # Suppress if hard negative detected
        if is_hard_neg:
            confidence = max(0.0, confidence * 0.15)
            if confidence < 0.25:
                category = "benign"

        # Identifier booster
        if identifiers and category != "benign" and not is_hard_neg:
            has_payment = bool(identifiers.get("upis") or identifiers.get("crypto_wallets"))
            has_contact = bool(identifiers.get("phones") or identifiers.get("usernames"))
            if has_payment:
                confidence = min(0.99, confidence + 0.12)
            if has_contact:
                confidence = min(0.99, confidence + 0.08)

        # Risk level determination
        if confidence >= 0.65 or (category in ("arms", "net_banking_kit", "bank_account") and confidence >= 0.50):
            risk_level = "High"
        elif confidence >= 0.35:
            risk_level = "Medium"
        elif confidence >= 0.15:
            risk_level = "Low"
        else:
            risk_level = "Clean"

        is_actionable = risk_level in ("High", "Medium")

        # 5. Why Flagged Explainability
        if risk_level == "Clean" or category == "benign":
            if is_hard_neg:
                why_flagged = "Classified as Clean: Legitimate advisory/notice disclaimers detected."
            else:
                why_flagged = "No illegal trade indicators or suspicious patterns detected."
        else:
            matched_terms_names = [t["term"] for t in score_res.matched_terms[:5]]
            reasons = []
            if matched_terms_names:
                reasons.append(f"matched slang/coded terms {matched_terms_names}")
            if cat_ml_prob >= 0.40:
                reasons.append(f"multilingual embedding probability {cat_ml_prob:.1%}")
            if identifiers and (identifiers.get("upis") or identifiers.get("crypto_wallets")):
                reasons.append("direct financial payment identifiers present")
            elif identifiers and identifiers.get("phones"):
                reasons.append("contact telephone numbers extracted")

            reason_str = "; ".join(reasons) if reasons else "suspicious structural pattern"
            why_flagged = (
                f"Flagged as {risk_level} Risk for category '{category}' "
                f"(confidence {confidence:.1%}): {reason_str}."
            )

        return ClassificationResult(
            category=category,
            confidence=confidence,
            risk_level=risk_level,
            is_actionable=is_actionable,
            why_flagged=why_flagged,
            matched_terms=score_res.matched_terms,
            ml_probabilities=ml_probs,
            lexicon_score=score_res.total_score,
            normalizations_applied=["nfkc", "homoglyph_fold", "devanagari_fold", "emoji_map"] if norm_text != text else [],
            model_architecture=self.model_name,
            language=lang_tag.value,
            detected_scripts=detected_scripts
        )
