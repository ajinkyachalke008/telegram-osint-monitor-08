"""Run end-to-end live ingestion from real public Telegram channels into operational.db."""
import os
import sys
from pathlib import Path

# Ensure we use operational.db
os.environ["DEMO_MODE"] = "0"
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import Database
from core.models import ChannelRecord
from ingestion.adapters import TGQPreviewAdapter
from ingestion.worker import IngestionWorker
from addons.evidence import verify_evidence_chain


def main():
    db = Database("data/operational.db")
    print(f"=== OPERATIONAL DB: {db.db_path} ===")
    print(f"Initial state: posts={len(db.list_posts())}, alerts={len(db.list_alerts())}, evidence={len(db.get_all_evidence_blocks())}")

    adapter = TGQPreviewAdapter()
    worker = IngestionWorker(db=db)

    channels = ["telegram", "durov", "tginfo"]
    total_ingested = 0
    flagged_posts = []
    all_extracted_idents = []

    for chan in channels:
        print(f"\n--- Fetching live real broadcast from @{chan} ---")
        db.upsert_channel(ChannelRecord(channel_id=chan, username=chan, title=f"Public @{chan}", risk_level="Low"))
        posts = adapter.fetch_channel_posts(chan, limit=10)
        print(f"Retrieved {len(posts)} real messages from @{chan}")

        chan_ingested = 0
        for p in posts:
            p.ingestion_source = "LIVE"
            success = worker.process_and_persist_post(p)
            if success:
                chan_ingested += 1
                total_ingested += 1
                idents = db.get_post_identifiers(p.post_uid)
                for ident in idents:
                    all_extracted_idents.append(ident["identifier_id"])

                if p.risk_level in ("High", "Critical", "Medium") or (p.threat_score and p.threat_score > 0):
                    flagged_posts.append({
                        "channel": p.channel_id,
                        "msg_id": p.message_id,
                        "score": p.threat_score,
                        "risk": p.risk_level,
                        "category": p.category,
                        "text": p.raw_text[:120].replace("\n", " "),
                        "identifiers": [i["identifier_id"] for i in idents]
                    })
        print(f"Ingested {chan_ingested}/{len(posts)} posts into operational.db")

    print("\n=== INGESTION SUMMARY ===")
    print(f"Total real posts ingested: {total_ingested}")
    print(f"Total unique identifiers extracted: {len(set(all_extracted_idents))}")
    print(f"Extracted identifier samples: {list(set(all_extracted_idents))[:15]}")
    print(f"Total flagged posts: {len(flagged_posts)}")
    for f in flagged_posts:
        print(f"  - [{f['risk']} / {f['score']:.1f}] Channel: @{f['channel']} Msg #{f['msg_id']} Cat: {f['category']}")
        print(f"    Text: {f['text']}")
        print(f"    Identifiers: {f['identifiers']}")

    # Check evidence chain
    evidence_blocks = db.get_all_evidence_blocks()
    print(f"\nChained Evidence Blocks Created: {len(evidence_blocks)}")
    if evidence_blocks:
        print(f"Genesis Block 1: Hash={evidence_blocks[0]['current_hash'][:16]}... Prev={evidence_blocks[0]['prev_hash'][:16]}...")
        print(f"Latest Block {len(evidence_blocks)}: Hash={evidence_blocks[-1]['current_hash'][:16]}... Prev={evidence_blocks[-1]['prev_hash'][:16]}...")
        is_valid, msg, count = verify_evidence_chain(evidence_blocks)
        print(f"Cryptographic Evidence Chain Verification: {'PASSED (100% Intact - ' + msg + ')' if is_valid else f'FAILED: ' + msg}")

    # Check alerts
    alerts = db.list_alerts()
    print(f"\nAlerts created in operational.db: {len(alerts)}")
    for a in alerts:
        print(f"  - Alert {a['alert_id']}: [{a['risk_level']}] {a['category']} (Score: {a['threat_score']}) Terms: {a.get('matched_terms')}")

    # Check provenance counts
    with db.get_connection() as conn:
        prov = dict(conn.execute("SELECT ingestion_source, COUNT(*) FROM posts GROUP BY ingestion_source").fetchall())
    print(f"\nDatabase Row Provenance Breakdown: {prov}")


if __name__ == "__main__":
    main()
