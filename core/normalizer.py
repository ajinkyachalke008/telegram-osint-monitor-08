"""Unicode and evasion normalization for OSINT message text.

Raw evidence is never overwritten. The analysis string is conservative around
contact identifiers, UPI handles, usernames and numeric phone/post IDs.
"""
import re
import unicodedata
from typing import Dict

HOMOGLYPH_MAP = {
    "а": "a", "А": "A", "с": "c", "С": "c", "е": "e", "Е": "E",
    "о": "o", "О": "O", "р": "p", "Р": "P", "х": "x", "Х": "X",
    "у": "y", "У": "Y", "і": "i", "І": "I", "ј": "j", "Ј": "J",
    "ѕ": "s", "Ѕ": "S", "Т": "T", "М": "M", "Н": "H", "В": "B",
    "α": "a", "β": "b", "γ": "g", "ε": "e", "ι": "i", "κ": "k",
    "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
}

LEET_MAP = {
    "$": "s", "@": "a", "!": "i", "0": "o", "1": "i", "3": "e",
    "4": "a", "5": "s", "7": "t", "8": "b",
}
DEVANAGARI_DIGIT_MAP = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}
NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}

# Compound emoji terms from the PS02 starter lexicon are mapped before the
# zero-width joiner is removed. Original glyphs remain available to the scorer.
EMOJI_TOKEN_MAP = {
    "🍀😮‍💨": " [EMOJI_DRUG_CODE_CANNABIS] ",
    "👃😛❄️": " [EMOJI_DRUG_CODE_COCAINE] ",
    "💊🍬": " [EMOJI_DRUG_CODE_MDMA] ",
    "🔌": " [EMOJI_DRUG_CODE_SUPPLIER] ",
    "🚀": " [EMOJI_DRUG_CODE_POTENCY] ",
    "🍁": " [EMOJI_DRUG] ", "🌿": " [EMOJI_DRUG] ", "💊": " [EMOJI_DRUG] ",
    "❄️": " [EMOJI_DRUG] ", "💉": " [EMOJI_DRUG] ", "🍄": " [EMOJI_DRUG] ",
    "💨": " [EMOJI_DRUG] ", "🧪": " [EMOJI_DRUG] ",
    "🔫": " [EMOJI_ARM] ", "🗡️": " [EMOJI_ARM] ", "⚔️": " [EMOJI_ARM] ",
    "💣": " [EMOJI_ARM] ", "💥": " [EMOJI_ARM] ",
    "🪪": " [EMOJI_DOC] ", "📄": " [EMOJI_DOC] ", "📑": " [EMOJI_DOC] ",
    "🏦": " [EMOJI_BANK] ", "🏛️": " [EMOJI_BANK] ", "💰": " [EMOJI_MONEY] ",
    "💸": " [EMOJI_MONEY] ", "💳": " [EMOJI_CARD] ", "🏧": " [EMOJI_CARD] ",
    "📲": " [EMOJI_SIM] ", "📶": " [EMOJI_SIM] ", "📳": " [EMOJI_SIM] ", "📞": " [EMOJI_SIM] ",
}

RE_ZERO_WIDTH = re.compile(r"[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E\u00AD]")
RE_SPACED_LETTERS = re.compile(r"(?<=\b[a-zA-Z])\s+(?=[a-zA-Z]\b)")
RE_DOTTED_ACRONYM = re.compile(r"(?i)(?<![A-Za-z0-9])(?:[A-Za-z][.\-_/]){1,4}[A-Za-z](?![A-Za-z0-9])")
RE_MENTION = re.compile(r"(?<![\w])@[A-Za-z][A-Za-z0-9_]{3,31}\b")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]{2,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_IDENTIFIER = re.compile(r"\b([A-Za-z0-9._-]{2,64})@([A-Za-z0-9._-]{2,32})\b")


def fold_homoglyphs(text: str) -> str:
    return "".join(HOMOGLYPH_MAP.get(ch, ch) for ch in text)


def fold_devanagari_digits(text: str) -> str:
    return "".join(DEVANAGARI_DIGIT_MAP.get(ch, ch) for ch in text)


def fold_number_words(text: str) -> str:
    def replace_word(match):
        return NUMBER_WORDS.get(match.group(0).lower(), match.group(0))
    pattern = r"\b(" + "|".join(NUMBER_WORDS.keys()) + r")\b"
    return re.sub(pattern, replace_word, text, flags=re.IGNORECASE)


def _protected_identifier_spans(text: str):
    """Protect mentions, email addresses and known/strongly shaped UPI tokens."""
    spans = [match.span() for pattern in (RE_MENTION, RE_EMAIL) for match in pattern.finditer(text)]
    try:
        from addons.extractors import UPI_HANDLES
        known_handles = {str(handle).lower() for handle in UPI_HANDLES}
    except Exception:
        known_handles = set()
    for match in RE_IDENTIFIER.finditer(text):
        local, handle = match.group(1), match.group(2).lower()
        if handle in known_handles or (len(local) >= 3 and len(handle) >= 5):
            spans.append(match.span())
    return sorted(spans)


def apply_leetspeak_folding(text: str) -> str:
    """Fold obfuscations without corrupting phones, UPI IDs or @handles."""
    if not text:
        return ""
    protected = _protected_identifier_spans(text)
    result = list(text)
    for index, char in enumerate(text):
        if char not in LEET_MAP or any(start <= index < end for start, end in protected):
            continue
        has_prev = index > 0 and text[index - 1].isalnum()
        has_next = index + 1 < len(text) and text[index + 1].isalnum()
        if not (has_prev and has_next):
            continue
        token_start, token_end = index, index + 1
        while token_start > 0 and (text[token_start - 1].isalnum() or text[token_start - 1] in "@$!"):
            token_start -= 1
        while token_end < len(text) and (text[token_end].isalnum() or text[token_end] in "@$!"):
            token_end += 1
        token = text[token_start:token_end]
        if any(letter.isalpha() for letter in token):
            result[index] = LEET_MAP[char]
    return "".join(result)


def collapse_dotted_acronyms(text: str) -> str:
    known = {"atm", "upi", "sim", "otp", "ib", "pan", "dl", "rc", "md"}
    def replace(match):
        letters = "".join(re.findall(r"[A-Za-z]", match.group(0)))
        return letters if letters.lower() in known else match.group(0)
    return RE_DOTTED_ACRONYM.sub(replace, text)


def collapse_spaced_letters(text: str) -> str:
    previous = None
    current = text
    while previous != current:
        previous = current
        current = RE_SPACED_LETTERS.sub("", current)
    return current


def map_threat_emojis(text: str) -> str:
    # Replace recognized multi-emoji codes with a single semantic marker so a
    # component glyph is not accidentally scored again as a second signal.
    compound_keys = {"🍀😮‍💨", "👃😛❄️", "💊🍬"}
    for glyph in sorted(compound_keys, key=len, reverse=True):
        if glyph in text:
            text = text.replace(glyph, EMOJI_TOKEN_MAP[glyph].strip())
    for glyph, token in sorted(EMOJI_TOKEN_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if glyph not in compound_keys and glyph in text:
            text = text.replace(glyph, f"{glyph}{token}")
    return text


def normalize_text(raw_text: str) -> str:
    """Return analysis text separately; retain the original message unchanged."""
    if not raw_text:
        return ""
    norm = unicodedata.normalize("NFKC", str(raw_text))
    norm = map_threat_emojis(norm)
    norm = RE_ZERO_WIDTH.sub("", norm)
    norm = fold_homoglyphs(norm)
    norm = fold_devanagari_digits(norm)
    norm = apply_leetspeak_folding(norm)
    norm = collapse_dotted_acronyms(norm)
    norm = fold_number_words(norm)
    norm = collapse_spaced_letters(norm)
    return re.sub(r"[ \t]+", " ", norm).strip()
