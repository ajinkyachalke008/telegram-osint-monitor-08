"""Unit tests for Workstream C: Hybrid Classifier, Evaluator, and Slang Suggester."""
import pytest
from pathlib import Path
from models.classifier import HybridClassifier, TRAIN_DATA_PATH
from addons.slang_suggester import SlangSuggester


@pytest.fixture(scope="module")
def trained_classifier():
    # Initialize and train
    clf = HybridClassifier(auto_load=True)
    if not clf.model_path.exists():
        clf.train_on_synthetic(TRAIN_DATA_PATH)
    return clf


def test_synthetic_data_exists():
    assert TRAIN_DATA_PATH.exists(), "Synthetic dataset file should exist"
    with open(TRAIN_DATA_PATH, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) >= 1000, f"Expected at least 1000 records, got {len(lines)}"


def test_blatant_illegal_drug_ad_classified_high(trained_classifier):
    text = "Fresh stock of pure mdma and charas available in Mumbai. Door delivery guaranteed. Ping @demo_seller."
    res = trained_classifier.classify(text, identifiers={"phones": ["9000012345"]})
    assert res.category == "drugs"
    assert res.risk_level == "High"
    assert res.is_actionable is True
    assert "matched" in res.why_flagged.lower() or "risk" in res.why_flagged.lower()


def test_mule_account_ad_classified_high(trained_classifier):
    text = "Selling fresh current account in HDFC with active netbanking kit and ATM card. High limit load. Contact @fin_deals."
    res = trained_classifier.classify(text, identifiers={"upis": ["demo.seller@ybl"]})
    assert res.category in ("bank_account", "atm_card", "net_banking_kit")
    assert res.risk_level == "High"
    assert res.confidence >= 0.60


def test_hard_negative_bank_notice_classified_clean(trained_classifier):
    text = "SECURITY ALERT: HDFC Bank never asks for your OTP, Netbanking password, UPI PIN or CVV. Beware of fraudsters offering fake loans."
    res = trained_classifier.classify(text)
    assert res.risk_level in ("Clean", "Low")
    assert res.is_actionable is False
    assert "advisory" in res.why_flagged.lower() or "clean" in res.why_flagged.lower()


def test_hard_negative_pharmacy_classified_clean(trained_classifier):
    text = "Apollo Pharmacy Health Tip: Paracetamol and cough syrup should only be taken as per doctor prescription. Licensed counter in Pune."
    res = trained_classifier.classify(text)
    assert res.risk_level in ("Clean", "Low")
    assert res.is_actionable is False


def test_hard_negative_shooting_sports(trained_classifier):
    text = "State Rifle Shooting Championship announced for 10m air rifle and air pistol in Jaipur. Registration open for junior athletes."
    res = trained_classifier.classify(text)
    assert res.risk_level in ("Clean", "Low")
    assert res.is_actionable is False


def test_slang_suggester_candidate_extraction():
    suggester = SlangSuggester()
    sample_posts = [
        {"text": "Special cryptoflow token dispatch for mule account.", "category": "bank_account"},
        {"text": "Cryptoflow transactions smooth, no hold on bank account.", "category": "bank_account"},
        {"text": "Get your cryptoflow fast here with atm kit.", "category": "bank_account"},
    ]
    candidates = suggester.extract_candidates(sample_posts, min_count=2)
    terms = [c["term"] for c in candidates]
    assert "cryptoflow" in terms
