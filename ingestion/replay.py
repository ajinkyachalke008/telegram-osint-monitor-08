"""Simulated Streaming Replay Engine for Live Demos.

Replays synthetic dataset (sample_data/synthetic_posts.json) into the unified database
at adjustable speed (posts per second), simulating a real-time Telegram monitoring feed.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import Database
from core.models import PostRecord, ChannelRecord, now_utc_iso
from core.normalizer import normalize_text
from addons.extractors import extract_all_entities
from addons.scorer import RuleScorer
from addons.evidence import build_evidence_record, EvidenceBlock

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("ingestion.replay")

SAMPLE_DATA_PATH = Path(__file__).parent.parent / "sample_data" / "synthetic_posts.json"
CHANNELS_DATA_PATH = Path(__file__).parent.parent / "sample_data" / "synthetic_channels.json"


def seed_synthetic_channels(db: Database):
    """Register demo channels into unified DB."""
    if CHANNELS_DATA_PATH.exists():
        with open(CHANNELS_DATA_PATH, "r", encoding="utf-8") as f:
            channels = json.load(f)
            for c in channels:
                db.upsert_channel(ChannelRecord(
                    channel_id=c.get("title", c.get("username")),
                    username=c.get("username", ""),
                    title=c.get("title", ""),
                    subscribers=c.get("subscribers", 1000),
                    risk_level=c.get("risk_level", "High")
                ))


def run_replay(speed_delay: float = 1.0, loop: bool = False, db: Optional[Database] = None):
    """
    Replay synthetic posts into unified database.
    delay: sleep in seconds between simulated posts.
    """
    database = db or Database()
    scorer = RuleScorer()
    seed_synthetic_channels(database)

    if not SAMPLE_DATA_PATH.exists():
        log.error("Synthetic demo data file not found: %s", SAMPLE_DATA_PATH)
        return

    with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
        demo_posts = json.load(f)

    log.info("Starting replay stream of %d demo posts (interval: %.1fs, loop=%s)", len(demo_posts), speed_delay, loop)

    iteration = 1
    while True:
        for idx, item in enumerate(demo_posts):
            ts = now_utc_iso()
            source = item.get("source", "Demo Channel")
            msg_id = f"demo_{iteration}_{item.get('post_id', idx+1)}"
            raw_text = item.get("text", "")
            norm_text = normalize_text(raw_text)

            # Ingest post
            post = PostRecord(
                platform=item.get("platform", "Telegram"),
                channel_id=source,
                message_id=msg_id,
                timestamp_utc=ts,
                raw_text=raw_text,
                normalized_text=norm_text,
                ingestion_source="SIMULATED"
            )

            # Extract & score
            extracted = extract_all_entities(norm_text)
            score_res = scorer.score(norm_text, identifiers=extracted)
            post.category = score_res.primary_category or "Clean"
            post.risk_level = score_res.risk_level
            post.threat_score = score_res.total_score

            inserted = database.insert_post(post)
            if inserted:
                # Link identifiers
                for ent in extracted.get("all_flat", []):
                    val = ent["value"]
                    etype = ent["type"]
                    ident_id = f"{etype.lower()}:{val}"
                    from core.models import IdentifierRecord
                    database.upsert_identifier(
                        IdentifierRecord(
                            identifier_id=ident_id,
                            type=etype,
                            raw_value=val,
                            normalized_value=val,
                            first_seen=ts,
                            last_seen=ts
                        ),
                        channel_id=source
                    )
                    database.link_post_identifier(post.post_uid, ident_id)
                    database.upsert_edge(source, ident_id, "mentions")

                # Chained Evidence
                from addons.evidence import build_chained_evidence_block
                ev_block = build_chained_evidence_block(database, post.post_uid, source, msg_id, ts, raw_text)
                database.record_evidence_block(ev_block)

                # Create Alert if actionable
                if score_res.is_actionable:
                    from core.models import AlertRecord
                    alert = AlertRecord(
                        alert_id=f"ALT-{ev_block.current_hash[:10].upper()}",
                        post_uid=post.post_uid,
                        category=post.category,
                        risk_level=post.risk_level,
                        threat_score=post.threat_score,
                        matched_terms=score_res.matched_terms,
                        status="new"
                    )
                    database.create_alert(alert)
                    log.warning("🚨 [REPLAY ALERT - %s] %s in %s (UPIs: %s)",
                                post.risk_level, post.category, source, extracted.get("upis"))
                else:
                    log.info("Replayed [CLEAN] post in %s", source)

            time.sleep(speed_delay)

        if not loop:
            break
        iteration += 1

    log.info("Replay stream completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay simulated Telegram stream into OSINT database.")
    parser.add_argument("--speed", type=float, default=1.0, help="Seconds delay between replayed posts (default: 1.0)")
    parser.add_argument("--loop", action="store_true", help="Loop indefinitely")
    args = parser.parse_args()

    run_replay(speed_delay=args.speed, loop=args.loop)
