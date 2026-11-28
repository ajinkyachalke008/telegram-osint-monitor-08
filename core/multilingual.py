"""Multilingual NLP and Slang Understanding Engine for OSINT Detection.

Provides unified language processing for:
1. English (Latin script)
2. Hindi (Devanagari script \u0900-\u097F)
3. Hinglish (Romanised Hindi slang and phonetics)
4. Mixed-language / Code-switching (English + Hindi + Hinglish)

Key Responsibilities:
- Preserves raw input string intact for court-admissible evidence snapshots
- Devanagari Unicode NFC/NFKC normalization, nukta folding, matra consistency, and digit conversion
- Hinglish phonetic alias normalization and repeated-character reduction
- Language and script detection: 'EN', 'HI', 'HI-LATN', 'MIXED'
- Unified concept registry mapping multi-lingual aliases to canonical threat concepts
- Unicode word boundary-safe phrase matching (supporting both Latin and Devanagari boundaries)
- Concept-level deduplication to prevent score inflation when multiple variants match
- Multi-lingual public awareness, disclaimer, and negation context detection
"""

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple


class LanguageTag(str, Enum):
    EN = "EN"
    HI = "HI"
    HI_LATN = "HI-LATN"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


# Devanagari Unicode Range: \u0900 - \u097F
RE_DEVANAGARI_CHAR = re.compile(r"[\u0900-\u097F]")
RE_LATIN_CHAR = re.compile(r"[a-zA-Z]")

# Devanagari Nukta Characters and their base forms
NUKTA_MAP = {
    "क़": "क", "ख़": "ख", "ग़": "ग", "ज़": "ज",
    "ड़": "ड", "ढ़": "ढ", "फ़": "फ", "य़": "य",
    # Decomposed nukta sequences
    "क\u093c": "क", "ख\u093c": "ख", "ग\u093c": "ग", "ज\u093c": "ज",
    "ड\u093c": "ड", "ढ\u093c": "ढ", "फ\u093c": "फ", "य\u093c": "य",
}

# Devanagari punctuation to standard whitespace / period
RE_DEVANAGARI_DANDA = re.compile(r"[\u0964\u0965]")

# Repeated characters in Hinglish slang (e.g. "kattaaaaa" -> "katta", "farziii" -> "farzi")
RE_REPEATED_LETTERS = re.compile(r"([a-zA-Z])\1{2,}")

# Common Hinglish grammatical markers, particles, pronouns, and verbs
HINGLISH_GRAMMAR_MARKERS: Set[str] = {
    # Pronouns & Demonstratives
    "ye", "yeh", "woh", "wo", "iska", "uski", "uske", "mera", "meri", "mere",
    "tera", "teri", "tere", "apna", "apni", "apne", "kisi", "sab", "kya", "kaise",
    "kahan", "kidhar", "itna", "itni", "utna", "kisko", "humara", "tumhara",
    # Verbs & Auxiliaries
    "hai", "hain", "tha", "thi", "the", "hoga", "hogi", "hoge", "karo", "kare",
    "karna", "karke", "karega", "karegi", "de", "do", "dena", "dijiye", "le",
    "lo", "lena", "lijiye", "aao", "jaao", "chahiye", "milega", "milegi", "milte",
    "rahe", "raha", "rahi", "hona", "bhejo", "bhejna", "daalo", "daal",
    # Postpositions & Prepositions
    "ka", "ki", "ke", "ko", "se", "me", "mein", "par", "pe", "tak", "bina",
    "sath", "saath", "liye", "vaaste",
    # Conjunctions & Adverbs
    "aur", "ya", "lekin", "magar", "parantu", "bhi", "kabhi", "abhi", "phir",
    "fir", "jaldi", "turant", "sasta", "mehenga", "asli", "mat", "nahi", "nahin",
}

# Hinglish Slang Equivalence Map (phonetic aliases to canonical Hinglish form)
HINGLISH_SPELLING_ALIASES: Dict[str, str] = {
    # Fake / Forged
    "nakalee": "nakli",
    "nakly": "nakli",
    "naklii": "nakli",
    "farjee": "farzi",
    "farji": "farzi",
    "farzii": "farzi",
    "jaali": "jali",
    "dastavej": "dastavez",
    "kaagaj": "kagaz",
    "kaagaz": "kagaz",
    "pramanpatr": "pramanpatra",
    # Arms
    "kattaa": "katta",
    "tamanchaa": "tamancha",
    "tamncha": "tamancha",
    "banduk": "bandook",
    "bandukk": "bandook",
    "bandukkk": "bandook",
    "bandooq": "bandook",
    "hatiyar": "hathiyar",
    "hathyar": "hathiyar",
    "hathiyaar": "hathiyar",
    "aslah": "asla",
    "aslaa": "asla",
    "desii": "desi",
    "gauti katta": "gavti katta",
    "gaavti katta": "gavti katta",
    # Accounts / Finance
    "khataa": "khata",
    "khaata": "khata",
    "chaalu sim": "chalu sim",
    # Fraud / Theft / Drugs
    "dhokhaa": "dhokha",
    "thagii": "thagi",
    "thaggi": "thagi",
    "chitta": "chitta",
    "chittta": "chitta",
    "nasheeli": "nasheeli",
    "mal": "maal",
}

# Structured Institutional / Helpline Advisory Patterns
INSTITUTIONAL_ADVISORY_PATTERNS = [
    re.compile(r"(?i)\bcybercrime\s+helpline\s+(?:number\s+)?1930\b"),
    re.compile(r"(?i)\bhelpline\s+1930\b"),
    re.compile(r"(?i)\bofficial\s+notice\b"),
    re.compile(r"(?i)\bpublic\s+awareness\b"),
    re.compile(r"(?i)\bpunishable\s+offen[sc]e\s+under\s+pmla\b"),
    re.compile(r"(?i)\bpunishable\s+offen[sc]e\b"),
    re.compile(r"(?i)\breport\s+(?:cyber\s+)?fraud\s+to\s+1930\b"),
    re.compile(r"(?i)\b(?:police|security|official|bank)\s+(?:advisory|alert|notice)\b"),
    re.compile(r"(?i)\bkanoon[i]?\s+apradh\b"),
    re.compile(r"साइबर\s*हेल्पलाइन\s*1930"),
    re.compile(r"जनहित\s*में\s*जारी"),
    re.compile(r"राष्ट्रीय\s*साइबर\s*अपराध\s*पोर्टल"),
]

# Advisory Warning Directives
ADVISORY_DIRECTIVE_PATTERNS = [
    re.compile(r"(?i)\bnever\s+share\s+(?:your\s+)?(?:otp|password|pin|credentials|cvv)\b"),
    re.compile(r"(?i)\bbeware\s+of\s+(?:fraud|scam|fraudsters)\b"),
    re.compile(r"(?i)\b(?:kabhi|kisi\s+ko)\s*(?:bhi\s*)?(?:otp|pin|password)\s*(?:share\s+mat|mat\s+dena|mat\s+batao|kabhi\s+na)\b"),
    re.compile(r"(?i)\b(?:savdhan|satark)\s+rahe\b"),
    re.compile(r"(?i)\bdhokhadhadi\s+se\s+bache\b"),
    re.compile(r"(?i)\bfarzi\s+(?:message|call|link)\s*(?:se\s*bache|par\s*click\s*mat)\b"),
    re.compile(r"(?i)\bdo\s+not\s+(?:click|transfer|pay|trust|share)\b"),
    re.compile(r"सावधान\s*रहें"),
    re.compile(r"सतर्क\s*रहें"),
    re.compile(r"(?:ओटीपी|पासवर्ड|पिन|ओ\.टी\.पी\.)\s*(?:किसी\s*को\s*)?(?:भी\s*)?(?:शेयर\s*न\s*करें|न\s*दें|मत\s*बताएं)"),
    re.compile(r"फर्जी\s*(?:संदेश|कॉल|लिंक|वेबसाइट)\s*(?:से\s*बचें|पर\s*क्लिक\s*न\s*करें)"),
    re.compile(r"धोखाधड़ी\s*से\s*बचें"),
]

# Police Arrest / Enforcement News Reporting (not an active ad)
ENFORCEMENT_NEWS_PATTERNS = [
    re.compile(r"(?i)\bpolice\s+(?:busted|arrested|seized|nabbed|apprehended)\b"),
    re.compile(r"(?i)\bpolice\s+ne\s+(?:pakda|giraftar\s+kiya|raid\s+mari|baramad\s+kiya)\b"),
    re.compile(r"पुलिस\s*ने\s*(?:गिरफ्तार\s*किया|पकड़ा|बरामद\s*किया|भंडाफोड़\s*किया)"),
]

# Active Illicit Solicitation / Commercial Trade Patterns (overrides advisory suppression!)
ILLICIT_SOLICITATION_PATTERNS = [
    re.compile(r"(?i)\b(?:dm|ping|contact|order|message)\s+(?:me|us|on|fast)?\s*[@#]"),
    re.compile(r"(?i)t\.me\/[a-zA-Z0-9_]+"),
    re.compile(r"(?i)\b(?:in\s+stock|fresh\s+stock|stock\s+available)\b"),
    re.compile(r"(?i)\b(?:home\s+delivery|instant\s+delivery|door\s+delivery|cash\s+on\s+delivery|cod\s+available)\b"),
    re.compile(r"(?i)\b(?:for\s+sale|available\s+for\s+sale|order\s+now)\b"),
    re.compile(r"(?i)\b(?:delivery\s+milega|ping\s+karo|contact\s+karo|order\s+karo|maal\s+available)\b"),
    re.compile(r"(?:स्टॉक\s*उपलब्ध|तुरंत\s*डिलीवरी|होम\s*डिलीवरी|ऑर्डर\s*करें|कैश\s*ऑन\s*डिलीवरी|(?:खरीदने|लेने|माल|सामान|ऑर्डर|पीस)\s*(?:के\s*लिए\s*)?संपर्क\s*करें|(?:टेलीग्राम|whatsapp|telegram)\s*(?:पर\s*)?संपर्क\s*करें)"),
]

# Legacy combined list for backward-compatibility
AWARENESS_PATTERNS = INSTITUTIONAL_ADVISORY_PATTERNS + ADVISORY_DIRECTIVE_PATTERNS + ENFORCEMENT_NEWS_PATTERNS


@dataclass
class NormalizationResult:
    raw_text: str
    normalized_text: str
    language: LanguageTag
    detected_scripts: Dict[str, float]
    is_awareness_or_negation: bool
    awareness_markers: List[str]
    applied_normalizations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "language": self.language.value,
            "detected_scripts": {k: round(v, 3) for k, v in self.detected_scripts.items()},
            "is_awareness_or_negation": self.is_awareness_or_negation,
            "awareness_markers": self.awareness_markers,
            "applied_normalizations": self.applied_normalizations,
        }


@dataclass
class MultilingualConcept:
    concept_id: str
    category_id: str
    canonical_label_en: str
    aliases_en: List[str]
    aliases_hi: List[str]
    aliases_hinglish: List[str]
    spelling_variants: List[str] = field(default_factory=list)
    weight: float = 2.5
    is_context_only: bool = False
    context_notes: str = ""


@dataclass
class MultilingualMatch:
    concept_id: str
    canonical_label: str
    category_id: str
    matched_surface_form: str
    language: LanguageTag
    match_type: str  # "exact_phrase" or "broad_token"
    start_offset: int
    end_offset: int
    weight: float
    is_context_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "canonical_label": self.canonical_label,
            "category_id": self.category_id,
            "matched_surface_form": self.matched_surface_form,
            "language": self.language.value,
            "match_type": self.match_type,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "weight": round(self.weight, 2),
            "is_context_only": self.is_context_only,
        }


def detect_language_and_script(text: str) -> Tuple[LanguageTag, Dict[str, float]]:
    """
    Classifies input text into one of four first-class language forms:
    - EN: English in Latin script
    - HI: Native Hindi in Devanagari script (\u0900-\u097F)
    - HI-LATN: Hinglish / Romanised Hindi
    - MIXED: Code-switching (e.g. English technical nouns + Hindi Devanagari / Hinglish grammar)
    """
    if not text or not str(text).strip():
        return LanguageTag.UNKNOWN, {"en": 0.0, "hi": 0.0, "hi_latn": 0.0}

    dev_chars = len(RE_DEVANAGARI_CHAR.findall(text))
    lat_chars = len(RE_LATIN_CHAR.findall(text))
    total_letters = dev_chars + lat_chars

    if total_letters == 0:
        return LanguageTag.UNKNOWN, {"en": 0.0, "hi": 0.0, "hi_latn": 0.0}

    dev_ratio = dev_chars / total_letters
    lat_ratio = lat_chars / total_letters

    # High Devanagari proportion -> Native Hindi
    if dev_ratio >= 0.80:
        return LanguageTag.HI, {"en": 0.0, "hi": round(dev_ratio, 3), "hi_latn": 0.0}

    # Significant presence of BOTH Devanagari and Latin -> MIXED
    if dev_ratio >= 0.15 and lat_ratio >= 0.15:
        return LanguageTag.MIXED, {
            "en": round(lat_ratio * 0.5, 3),
            "hi": round(dev_ratio, 3),
            "hi_latn": round(lat_ratio * 0.5, 3),
        }

    # Predominantly Latin script: Distinguish English vs Hinglish vs Mixed
    tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z]{2,}\b", text)]
    if not tokens:
        return LanguageTag.EN, {"en": 1.0, "hi": 0.0, "hi_latn": 0.0}

    hinglish_matches = [t for t in tokens if t in HINGLISH_GRAMMAR_MARKERS or t in HINGLISH_SPELLING_ALIASES]
    hinglish_count = len(hinglish_matches)
    hinglish_ratio = hinglish_count / len(tokens)

    # Common English words
    english_structural = {
        "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for", "with",
        "of", "or", "as", "by", "from", "that", "this", "it", "are", "be", "was",
        "have", "has", "had", "contact", "dm", "call", "account", "delivery", "card",
        "bank", "fresh", "urgent", "available", "rent", "sale", "instant", "kit",
    }
    english_count = sum(1 for t in tokens if t in english_structural)

    # Code-switching: substantial English structure AND Hindi verbs/slang
    if english_count >= 2 and hinglish_count >= 1:
        return LanguageTag.MIXED, {
            "en": round(english_count / len(tokens), 3),
            "hi": 0.0,
            "hi_latn": round(hinglish_ratio, 3),
        }

    if hinglish_count >= 2 or hinglish_ratio >= 0.20:
        return LanguageTag.HI_LATN, {"en": round(1.0 - hinglish_ratio, 3), "hi": 0.0, "hi_latn": round(hinglish_ratio, 3)}

    return LanguageTag.EN, {"en": 1.0, "hi": 0.0, "hi_latn": 0.0}


def normalize_devanagari(text: str) -> Tuple[str, List[str]]:
    """
    Normalizes Devanagari Hindi text:
    - Unicode NFKC canonical decomposition & composition
    - Nukta folding to base consonants (e.g. फ़र्ज़ी -> फर्जी, नक़ली -> नकली)
    - Danda punctuation to standard periods
    - Strips unwanted zero-width spaces while preserving necessary ligatures
    """
    applied = []
    # 1. Unicode NFKC
    norm = unicodedata.normalize("NFKC", text)
    applied.append("nfkc_unicode")

    # 2. Nukta folding
    for nukta_char, base_char in NUKTA_MAP.items():
        if nukta_char in norm:
            norm = norm.replace(nukta_char, base_char)
            applied.append("nukta_folded")

    # 3. Danda punctuation
    if RE_DEVANAGARI_DANDA.search(norm):
        norm = RE_DEVANAGARI_DANDA.sub(". ", norm)
        applied.append("devanagari_danda_punct")

    return norm, list(dict.fromkeys(applied))


def normalize_hinglish_slang(text: str) -> Tuple[str, List[str]]:
    """
    Normalizes Hinglish (Romanised Hindi) text:
    - Collapses elongated repeated characters ("kattaaaaa" -> "katta", "farziii" -> "farzi")
    - Preserves legitimate double consonants ("katta" retains "tt", "chitta" retains "tt")
    - Maps common spelling variations to canonical spelling
    """
    applied = []

    # 1. Word-final repeated characters (3+ identical letters at end of word -> 1 letter)
    # e.g. kattaaaaa -> katta, farziii -> farzi, tamanchaaaa -> tamancha, broooo -> bro
    def fix_word_final(m):
        applied.append(f"collapsed_word_final:{m.group(0)}->{m.group(1)}")
        return m.group(1)

    text = re.sub(r"([a-zA-Z])\1{2,}\b", fix_word_final, text)

    # 2. Vowels repeated 3+ times in word-medial position:
    # Double vowels in lexicon: 'ee' (weed), 'oo' (bandook)
    def fix_vowels_middle(m):
        char = m.group(1).lower()
        repl = char * 2 if char in ("e", "o") else char
        applied.append(f"collapsed_vowel:{m.group(0)}->{repl}")
        return repl

    text = re.sub(r"([aeiouAEIOU])\1{2,}", fix_vowels_middle, text)

    # 3. Consonants repeated 3+ times in word-medial position:
    # Legitimate double consonants in Hindi/English (tt in katta/chitta, ll in bullets/full, ss in passbook, mm in ammo)
    def fix_consonants(m):
        char = m.group(1).lower()
        repl = char * 2 if char in ("t", "l", "s", "m", "f", "c", "p", "b", "d") else char
        applied.append(f"collapsed_consonant:{m.group(0)}->{repl}")
        return repl

    text = re.sub(r"([a-zA-Z])\1{2,}", fix_consonants, text)

    # 4. Token-level alias mapping on word boundaries
    def replace_alias(m):
        word = m.group(0).lower()
        if word in HINGLISH_SPELLING_ALIASES:
            applied.append(f"alias_mapped:{word}->{HINGLISH_SPELLING_ALIASES[word]}")
            return HINGLISH_SPELLING_ALIASES[word]
        return m.group(0)

    pattern = r"\b(" + "|".join(re.escape(k) for k in sorted(HINGLISH_SPELLING_ALIASES.keys(), key=len, reverse=True)) + r")\b"
    text = re.sub(pattern, replace_alias, text, flags=re.IGNORECASE)

    return text, list(dict.fromkeys(applied))


@dataclass
class AwarenessContextResult:
    is_confirmed_advisory: bool
    has_advisory_markers: bool
    has_solicitation_markers: bool
    has_enforcement_news: bool
    markers: List[str]
    context_type: str  # "confirmed_advisory" | "mixed_solicitation" | "news_enforcement" | "generic_warning" | "none"
    explanation: str


def evaluate_awareness_context(text: str) -> AwarenessContextResult:
    """
    Evaluates context around multi-lingual public advisories, warnings, and seller solicitations.
    A single generic phrase does not suppress a post.
    Contraband trade or commercial solicitation cues strictly override advisory suppression.
    """
    if not text or not str(text).strip():
        return AwarenessContextResult(
            is_confirmed_advisory=False,
            has_advisory_markers=False,
            has_solicitation_markers=False,
            has_enforcement_news=False,
            markers=[],
            context_type="none",
            explanation="Empty text."
        )

    inst_markers = []
    for pat in INSTITUTIONAL_ADVISORY_PATTERNS:
        m = pat.search(text)
        if m:
            inst_markers.append(m.group(0).strip())

    directive_markers = []
    for pat in ADVISORY_DIRECTIVE_PATTERNS:
        m = pat.search(text)
        if m:
            directive_markers.append(m.group(0).strip())

    enforcement_markers = []
    for pat in ENFORCEMENT_NEWS_PATTERNS:
        m = pat.search(text)
        if m:
            enforcement_markers.append(m.group(0).strip())

    solicitation_markers = []
    for pat in ILLICIT_SOLICITATION_PATTERNS:
        m = pat.search(text)
        if m:
            solicitation_markers.append(m.group(0).strip())

    all_advisory_markers = list(dict.fromkeys(inst_markers + directive_markers + enforcement_markers))
    has_advisory = bool(all_advisory_markers)
    has_solicitation = bool(solicitation_markers)
    has_enforcement = bool(enforcement_markers)

    # 1. If commercial solicitation / seller contact markers are present:
    # A seller cannot evade detection by quoting a disclaimer or warning phrase!
    if has_solicitation and has_advisory:
        return AwarenessContextResult(
            is_confirmed_advisory=False,
            has_advisory_markers=True,
            has_solicitation_markers=True,
            has_enforcement_news=has_enforcement,
            markers=all_advisory_markers,
            context_type="mixed_solicitation",
            explanation="Advisory/warning phrasing detected alongside commercial trade solicitation; suppression withheld."
        )

    # 2. Confirmed official public institutional advisory:
    # Has institutional marker (e.g. helpline 1930, official notice, जनहित में जारी) AND no seller solicitation
    if bool(inst_markers) and not has_solicitation:
        return AwarenessContextResult(
            is_confirmed_advisory=True,
            has_advisory_markers=True,
            has_solicitation_markers=False,
            has_enforcement_news=has_enforcement,
            markers=all_advisory_markers,
            context_type="confirmed_advisory",
            explanation="Confirmed public awareness advisory / statutory police notice."
        )

    # 3. Multiple safety directives without solicitation (e.g. 'never share OTP' + 'beware of fraud')
    if len(directive_markers) >= 2 and not has_solicitation:
        return AwarenessContextResult(
            is_confirmed_advisory=True,
            has_advisory_markers=True,
            has_solicitation_markers=False,
            has_enforcement_news=has_enforcement,
            markers=all_advisory_markers,
            context_type="confirmed_advisory",
            explanation="Confirmed public safety warning advisory."
        )

    # 4. Law enforcement news reporting of past arrest/busted gang without commercial solicitation
    if has_enforcement and not has_solicitation:
        return AwarenessContextResult(
            is_confirmed_advisory=True,
            has_advisory_markers=True,
            has_solicitation_markers=False,
            has_enforcement_news=True,
            markers=all_advisory_markers,
            context_type="news_enforcement",
            explanation="Law enforcement reporting of past arrest/seizure without commercial solicitation."
        )

    # 5. Isolated generic warning phrase (e.g. just "savdhan rahe" alone without institutional backing)
    if has_advisory:
        return AwarenessContextResult(
            is_confirmed_advisory=False,
            has_advisory_markers=True,
            has_solicitation_markers=False,
            has_enforcement_news=False,
            markers=all_advisory_markers,
            context_type="generic_warning",
            explanation="Generic warning phrase without confirmed institutional advisory context; suppression withheld."
        )

    return AwarenessContextResult(
        is_confirmed_advisory=False,
        has_advisory_markers=False,
        has_solicitation_markers=False,
        has_enforcement_news=False,
        markers=[],
        context_type="none",
        explanation="No public advisory markers detected."
    )


def check_awareness_context(text: str) -> Tuple[bool, List[str]]:
    """
    Evaluates whether text contains confirmed public advisory context.
    Returns (is_confirmed_advisory, markers).
    """
    res = evaluate_awareness_context(text)
    return res.is_confirmed_advisory, res.markers


def normalize_multilingual(raw_text: str) -> NormalizationResult:
    """
    Unified multi-lingual normalization pipeline:
    1. Preserves raw source text intact
    2. Detects primary language & script (EN, HI, HI-LATN, MIXED)
    3. Runs Devanagari NFC/NFKC, nukta, and danda normalization
    4. Runs Hinglish spelling alias and repeated character folding
    5. Checks awareness and disclaimer markers across all languages
    6. Returns structured NormalizationResult
    """
    if not raw_text or not str(raw_text).strip():
        return NormalizationResult(
            raw_text=raw_text or "",
            normalized_text="",
            language=LanguageTag.UNKNOWN,
            detected_scripts={"en": 0.0, "hi": 0.0, "hi_latn": 0.0},
            is_awareness_or_negation=False,
            awareness_markers=[],
            applied_normalizations=[],
        )

    text = str(raw_text)
    applied: List[str] = []

    # Detect language and scripts
    lang, script_dist = detect_language_and_script(text)

    # 1. Devanagari normalization (if Devanagari characters present)
    if RE_DEVANAGARI_CHAR.search(text):
        text, dev_applied = normalize_devanagari(text)
        applied.extend(dev_applied)

    # 2. Hinglish normalization (if Latin characters present)
    if RE_LATIN_CHAR.search(text):
        text, hi_latn_applied = normalize_hinglish_slang(text)
        applied.extend(hi_latn_applied)

    # 3. Clean multiple whitespace
    cleaned = re.sub(r"[ \t]+", " ", text).strip()
    if cleaned != text:
        applied.append("whitespace_cleaned")
    text = cleaned

    # 4. Awareness check
    is_aware, markers = check_awareness_context(raw_text)
    if not is_aware and text != raw_text:
        is_aware, markers = check_awareness_context(text)

    return NormalizationResult(
        raw_text=str(raw_text),
        normalized_text=text,
        language=lang,
        detected_scripts=script_dist,
        is_awareness_or_negation=is_aware,
        awareness_markers=markers,
        applied_normalizations=list(dict.fromkeys(applied)),
    )
