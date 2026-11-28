"""Advanced Text Normalization Engine for OSINT Detection.

Features:
- Unicode NFKC normalization
- Removal of zero-width, non-printing, and bidirectional control characters
- Homoglyph folding (e.g., Cyrillic lookalikes to Latin)
- Leetspeak character mapping ($ -> s, 0 -> o, 3 -> e, @ -> a)
- Spaced-out character sequence collapse ('a t m' -> 'atm', 'k h a t a' -> 'khata')
- Devanagari/Marathi numerals ('०-९') and English number words ('nine eight seven...') to ASCII digits
- Semantic token mapping for threat emojis
- Preserves raw input string intact for court-admissible evidence snapshots
"""
import re
import unicodedata
from typing import Dict, Tuple

# Cyrillic and Greek homoglyphs commonly used to evade keyword filters
HOMOGLYPH_MAP = {
    # Cyrillic to Latin
    "а": "a", "А": "A", "с": "c", "С": "C", "е": "e", "Е": "E",
    "о": "o", "О": "O", "р": "p", "Р": "P", "х": "x", "Х": "X",
    "у": "y", "У": "Y", "і": "i", "І": "I", "ј": "j", "Ј": "J",
    "ѕ": "s", "Ѕ": "S", "Т": "T", "М": "M", "Н": "H", "В": "B",
    # Greek to Latin
    "α": "a", "β": "b", "γ": "g", "ε": "e", "ι": "i", "κ": "k",
    "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
}

# Leetspeak translation table
LEET_MAP = {
    "$": "s",
    "@": "a",
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
}

# Devanagari / Marathi numerals to ASCII digits
DEVANAGARI_DIGIT_MAP = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}

# English number words to digit characters
NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}

# Threat emojis to semantic tokens
EMOJI_TOKEN_MAP = {
    # Drugs
    "🍁": " [EMOJI_DRUG] ", "🌿": " [EMOJI_DRUG] ", "💊": " [EMOJI_DRUG] ",
    "❄️": " [EMOJI_DRUG] ", "💉": " [EMOJI_DRUG] ", "🍄": " [EMOJI_DRUG] ",
    "💨": " [EMOJI_DRUG] ", "🧪": " [EMOJI_DRUG] ",
    # Arms
    "🔫": " [EMOJI_ARM] ", "🗡️": " [EMOJI_ARM] ", "⚔️": " [EMOJI_ARM] ",
    "💣": " [EMOJI_ARM] ", "💥": " [EMOJI_ARM] ",
    # Documents
    "🪪": " [EMOJI_DOC] ", "📄": " [EMOJI_DOC] ", "📑": " [EMOJI_DOC] ",
    # Financial / Mule
    "🏦": " [EMOJI_BANK] ", "🏛️": " [EMOJI_BANK] ", "💰": " [EMOJI_MONEY] ",
    "💸": " [EMOJI_MONEY] ", "💳": " [EMOJI_CARD] ", "🏧": " [EMOJI_CARD] ",
    # SIM / Phone
    "📲": " [EMOJI_SIM] ", "📶": " [EMOJI_SIM] ", "📳": " [EMOJI_SIM] ", "📞": " [EMOJI_SIM] ",
}

# Zero-width, non-printing, and bidirectional override characters
RE_ZERO_WIDTH = re.compile(r"[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E\u00AD]")

# Single-spaced letters: e.g. "a t m", "k h a t a", "d r u g"
RE_SPACED_LETTERS = re.compile(r"(?<=\b[a-zA-Z])\s+(?=[a-zA-Z]\b)")


def fold_homoglyphs(text: str) -> str:
    """Fold visually identical Cyrillic/Greek homoglyphs to Latin."""
    return "".join(HOMOGLYPH_MAP.get(ch, ch) for ch in text)


def fold_devanagari_digits(text: str) -> str:
    """Translate Devanagari numerals to ASCII digits."""
    return "".join(DEVANAGARI_DIGIT_MAP.get(ch, ch) for ch in text)


def fold_number_words(text: str) -> str:
    """Convert spelled-out number words (e.g. 'nine eight seven...') to numeric digits."""
    def replace_word(m):
        w = m.group(0).lower()
        return NUMBER_WORDS.get(w, m.group(0))

    pattern = r"\b(" + "|".join(NUMBER_WORDS.keys()) + r")\b"
    return re.sub(pattern, replace_word, text, flags=re.IGNORECASE)


def collapse_spaced_letters(text: str) -> str:
    """
    Collapse spaced-out character evasions (e.g. 'a t m' -> 'atm', 'k h a t a' -> 'khata').
    Iterates to handle sequences longer than 2 characters.
    """
    prev = None
    curr = text
    while prev != curr:
        prev = curr
        curr = RE_SPACED_LETTERS.sub("", curr)
    return curr


def apply_leetspeak_folding(text: str) -> str:
    """Convert common leetspeak character substitutions to alphabet equivalents."""
    # Only substitute when within words or next to alphabetic characters
    result = []
    for i, ch in enumerate(text):
        if ch in LEET_MAP:
            # Check context
            has_prev = i > 0 and text[i-1].isalnum()
            has_next = i + 1 < len(text) and text[i+1].isalnum()
            if has_prev or has_next:
                result.append(LEET_MAP[ch])
            else:
                result.append(ch)
        else:
            result.append(ch)
    return "".join(result)


def map_threat_emojis(text: str) -> str:
    """Replace threat-indicative emojis with semantic bracketed tokens."""
    for emoji_char, token in EMOJI_TOKEN_MAP.items():
        if emoji_char in text:
            text = text.replace(emoji_char, token)
    return text


def normalize_text(raw_text: str) -> str:
    """
    Full normalization pipeline for detection:
    1. Unicode NFKC normalization
    2. Strip zero-width and control characters
    3. Fold homoglyphs
    4. Fold Devanagari numerals
    5. Convert spelled-out number words
    6. Collapse spaced-out letters
    7. Map threat emojis to tokens
    8. Normalize multiple whitespace
    """
    if not raw_text:
        return ""

    # 1. Unicode NFKC
    norm = unicodedata.normalize("NFKC", str(raw_text))

    # 2. Remove zero-width characters
    norm = RE_ZERO_WIDTH.sub("", norm)

    # 2b. Devanagari Unicode Normalization (Nukta & Danda)
    from core.multilingual import normalize_devanagari, normalize_hinglish_slang
    if re.search(r"[\u0900-\u097F]", norm):
        norm, _ = normalize_devanagari(norm)

    # 3. Homoglyph folding
    norm = fold_homoglyphs(norm)

    # 4. Devanagari numerals
    norm = fold_devanagari_digits(norm)

    # 5. Number words
    norm = fold_number_words(norm)

    # 6. Spaced letters
    norm = collapse_spaced_letters(norm)

    # 6b. Hinglish slang phonetic and repeated-letter normalization
    if re.search(r"[a-zA-Z]", norm):
        norm, _ = normalize_hinglish_slang(norm)

    # 7. Map emojis
    norm = map_threat_emojis(norm)

    # 8. Clean multiple whitespace
    norm = re.sub(r"[ \t]+", " ", norm).strip()

    return norm


# Re-export multilingual definitions for clean imports across the application
from core.multilingual import (
    LanguageTag,
    NormalizationResult,
    detect_language_and_script,
    normalize_multilingual,
    check_awareness_context,
)
