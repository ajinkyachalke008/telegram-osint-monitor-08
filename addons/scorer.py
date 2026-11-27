"""Rule Scorer for OSINT Post Risk Classification and Explainability.

Scores messages against multi-lingual slang categories (lexicon.yaml):
- drugs, arms, fake_documents, bank_account, atm_card, sim_card, net_banking_kit
Computes weighted scores, extracts matched terms, identifies primary category,
and assigns risk tiers (High / Medium / Low / Clean).
"""
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import yaml

LEXICON_PATH = Path(__file__).parent / "lexicon.yaml"
FEEDBACK_PATH = Path(__file__).parent / "lexicon_feedback.yaml"


@dataclass
class MatchedTerm:
    term: str
    category: str
    section: str  # slang_en, slang_hinglish, slang_marathi, coded_words, emojis
    weight: float


@dataclass
class CategoryScore:
    category: str
    label: str
    raw_score: float
    weighted_score: float
    matched_terms: List[MatchedTerm] = field(default_factory=list)


@dataclass
class ScoreResult:
    risk_level: str  # "High" | "Medium" | "Low" | "Clean"
    total_score: float
    primary_category: Optional[str]
    category_scores: Dict[str, CategoryScore]
    matched_terms: List[Dict[str, Any]]
    is_actionable: bool  # True if High or Medium risk

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "total_score": round(self.total_score, 2),
            "primary_category": self.primary_category,
            "is_actionable": self.is_actionable,
            "matched_terms": self.matched_terms,
            "category_scores": {
                cat: {
                    "label": cs.label,
                    "weighted_score": round(cs.weighted_score, 2),
                    "term_count": len(cs.matched_terms),
                    "terms": [t.term for t in cs.matched_terms],
                }
                for cat, cs in self.category_scores.items() if cs.weighted_score > 0
            }
        }


class RuleScorer:
    def __init__(self, lexicon_file: Optional[Path] = None, feedback_file: Optional[Path] = None):
        self.lexicon_file = lexicon_file or LEXICON_PATH
        self.feedback_file = feedback_file or FEEDBACK_PATH
        self.lexicon = self._load_lexicon()
        self.feedback_weights = self._load_feedback()
        self._compiled_patterns = self._compile_patterns()

    def _load_lexicon(self) -> Dict[str, Any]:
        if not self.lexicon_file.exists():
            raise FileNotFoundError(f"Lexicon file not found at {self.lexicon_file}")
        with open(self.lexicon_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_feedback(self) -> Dict[str, Any]:
        """Load analyst feedback term weight overrides."""
        if not self.feedback_file.exists():
            return {}
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("overrides", {})
        except Exception:
            return {}

    def _compile_patterns(self) -> Dict[str, List[Tuple[str, str, float, re.Pattern]]]:
        """Pre-compile regex patterns for terms for fast matching, applying analyst feedback weights."""
        compiled = {}
        categories = self.lexicon.get("categories", {})
        
        for cat_name, cat_data in categories.items():
            compiled[cat_name] = []
            multiplier = float(cat_data.get("weight_multiplier", 1.0))
            def_weight = float(cat_data.get("default_weight", 2.0))
            
            sections = ["slang_en", "slang_hinglish", "slang_marathi", "coded_words", "emojis"]
            for sec in sections:
                terms = cat_data.get(sec, [])
                for item in terms:
                    term_str = str(item).strip()
                    if not term_str:
                        continue
                    
                    # Check if analyst has set a feedback override for this term
                    lookup_key = f"{cat_name}:{term_str.lower()}"
                    global_key = term_str.lower()

                    if lookup_key in self.feedback_weights:
                        weight = float(self.feedback_weights[lookup_key].get("weight", def_weight))
                    elif global_key in self.feedback_weights:
                        weight = float(self.feedback_weights[global_key].get("weight", def_weight))
                    else:
                        # Baseline weight determination
                        if sec == "emojis":
                            weight = 1.0 * multiplier
                        elif sec == "coded_words":
                            weight = (def_weight + 0.5) * multiplier
                        else:
                            weight = def_weight * multiplier
                        
                    pattern = re.compile(re.escape(term_str)) if sec == "emojis" else re.compile(r"(?i)\b" + re.escape(term_str) + r"\b")
                    compiled[cat_name].append((term_str, sec, weight, pattern))
        return compiled

    def adjust_term_weight(
        self,
        category: str,
        term: str,
        new_weight: float,
        analyst_id: str = "certified_analyst",
        reason: str = "Analyst triage feedback"
    ) -> Dict[str, Any]:
        """
        Analyst feedback loop: Adjusts term weights in lexicon_feedback.yaml ONLY.
        STRICT COMPLIANCE GUARANTEE: Never retrains or fine-tunes ML models on collected posts.
        """
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()
        clean_term = term.strip().lower()
        key = f"{category}:{clean_term}"

        # Load existing overrides
        existing = {}
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, "r", encoding="utf-8") as f:
                    existing = yaml.safe_load(f) or {}
            except Exception:
                existing = {}

        overrides = existing.get("overrides", {})
        overrides[key] = {
            "category": category,
            "term": clean_term,
            "weight": float(new_weight),
            "updated_by": analyst_id,
            "updated_at": ts,
            "reason": reason,
        }
        existing["overrides"] = overrides
        existing["last_updated"] = ts
        existing["compliance_notice"] = "TERM WEIGHTS ADJUSTED ONLY. ZERO ML RETRAINING ON COLLECTED POSTS."

        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.feedback_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(existing, f, sort_keys=False)

        # Reload weights and recompile patterns immediately
        self.feedback_weights = overrides
        self._compiled_patterns = self._compile_patterns()

        # Record in system audit log
        try:
            from core.db import Database
            db = Database()
            db.record_audit_log(
                action="LEXICON_WEIGHT_ADJUSTMENT",
                details={
                    "category": category,
                    "term": clean_term,
                    "new_weight": float(new_weight),
                    "analyst": analyst_id,
                    "reason": reason,
                    "retrained_ml_model": False,
                }
            )
        except Exception:
            pass

        return {
            "category": category,
            "term": clean_term,
            "new_weight": float(new_weight),
            "updated_by": analyst_id,
            "retrained_ml_model": False,
            "compliance_status": "COMPLIANT: Term weight adjusted in lexicon only. No model retraining.",
        }

    def reset_feedback_weights(self):
        """Reset all analyst feedback overrides back to baseline defaults."""
        if self.feedback_file.exists():
            self.feedback_file.unlink()
        self.feedback_weights = {}
        self._compiled_patterns = self._compile_patterns()

    def score(self, text: str, identifiers: Optional[Dict[str, Any]] = None) -> ScoreResult:
        """
        Evaluate text against lexicon categories and calculate composite risk score.
        Incorporates identifier presence (UPI, phone, crypto) to boost confidence.
        """
        if not text:
            return ScoreResult(
                risk_level="Clean",
                total_score=0.0,
                primary_category=None,
                category_scores={},
                matched_terms=[],
                is_actionable=False
            )

        cat_scores: Dict[str, CategoryScore] = {}
        all_matched_terms: List[Dict[str, Any]] = []
        categories = self.lexicon.get("categories", {})

        for cat_name, cat_data in categories.items():
            label = cat_data.get("label", cat_name)
            multiplier = float(cat_data.get("weight_multiplier", 1.0))
            matched_for_cat: List[MatchedTerm] = []
            cat_raw_score = 0.0

            for term_str, sec, weight, pattern in self._compiled_patterns.get(cat_name, []):
                # Search pattern
                if pattern.search(text):
                    mt = MatchedTerm(term=term_str, category=cat_name, section=sec, weight=weight)
                    matched_for_cat.append(mt)
                    cat_raw_score += weight
                    all_matched_terms.append({
                        "term": term_str,
                        "category": cat_name,
                        "category_label": label,
                        "section": sec,
                        "weight": round(weight, 2)
                    })

            cat_weighted_score = cat_raw_score * multiplier
            cat_scores[cat_name] = CategoryScore(
                category=cat_name,
                label=label,
                raw_score=cat_raw_score,
                weighted_score=cat_weighted_score,
                matched_terms=matched_for_cat
            )

        # Total score
        total_score = sum(cs.weighted_score for cs in cat_scores.values())

        # Presence of payment/contact identifiers amplifies risk if illegal terms matched
        if identifiers and total_score > 0:
            if identifiers.get("upis") or identifiers.get("crypto_wallets"):
                total_score += 1.5  # Direct payment channel present
            if identifiers.get("bank_accounts"):
                total_score += 1.5  # Context-labelled bank account candidate present
            if identifiers.get("phones"):
                total_score += 1.0  # Contact channel present

        # Find primary category (highest weighted score)
        primary_category = None
        max_score = 0.0
        for cat_name, cs in cat_scores.items():
            if cs.weighted_score > max_score:
                max_score = cs.weighted_score
                primary_category = cat_name

        # Risk level classification
        if total_score >= 5.0 or (primary_category in ("arms", "net_banking_kit", "bank_account") and total_score >= 4.0):
            risk_level = "High"
        elif total_score >= 2.0:
            risk_level = "Medium"
        elif total_score > 0.0:
            risk_level = "Low"
        else:
            risk_level = "Clean"

        is_actionable = risk_level in ("High", "Medium")

        return ScoreResult(
            risk_level=risk_level,
            total_score=total_score,
            primary_category=primary_category,
            category_scores=cat_scores,
            matched_terms=all_matched_terms,
            is_actionable=is_actionable
        )
