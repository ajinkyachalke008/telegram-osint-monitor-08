"""Unit tests for Phase 1 Detection Add-ons:
- UPI ID extraction & email rejection
- Phone numbers (Devanagari digits, +91, 10-digit)
- IFSC codes
- Crypto wallets
- Rule Scorer & multi-lingual slang categories
- Evidence canonical hashing & tamper detection
- External CSV / JSON Importer
"""
import json
import tempfile
from pathlib import Path
import pytest

from addons.extractors import (
    extract_upis,
    extract_indian_phones,
    extract_ifsc_codes,
    extract_crypto_wallets,
    extract_usernames,
    extract_tme_links,
    extract_locations,
    extract_all_entities,
    normalize_devanagari_digits,
)
from addons.scorer import RuleScorer
from addons.evidence import (
    canonical_json,
    compute_sha256,
    build_evidence_record,
    verify_evidence_record,
)
from addons.importer import DataImporter


# ---------------------------------------------------------------------------
# Extractor Tests
# ---------------------------------------------------------------------------

def test_upi_extraction_valid_handles():
    text = "Send advance payment to demo.seller@ybl or support@okaxis or payout@paytm for fast dispatch."
    upis = extract_upis(text)
    assert "demo.seller@ybl" in upis
    assert "support@okaxis" in upis
    assert "payout@paytm" in upis


def test_upi_extraction_rejects_emails():
    text = "Contact me at seller.help@gmail.com or admin@yahoo.com or john@outlook.com or info@proton.me"
    upis = extract_upis(text)
    # None of these common email providers should match as a UPI handle!
    assert len(upis) == 0


def test_phone_extraction_standard_formats():
    text = "Call us on +91 98765 43210 or 98765-43210 or 919876543210 for deals."
    phones = extract_indian_phones(text)
    assert "+919876543210" in phones


def test_phone_extraction_devanagari_numerals():
    # Devanagari numerals: ९८७६५४३२१० = 9876543210
    text = "व्हाट्सअँप करा: ९८७६५४३२१०"
    assert normalize_devanagari_digits("९८७६५४३२१०") == "9876543210"
    phones = extract_indian_phones(text)
    assert "+919876543210" in phones


def test_ifsc_extraction():
    text = "Transfer to Kotak Bank IFSC: KKBK0000123 or SBI IFSC: SBIN0001234"
    ifscs = extract_ifsc_codes(text)
    assert "KKBK0000123" in ifscs
    assert "SBIN0001234" in ifscs


def test_crypto_extraction():
    text = "Send USDT to TRC20: TYDzsYUEHG1AwueRyNng69nsT5Dn757guU or ETH: 0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    cryptos = extract_crypto_wallets(text)
    addrs = [c[0] for c in cryptos]
    assert "TYDzsYUEHG1AwueRyNng69nsT5Dn757guU" in addrs
    assert "0x71C7656EC7ab88b098defB751B7401B5f6d8976F" in addrs


def test_username_and_tme_links():
    text = "DM @dark_seller or join https://t.me/fake_cards_channel immediately!"
    entities = extract_all_entities(text)
    assert "@dark_seller" in entities["usernames"]
    assert any("fake_cards_channel" in link for link in entities["tme_links"])


def test_location_extraction():
    text = "Delivery available across Mumbai, Jaipur, and Mewat within 24 hours."
    locs = extract_locations(text)
    assert "Mumbai" in locs
    assert "Jaipur" in locs
    assert "Mewat" in locs


# ---------------------------------------------------------------------------
# Scorer Tests
# ---------------------------------------------------------------------------

def test_scorer_drugs_category():
    scorer = RuleScorer()
    text = "Pure mdma and high quality maal available. Home delivery available. Contact @vendor."
    res = scorer.score(text)
    assert res.primary_category == "drugs"
    assert res.risk_level in ("High", "Medium")
    assert res.is_actionable is True
    # Verify explainability
    terms = [t["term"] for t in res.matched_terms]
    assert "mdma" in terms or "maal" in terms


def test_scorer_bank_account_mule():
    scorer = RuleScorer()
    text = "Current account for rent chahiye commission base par. Daily limit 50L. DM with fastag khata."
    res = scorer.score(text)
    assert res.primary_category == "bank_account"
    assert res.risk_level == "High"
    assert res.is_actionable is True


def test_scorer_arms_category():
    scorer = RuleScorer()
    text = "Desi katta and 315 bore piece available with fresh ammo. Contact @gun_supplier."
    res = scorer.score(text)
    assert res.primary_category == "arms"
    assert res.risk_level == "High"


def test_scorer_clean_message():
    scorer = RuleScorer()
    text = "Good morning everyone. The weather in Jaipur is very pleasant today."
    res = scorer.score(text)
    assert res.risk_level == "Clean"
    assert res.total_score == 0.0
    assert res.is_actionable is False


# ---------------------------------------------------------------------------
# Evidence & Chain of Custody Tests
# ---------------------------------------------------------------------------

def test_canonical_json_determinism():
    dict1 = {"channel": "TestChannel", "message_id": 101, "timestamp_utc": "2026-11-24T12:00:00Z", "text": "Hello"}
    dict2 = {"text": "Hello", "timestamp_utc": "2026-11-24T12:00:00Z", "channel": "TestChannel", "message_id": 101}
    # Regardless of insertion order, canonical string and hash MUST be identical
    canon1 = canonical_json(dict1)
    canon2 = canonical_json(dict2)
    assert canon1 == canon2
    assert compute_sha256(canon1) == compute_sha256(canon2)


def test_evidence_tamper_verification():
    record = build_evidence_record(
        channel="DarkMuleChat",
        message_id=505,
        timestamp="2026-11-24T12:30:00Z",
        text="Bank account for rent demo.seller@ybl",
        category="bank_account",
        risk_level="High"
    )
    # Check valid
    valid, msg = verify_evidence_record(record)
    assert valid is True

    # Tamper with the text in the core record
    tampered_record = json.loads(json.dumps(record))
    tampered_record["core"]["text"] = "Legitimate store product"
    valid_tampered, msg_tampered = verify_evidence_record(tampered_record)
    assert valid_tampered is False
    assert "tampering detected" in msg_tampered.lower()


# ---------------------------------------------------------------------------
# Importer Tests
# ---------------------------------------------------------------------------

def test_importer_csv(tmp_path):
    csv_file = tmp_path / "external_leak.csv"
    csv_content = """platform,channel,post_id,timestamp,text
WhatsApp,DarkGroup1,1001,2026-11-24T10:00:00Z,Khata sale with full net banking kit call +91 98765 43210 demo.seller@ybl
Forum,CardingHub,2002,2026-11-24T11:00:00Z,Normal discussion about python programming
"""
    csv_file.write_text(csv_content, encoding="utf-8")
    
    importer = DataImporter()
    records = importer.import_from_csv(csv_file)
    assert len(records) == 2
    
    # First record should be flagged as High risk
    rec1 = records[0]
    assert rec1["risk_level"] in ("High", "Medium")
    assert "+919876543210" in rec1["extracted"]["phones"]
    assert "demo.seller@ybl" in rec1["extracted"]["upis"]
    assert rec1["evidence"]["evidence_hash"] is not None

    # Second record should be Clean
    rec2 = records[1]
    assert rec2["risk_level"] == "Clean"


def test_importer_json(tmp_path):
    json_file = tmp_path / "feed.json"
    data = [
        {
            "service": "Telegram_Archive",
            "source": "UndergroundMarket",
            "msg_id": 9999,
            "created_at": "2026-11-24T12:00:00Z",
            "content": "Desi katta available for wholesale in Mewat @gunman"
        }
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")
    
    importer = DataImporter()
    records = importer.import_from_json(json_file)
    assert len(records) == 1
    assert records[0]["primary_category"] == "arms"
    assert "@gunman" in records[0]["extracted"]["usernames"]
