"""End-to-end integration test for operational live ingestion pipeline."""
import pytest
from core.db import Database
from core.models import ChannelRecord, PostRecord
from ingestion.worker import IngestionWorker
from dashboard.db_reader import load_dashboard_data
from addons.evidence import verify_evidence_chain


def test_operational_pipeline_end_to_end(tmp_path):
    """Verify live posts process through worker, persist evidence blocks, and load into dashboard."""
    db_file = tmp_path / "operational.db"
    db = Database(db_file)

    # Setup channel
    db.upsert_channel(ChannelRecord(channel_id="telegram", title="Telegram News", risk_level="Low"))
    worker = IngestionWorker(db=db)

    # Simulate real-format live post retrieved via preview
    p1 = PostRecord(
        platform="Telegram",
        channel_id="telegram",
        message_id="460",
        timestamp_utc="2026-08-26T19:12:34+00:00",
        raw_text="For all the info from today's update and 13 years of Telegram features visit @BotFather.",
        ingestion_source="LIVE"
    )

    success = worker.process_and_persist_post(p1)
    assert success is True

    # Duplicate should be ignored idempotently
    assert worker.process_and_persist_post(p1) is False

    # Check database persistence
    posts = db.list_posts()
    assert len(posts) == 1
    assert posts[0]["message_id"] == "460"
    assert posts[0]["ingestion_source"] == "LIVE"

    # Check evidence chain
    evidence = db.get_all_evidence_blocks()
    assert len(evidence) == 1
    is_valid, msg, count = verify_evidence_chain(evidence)
    assert is_valid is True
    assert count == 1

    # Check dashboard reader loads this operational post
    dash_posts = load_dashboard_data(db=db)
    assert len(dash_posts) == 1
    assert dash_posts[0]["post_id"] == "460"
    assert dash_posts[0]["source"] == "telegram"
