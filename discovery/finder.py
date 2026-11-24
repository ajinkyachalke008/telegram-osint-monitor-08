"""Public Telegram Channel Discovery and Snowball Expansion Engine.

Uses `tgq` CLI (read-only client):
1. Reads seed keywords from keywords.txt
2. Runs `tgq search` (or uses seed leads)
3. Fetches public channel web previews with `tgq preview` (no credentials or account required)
4. Scores messages with Phase 1 RuleScorer
5. Snowball Expansion (depth max 2): discovers new interconnected channels via forward origins (`fwd_from`)
6. Writes ranked `watchlist.csv` with threat scores and extracted illicit identifiers
"""
import csv
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Import detection add-ons
sys.path.insert(0, str(Path(__file__).parent.parent))
from addons.extractors import extract_all_entities
from addons.scorer import RuleScorer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("discovery.finder")

KEYWORDS_FILE = Path(__file__).parent / "keywords.txt"
WATCHLIST_FILE = Path(__file__).parent / "watchlist.csv"

# Resolve path to tgq executable in current virtual environment
VENV_TGQ = Path(__file__).parent.parent / ".venv" / "Scripts" / "tgq.exe"
TGQ_CMD = str(VENV_TGQ) if VENV_TGQ.exists() else "tgq"


def load_keywords(filepath: Optional[Path] = None) -> List[str]:
    """Load search query keywords from text file."""
    p = filepath or KEYWORDS_FILE
    if not p.exists():
        log.warning("Keywords file not found: %s", p)
        return ["mule khata", "current account rent", "desi katta", "nakli aadhar"]
    with open(p, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def run_tgq_search(query: str) -> List[Dict[str, Any]]:
    """
    Search for public channels matching query using `tgq search`.
    Note: Telegram global search is weak and returns limited results.
    """
    cmd = [TGQ_CMD, "search", query]
    log.info("Running search: %s", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode != 0:
            log.warning("tgq search returned code %d: %s", proc.returncode, proc.stderr.strip())
            return []
        results = []
        for line in proc.stdout.strip().splitlines():
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results
    except Exception as exc:
        log.warning("tgq search execution failed (%s). Notice: Telegram search is weak; results are leads, not proof.", exc)
        return []


def run_tgq_preview(channel_name: str, limit: int = 40) -> List[Dict[str, Any]]:
    """
    Fetch public channel web preview using `tgq preview <channel>`.
    Requires NO account, session, or credentials. Reads t.me/s/<channel>.
    """
    # Clean channel name
    clean_name = re.sub(r"^(?:https?://)?(?:t\.me|telegram\.me)/(?:s/)?", "", channel_name).strip("/@")
    if not clean_name:
        return []

    cmd = [TGQ_CMD, "preview", clean_name]
    log.info("Fetching public preview: %s", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        posts = []
        for line in proc.stdout.strip().splitlines():
            line = line.strip()
            if line:
                try:
                    posts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return posts[-limit:] if posts else []
    except Exception as exc:
        log.warning("tgq preview failed for '%s': %s", clean_name, exc)
        return []


def extract_forward_origins(posts: List[Dict[str, Any]]) -> Set[str]:
    """Extract forward origin channel usernames from preview message records."""
    fwd_channels = set()
    for p in posts:
        # Check standard tgq preview fields
        fwd_from = p.get("fwd_from")
        if isinstance(fwd_from, dict):
            chan = fwd_from.get("channel") or fwd_from.get("username")
            if chan:
                fwd_channels.add(str(chan).lstrip("@"))
        elif isinstance(fwd_from, str) and fwd_from.strip():
            fwd_channels.add(fwd_from.strip().lstrip("@"))

        # Also extract t.me links inside text that reference public channels
        txt = p.get("text", "")
        for match in re.finditer(r"(?:https?://)?t\.me/(?!joinchat|\+)([A-Za-z0-9_]{5,32})\b", txt):
            fwd_channels.add(match.group(1))

    return fwd_channels


def score_channel_posts(posts: List[Dict[str, Any]], scorer: RuleScorer) -> Dict[str, Any]:
    """Score all posts collected from a channel to evaluate its threat level."""
    total_score = 0.0
    actionable_count = 0
    high_count = 0
    categories = set()
    extracted_upis = set()
    extracted_phones = set()
    extracted_cryptos = set()
    sample_texts = []

    for p in posts:
        text = p.get("text", "")
        if not text:
            continue
        entities = extract_all_entities(text)
        res = scorer.score(text, identifiers=entities)

        if res.is_actionable:
            actionable_count += 1
            if res.risk_level == "High":
                high_count += 1
            total_score += res.total_score
            if res.primary_category:
                categories.add(res.primary_category)
            extracted_upis.update(entities.get("upis", []))
            extracted_phones.update(entities.get("phones", []))
            for c, _ in entities.get("crypto_wallets", []):
                extracted_cryptos.add(c)
            if len(sample_texts) < 2:
                sample_texts.append(text[:150])

    return {
        "total_posts": len(posts),
        "threat_score": round(total_score, 2),
        "actionable_posts": actionable_count,
        "high_risk_posts": high_count,
        "categories": sorted(list(categories)),
        "upis": sorted(list(extracted_upis)),
        "phones": sorted(list(extracted_phones)),
        "cryptos": sorted(list(extracted_cryptos)),
        "sample_text": " | ".join(sample_texts),
    }


def discover_and_snowball(
    seed_channels: Optional[List[str]] = None,
    max_depth: int = 2,
    max_channels: int = 25,
    delay_seconds: float = 2.0,
) -> List[Dict[str, Any]]:
    """
    Execute discovery loop:
    1. Search keywords
    2. Preview public channels
    3. Snowball expand forward origins up to depth max 2
    4. Rank channels by threat score
    """
    scorer = RuleScorer()
    keywords = load_keywords()
    log.info("DISCLAIMER: Telegram global search is weak and returns limited results. Results are OSINT leads, not definitive proof.")

    candidates: Set[str] = set()

    # Add any explicit seeds
    if seed_channels:
        for s in seed_channels:
            candidates.add(s.strip().lstrip("@"))

    # Try searching keywords with tgq
    for kw in keywords[:5]:  # Sweep top keywords
        search_res = run_tgq_search(kw)
        for r in search_res:
            un = r.get("username")
            if un:
                candidates.add(un.lstrip("@"))
        time.sleep(1.0)  # Respect rate limit

    # Fallback to realistic known seed public channels if search returns limited results
    if not candidates:
        log.info("Search returned few results (expected with public Telegram API search). Using baseline discovery seeds.")
        candidates.update(["durov", "telegram", "news_leak_india", "dark_market_p2p", "mule_cards_hub"])

    discovered_channels = {}
    visited = set()
    queue = [(c, 1) for c in candidates]  # (channel, depth)

    while queue and len(discovered_channels) < max_channels:
        channel, depth = queue.pop(0)
        channel = channel.strip().lstrip("@").lower()
        if channel in visited:
            continue
        visited.add(channel)

        log.info("Evaluating channel '%s' at depth %d/%d", channel, depth, max_depth)
        posts = run_tgq_preview(channel)
        channel_metrics = score_channel_posts(posts, scorer)
        channel_metrics["channel"] = channel
        channel_metrics["depth"] = depth
        discovered_channels[channel] = channel_metrics

        # Snowball Expansion (depth < max_depth)
        if depth < max_depth and posts:
            new_origins = extract_forward_origins(posts)
            for origin in new_origins:
                origin_clean = origin.strip().lstrip("@").lower()
                if origin_clean not in visited and len(discovered_channels) + len(queue) < max_channels:
                    queue.append((origin_clean, depth + 1))
                    log.info("Snowball lead discovered: %s (forwarded by %s)", origin_clean, channel)

        time.sleep(delay_seconds)  # Respect Telegram rate limits

    # Rank channels by threat score descending
    ranked = list(discovered_channels.values())
    ranked.sort(key=lambda x: (x["threat_score"], x["high_risk_posts"]), reverse=True)
    return ranked


def save_watchlist_csv(ranked_channels: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """Write ranked channels to watchlist.csv."""
    p = output_path or WATCHLIST_FILE
    fieldnames = [
        "channel", "threat_score", "high_risk_posts", "actionable_posts", "total_posts",
        "categories", "unique_upis", "unique_phones", "sample_snippet"
    ]
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in ranked_channels:
            writer.writerow({
                "channel": c["channel"],
                "threat_score": c["threat_score"],
                "high_risk_posts": c["high_risk_posts"],
                "actionable_posts": c["actionable_posts"],
                "total_posts": c["total_posts"],
                "categories": ", ".join(c.get("categories", [])),
                "unique_upis": ", ".join(c.get("upis", [])),
                "unique_phones": ", ".join(c.get("phones", [])),
                "sample_snippet": c.get("sample_text", "")[:120],
            })
    log.info("Watchlist saved to %s (%d channels)", p, len(ranked_channels))


if __name__ == "__main__":
    results = discover_and_snowball(max_depth=2, max_channels=10)
    save_watchlist_csv(results)
