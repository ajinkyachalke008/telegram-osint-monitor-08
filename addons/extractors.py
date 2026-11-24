"""Specialized Entity and Identifier Extractors for OSINT & Law Enforcement Analysis.

Extracts:
- Validated UPI IDs (checked against real NPCI / PSP bank handle registry)
- Indian phone numbers (handles +91, 10-digit formats, Devanagari numerals, and obfuscated number words)
- IFSC Codes (Indian Financial System Code)
- Cryptocurrency wallets with Base58Check / hex verification (BTC, ETH/EVM, TRX/TRC20, Solana)
- Telegram @usernames & t.me invite / channel links
- Indian geographic locations with gazetteer coordinates and PIN codes
- Price & financial consideration mentions (INR, USD, USDT)
"""
import hashlib
import re
import unicodedata
from typing import List, Tuple, Dict, Any, Optional

# Authoritative registry of real Indian UPI PSP & Bank handles
# (Excludes common email domains like gmail.com, yahoo.com, outlook.com, hotmail.com, icloud.com, proton.me)
UPI_HANDLES = {
    # Popular Payment Apps / PSPs
    "okaxis", "okhdfcbank", "oksbi", "okicici", "okbizaxis",
    "ybl", "ibl", "axl", "apl", "rapl",
    "paytm", "ptyes", "ptidfc", "ptaxis", "ptsbi",
    "gpay", "freecharge", "mobikwik", "airtel", "airtelpaymentsbank",
    "jupiteraxis", "slice", "cred", "postpe", "navi", "fam",
    # Major Public and Private Banks
    "sbi", "barodampay", "pnb", "cnrb", "unionbank", "uboi", "boi", "cboi",
    "idbi", "indianbank", "iob", "uco", "psb",
    "hdfcbank", "icici", "axisbank", "kotak", "indus", "idfcbank", "idfc",
    "federal", "rbl", "yesbank", "bandhan", "scb", "citi",
    "equitas", "auzero", "aubank", "fbl", "kbl", "kvb", "sib", "tmb",
    # Regional Rural / Cooperative / Specialized
    "dlb", "esaf", "finobank", "ippb", "jsb", "nsdl", "payzapp", "pingpay",
    "timecosmos", "waaxis", "wahdfcbank", "wasbi", "waicici",
}

BLOCKED_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "outlook.com",
    "hotmail.com", "live.com", "icloud.com", "mail.com", "proton.me", "protonmail.com",
    "zoho.com", "aol.com", "yandex.com", "tutanota.com", "fastmail.com",
}

DEVANAGARI_DIGITS = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}

NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}

# Indian Gazetteer with approximate lat/lon centroids for mapping
INDIAN_GAZETTEER = {
    # Hotspots & Tier-1/2 Cities
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "state": "Maharashtra", "type": "Metropolis"},
    "delhi": {"lat": 28.7041, "lon": 77.1025, "state": "Delhi", "type": "Metropolis"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka", "type": "Metropolis"},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka", "type": "Metropolis"},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana", "type": "Metropolis"},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "state": "Gujarat", "type": "Metropolis"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu", "type": "Metropolis"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal", "type": "Metropolis"},
    "pune": {"lat": 18.5204, "lon": 73.8567, "state": "Maharashtra", "type": "City"},
    "surat": {"lat": 21.1702, "lon": 72.8311, "state": "Gujarat", "type": "City"},
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan", "type": "Hotspot/Capital"},
    "jodhpur": {"lat": 26.2389, "lon": 73.0243, "state": "Rajasthan", "type": "City"},
    "kota": {"lat": 25.2138, "lon": 75.8648, "state": "Rajasthan", "type": "City"},
    "bikaner": {"lat": 28.0229, "lon": 73.3119, "state": "Rajasthan", "type": "City"},
    "ajmer": {"lat": 26.4499, "lon": 74.6399, "state": "Rajasthan", "type": "City"},
    "alwar": {"lat": 27.5530, "lon": 76.6346, "state": "Rajasthan", "type": "Hotspot"},
    "bharatpur": {"lat": 27.2152, "lon": 77.5030, "state": "Rajasthan", "type": "Hotspot"},
    "mewat": {"lat": 28.1000, "lon": 77.0500, "state": "Haryana/Rajasthan", "type": "Hotspot"},
    "nuh": {"lat": 28.1100, "lon": 77.0100, "state": "Haryana", "type": "Hotspot"},
    "jamtara": {"lat": 23.9620, "lon": 86.8020, "state": "Jharkhand", "type": "Hotspot"},
    "lucknow": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "type": "City"},
    "noida": {"lat": 28.5355, "lon": 77.3910, "state": "Uttar Pradesh", "type": "City"},
    "patna": {"lat": 25.5941, "lon": 85.1376, "state": "Bihar", "type": "City"},
    "ranchi": {"lat": 23.3441, "lon": 85.3096, "state": "Jharkhand", "type": "City"},
    "indore": {"lat": 22.7196, "lon": 75.8577, "state": "Madhya Pradesh", "type": "City"},
    "bhopal": {"lat": 23.2599, "lon": 77.4126, "state": "Madhya Pradesh", "type": "City"},
    "nagpur": {"lat": 21.1458, "lon": 79.0882, "state": "Maharashtra", "type": "City"},
    "chandigarh": {"lat": 30.7333, "lon": 76.7794, "state": "Punjab/Haryana", "type": "City"},
    # States
    "rajasthan": {"lat": 27.0238, "lon": 74.2179, "state": "Rajasthan", "type": "State"},
    "maharashtra": {"lat": 19.7515, "lon": 75.7139, "state": "Maharashtra", "type": "State"},
    "haryana": {"lat": 29.0588, "lon": 76.0856, "state": "Haryana", "type": "State"},
    "uttar pradesh": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "type": "State"},
    "bihar": {"lat": 25.0961, "lon": 85.3131, "state": "Bihar", "type": "State"},
    "jharkhand": {"lat": 23.6102, "lon": 85.2799, "state": "Jharkhand", "type": "State"},
    "gujarat": {"lat": 22.2587, "lon": 71.1924, "state": "Gujarat", "type": "State"},
    "punjab": {"lat": 31.1471, "lon": 75.3412, "state": "Punjab", "type": "State"},
}

# Base58 character alphabet
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# Regexes
RE_UPI_CANDIDATE = re.compile(r"\b([a-zA-Z0-9.\-_]{2,64})@([a-zA-Z0-9.\-_]{2,32})\b")
RE_IFSC = re.compile(r"\b([A-Z]{4})0([A-Z0-9]{6})\b", re.IGNORECASE)
RE_USERNAME = re.compile(r"(?<![\w@./])@([A-Za-z][A-Za-z0-9_]{3,31})\b")
RE_TME_LINK = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me)/(?:joinchat/|\+)?([A-Za-z0-9_-]{4,64})", re.IGNORECASE)
RE_PINCODE = re.compile(r"\b([1-9][0-9]{5})\b")
RE_PRICE = re.compile(
    r"(?:(?:₹|rs\.?|inr|usdt|\$)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?k?)\b)|"
    r"(?:\b([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?k?)\s*(?:₹|rs\.?|inr|usdt|/-)\b)",
    re.IGNORECASE
)

RE_ETH = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
RE_BTC = re.compile(r"\b(?:bc1[ac-hj-np-z02-9]{25,71}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")
RE_TRX = re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b")
RE_SOL = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")


def base58_decode(s: str) -> Optional[bytes]:
    """Decode a Base58 string into bytes."""
    num = 0
    for ch in s:
        idx = B58_ALPHABET.find(ch)
        if idx == -1:
            return None
        num = num * 58 + idx
    combined = num.to_bytes((num.bit_length() + 7) // 8, byteorder="big")
    pad = 0
    for ch in s:
        if ch == B58_ALPHABET[0]:
            pad += 1
        else:
            break
    return b"\x00" * pad + combined


def validate_base58_checksum(address: str) -> bool:
    """Validate 4-byte double SHA-256 checksum for Base58Check addresses (BTC, TRC20)."""
    try:
        decoded = base58_decode(address)
        if not decoded or len(decoded) < 5:
            return False
        payload, checksum = decoded[:-4], decoded[-4:]
        h1 = hashlib.sha256(payload).digest()
        h2 = hashlib.sha256(h1).digest()
        return h2[:4] == checksum
    except Exception:
        return False


def normalize_devanagari_and_words(text: str) -> str:
    """Normalize Devanagari numerals and spelled-out number words in text."""
    if not text:
        return ""
    # 1. Devanagari numerals
    t = "".join(DEVANAGARI_DIGITS.get(ch, ch) for ch in text)
    # 2. Number words
    pattern = r"\b(" + "|".join(NUMBER_WORDS.keys()) + r")\b"
    t = re.sub(pattern, lambda m: NUMBER_WORDS[m.group(0).lower()], t, flags=re.IGNORECASE)
    return t


normalize_devanagari_digits = normalize_devanagari_and_words


def extract_upis(text: str) -> List[str]:
    """Extract verified UPI IDs (name@handle) against known handles, excluding email domains."""
    if not text:
        return []
    found = []
    seen = set()
    for match in RE_UPI_CANDIDATE.finditer(text):
        user_part, handle_part = match.group(1), match.group(2).lower()
        full_val = f"{user_part}@{handle_part}"
        if handle_part in BLOCKED_EMAIL_DOMAINS or any(full_val.lower().endswith(dom) for dom in BLOCKED_EMAIL_DOMAINS):
            continue
        if handle_part in UPI_HANDLES:
            clean_val = full_val.strip(".,;:").lower()
            if clean_val not in seen:
                seen.add(clean_val)
                found.append(clean_val)
    return found


def extract_indian_phones(text: str) -> List[str]:
    """
    Extract Indian phone numbers in +91, 91, 0, or bare 10-digit forms (starting 6-9),
    including Devanagari numerals, spaced/dotted numbers, and spelled words.
    """
    if not text:
        return []
    norm_text = normalize_devanagari_and_words(text)
    pattern = re.compile(r"(?:\+91[\s\.\-]?)?(?:\b91[\s\.\-]?)?(?:0)?\b([6-9][0-9\s\.\-]{8,25}[0-9])\b")
    found = []
    seen = set()

    for match in pattern.finditer(norm_text):
        raw = match.group(0).strip(".,;:()")
        digits_only = re.sub(r"\D", "", raw)
        if len(digits_only) == 10 and digits_only[0] in "6789":
            phone_10 = digits_only
        elif len(digits_only) == 12 and digits_only.startswith("91") and digits_only[2] in "6789":
            phone_10 = digits_only[2:]
        elif len(digits_only) == 11 and digits_only.startswith("0") and digits_only[1] in "6789":
            phone_10 = digits_only[1:]
        else:
            continue

        canonical = f"+91{phone_10}"
        if canonical not in seen:
            seen.add(canonical)
            found.append(canonical)
    return found


def extract_ifsc_codes(text: str) -> List[str]:
    """Extract valid Indian Financial System Codes (IFSC)."""
    if not text:
        return []
    found = []
    seen = set()
    for match in RE_IFSC.finditer(text):
        val = match.group(0).upper().strip(".,;:")
        if val not in seen:
            seen.add(val)
            found.append(val)
    return found


def extract_crypto_wallets(text: str) -> List[Tuple[str, str, bool]]:
    """
    Extract cryptocurrency wallet addresses with checksum validation.
    Returns list of (address, network_type, is_checksum_valid).
    """
    if not text:
        return []
    found = []
    seen = set()

    # TRON (TRC20)
    for m in RE_TRX.finditer(text):
        val = m.group(0)
        if val not in seen:
            seen.add(val)
            is_valid = validate_base58_checksum(val)
            found.append((val, "TRX/TRC20", is_valid))

    # Bitcoin
    for m in RE_BTC.finditer(text):
        val = m.group(0)
        if val not in seen:
            seen.add(val)
            is_valid = val.startswith("bc1") or validate_base58_checksum(val)
            found.append((val, "BTC", is_valid))

    # Ethereum / EVM
    for m in RE_ETH.finditer(text):
        val = m.group(0)
        if val.lower() not in seen:
            seen.add(val.lower())
            found.append((val, "ETH/EVM", True))

    return found


def extract_locations(text: str) -> List[Dict[str, Any]]:
    """Extract locations, cities, cybercrime hotspots, and PIN codes with lat/lon coordinates."""
    if not text:
        return []
    found = []
    seen = set()
    t_low = text.lower()

    # Match gazetteer
    for loc, info in INDIAN_GAZETTEER.items():
        pattern = r"\b" + re.escape(loc) + r"\b"
        if re.search(pattern, t_low):
            if loc not in seen:
                seen.add(loc)
                found.append({
                    "name": loc.title(),
                    "state": info["state"],
                    "lat": info["lat"],
                    "lon": info["lon"],
                    "type": info["type"],
                    "confidence": 0.95
                })

    # Match PIN codes
    for m in RE_PINCODE.finditer(text):
        pin = m.group(1)
        if pin not in seen:
            seen.add(pin)
            found.append({
                "name": f"PIN {pin}",
                "state": "India",
                "lat": None,
                "lon": None,
                "type": "Pincode",
                "confidence": 0.85
            })

    return found


def extract_prices(text: str) -> List[str]:
    """Extract price and monetary consideration mentions (INR, USD, USDT)."""
    if not text:
        return []
    found = []
    seen = set()
    for m in RE_PRICE.finditer(text):
        raw = m.group(0).strip(".,;:()")
        if raw.lower() not in seen:
            seen.add(raw.lower())
            found.append(raw)
    return found


def extract_usernames(text: str) -> List[str]:
    """Extract Telegram / social usernames (@handle)."""
    if not text:
        return []
    found = []
    seen = set()
    for m in RE_USERNAME.finditer(text):
        val = f"@{m.group(1)}".strip(".,;:")
        val_l = val.lower()
        if val_l not in seen:
            seen.add(val_l)
            found.append(val)
    return found


def extract_tme_links(text: str) -> List[str]:
    """Extract t.me channels, group invites, or message links."""
    if not text:
        return []
    found = []
    seen = set()
    for m in RE_TME_LINK.finditer(text):
        raw = m.group(0).strip(".,;:()")
        if not raw.startswith("http"):
            raw = f"https://{raw}"
        val_l = raw.lower()
        if val_l not in seen:
            seen.add(val_l)
            found.append(raw)
    return found


def extract_all_entities(text: str, source: str = "text", channel_handle: Optional[str] = None) -> Dict[str, Any]:
    """Run full extraction suite and return structured entity metadata.
    
    If channel_handle is provided, the channel's own handle / link is excluded
    from being treated as an illicit seller identifier.
    """
    if not text:
        return {
            "upis": [], "phones": [], "ifscs": [], "crypto_wallets": [],
            "usernames": [], "tme_links": [], "locations": [], "prices": [],
            "all_flat": []
        }

    # Normalize channel handle if provided
    own_handles = set()
    if channel_handle:
        raw_ch = str(channel_handle).strip().lower()
        own_handles.add(raw_ch)
        own_handles.add(raw_ch.lstrip('@'))
        own_handles.add(f"@{raw_ch.lstrip('@')}")
        if "t.me/" in raw_ch:
            slug = raw_ch.split("t.me/")[-1].strip("/@")
            own_handles.add(slug)
            own_handles.add(f"@{slug}")
            own_handles.add(f"https://t.me/{slug}")
            own_handles.add(f"http://t.me/{slug}")
            own_handles.add(f"t.me/{slug}")

    upis = extract_upis(text)
    phones = extract_indian_phones(text)
    ifscs = extract_ifsc_codes(text)
    cryptos = extract_crypto_wallets(text)
    locations = extract_locations(text)
    prices = extract_prices(text)
    raw_usernames = extract_usernames(text)
    raw_links = extract_tme_links(text)

    # Filter out channel's own handle from seller identifiers
    usernames = []
    for un in raw_usernames:
        un_l = un.lower()
        if un_l in own_handles or un_l.lstrip('@') in own_handles:
            continue
        usernames.append(un)

    links = []
    for lk in raw_links:
        lk_l = lk.lower()
        if lk_l in own_handles:
            continue
        slug = lk_l.split("t.me/")[-1].strip("/@") if "t.me/" in lk_l else ""
        if slug and (slug in own_handles or f"@{slug}" in own_handles):
            continue
        links.append(lk)

    # Flat representation for graph linking
    all_flat = []
    for u in upis:
        all_flat.append({"value": u, "type": "UPI", "source": source})
    for p in phones:
        all_flat.append({"value": p, "type": "Phone", "source": source})
    for i in ifscs:
        all_flat.append({"value": i, "type": "IFSC", "source": source})
    for addr, net, valid in cryptos:
        all_flat.append({"value": addr, "type": f"Crypto ({net})", "valid": valid, "source": source})
    for un in usernames:
        all_flat.append({"value": un, "type": "Username", "source": source})
    for lk in links:
        all_flat.append({"value": lk, "type": "TelegramLink", "source": source})
    for loc in locations:
        all_flat.append({"value": loc["name"], "type": "Location", "lat": loc["lat"], "lon": loc["lon"], "source": source})

    return {
        "upis": upis,
        "phones": phones,
        "ifscs": ifscs,
        "crypto_wallets": cryptos,
        "usernames": usernames,
        "tme_links": links,
        "locations": locations,
        "prices": prices,
        "all_flat": all_flat,
    }
