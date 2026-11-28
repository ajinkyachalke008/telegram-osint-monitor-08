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

# Canonical concepts for concept-level deduplication across multi-lingual aliases
CANONICAL_CONCEPTS: Dict[str, str] = {
    # arms
    "katta": "country_pistol",
    "desi katta": "country_pistol",
    "gavti katta": "country_pistol",
    "tamancha": "country_pistol",
    "desi pistol": "country_pistol",
    "कट्टा": "country_pistol",
    "देसी कट्टा": "country_pistol",
    "तमंचा": "country_pistol",
    "देसी पिस्टल": "country_pistol",
    "bandook": "firearm_rifle",
    "banduk": "firearm_rifle",
    "बंदूक": "firearm_rifle",
    "rifle": "firearm_rifle",
    "राइफल": "firearm_rifle",
    "shotgun": "firearm_rifle",
    "pistol": "handgun",
    "पिस्तौल": "handgun",
    "revolver": "handgun",
    "रिवाल्वर": "handgun",
    "glock": "handgun",
    "hathiyar": "weapon_generic",
    "हथियार": "weapon_generic",
    "asla": "weapon_generic",
    "असला": "weapon_generic",
    "ammo": "ammunition",
    "bullets": "ammunition",
    "cartridge": "ammunition",
    "goli": "ammunition",
    "गोली": "ammunition",
    "कारतूस": "ammunition",

    # fake_documents
    "aadhar": "fake_aadhar",
    "nakli aadhar": "fake_aadhar",
    "आधार": "fake_aadhar",
    "नकली आधार": "fake_aadhar",
    "farzi aadhar": "fake_aadhar",
    "pan card": "fake_pan",
    "पैन कार्ड": "fake_pan",
    "nakli pan": "fake_pan",
    "driving license": "fake_dl",
    "ड्राइविंग लाइसेंस": "fake_dl",
    "passport": "fake_passport",
    "पासपोर्ट": "fake_passport",
    "marksheet": "fake_marksheet",
    "अंकतालिका": "fake_marksheet",
    "voter id": "fake_voter_id",
    "पहचान पत्र": "fake_voter_id",

    # bank_account / net_banking_kit / atm_card
    "mule account": "mule_account",
    "mule khata": "mule_account",
    "current account": "mule_account",
    "khata": "mule_account",
    "खाता": "mule_account",
    "corporate account": "mule_account",
    "atm card": "card_cloning",
    "debit card": "card_cloning",
    "clone card": "card_cloning",
    "क्लोन कार्ड": "card_cloning",
    "netbanking kit": "banking_kit",
    "नेटबैंकिंग किट": "banking_kit",
    "फुल किट": "banking_kit",
    "full kit": "banking_kit",

    # sim_card
    "chalu sim": "mule_sim",
    "चालू सिम": "mule_sim",
    "fake kyc sim": "mule_sim",
    "फर्जी सिम": "mule_sim",
    "pre activated sim": "mule_sim",

    # drugs
    "mdma": "mdma",
    "एमडीएमए": "mdma",
    "charas": "cannabis_resin",
    "चरस": "cannabis_resin",
    "hashish": "cannabis_resin",
    "ganja": "cannabis_herb",
    "गांजा": "cannabis_herb",
    "weed": "cannabis_herb",
    "heroin": "opiate",
    "हेरोइन": "opiate",
    "chitta": "opiate",
    "smack": "opiate",
    "brown sugar": "opiate",
    "ब्राउन शुगर": "opiate",
    "cocaine": "cocaine",
    "कोकीन": "cocaine",
    "c0ke": "cocaine",
    "afeem": "opium",
    "अफीम": "opium",
    "meow meow": "mephedrone",
    "mephedrone": "mephedrone",
    "मेफेड्रोन": "mephedrone",
}


# Generic / Neutral Weapons Context Terms (Context-Only by default unless accompanied by active trade solicitation)
GENERIC_WEAPONS_TERMS: Set[str] = {
    # English
    "gun", "guns", "firearm", "firearms", "weapon", "weapons", "arms", "pistol",
    "revolver", "rifle", "shotgun", "handgun", "ammunition", "ammo", "bullet",
    "bullets", "cartridge", "knife", "blade",
    # Hinglish
    "desi katta", "katta", "tamancha", "bandook", "banduk", "hathiyar", "asla", "desi pistol",
    # Hindi Devanagari
    "पिस्तौल", "रिवाल्वर", "कट्टा", "देसी कट्टा", "तमंचा", "बंदूक", "हथियार",
    "गोली", "कारतूस", "असला", "राइफल", "छुरी", "लोहा", "देसी पिस्टल", "चाकु", "तलवार",
    # Marathi
    "gavti katta", "gavthi katta", "banduk", "chaku", "talwar"
}


@dataclass
class MatchedTerm:
    term: str
    category: str
    section: str  # slang_en, slang_hi, slang_hinglish, slang_marathi, coded_words, emojis
    weight: float
    is_context_only: bool = False


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
    language: str = "EN"
    is_awareness: bool = False
    awareness_markers: List[str] = field(default_factory=list)
    advisory_context_type: str = "none"
    advisory_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "total_score": round(self.total_score, 2),
            "primary_category": self.primary_category,
            "is_actionable": self.is_actionable,
            "language": self.language,
            "is_awareness": self.is_awareness,
            "awareness_markers": self.awareness_markers,
            "advisory_context_type": self.advisory_context_type,
            "advisory_explanation": self.advisory_explanation,
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
            
            sections = ["slang_en", "slang_hi", "slang_hinglish", "slang_marathi", "coded_words", "emojis"]
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
                        base_weight = float(self.feedback_weights[lookup_key].get("weight", def_weight))
                    elif global_key in self.feedback_weights:
                        base_weight = float(self.feedback_weights[global_key].get("weight", def_weight))
                    else:
                        # Baseline weight determination (base weight, NOT multiplied by category multiplier here)
                        # Multiplier is applied to cat_raw_score in score() to eliminate double-multiplication
                        if sec == "emojis":
                            base_weight = 1.0
                        elif sec == "coded_words":
                            base_weight = def_weight + 0.5
                        else:
                            base_weight = def_weight
                        
                    if sec == "emojis":
                        pattern = re.compile(re.escape(term_str))
                    else:
                        # Unicode boundary matching supporting both Latin and Devanagari scripts accurately
                        pattern = re.compile(rf"(?i)(?<![\u0900-\u097F\w]){re.escape(term_str)}(?![\u0900-\u097F\w])")
                    compiled[cat_name].append((term_str, sec, base_weight, pattern))
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
        Supports English, Hindi Devanagari, and Hinglish with concept-level deduplication,
        context-only neutral weapons boundary, and validated public awareness suppression.
        """
        if not text:
            return ScoreResult(
                risk_level="Clean",
                total_score=0.0,
                primary_category=None,
                category_scores={},
                matched_terms=[],
                is_actionable=False,
                language="UNKNOWN",
                advisory_context_type="none",
                advisory_explanation="Empty text."
            )

        # 1. Ensure shared normalized text pipeline is used across all callers
        from core.normalizer import normalize_text
        norm_text = normalize_text(text)

        # 2. Multilingual script detection and validated awareness context evaluation
        from core.multilingual import detect_language_and_script, evaluate_awareness_context
        lang_tag, detected_scripts = detect_language_and_script(norm_text)
        awareness_res = evaluate_awareness_context(norm_text)

        # 3. Detect active commercial trade / seller solicitation cues
        has_contact_or_payment = bool(
            identifiers and (
                identifiers.get("phones") or identifiers.get("upis") or
                identifiers.get("crypto_wallets") or identifiers.get("usernames")
            )
        )
        trade_cues_pat = re.compile(
            r"(?i)\b(?:in\s+stock|available|fresh\s+stock|deliver(?:y|ed)?|for\s+sale|price|rates?|piece|cash\s+on\s+delivery|cod|ping|dm|contact|order|payment|cash\s+payment|loaded|full\s+loaded|consignment|deal|dispatch|selling|ready\s+stock|ready)\b"
        )
        indic_trade_cues_pat = re.compile(
            r"(?:स्टॉक|उपलब्ध|डिलीवरी|बिक्री|कीमत|भाव|कैश\s*ऑन\s*डिलीवरी|संपर्क|ऑर्डर|नकद|भुगतान|सौदा|तैयार)"
        )
        has_trade_cues = bool(trade_cues_pat.search(norm_text) or indic_trade_cues_pat.search(norm_text) or has_contact_or_payment)

        cat_scores: Dict[str, CategoryScore] = {}
        all_matched_terms: List[Dict[str, Any]] = []
        categories = self.lexicon.get("categories", {})

        for cat_name, cat_data in categories.items():
            label = cat_data.get("label", cat_name)
            multiplier = float(cat_data.get("weight_multiplier", 1.0))
            matched_for_cat: List[MatchedTerm] = []
            cat_raw_score = 0.0
            seen_concepts_in_cat = set()

            for term_str, sec, base_weight, pattern in self._compiled_patterns.get(cat_name, []):
                # Search pattern on normalized text
                if pattern.search(norm_text):
                    # Check context-only boundary for arms category
                    is_context_only = False
                    term_weight = base_weight

                    if cat_name == "arms" and sec != "coded_words":
                        clean_lower = term_str.lower()
                        if clean_lower in GENERIC_WEAPONS_TERMS:
                            if not has_trade_cues:
                                # Isolated neutral mention: strictly context-only, zero score inflation
                                is_context_only = True
                                term_weight = 0.0

                    mt = MatchedTerm(
                        term=term_str,
                        category=cat_name,
                        section=sec,
                        weight=term_weight,
                        is_context_only=is_context_only
                    )
                    matched_for_cat.append(mt)

                    # Canonical concept for deduplication within the post
                    canonical = CANONICAL_CONCEPTS.get(term_str.lower(), term_str.lower())
                    if canonical not in seen_concepts_in_cat:
                        seen_concepts_in_cat.add(canonical)
                        cat_raw_score += term_weight

                    all_matched_terms.append({
                        "term": term_str,
                        "category": cat_name,
                        "category_label": label,
                        "section": sec,
                        "weight": round(term_weight * multiplier, 2),
                        "canonical_concept": canonical,
                        "is_context_only": is_context_only
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

        # Presence of payment/contact identifiers amplifies risk if non-context illegal terms matched
        if identifiers and total_score > 0 and not awareness_res.is_confirmed_advisory:
            if identifiers.get("upis") or identifiers.get("crypto_wallets"):
                total_score += 1.5  # Direct payment channel present
            if identifiers.get("phones"):
                total_score += 1.0  # Contact channel present

        # Validated institutional advisory suppression (only when confirmed benign)
        is_awareness = awareness_res.is_confirmed_advisory
        if is_awareness and total_score > 0:
            total_score = min(total_score * 0.1, 0.5)

        # Find primary category (highest weighted score)
        primary_category = None
        max_score = 0.0
        for cat_name, cs in cat_scores.items():
            if cs.weighted_score > max_score:
                max_score = cs.weighted_score
                primary_category = cat_name

        # Risk level classification
        if is_awareness:
            risk_level = "Clean" if total_score < 0.5 else "Low"
        elif total_score >= 5.0 or (primary_category in ("arms", "net_banking_kit", "bank_account") and total_score >= 4.0):
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
            is_actionable=is_actionable,
            language=lang_tag.value,
            is_awareness=is_awareness,
            awareness_markers=awareness_res.markers,
            advisory_context_type=awareness_res.context_type,
            advisory_explanation=awareness_res.explanation
        )
