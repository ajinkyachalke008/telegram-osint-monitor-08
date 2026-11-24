"""Near-Live Watchlist Poller for Public Broadcast Channels.

Periodically inspects top-ranked channels from watchlist.csv using `tgq preview`.
Requires NO user account, joins, or session credentials.
Surfaces near-live high-risk alerts and recommends the top critical channels
for the analyst to monitor inside TGSherlock Live Monitor.
"""
import csv
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from addons.extractors import extract_all_entities
from addons.scorer import RuleScorer
from addons.evidence import build_evidence_record
from discovery.finder import run_tgq_preview, WATCHLIST_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("discovery.monitor")


def load_top_watchlist(limit: int = 5, filepath: Optional[Path] = None) -> List[str]:
    """Read top prioritized channels from watchlist.csv."""
    p = filepath or WATCHLIST_FILE
    if not p.exists():
        log.warning("Watchlist file %s does not exist yet. Run finder.py first.", p)
        return []
    channels = []
    with open(p, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch = row.get("channel")
            if ch:
                channels.append(ch)
            if len(channels) >= limit:
                break
    return channels


def poll_watchlist_once(channels: List[str], scorer: Optional[RuleScorer] = None) -> List[Dict[str, Any]]:
    """Poll recent preview posts from each channel and return flagged alerts."""
    sc = scorer or RuleScorer()
    actionable_alerts = []

    for chan in channels:
        log.info("Polling preview for watchlist channel: @%s", chan)
        posts = run_tgq_preview(chan, limit=15)
        for p in posts:
            text = p.get("text", "")
            if not text:
                continue
            extracted = extract_all_entities(text)
            res = sc.score(text, identifiers=extracted)

            if res.is_actionable:
                alert = {
                    "channel": chan,
                    "post_id": p.get("id"),
                    "date": p.get("date"),
                    "risk_level": res.risk_level,
                    "category": res.primary_category,
                    "text": text[:200],
                    "extracted": extracted,
                    "evidence": build_evidence_record(
                        channel=chan,
                        message_id=p.get("id", 0),
                        timestamp=p.get("date"),
                        text=text,
                        matched_terms=res.matched_terms,
                        extracted_identifiers=extracted,
                        category=res.primary_category,
                        risk_level=res.risk_level,
                    )
                }
                actionable_alerts.append(alert)
                log.warning(
                    "🚨 [%s RISK] Detected in @%s: Category=%s, UPIs=%s, Phones=%s",
                    res.risk_level, chan, res.primary_category,
                    extracted.get("upis"), extracted.get("phones")
                )
        time.sleep(2.0)  # Gentle delay between requests

    return actionable_alerts


def start_monitor_loop(poll_interval_seconds: int = 60, iterations: int = 1):
    """Run scheduled near-live monitor loop."""
    top_channels = load_top_watchlist(limit=5)
    if not top_channels:
        log.info("No channels in watchlist. Using default test channels.")
        top_channels = ["durov", "telegram"]

    log.info("Starting near-live monitoring on %d channels: %s", len(top_channels), top_channels)
    scorer = RuleScorer()

    for i in range(iterations):
        log.info("--- Watchlist Poll Cycle %d/%d ---", i + 1, iterations)
        alerts = poll_watchlist_once(top_channels, scorer)
        log.info("Cycle %d complete. Actionable alerts found: %d", i + 1, len(alerts))
        if i + 1 < iterations:
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    start_monitor_loop(poll_interval_seconds=30, iterations=1)
