"""Unit and integration tests for PS02 Multi-Lingual Search Terms Catalog (10 Categories).

Validates:
- 10 distinct categories in the official catalogue
- English, Hindi/Hinglish, and Marathi dialect coverage
- Contextual weapons searches (gun, firearm, weapon, pistol, revolver, rifle, shotgun,
  desi katta, katta, tamancha, bandook, banduk, hathiyar, asla, desi pistol, gavti katta)
- Exact phrase vs broad search semantics
- False-positive suppression (machine learning, toy gun, water pistol)
- Attachment preview byte retrieval from actual archive and traversal safety
- Comprehensive PII redaction (phones, emails, UPI, bank accounts, usernames)
- Telegram channel/chat and social platform filtering
- Exact statutory disclaimer string matching Section 63 BSA audit requirements
- Genuine search against actual committee dataset archive
"""

import json
from pathlib import Path
import pytest

from ps02_dataset.catalog import SearchTermsCatalog, SearchMatch, CATALOG_JSON_PATH, OFFICIAL_DISCLAIMER


@pytest.fixture
def catalog():
    return SearchTermsCatalog()


def test_catalog_loads_10_categories(catalog):
    """Ensure catalog has exactly 10 distinct threat categories."""
    categories = catalog.get_categories()
    assert len(categories) == 10
    cat_ids = set(catalog.get_category_ids())
    expected_ids = {
        "general_fraud_forgery",
        "phishing_impersonation",
        "otp_kyc_credentials",
        "upi_payment_card",
        "identity_document",
        "loan_job_advance_fee",
        "investment_lottery",
        "marketplace_delivery",
        "extortion_malware",
        "weapons_firearm_context",
    }
    assert cat_ids == expected_ids


def test_weapons_firearms_category_terms(catalog):
    """Verify presence of required ordinary contextual firearm terms and Marathi variants."""
    cat = catalog.get_category("weapons_firearm_context")
    assert cat is not None

    all_terms = [t.lower() for t in catalog.get_all_terms_for_category("weapons_firearm_context")]

    # Ordinary English vocabulary
    for expected in ["gun", "firearm", "weapon", "pistol", "revolver", "rifle", "shotgun"]:
        assert expected in all_terms, f"Missing English contextual term: {expected}"

    # Hindi / Hinglish aliases
    for expected in ["desi katta", "katta", "tamancha", "bandook", "banduk", "hathiyar", "asla", "desi pistol"]:
        assert expected in all_terms, f"Missing Hinglish term: {expected}"

    # Marathi variants
    for expected in ["gavti katta", "banduk", "chaku", "talwar"]:
        assert expected in all_terms, f"Missing Marathi term: {expected}"


def test_case_insensitive_matching(catalog):
    """Matches should be case-insensitive across uppercase, lowercase, and title case."""
    sample_text = "Urgent: DESI KATTA and 9MM PISTOL report near Jaipur highway. Tamancha piece."
    matches = catalog.search_text(sample_text, category_filter="weapons_firearm_context")
    matched_terms = [m[1].lower() for m in matches]

    assert "desi katta" in matched_terms
    assert "pistol" in matched_terms
    assert "tamancha" in matched_terms


def test_exact_phrase_vs_broad_search(catalog):
    """Verify distinction between exact phrase matches and broad token matches."""
    # 1. Exact phrase present
    text_with_phrase = "Special report: country made pistol recovered in Jaipur."
    phrase_matches = catalog.search_text(text_with_phrase, category_filter="weapons_firearm_context", exact_phrase_only=True)
    phrase_terms = [m[1].lower() for m in phrase_matches]
    assert "country made pistol" in phrase_terms
    assert all(m[2] == "exact_phrase" for m in phrase_matches)

    # 2. Words separated (not exact contiguous phrase)
    text_words_separated = "He visited a country far away and made a model pistol."
    separated_matches = catalog.search_text(text_words_separated, category_filter="weapons_firearm_context", exact_phrase_only=True)
    separated_terms = [m[1].lower() for m in separated_matches]
    assert "country made pistol" not in separated_terms

    # But broad search will match single token 'pistol'
    broad_matches = catalog.search_text(text_words_separated, category_filter="weapons_firearm_context", exact_phrase_only=False)
    broad_terms = [m[1].lower() for m in broad_matches]
    assert "pistol" in broad_terms


def test_marathi_variants_matching(catalog):
    """Test Marathi arms variants: gavti katta, banduk, chaku, talwar."""
    text_marathi = "Mumbai Pune report: gavti katta ani talwar with extra banduk."
    matches = catalog.search_text(text_marathi, category_filter="weapons_firearm_context")
    matched_terms = [m[1].lower() for m in matches]

    assert "gavti katta" in matched_terms
    assert "talwar" in matched_terms
    assert "banduk" in matched_terms


def test_false_positive_suppression(catalog):
    """Verify benign terms like 'toy gun' or 'water pistol' are suppressed."""
    fp_text_1 = "Buying a toy gun for kids birthday party along with a water pistol."
    matches_1 = catalog.search_text(fp_text_1, category_filter="weapons_firearm_context")
    assert len(matches_1) == 0

    fp_text_2 = "Attending a machine learning and data science seminar."
    matches_2 = catalog.search_text(fp_text_2, category_filter="weapons_firearm_context")
    assert len(matches_2) == 0


def test_comprehensive_pii_sanitization(catalog):
    """Verify phone numbers, emails, UPI handles, bank accounts, and usernames are scrubbed."""
    text_with_pii = (
        "Contact officer @admin_cop via email support.desk@police.gov.in or call +91 9876543210. "
        "Do not send money to scammer.pay@okaxis or account 1234567890123 on t.me/fake_channel."
    )
    high, raw = catalog.redact_and_highlight(text_with_pii, "support")

    assert "+91 9876543210" not in high
    assert "9876543210" not in high
    assert "[REDACTED_PHONE]" in high

    assert "support.desk@police.gov.in" not in high
    assert "[REDACTED_EMAIL]" in high

    assert "scammer.pay@okaxis" not in high
    assert "[REDACTED_PAYMENT_ID]" in high

    assert "1234567890123" not in high
    assert "[REDACTED_ACCT]" in high

    assert "@admin_cop" not in high
    assert "[REDACTED_USER]" in high

    assert "t.me/fake_channel" not in high
    assert "[REDACTED_LINK]" in high


def test_disclaimer_content():
    """Verify statutory evidentiary disclaimer string matches the exact required wording."""
    expected = (
        "A keyword match is a search result, not proof of wrongdoing. "
        "Context, provenance, integrity and independent verification are necessary "
        "before any legal or operational reliance."
    )
    assert OFFICIAL_DISCLAIMER == expected


@pytest.mark.parametrize(
    "cat_id,synthetic_text,expected_term",
    [
        ("general_fraud_forgery", "Online cyber fraud and forged document reported.", "fraud"),
        ("phishing_impersonation", "Urgent: bank impersonation with fake bank call.", "impersonation"),
        ("otp_kyc_credentials", "Never disclose your secret banking otp or credentials.", "otp"),
        ("upi_payment_card", "QR code payment scam and UPI fraud incident.", "upi"),
        ("identity_document", "Duplicate certificate and fake aadhaar verification.", "certificate"),
        ("loan_job_advance_fee", "Instant loan approval with advance processing fee.", "loan"),
        ("investment_lottery", "High return lottery scheme and investment circulation.", "lottery"),
        ("marketplace_delivery", "Online courier scam and fake delivery message.", "delivery"),
        ("extortion_malware", "Critical malware alert and digital extortion threat.", "malware"),
        ("weapons_firearm_context", "Police incident report: unlicensed firearm and pistol recovered.", "firearm"),
        ("weapons_firearm_context", "Gavti katta ani banduk seized in Pune outskirts.", "gavti katta"),
    ],
)
def test_all_10_categories_synthetic_fixtures(catalog, cat_id, synthetic_text, expected_term):
    """Test every one of the 10 threat categories against synthetic test fixtures."""
    matches = catalog.search_text(synthetic_text, category_filter=cat_id)
    assert len(matches) > 0, f"Expected matches for category '{cat_id}' with text '{synthetic_text}', got none."
    matched_terms = [m[1].lower() for m in matches]
    assert any(expected_term.lower() in t for t in matched_terms), (
        f"Category '{cat_id}' failed to match expected term '{expected_term}' in text: '{synthetic_text}'. "
        f"Matched terms were: {matched_terms}"
    )


def test_attachment_bytes_retrieval_and_safety(catalog):
    """Verify in-memory byte extraction and directory traversal rejection."""
    candidate_zip = Path("data/participant_input/PS02_demo_data.zip")
    if not candidate_zip.exists():
        pytest.skip("Local PS02 committee dataset zip not found.")

    # 1. Traversal attempt rejected
    assert catalog.get_attachment_bytes(candidate_zip, "../../etc/passwd") is None
    assert catalog.get_attachment_bytes(candidate_zip, "/absolute/path/image.jpg") is None
    assert catalog.get_attachment_bytes(candidate_zip, "") is None

    # 2. Valid image byte extraction from archive
    valid_photo = "photo_50@11-10-2026_22-01-06.jpg"
    img_bytes = catalog.get_attachment_bytes(candidate_zip, valid_photo)
    assert img_bytes is not None
    assert len(img_bytes) > 0
    # First few bytes of JPEG are \xff\xd8\xff
    assert img_bytes[:2] == b"\xff\xd8"


def test_offline_committee_dataset_genuine_search(catalog):
    """Test genuine keyword search on actual committee archive with channel and platform filters."""
    candidate_zip = Path("data/participant_input/PS02_demo_data.zip")
    if not candidate_zip.exists():
        pytest.skip("Local PS02 committee dataset zip not found.")

    # Search Aadhaar in Telegram channels
    matches = catalog.search_committee_dataset(
        candidate_zip,
        query_text="aadhaar",
        platform_filter="Telegram",
        channel_filter="PVC Print Hub",
        limit=5
    )
    assert len(matches) > 0
    first = matches[0]
    assert first.source_type == "Telegram"
    assert "PVC Print Hub" in first.channel_or_platform
    assert "aadhaar" in first.matched_term.lower()
    assert first.disclaimer == OFFICIAL_DISCLAIMER
    assert "[REDACTED" in first.highlighted_context or not any(x in first.raw_snippet for x in ["@paytm", "+91"])
