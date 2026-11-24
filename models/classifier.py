"""Hybrid ML and Rule-Based Classifier for Illegal Trade Detection.

Combines:
1. Normalizer (NFKC, homoglyphs, leetspeak, Devanagari numerals)
2. Lexicon RuleScorer (multi-lingual slang, emojis, weighted categories)
3. Synthetic-Trained Scikit-Learn Pipeline (TF-IDF + Logistic Regression)
4. Calibrated Hybrid Scoring with Hard-Negative Suppression & Explainability
"""
import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

from core.normalizer import normalize_text
from addons.scorer import RuleScorer, ScoreResult

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "classifier_weights.joblib"
TRAIN_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "train_synthetic.jsonl"


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
        }


class HybridClassifier:
    """
    Hybrid OSINT classifier that combines semantic TF-IDF ML inference with
    rule-based lexicon scoring and hard-negative suppression.
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
    ]

    def __init__(self, model_path: Optional[Path] = None, auto_load: bool = True):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.scorer = RuleScorer()
        self.pipeline: Optional[Pipeline] = None

        if auto_load and self.model_path.exists():
            self.load(self.model_path)

    def train_on_synthetic(self, data_path: Optional[Path] = None) -> Dict[str, Any]:
        """Train scikit-learn pipeline on synthetic JSONL dataset."""
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
                # Normalize text before training for consistency
                norm_text = normalize_text(record["text"])
                texts.append(norm_text)
                labels.append(record["category"])

        self.pipeline = Pipeline([
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

        self.pipeline.fit(texts, labels)
        self.save(self.model_path)
        return {"samples": len(texts), "classes": list(self.pipeline.classes_)}

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, str(path))

    def load(self, path: Path):
        self.pipeline = joblib.load(str(path))

    def _check_hard_negative(self, text: str) -> bool:
        """Returns True if text contains unmistakable legitimate/warning disclaimer markers."""
        for pat in self.BENIGN_SUPPRESSION_PATTERNS:
            if pat.search(text):
                return True
        return False

    def classify(self, text: str, identifiers: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """
        Classifies post using hybrid pipeline:
        1. Normalize text
        2. Rule-based lexicon scoring
        3. ML inference
        4. Calibration & hard-negative suppression
        5. Explainability generation
        """
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
                normalizations_applied=[]
            )

        # 1. Normalize
        norm_text = normalize_text(text)

        # 2. Rule scoring on normalized text
        score_res: ScoreResult = self.scorer.score(norm_text, identifiers)

        # 3. ML inference
        ml_probs: Dict[str, float] = {}
        top_ml_category = "benign"
        top_ml_prob = 0.0

        if self.pipeline is not None:
            classes = self.pipeline.classes_
            probs = self.pipeline.predict_proba([norm_text])[0]
            for cls_name, prob in zip(classes, probs):
                ml_probs[cls_name] = float(prob)
                if cls_name != "benign" and prob > top_ml_prob:
                    top_ml_prob = prob
                    top_ml_category = cls_name

        # 4. Calibration & Hard-Negative Suppression
        is_hard_neg = self._check_hard_negative(text) or self._check_hard_negative(norm_text)
        
        # Calculate aggregate illegal probability vs benign probability
        total_illegal_prob = sum(prob for cls, prob in ml_probs.items() if cls != "benign")
        benign_prob = ml_probs.get("benign", 0.0)

        # Determine dominant category
        if score_res.primary_category and score_res.total_score >= 2.5:
            category = score_res.primary_category
            cat_ml_prob = ml_probs.get(category, top_ml_prob)
        elif top_ml_prob >= 0.30 and total_illegal_prob > benign_prob:
            category = top_ml_category
            cat_ml_prob = top_ml_prob
        elif score_res.primary_category and score_res.total_score > 0:
            category = score_res.primary_category
            cat_ml_prob = ml_probs.get(category, 0.2)
        else:
            category = "benign"
            cat_ml_prob = 0.0

        # Confidence calculation
        lex_norm = min(1.0, score_res.total_score / 6.0)
        if category == "benign":
            confidence = 0.0
        else:
            confidence = 0.55 * cat_ml_prob + 0.45 * lex_norm

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
        if confidence >= 0.70 or (category in ("arms", "net_banking_kit", "bank_account") and confidence >= 0.55):
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
                reasons.append(f"ML intent probability {cat_ml_prob:.1%}")
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
            normalizations_applied=["nfkc", "homoglyph_fold", "devanagari_fold", "emoji_map"] if norm_text != text else []
        )
