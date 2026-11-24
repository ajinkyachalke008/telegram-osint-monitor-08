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


def test_alert_dedup_per_channel(temp_db):
    """Test that alert deduplication is keyed on (channel, normalized_text, category)."""
    # 1. Post in Channel A
    p1 = PostRecord(
        platform="telegram",
        channel_id="ch_a",
        message_id="101",
        timestamp_utc="2026-11-24T12:00:00Z",
        raw_text="Fresh ICICI bank account for rent commission 10%",
        normalized_text="fresh icici bank account for rent commission 10%",
        category="bank_account",
        risk_level="High",
        threat_score=8.5
    )
    temp_db.insert_post(p1)

    a1 = AlertRecord(
        alert_id="ALT-001",
        post_uid=p1.post_uid,
        category="bank_account",
        risk_level="High",
        threat_score=8.5,
        matched_terms=["icici", "rent", "bank account"]
    )
    # First alert in Channel A -> True (created)
    assert temp_db.create_alert(a1) is True

    # Duplicate post_uid -> False
    assert temp_db.create_alert(a1) is False

    # 2. Second post in Channel A with identical text and category -> False (deduped within channel)
    p2 = PostRecord(
        platform="telegram",
        channel_id="ch_a",
        message_id="102",
        timestamp_utc="2026-11-24T12:05:00Z",
        raw_text="Fresh ICICI bank account for rent commission 10%",
        normalized_text="fresh icici bank account for rent commission 10%",
        category="bank_account",
        risk_level="High",
        threat_score=8.5
    )
    temp_db.insert_post(p2)
    a2 = AlertRecord(
        alert_id="ALT-002",
        post_uid=p2.post_uid,
        category="bank_account",
        risk_level="High",
        threat_score=8.5,
        matched_terms=["icici", "rent", "bank account"]
    )
    assert temp_db.create_alert(a2) is False

    # 3. Third post in Channel B with IDENTICAL text and category -> True (different channel)
    p3 = PostRecord(
        platform="telegram",
        channel_id="ch_b",
        message_id="201",
        timestamp_utc="2026-11-24T12:10:00Z",
        raw_text="Fresh ICICI bank account for rent commission 10%",
        normalized_text="fresh icici bank account for rent commission 10%",
        category="bank_account",
        risk_level="High",
        threat_score=8.5
    )
    temp_db.insert_post(p3)
    a3 = AlertRecord(
        alert_id="ALT-003",
        post_uid=p3.post_uid,
        category="bank_account",
        risk_level="High",
        threat_score=8.5,
        matched_terms=["icici", "rent", "bank account"]
    )
    assert temp_db.create_alert(a3) is True


def test_inject_scripted_demo_post(temp_db):
    """Test that inject_scripted_demo_post executes full pipeline end-to-end."""
    from ingestion.demo_injector import inject_scripted_demo_post
    res = inject_scripted_demo_post(temp_db)
    assert res["alert_id"].startswith("ALT-")
    assert res["block_height"] >= 1
    assert len(res["current_hash"]) == 64
    assert res["category"] == "bank_account"
    assert res["risk_level"] in ("High", "Medium")
    # Verify post and alert exist in DB
    with temp_db.get_connection() as conn:
        post_row = conn.execute("SELECT * FROM posts WHERE post_uid = ?", (res["post_uid"],)).fetchone()
        assert post_row is not None
        assert "mule.syndicate@ybl" in post_row["raw_text"]
        alert_row = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (res["alert_id"],)).fetchone()
        assert alert_row is not None
        ident_row = conn.execute("SELECT * FROM identifiers WHERE identifier_id = 'upi:mule.syndicate@ybl'").fetchone()
        assert ident_row is not None


def test_operational_db_protected_from_reset_and_injection(tmp_path):
    """Operational DB must be strictly protected against reset, wipe, and synthetic injection."""
    from ingestion.demo_injector import inject_scripted_demo_post
    from scripts.generate_demo_data import seed_demo_database

    op_db = Database(tmp_path / "operational.db")
    with pytest.raises(PermissionError, match="strictly prohibited on operational.db"):
        op_db.reset_db()

    with pytest.raises(PermissionError, match="strictly prohibited on operational.db"):
        op_db.wipe_all_data()

    with pytest.raises(PermissionError, match="strictly prohibited on operational.db"):
        inject_scripted_demo_post(op_db)

    with pytest.raises(PermissionError, match="strictly prohibited on operational.db"):
        seed_demo_database(db=op_db, reset=True)


def test_default_db_path_selection(monkeypatch):
    """Verify DEFAULT_DB_PATH routes to demo.db when DEMO_MODE=1, else operational.db."""
    from core.db import get_default_db_path

    monkeypatch.delenv("DEMO_MODE", raising=False)
    assert get_default_db_path().name == "operational.db"

    monkeypatch.setenv("DEMO_MODE", "0")
    assert get_default_db_path().name == "operational.db"

    monkeypatch.setenv("DEMO_MODE", "1")
    assert get_default_db_path().name == "demo.db"


