"""Unit tests for Workstream A Unified SQLite Database."""
import tempfile
from pathlib import Path
import pytest

from core.db import Database
from core.models import ChannelRecord, PostRecord, IdentifierRecord, EvidenceBlock, AlertRecord


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_osint.db"
    return Database(db_file)


def test_db_wal_mode_and_init(temp_db):
    with temp_db.get_connection() as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.upper() == "WAL"
        # Check tables exist
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "posts" in tables
        assert "channels" in tables
        assert "identifiers" in tables
        assert "post_identifiers" in tables
        assert "evidence" in tables
        assert "alerts" in tables
        assert "entities_edges" in tables


def test_idempotent_post_insertion(temp_db):
    ch = ChannelRecord(channel_id="chan_01", title="Test Channel")
    temp_db.upsert_channel(ch)

    post1 = PostRecord(
        platform="Telegram",
        channel_id="chan_01",
        message_id="100",
        timestamp_utc="2026-11-24T12:00:00Z",
        raw_text="Khata for rent",
        ingestion_source="LIVE"
    )
    # First insert -> True
    assert temp_db.insert_post(post1) is True

    # Second insert with exact same platform, channel_id, message_id -> False (idempotent ignore)
    assert temp_db.insert_post(post1) is False

    # Verify single row exists
    posts = temp_db.list_posts()
    assert len(posts) == 1


def test_cross_channel_identifier_linking(temp_db):
    ch1 = ChannelRecord(channel_id="ch_a", title="Channel A")
    ch2 = ChannelRecord(channel_id="ch_b", title="Channel B")
    temp_db.upsert_channel(ch1)
    temp_db.upsert_channel(ch2)

    p1 = PostRecord(platform="Telegram", channel_id="ch_a", message_id="1", timestamp_utc="2026-11-24T10:00:00Z", raw_text="Post 1")
    p2 = PostRecord(platform="Telegram", channel_id="ch_b", message_id="2", timestamp_utc="2026-11-24T11:00:00Z", raw_text="Post 2")
    temp_db.insert_post(p1)
    temp_db.insert_post(p2)

    ident = IdentifierRecord(
        identifier_id="upi:demo.seller@ybl",
        type="UPI",
        raw_value="demo.seller@ybl",
        normalized_value="demo.seller@ybl"
    )
    temp_db.upsert_identifier(ident, channel_id="ch_a")
    temp_db.link_post_identifier(p1.post_uid, ident.identifier_id)

    # In 1 channel: cross_channel is 0
    with temp_db.get_connection() as conn:
        row = conn.execute("SELECT cross_channel, channel_count FROM identifiers WHERE identifier_id = ?", (ident.identifier_id,)).fetchone()
        assert row["cross_channel"] == 0
        assert row["channel_count"] == 1

    # Link to second channel's post
    temp_db.link_post_identifier(p2.post_uid, ident.identifier_id)

    # In 2 channels: cross_channel is 1!
    with temp_db.get_connection() as conn:
        row = conn.execute("SELECT cross_channel, channel_count FROM identifiers WHERE identifier_id = ?", (ident.identifier_id,)).fetchone()
        assert row["cross_channel"] == 1
        assert row["channel_count"] == 2

    # Query helper
    cross_list = temp_db.list_cross_channel_identifiers()
    assert len(cross_list) == 1
    assert "ch_a" in cross_list[0]["linked_channels"]
    assert "ch_b" in cross_list[0]["linked_channels"]


def test_evidence_hash_chain_storage(temp_db):
    p = PostRecord(platform="Telegram", channel_id="ch_a", message_id="5", timestamp_utc="2026-11-24T12:00:00Z", raw_text="Test")
    temp_db.insert_post(p)

    ev = EvidenceBlock(
        evidence_id="EV-TEST-1",
        post_uid=p.post_uid,
        canonical_json='{"channel":"ch_a","message_id":"5"}',
        current_hash="abc123hash",
        prev_hash="0"*64,
        block_height=1
    )
    temp_db.record_evidence_block(ev)

    latest = temp_db.get_latest_evidence_block()
    assert latest is not None
    assert latest["evidence_id"] == "EV-TEST-1"
    assert latest["block_height"] == 1
