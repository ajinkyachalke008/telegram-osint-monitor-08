"""Slang Suggester for OSINT Analysts.

Analyzes newly collected or flagged posts to identify frequent emerging terms,
slang, and coded expressions not yet present in lexicon.yaml.
Surfaces candidate keywords with frequency, category correlation, and confidence score.
"""
import re
from typing import Dict, List, Any, Optional
from collections import Counter
import yaml
from pathlib import Path

LEXICON_PATH = Path(__file__).resolve().parent.parent / "addons" / "lexicon.yaml"


class SlangSuggester:
    """Discovers candidate slang terms from suspicious or unflagged post tokens."""

    STOP_WORDS = {
        "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for", "with",
        "of", "or", "as", "by", "from", "that", "this", "it", "are", "be", "was",
        "have", "has", "had", "contact", "dm", "call", "ping", "telegram", "whatsapp",
        "available", "fresh", "stock", "rate", "best", "delivery", "urgent", "sale"
    }

    def __init__(self, lexicon_file: Optional[Path] = None):
        self.lexicon_file = lexicon_file or LEXICON_PATH
        self.existing_terms = self._load_existing_terms()

    def _load_existing_terms(self) -> set:
        terms = set()
        if self.lexicon_file.exists():
            with open(self.lexicon_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for cat, cdata in data.get("categories", {}).items():
                    for sec in ["slang_en", "slang_hinglish", "slang_marathi", "coded_words"]:
                        for t in cdata.get(sec, []):
                            terms.add(str(t).lower().strip())
        return terms

    def extract_candidates(self, posts: List[Dict[str, Any]], min_count: int = 2) -> List[Dict[str, Any]]:
        """
        Extracts candidate slang tokens from a list of post dicts (containing 'text' and optional 'category').
        Filters out known lexicon terms and common stopwords.
        """
        category_token_counts: Dict[str, Counter] = {}
        global_counts: Counter = Counter()

        for post in posts:
            text = post.get("text", "")
            cat = post.get("category", "unclassified")
            if cat not in category_token_counts:
                category_token_counts[cat] = Counter()

            # Tokenize words (ignoring URLs and mentions)
            clean_text = re.sub(r"https?://\S+|@\S+|\b\d+\b", " ", text.lower())
            tokens = re.findall(r"\b[a-z]{3,18}\b", clean_text)

            for tok in tokens:
                if tok in self.STOP_WORDS or tok in self.existing_terms:
                    continue
                category_token_counts[cat][tok] += 1
                global_counts[tok] += 1

        candidates = []
        for term, count in global_counts.most_common():
            if count < min_count:
                continue

            # Find top associated category
            best_cat = "unclassified"
            best_cat_count = 0
            for cat, c_counter in category_token_counts.items():
                if c_counter[term] > best_cat_count:
                    best_cat_count = c_counter[term]
                    best_cat = cat

            category_affinity = best_cat_count / count

            candidates.append({
                "term": term,
                "frequency": count,
                "top_associated_category": best_cat,
                "category_affinity": round(category_affinity, 2),
                "recommendation": "High Priority Review" if count >= 5 and category_affinity >= 0.7 else "Moderate Lead"
            })

        return candidates
