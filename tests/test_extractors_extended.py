"""Unit tests for Workstream E Extended Identifier Extractors."""
import pytest
from addons.extractors import (
    extract_indian_phones,
    extract_crypto_wallets,
    extract_locations,
    extract_prices,
    validate_base58_checksum,
)


def test_phone_spelled_words():
    text = "Call seller on nine eight seven six five four three two one zero for immediate dispatch."
    phones = extract_indian_phones(text)
    assert "+919876543210" in phones


def test_phone_spaced_and_dotted():
    text = "WhatsApp at 9.8.7.6.5.4.3.2.1.0 or 9 8 7 6 5 4 3 2 1 0"
    phones = extract_indian_phones(text)
    assert "+919876543210" in phones


def test_tron_wallet_checksum():
    # Valid real TRON mainnet address (Base58Check verified)
    valid_tron = "TYDzsYUEHG1AwueRyNng69nsT5Dn3URPUS"
    assert validate_base58_checksum(valid_tron) is True

    # Tampered TRON address (corrupted checksum)
    invalid_tron = "TYDzsYUEHG1AwueRyNng69nsT5Dn757guU"
    assert validate_base58_checksum(invalid_tron) is False

    text = f"Send payment to TRC20 {valid_tron} only."
    cryptos = extract_crypto_wallets(text)
    assert len(cryptos) >= 1
    addr, net, is_valid = cryptos[0]
    assert addr == valid_tron
    assert is_valid is True


def test_locations_with_lat_lon_and_pincodes():
    text = "Mule kit delivery ready in Jaipur and Mewat near PIN 302001."
    locs = extract_locations(text)
    names = [l["name"] for l in locs]
    assert "Jaipur" in names
    assert "Mewat" in names
    assert "PIN 302001" in names

    jaipur_loc = next(l for l in locs if l["name"] == "Jaipur")
    assert jaipur_loc["lat"] is not None
    assert jaipur_loc["lon"] is not None
    assert jaipur_loc["state"] == "Rajasthan"


def test_price_extractions():
    text = "Current account khata for rent ₹50,000 per month or 500 usdt per day."
    prices = extract_prices(text)
    assert any("50,000" in p or "50000" in p for p in prices)
    assert any("500" in p for p in prices)
