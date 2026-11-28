"""PS02 Search Terms Catalog & Multi-Lingual Contextual Search Engine.

Implements the official 10-category threat catalog:
1. General fraud, deception and forgery
2. Phishing, spoofing and impersonation
3. OTP, credentials and KYC-related scams
4. UPI, QR, card and digital-payment fraud
5. Identity-document and certificate fraud
6. Loan, job, task and advance-fee scams
7. Investment, lottery and money-circulation scams
8. Marketplace, delivery and consumer-purchase scams
9. Extortion, blackmail and malicious-software reports
10. Weapons and firearm references (context only)

STRICT EVIDENTIARY & PRIVACY GUARDRAILS:
- Explicit disclaimer: A keyword match is a search result, not proof of wrongdoing.
- Differentiates broad token searches from exact phrase searches.
- Context-only weapons references: ordinary object names and incident terminology with zero automatic suspicion scoring.
- Zero citizen or sender profiling; NO buyer/seller classification; NO individual sender lookup; NO identity graphs.
- PII sanitization: strictly redacts phone numbers, emails, payment IDs, bank account numbers, usernames, and invite links.
- Ephemeral in-memory image byte retrieval directly from ZIP archive without disk extraction.
"""

import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

CATALOG_JSON_PATH = Path(__file__).resolve().parent / "search_terms_catalog.json"
OFFICIAL_DISCLAIMER = (
    "A keyword match is a search result, not proof of wrongdoing. "
    "Context, provenance, integrity and independent verification are necessary "
    "before any legal or operational reliance."
)

# Regexes to safely redact private identifiers and handles
RE_PHONE = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
RE_UPI = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b")
RE_BANK_ACCT = re.compile(r"\b\d{9,18}\b")
RE_USERNAME = re.compile(r"@\w{3,32}\b")
RE_TME = re.compile(r"t\.me/[A-Za-z0-9_]{3,32}\b")


@dataclass
class SearchMatch:
    category_id: str
    category_label: str
    matched_term: str
    match_type: str  # "exact_phrase" or "broad_term"
    source_type: str  # "Telegram" or "SocialMedia"
    channel_or_platform: str
    timestamp_ist: str
    highlighted_context: str
    raw_snippet: str
    media_file: Optional[str] = None
    media_resolved: bool = False
    is_context_only: bool = False
    disclaimer: str = OFFICIAL_DISCLAIMER


class SearchTermsCatalog:
    """Multi-lingual search catalog and query evaluator."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = Path(catalog_path) if catalog_path else CATALOG_JSON_PATH
        self.catalog_data = self._load_catalog()
        self.categories: Dict[str, Dict[str, Any]] = {
            c["id"]: c for c in self.catalog_data.get("categories", [])
        }

    def _load_catalog(self) -> Dict[str, Any]:
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog JSON not found at {self.catalog_path}")
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_categories(self) -> List[Dict[str, Any]]:
        return list(self.categories.values())

    def get_category_ids(self) -> List[str]:
        return list(self.categories.keys())

    def get_category(self, cat_id: str) -> Optional[Dict[str, Any]]:
        return self.categories.get(cat_id)

    def get_all_terms_for_category(self, cat_id: str) -> List[str]:
        cat = self.get_category(cat_id)
        if not cat:
            return []
        all_terms = []
        # Support official schema
        all_terms.extend(cat.get("high_context_phrases", []))
        all_terms.extend(cat.get("broad_terms", []))
        for alias_list in cat.get("regional_aliases", {}).values():
            if isinstance(alias_list, list):
                all_terms.extend(alias_list)
        # Support legacy keys if present
        for key in ("terms_en", "terms_hinglish", "terms_marathi", "coded_phrases"):
            all_terms.extend(cat.get(key, []))
        return list(dict.fromkeys([t.strip() for t in all_terms if t and t.strip()]))

    def is_false_positive(self, text: str, cat_id: str) -> bool:
        """Check if match context contains known false-positive exemptions."""
        cat = self.get_category(cat_id)
        if not cat:
            return False
        text_lower = text.lower()
        # Common benign/toy exemptions
        default_fps = [
            "toy gun", "water gun", "glue gun", "massage gun", "radar gun",
            "machine learning", "water pistol", "bubble gun"
        ]
        fps = cat.get("false_positive_exceptions", default_fps if "weapon" in cat_id else [])
        for fp in fps:
            if fp.lower() in text_lower:
                return True
        return False

    def search_text(
        self,
        text: str,
        category_filter: Optional[str] = None,
        exact_phrase_only: bool = False,
    ) -> List[Tuple[str, str, str]]:
        """Search text against catalog.

        Returns list of tuples: (category_id, matched_term, match_type)
        """
        if not text or not isinstance(text, str):
            return []

        clean_text = text.strip()
        if not clean_text:
            return []

        results: List[Tuple[str, str, str]] = []
        cats_to_check = [category_filter] if category_filter and category_filter in self.categories else list(self.categories.keys())

        for cat_id in cats_to_check:
            if self.is_false_positive(clean_text, cat_id):
                continue

            cat = self.categories[cat_id]
            
            multi_word_terms = list(cat.get("high_context_phrases", []))
            single_word_terms = []

            # Process broad_terms and regional_aliases
            candidates = list(cat.get("broad_terms", []))
            for alias_list in cat.get("regional_aliases", {}).values():
                if isinstance(alias_list, list):
                    candidates.extend(alias_list)

            # Process legacy term lists if present
            for term_list_key in ("terms_en", "terms_hinglish", "terms_marathi", "coded_phrases"):
                candidates.extend(cat.get(term_list_key, []))

            for term in candidates:
                t = term.strip()
                if " " in t or "-" in t or "." in t:
                    multi_word_terms.append(t)
                else:
                    single_word_terms.append(t)

            # 1. Exact phrase matching (multi-word terms)
            for phrase in multi_word_terms:
                p_lower = phrase.lower()
                pattern = r"(?<!\w)" + re.escape(p_lower) + r"(?!\w)"
                if re.search(pattern, clean_text, re.IGNORECASE):
                    results.append((cat_id, phrase, "exact_phrase"))

            # 2. Broad term matching (single word tokens)
            if not exact_phrase_only:
                for term in single_word_terms:
                    t_lower = term.lower()
                    pattern = r"(?<!\w)" + re.escape(t_lower) + r"(?!\w)"
                    if re.search(pattern, clean_text, re.IGNORECASE):
                        results.append((cat_id, term, "broad_term"))

        # Deduplicate results by (cat_id, term)
        seen = set()
        deduped = []
        for r in results:
            key = (r[0], r[1].lower())
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        return deduped

    def redact_and_highlight(self, text: str, matched_term: str) -> Tuple[str, str]:
        """Scrub private identifiers (phones, emails, UPIs, accounts, usernames) and highlight matched term."""
        if not text:
            return "", ""

        # Step 1: Redact PII
        redacted = RE_EMAIL.sub("[REDACTED_EMAIL]", text)
        redacted = RE_UPI.sub("[REDACTED_PAYMENT_ID]", redacted)
        redacted = RE_PHONE.sub("[REDACTED_PHONE]", redacted)
        redacted = RE_BANK_ACCT.sub("[REDACTED_ACCT]", redacted)
        redacted = RE_TME.sub("[REDACTED_LINK]", redacted)
        redacted = RE_USERNAME.sub("[REDACTED_USER]", redacted)

        # Step 2: Highlight term safely
        highlighted = redacted
        if matched_term:
            term_esc = re.escape(matched_term)
            pattern = re.compile(rf"(?<!\w)({term_esc})(?!\w)", re.IGNORECASE)
            highlighted = pattern.sub(r"**[\1]**", redacted)

        return highlighted, redacted

    @staticmethod
    def get_attachment_bytes(dataset_zip_path: Path, image_ref: str) -> Optional[bytes]:
        """Safely read image bytes directly from ZIP in memory without disk extraction."""
        if not image_ref or not dataset_zip_path or not dataset_zip_path.exists():
            return None
        # Reject directory traversal attempts
        if ".." in image_ref or image_ref.startswith(("/", "\\")):
            return None
        ref_name = Path(image_ref).name.lower()
        try:
            with zipfile.ZipFile(dataset_zip_path, "r") as z:
                for name in z.namelist():
                    if Path(name).name.lower() == ref_name and name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        return z.read(name)
        except Exception:
            return None
        return None

    def search_committee_dataset(
        self,
        dataset_zip_path: Path,
        query_text: Optional[str] = None,
        category_filter: Optional[str] = None,
        exact_phrase_only: bool = False,
        platform_filter: Optional[str] = None,
        channel_filter: Optional[str] = None,
        has_image_only: bool = False,
        limit: int = 50,
    ) -> List[SearchMatch]:
        """Execute safe offline search across the official committee dataset ZIP.

        Extracts matching records with strictly redacted context and verified
        media resolution, adhering to Section 63 BSA audit standards.
        """
        zip_path = Path(dataset_zip_path)
        if not zip_path.exists():
            return []

        matches: List[SearchMatch] = []
        
        # Load available images in archive
        resolved_images: Set[str] = set()
        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()
            for n in names:
                if n.lower().endswith((".jpg", ".jpeg", ".png")):
                    resolved_images.add(Path(n).name.lower())

            # 1. Search Social Media CSVs (unless platform filter restricts to Telegram)
            include_social = not platform_filter or platform_filter.lower() in ("all", "social", "socialmedia", "instagram", "facebook", "twitter")
            if include_social:
                social_files = [n for n in names if "/02_social_media/" in n and n.endswith(".csv")]
                for s_file in social_files:
                    import csv
                    import io
                    content = z.read(s_file).decode("utf-8", errors="replace")
                    reader = csv.DictReader(io.StringIO(content))
                    for row in reader:
                        p_name = row.get("platform", "Social Media")
                        if platform_filter and platform_filter.lower() not in ("all", "social", "socialmedia") and platform_filter.lower() != p_name.lower():
                            continue

                        text_content = row.get("text", "")
                        if not text_content:
                            continue

                        img_file = row.get("image_file", "")
                        img_name = Path(img_file).name.lower() if img_file else ""
                        has_media = bool(img_name and img_name in resolved_images)

                        if has_image_only and not has_media:
                            continue

                        # Direct query string search if specified
                        if query_text:
                            q = query_text.strip().lower()
                            if exact_phrase_only:
                                pattern = r"(?<!\w)" + re.escape(q) + r"(?!\w)"
                                if not re.search(pattern, text_content, re.IGNORECASE):
                                    continue
                                match_tuples = [(category_filter or "custom_query", query_text, "exact_phrase")]
                            else:
                                if q not in text_content.lower():
                                    continue
                                match_tuples = [(category_filter or "custom_query", query_text, "broad_term")]
                        else:
                            match_tuples = self.search_text(
                                text_content,
                                category_filter=category_filter,
                                exact_phrase_only=exact_phrase_only,
                            )

                        if not match_tuples:
                            continue

                        for cat_id, term, m_type in match_tuples:
                            cat_label = self.categories.get(cat_id, {}).get("label", cat_id.replace("_", " ").title())
                            is_context = "weapon" in cat_id.lower()
                            high, raw = self.redact_and_highlight(text_content, term)
                            ts = row.get("posted_at_ist") or "Timestamp Not Available"

                            matches.append(SearchMatch(
                                category_id=cat_id,
                                category_label=cat_label,
                                matched_term=term,
                                match_type=m_type,
                                source_type="SocialMedia",
                                channel_or_platform=p_name,
                                timestamp_ist=ts,
                                highlighted_context=high,
                                raw_snippet=raw,
                                media_file=img_file if img_file and img_file.lower() != "none" else None,
                                media_resolved=has_media,
                                is_context_only=is_context,
                            ))
                            if len(matches) >= limit:
                                return matches

            # 2. Search Telegram JSON Exports (unless platform filter restricts to Social)
            include_telegram = not platform_filter or platform_filter.lower() in ("all", "telegram")
            if include_telegram:
                tg_files = [n for n in names if "/01_telegram_exports/" in n and n.endswith(".json")]
                for tg_file in tg_files:
                    try:
                        data = json.loads(z.read(tg_file).decode("utf-8", errors="replace"))
                    except Exception:
                        continue

                    ch_name = data.get("name", Path(tg_file).parent.name)
                    if channel_filter and channel_filter.lower() not in ch_name.lower():
                        continue

                    messages = data.get("messages", [])

                    for msg in messages:
                        if msg.get("type") != "message":
                            continue
                        text_val = msg.get("text", "")
                        if isinstance(text_val, list):
                            text_val = "".join(part if isinstance(part, str) else part.get("text", "") for part in text_val)

                        if not text_val or not isinstance(text_val, str):
                            continue

                        photo_ref = msg.get("photo", "")
                        photo_name = Path(photo_ref).name.lower() if photo_ref else ""
                        has_photo = bool(photo_name and photo_name in resolved_images)

                        if has_image_only and not has_photo:
                            continue

                        if query_text:
                            q = query_text.strip().lower()
                            if exact_phrase_only:
                                pattern = r"(?<!\w)" + re.escape(q) + r"(?!\w)"
                                if not re.search(pattern, text_val, re.IGNORECASE):
                                    continue
                                match_tuples = [(category_filter or "custom_query", query_text, "exact_phrase")]
                            else:
                                if q not in text_val.lower():
                                    continue
                                match_tuples = [(category_filter or "custom_query", query_text, "broad_term")]
                        else:
                            match_tuples = self.search_text(
                                text_val,
                                category_filter=category_filter,
                                exact_phrase_only=exact_phrase_only,
                            )

                        if not match_tuples:
                            continue

                        ts = msg.get("date") or "Timestamp Not Available"
                        if "T" in ts:
                            ts = ts.replace("T", " ") + " IST"

                        for cat_id, term, m_type in match_tuples:
                            cat_label = self.categories.get(cat_id, {}).get("label", cat_id.replace("_", " ").title())
                            is_context = "weapon" in cat_id.lower()
                            high, raw = self.redact_and_highlight(text_val, term)

                            matches.append(SearchMatch(
                                category_id=cat_id,
                                category_label=cat_label,
                                matched_term=term,
                                match_type=m_type,
                                source_type="Telegram",
                                channel_or_platform=ch_name,
                                timestamp_ist=ts,
                                highlighted_context=high,
                                raw_snippet=raw,
                                media_file=photo_ref if photo_ref else None,
                                media_resolved=has_photo,
                                is_context_only=is_context,
                            ))
                            if len(matches) >= limit:
                                return matches

        return matches
