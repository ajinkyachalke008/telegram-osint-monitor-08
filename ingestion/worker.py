"""Background Continuous Ingestion Worker Process.

Coordinates ingestion from:
1. Live TGSherlock SQLite database (when Telegram account is active)
2. TGQ Preview Watchlist Poller (for public broadcast channels)
Runs text normalization, identifier extraction, threat scoring,
evidence hash-chaining, and alert generation.
"""
import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import Database
from core.models import PostRecord, IdentifierRecord, AlertRecord, now_utc_iso
from core.normalizer import normalize_text
from ingestion.adapters import TGSherlockAdapter, TGQPreviewAdapter
from addons.extractors import extract_all_entities
from addons.scorer import RuleScorer
from addons.evidence import build_chained_evidence_block
from discovery.finder import WATCHLIST_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("ingestion.worker")


class IngestionWorker:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.tg_adapter = TGSherlockAdapter()
        self.tgq_adapter = TGQPreviewAdapter()
        self.scorer = RuleScorer()

    def process_and_persist_post(self, post: PostRecord) -> bool:
        """Run normalization, extraction, scoring, hash-chaining, and persistence."""
        post.normalized_text = normalize_text(post.raw_text)

        # Extraction & Scoring
        extracted = extract_all_entities(post.normalized_text)
        score_res = self.scorer.score(post.normalized_text, identifiers=extracted)
        post.category = score_res.primary_category or "Clean"
        post.risk_level = score_res.risk_level
        post.threat_score = score_res.total_score

        # 1. Idempotent Post Insertion
        inserted = self.db.insert_post(post)
        if not inserted:
            return False  # Already processed

        # 2. Persist & Link Identifiers
        for ent in extracted.get("all_flat", []):
            val = ent["value"]
            etype = ent["type"]
            ident_id = f"{etype.lower()}:{val}"
            self.db.upsert_identifier(
                IdentifierRecord(
                    identifier_id=ident_id,
                    type=etype,
                    raw_value=val,
                    normalized_value=val,
                    first_seen=post.timestamp_utc,
                    last_seen=post.timestamp_utc
                ),
                channel_id=post.channel_id
            )
            self.db.link_post_identifier(post.post_uid, ident_id)
            self.db.upsert_edge(post.channel_id, ident_id, "mentions")

        # 3. Hash Chained Evidence
        ev_block = build_chained_evidence_block(
            self.db, post.post_uid, post.channel_id, post.message_id, post.timestamp_utc, post.raw_text
        )
        self.db.record_evidence_block(ev_block)

        # 4. Create Alert if Actionable
        if score_res.is_actionable:
            alert = AlertRecord(
                alert_id=f"ALT-{ev_block.current_hash[:10].upper()}",
                post_uid=post.post_uid,
                category=post.category,
                risk_level=post.risk_level,
                threat_score=post.threat_score,
                matched_terms=score_res.matched_terms,
                status="new"
            )
            self.db.create_alert(alert)
            log.warning("🚨 [LIVE ALERT - %s] %s in %s (UPIs: %s, Phones: %s)",
                        post.risk_level, post.category, post.channel_id,
                        extracted.get("upis"), extracted.get("phones"))
        return True

    def poll_tgsherlock_live(self):
        """Poll incoming messages from local TGSherlock DB."""
        posts = self.tg_adapter.read_recent_posts(limit=50)
        new_count = sum(1 for p in posts if self.process_and_persist_post(p))
        if new_count > 0:
            log.info("Ingested %d new live posts from TGSherlock", new_count)

    def poll_watchlist_preview(self):
        """Poll preview posts from watchlist.csv."""
        if not WATCHLIST_FILE.exists():
            return
        import csv
        top_channels = []
        with open(WATCHLIST_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                ch = r.get("channel")
                if ch:
                    top_channels.append(ch)
                if len(top_channels) >= 5:
                    break

        for ch in top_channels:
            posts = self.tgq_adapter.fetch_channel_posts(ch, limit=15)
            new_count = sum(1 for p in posts if self.process_and_persist_post(p))
            if new_count > 0:
                log.info("Ingested %d new posts from watchlist preview @%s", new_count, ch)
            time.sleep(1.0)

    def run_loop(self, poll_interval: int = 15):
        log.info("Starting OSINT Live Ingestion Worker (interval: %ds)...", poll_interval)
        while True:
            try:
                self.poll_tgsherlock_live()
                self.poll_watchlist_preview()
            except Exception as exc:
                log.error("Worker error during poll cycle: %s", exc)
            time.sleep(poll_interval)


# Alias for backward-compatibility
PipelineWorker = IngestionWorker



if __name__ == "__main__":
    worker = IngestionWorker()
    worker.run_loop(poll_interval=15)
