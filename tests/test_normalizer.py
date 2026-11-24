"""Unit tests for Workstream B Text Normalization Engine."""
import pytest
from core.normalizer import (
    normalize_text,
    fold_homoglyphs,
    fold_devanagari_digits,
    fold_number_words,
    collapse_spaced_letters,
    map_threat_emojis,
)


def test_zero_width_and_control_removal():
    # Insert zero-width space (\u200b) and soft hyphen (\u00ad)
    evasion = "c\u200bo\u200bk\u200be\u00addeal"
    cleaned = normalize_text(evasion)
    assert cleaned == "cokedeal"


def test_homoglyph_folding():
    # Cyrillic 'а' (U+0430) and 'с' (U+0441) looks like Latin 'a' and 'c'
    cyrillic_evasion = "k\u0430tt\u0430"  # k + Cyrillic а + tt + Cyrillic а
    folded = fold_homoglyphs(cyrillic_evasion)
    assert folded == "katta"


def test_spaced_out_letters_collapse():
    text1 = "Need a t m card urgently"
    assert collapse_spaced_letters(text1) == "Need atm card urgently"

    text2 = "Fresh k h a t a available"
    assert collapse_spaced_letters(text2) == "Fresh khata available"

    text3 = "c o k e delivery"
    assert collapse_spaced_letters(text3) == "coke delivery"


def test_devanagari_digits_folding():
    hindi_num = "९८७६५४३२१०"
    assert fold_devanagari_digits(hindi_num) == "9876543210"


def test_number_words_conversion():
    text = "call me on nine eight seven six five four three two one zero"
    converted = fold_number_words(text)
    assert "9 8 7 6 5 4 3 2 1 0" in converted


def test_emoji_mapping():
    text = "High quality 🍁 and fresh 🔫 available"
    mapped = map_threat_emojis(text)
    assert "[EMOJI_DRUG]" in mapped
    assert "[EMOJI_ARM]" in mapped


def test_full_evasion_normalization():
    # Multi-vector evasion combining zero-width, homoglyph, spaced letters, and emoji
    tricky = "Fresh   k\u200bh\u200ba\u200bt\u200ba   deal 🏦 call nine eight seven six five four three two one zero"
    normalized = normalize_text(tricky)
    assert "khata" in normalized
    assert "[EMOJI_BANK]" in normalized
    assert "9 8 7 6 5 4 3 2 1 0" in normalized
