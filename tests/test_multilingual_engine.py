"""Unit tests for Multilingual Engine (English, Hindi Devanagari, and Hinglish Romanised).

Covers:
1. Script & Language Detection (EN, HI, HI_LATN, MIXED)
2. Unicode Normalization (Devanagari Nukta, Danda, ZWJ/ZWNJ, Repeated Characters)
3. Phonetic Hinglish Alias Folding
4. Multi-lingual Rule Scoring (slang_en, slang_hi, slang_hinglish)
5. Concept-Level Deduplication (katta, tamancha, कट्टा)
6. Single Multiplier Verification (Bug fix verification)
7. Public Awareness Advisory Suppression (Hard Negatives in EN, HI, Hinglish)
8. HybridClassifier Multilingual Metadata & Classification
"""
import pytest
from core.multilingual import (
    LanguageTag,
    detect_language_and_script,
    normalize_devanagari,
    normalize_hinglish_slang,
    check_awareness_context,
    normalize_multilingual,
)
from core.normalizer import normalize_text
from addons.scorer import RuleScorer
from models.classifier import HybridClassifier


# ---------------------------------------------------------------------------
# 1. Script & Language Detection Tests
# ---------------------------------------------------------------------------

def test_detect_language_english():
    text = "Pure mdma and high quality weed available for immediate delivery."
    tag, scripts = detect_language_and_script(text)
    assert tag == LanguageTag.EN
    assert scripts.get("en", 0) > 0.8


def test_detect_language_hindi_devanagari():
    text = "देसी कट्टा और ३१५ बोर कारतूस तुरंत डिलीवरी के लिए उपलब्ध है।"
    tag, scripts = detect_language_and_script(text)
    assert tag == LanguageTag.HI
    assert scripts.get("hi", 0) > 0.8


def test_detect_language_hinglish():
    text = "bhai ye maal kaisa hai delivery kab milega contact karo jaldi"
    tag, scripts = detect_language_and_script(text)
    assert tag in (LanguageTag.HI_LATN, LanguageTag.MIXED)
    assert scripts.get("hi_latn", 0) > 0.3 or tag == LanguageTag.MIXED


def test_detect_language_code_switching_mixed():
    text = "Original MDMA पाउडर उपलब्ध है, contact on telegram for direct delivery"
    tag, scripts = detect_language_and_script(text)
    assert tag == LanguageTag.MIXED
    assert scripts.get("hi", 0) > 0.1
    assert scripts.get("en", 0) > 0.1


# ---------------------------------------------------------------------------
# 2. Unicode Normalization & Cleaning Tests
# ---------------------------------------------------------------------------

def test_devanagari_nukta_folding():
    # क़ -> क, फ़ -> फ, ज़ -> ज
    text_with_nukta = "क़ट्टा फ़र्ज़ी दस्तावेज़"
    normalized, applied = normalize_devanagari(text_with_nukta)
    assert "क" in normalized
    assert "फ" in normalized
    assert "ज" in normalized
    assert "nukta_folded" in applied


def test_devanagari_danda_replacement():
    text = "हथियार उपलब्ध हैं। संपर्क करें॥"
    normalized, applied = normalize_devanagari(text)
    assert "।" not in normalized
    assert "॥" not in normalized


def test_repeated_characters_folding():
    text = "kattaaaaa availableee brooo tamanchaaaa"
    norm, applied = normalize_hinglish_slang(text)
    assert "katta" in norm
    assert "tamancha" in norm


def test_phonetic_hinglish_aliases():
    text = "nakalee aadhar card and farjee dastavej ready"
    norm, applied = normalize_hinglish_slang(text)
    assert "nakli" in norm
    assert "farzi" in norm
    assert "dastavez" in norm


def test_normalize_multilingual_audit_record():
    raw = "देसी कट्टा और कारतूस चाहिए तो msg karo"
    res = normalize_multilingual(raw)
    assert res.raw_text == raw
    assert res.language in (LanguageTag.HI, LanguageTag.MIXED)
    assert res.detected_scripts.get("hi", 0) > 0.5
    assert isinstance(res.applied_normalizations, list)


# ---------------------------------------------------------------------------
# 3. RuleScorer Multi-Lingual & Deduplication Tests
# ---------------------------------------------------------------------------

def test_scorer_hindi_devanagari_arms():
    scorer = RuleScorer()
    text = "देसी कट्टा और 315 बोर गोली उपलब्ध है। तुरंत संपर्क करें।"
    res = scorer.score(text)
    assert res.primary_category == "arms"
    assert res.risk_level in ("High", "Medium")
    assert res.is_actionable is True
    matched_terms = [t["term"] for t in res.matched_terms]
    assert any(term in ("देसी कट्टा", "कट्टा", "गोली") for term in matched_terms)


def test_scorer_hindi_devanagari_drugs():
    scorer = RuleScorer()
    text = "एमडीएमए और चरस की ताजा खेप उपलब्ध है। होम डिलीवरी।"
    res = scorer.score(text)
    assert res.primary_category == "drugs"
    assert res.risk_level in ("High", "Medium")
    matched_sections = [t["section"] for t in res.matched_terms]
    assert "slang_hi" in matched_sections


def test_scorer_concept_deduplication():
    scorer = RuleScorer()
    # Post repeats country pistol synonyms in multiple forms: katta, tamancha, कट्टा, देसी कट्टा
    text = "Fresh stock of desi katta, tamancha and कट्टा available with full brass ammo."
    res = scorer.score(text)
    assert res.primary_category == "arms"
    
    # Check that multiple terms were extracted for explainability
    matched_arms = [t for t in res.matched_terms if t["category"] == "arms"]
    assert len(matched_arms) >= 2
    
    # Check that country_pistol concept weight was only added ONCE to raw score
    arms_score = res.category_scores["arms"]
    # If 3 country pistol terms matched, raw score should NOT be 3 * 3.0 = 9.0;
    # It counts country_pistol once (3.0) + ammunition once (3.0) = 6.0
    assert arms_score.raw_score <= 6.5


def test_single_multiplier_calculation():
    scorer = RuleScorer()
    text = "Fresh desi katta available"
    res = scorer.score(text)
    arms_score = res.category_scores["arms"]
    # Default weight is 3.0, arms multiplier is 1.2
    # Single multiplication: 3.0 * 1.2 = 3.6
    # If double multiplication existed, it would be 3.0 * 1.2 * 1.2 = 4.32
    assert arms_score.raw_score == 3.0
    assert round(arms_score.weighted_score, 2) == 3.60


# ---------------------------------------------------------------------------
# 4. Public Awareness Advisory Suppression Tests (Hard Negatives)
# ---------------------------------------------------------------------------

def test_awareness_suppression_english():
    text = "SECURITY WARNING: Never share your OTP, netbanking password or ATM PIN with anyone. Police cyber helpline 1930."
    is_aware, markers = check_awareness_context(text)
    assert is_aware is True
    scorer = RuleScorer()
    res = scorer.score(text)
    assert res.risk_level in ("Clean", "Low")
    assert res.is_actionable is False


def test_awareness_suppression_hindi():
    text = "सावधान रहें: साइबर अपराध से बचें। कभी किसी को अपना ओटीपी या बैंक खाता शेयर न करें। साइबर हेल्पलाइन 1930 पर संपर्क करें।"
    is_aware, markers = check_awareness_context(text)
    assert is_aware is True
    scorer = RuleScorer()
    res = scorer.score(text)
    assert res.risk_level in ("Clean", "Low")
    assert res.is_actionable is False


def test_awareness_suppression_hinglish():
    text = "Savdhan rahe: apna OTP kisi ko share mat karo. Ye farzi sandesh hai. Police cybercrime helpline 1930."
    is_aware, markers = check_awareness_context(text)
    assert is_aware is True
    scorer = RuleScorer()
    res = scorer.score(text)
    assert res.risk_level in ("Clean", "Low")
    assert res.is_actionable is False


# ---------------------------------------------------------------------------
# 5. HybridClassifier Multilingual Metadata Tests
# ---------------------------------------------------------------------------

def test_classifier_multilingual_metadata_and_classification():
    clf = HybridClassifier(auto_load=True)
    
    # 1. Hindi post
    hi_post = "देसी कट्टा और कारतूस डिलीवरी के लिए उपलब्ध है। संपर्क करें।"
    res_hi = clf.classify(hi_post)
    assert res_hi.language in ("HI", "MIXED")
    assert res_hi.detected_scripts.get("hi", 0) > 0.5
    assert res_hi.category == "arms"
    assert res_hi.risk_level in ("High", "Medium")
    
    # 2. Hinglish post
    hinglish_post = "Current account for rent chahiye high commission daily payout khata ready."
    res_hgl = clf.classify(hinglish_post)
    assert res_hgl.language in ("HI_LATN", "MIXED")
    assert res_hgl.category in ("bank_account", "net_banking_kit")
    assert res_hgl.is_actionable is True
    
    # 3. Hindi public advisory suppression
    hi_notice = "जनहित में जारी: पुलिस ने फर्जी सिम और अवैध हथियार गिरोह को गिरफ्तार किया। ऐसे विज्ञापनों से सतर्क रहें।"
    res_notice = clf.classify(hi_notice)
    assert res_notice.risk_level in ("Clean", "Low")
    assert res_notice.is_actionable is False
