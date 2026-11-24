"""Unit tests for Workstream D: Financial-Ad Detector (R3)."""
import pytest
from addons.financial_detector import FinancialAdDetector


@pytest.fixture
def detector():
    return FinancialAdDetector()


def test_mule_recruitment_pattern_detection(detector):
    text = "Sell your idle HDFC bank account or rent your khata and earn daily commission of 10,000 INR. DM @money_rent."
    res = detector.detect(text)
    assert res.is_financial_ad is True
    assert res.intent in ("recruit", "rent")
    assert "commission" in res.signals
    assert res.mule_recruitment_pattern is True
    assert res.risk_assessment == "High"
    assert len(res.evidence_spans) >= 2


def test_corporate_netbanking_kit_sale(detector):
    text = "Selling fresh corporate netbanking kit in ICICI with maker-checker tokens and ATM card. Clean KYC, daily limit 50L."
    res = detector.detect(text)
    assert res.is_financial_ad is True
    assert res.intent == "sell"
    assert "corporate_account" in res.instruments or "net_banking_kit" in res.instruments
    assert "atm_card" in res.instruments
    assert "kyc_less" in res.signals
    assert "high_limit" in res.signals
    assert res.risk_assessment == "High"


def test_atm_card_rent_intent(detector):
    text = "Multiple SBI ATM cards available for rent. High commission paid for daily usage. WhatsApp 9800012345."
    res = detector.detect(text)
    assert res.is_financial_ad is True
    assert res.intent == "rent"
    assert "atm_card" in res.instruments
    assert "commission" in res.signals
    assert res.risk_assessment == "High"


def test_pre_activated_sim_cards(detector):
    text = "Bulk pre-activated Airtel SIM cards available without documents. OTP verification ready."
    res = detector.detect(text)
    assert res.is_financial_ad is True
    assert "sim_card" in res.instruments
    assert "kyc_less" in res.signals


def test_exact_evidence_spans_captured(detector):
    text = "Need savings account for rent on 10% commission basis."
    res = detector.detect(text)
    assert len(res.evidence_spans) >= 3
    # Verify span substrings match text offsets exactly
    for span in res.evidence_spans:
        assert text[span.start:span.end] == span.text


def test_benign_security_advisory_suppressed(detector):
    text = "RBI Public Awareness Notice: Do not fall for mule account recruitment schemes on social media promising easy commission. Report to cybercrime helpline 1930."
    res = detector.detect(text)
    assert res.is_financial_ad is False
    assert res.mule_recruitment_pattern is False
    assert res.risk_assessment == "Clean"
