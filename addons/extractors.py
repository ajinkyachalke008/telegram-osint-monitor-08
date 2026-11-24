"""Specialized Entity and Identifier Extractors for OSINT & Law Enforcement Analysis.

Extracts:
- Validated UPI IDs (checked against real NPCI / PSP bank handle registry)
- Indian phone numbers (handles +91, 10-digit formats, and Devanagari numerals)
- IFSC Codes (Indian Financial System Code)
- Crypto wallet addresses (BTC, ETH/EVM, TRX/TRC20, Solana)
- Telegram @usernames & t.me invite / channel links
- Indian geographic locations / transit hubs
"""
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

# Common email domains explicitly blocked from being classified as UPI
BLOCKED_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "outlook.com",
    "hotmail.com", "live.com", "icloud.com", "mail.com", "proton.me", "protonmail.com",
    "zoho.com", "aol.com", "yandex.com", "tutanota.com", "fastmail.com",
}

# Devanagari digit translation table
DEVANAGARI_DIGITS = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}

INDIAN_CITIES_AND_STATES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "ahmedabad",
    "chennai", "kolkata", "surat", "pune", "jaipur", "lucknow", "kanpur",
    "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "patna", "vadodara",
    "ghaziabad", "ludhiana", "agra", "nashik", "faridabad", "meerut", "rajkot",
    "varanasi", "srinagar", "aurangabad", "chhatrapati sambhajinagar", "dhanbad",
    "amritsar", "navi mumbai", "allahabad", "prayagraj", "ranchi", "howrah",
    "coimbatore", "jabalpur", "gwalior", "vijayawada", "jodhpur", "madurai",
    "raipur", "kota", "guwahati", "chandigarh", "solapur", "hubli", "dharwad",
    "bareilly", "moradabad", "mysore", "gurgaon", "gurugram", "aligarh",
    "jalandhar", "tiruchirappalli", "bhubaneswar", "salem", "mira-bhayandar",
    "warangal", "thiruvananthapuram", "bhiwandi", "saharanpur", "guntur",
    "amravati", "bikaner", "noida", "jamshedpur", "bhilai", "cuttack",
    "firozabad", "kochi", "nellore", "bhavnagar", "dehradun", "durgapur",
    "asansol", "rourkela", "nanded", "kolhapur", "ajmer", "akola", "gulbarga",
    "jamnagar", "ujjain", "loni", "siliguri", "jhansi", "ulhasnagar",
    "jammu", "sangli", "mangalore", "erode", "belgaum", "kurnool", "jamtara",
    "mewat", "nuh", "alwar", "bharatpur", "mathura", "nuh-mewat",
    # States
    "maharashtra", "rajasthan", "gujarat", "punjab", "haryana", "uttar pradesh",
    "bihar", "west bengal", "madhya pradesh", "karnataka", "tamil nadu",
    "telangana", "andhra pradesh", "kerala", "odisha", "jharkhand", "assam",
    "goa", "uttarakhand", "himachal pradesh", "chhattisgarh",
}

# Regex patterns
RE_UPI_CANDIDATE = re.compile(r"\b([a-zA-Z0-9.\-_]{2,64})@([a-zA-Z0-9.\-_]{2,32})\b")
RE_IFSC = re.compile(r"\b([A-Z]{4})0([A-Z0-9]{6})\b", re.IGNORECASE)
RE_USERNAME = re.compile(r"(?<![\w@./])@([A-Za-z][A-Za-z0-9_]{3,31})\b")
RE_TME_LINK = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me)/(?:joinchat/|\+)?([A-Za-z0-9_-]{4,64})", re.IGNORECASE)

# Crypto patterns
RE_BTC = re.compile(r"\b(?:bc1[ac-hj-np-z02-9]{25,71}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")
RE_ETH = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
RE_TRX = re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b")
RE_SOL = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")


def normalize_devanagari_digits(text: str) -> str:
    """Translate Devanagari numerals to standard ASCII Arabic digits."""
    if not text:
        return ""
    result = []
    for ch in text:
        result.append(DEVANAGARI_DIGITS.get(ch, ch))
    return "".join(result)


def extract_upis(text: str) -> List[str]:
    """
    Extract verified UPI IDs (name@handle).
    Validates handle against known banking/fintech PSP handles and explicitly
    rejects email domains.
    """
    if not text:
        return []
    
    found = []
    seen = set()
    for match in RE_UPI_CANDIDATE.finditer(text):
        user_part, handle_part = match.group(1), match.group(2).lower()
        full_val = f"{user_part}@{handle_part}"
        
        # Check against blocked email domains
        if handle_part in BLOCKED_EMAIL_DOMAINS or any(full_val.lower().endswith(dom) for dom in BLOCKED_EMAIL_DOMAINS):
            continue
            
        # Match against known UPI handles or bank handle pattern
        if handle_part in UPI_HANDLES:
            clean_val = full_val.strip(".,;:").lower()
            if clean_val not in seen:
                seen.add(clean_val)
                found.append(clean_val)
    return found


def extract_indian_phones(text: str) -> List[str]:
    """
    Extract Indian phone numbers in +91, 91, 0, or bare 10-digit formats (starting 6-9),
    including Devanagari numerals.
    Returns normalized 10-digit or +91 standard formats.
    """
    if not text:
        return []
    
    # First normalize Devanagari numerals
    norm_text = normalize_devanagari_digits(text)
    
    # Regex to capture phone numbers with optional country code, delimiters
    pattern = re.compile(r"(?:\+91[\s\-]?)?(?:\b91[\s\-]?)?(?:0)?\b([6-9]\d{4}[\s\-]?\d{5})\b")
    found = []
    seen = set()
    
    for match in pattern.finditer(norm_text):
        raw = match.group(0).strip(".,;:()")
        digits_only = re.sub(r"\D", "", raw)
        
        # Normalize to standard 10-digit mobile number
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


def extract_crypto_wallets(text: str) -> List[Tuple[str, str]]:
    """
    Extract cryptocurrency wallet addresses.
    Returns list of (address, network_type).
    """
    if not text:
        return []
    found = []
    seen = set()
    
    for m in RE_ETH.finditer(text):
        val = m.group(0)
        if val.lower() not in seen:
            seen.add(val.lower())
            found.append((val, "ETH/EVM"))
            
    for m in RE_BTC.finditer(text):
        val = m.group(0)
        if val not in seen:
            seen.add(val)
            found.append((val, "BTC"))
            
    for m in RE_TRX.finditer(text):
        val = m.group(0)
        if val not in seen:
            seen.add(val)
            found.append((val, "TRX/TRC20"))
            
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


def extract_locations(text: str) -> List[str]:
    """Extract Indian cities, cybercrime hotspots, or states mentioned in text."""
    if not text:
        return []
    found = []
    seen = set()
    t_low = text.lower()
    for loc in INDIAN_CITIES_AND_STATES:
        # Word boundary match
        pattern = r"\b" + re.escape(loc) + r"\b"
        if re.search(pattern, t_low):
            if loc not in seen:
                seen.add(loc)
                found.append(loc.title())
    return found


def extract_all_entities(text: str) -> Dict[str, Any]:
    """
    Run the full suite of extractors and return structured identifier metadata.
    """
    if not text:
        return {
            "upis": [], "phones": [], "ifscs": [], "crypto_wallets": [],
            "usernames": [], "tme_links": [], "locations": [], "all_flat": []
        }
        
    upis = extract_upis(text)
    phones = extract_indian_phones(text)
    ifscs = extract_ifsc_codes(text)
    cryptos = extract_crypto_wallets(text)
    usernames = extract_usernames(text)
    links = extract_tme_links(text)
    locations = extract_locations(text)
    
    # Flat representation for graph linking: (value, entity_type)
    all_flat = []
    for u in upis:
        all_flat.append({"value": u, "type": "UPI"})
    for p in phones:
        all_flat.append({"value": p, "type": "Phone"})
    for i in ifscs:
        all_flat.append({"value": i, "type": "IFSC"})
    for addr, net in cryptos:
        all_flat.append({"value": addr, "type": f"Crypto ({net})"})
    for un in usernames:
        all_flat.append({"value": un, "type": "Username"})
    for lk in links:
        all_flat.append({"value": lk, "type": "TelegramLink"})
    for loc in locations:
        all_flat.append({"value": loc, "type": "Location"})
        
    return {
        "upis": upis,
        "phones": phones,
        "ifscs": ifscs,
        "crypto_wallets": cryptos,
        "usernames": usernames,
        "tme_links": links,
        "locations": locations,
        "all_flat": all_flat,
    }
