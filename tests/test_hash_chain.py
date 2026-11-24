"""Unit tests for Cryptographic Evidence Hash Chain."""
import pytest
from core.db import Database
from core.models import PostRecord
from addons.evidence import (
    build_chained_evidence_block,
    verify_evidence_chain,
    GENESIS_PREV_HASH,
    canonical_json,
    compute_sha256,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "chain_test.db"
    return Database(db_file)


def test_hash_chain_sequential_linking(temp_db):
    # Insert 3 posts and build chained evidence blocks
    for i in range(1, 4):
        p = PostRecord(platform="Telegram", channel_id="ch_chain", message_id=str(i), timestamp_utc="2026-11-24T12:00:00Z", raw_text=f"Ad {i}")
        temp_db.insert_post(p)
        blk = build_chained_evidence_block(temp_db, p.post_uid, p.channel_id, p.message_id, p.timestamp_utc, p.raw_text)
        temp_db.record_evidence_block(blk)

    blocks = temp_db.get_all_evidence_blocks()
    assert len(blocks) == 3

    # Check Block 1
    assert blocks[0]["block_height"] == 1
    assert blocks[0]["prev_hash"] == GENESIS_PREV_HASH

    # Check Block 2 links to Block 1
    assert blocks[1]["block_height"] == 2
    assert blocks[1]["prev_hash"] == blocks[0]["current_hash"]

    # Check Block 3 links to Block 2
    assert blocks[2]["block_height"] == 3
    assert blocks[2]["prev_hash"] == blocks[1]["current_hash"]

    # Verify entire chain passes
    valid, msg, count = verify_evidence_chain(blocks)
    assert valid is True
    assert count == 3


def test_hash_chain_tamper_detection(temp_db):
    for i in range(1, 4):
        p = PostRecord(platform="Telegram", channel_id="ch_tamper", message_id=str(i), timestamp_utc="2026-11-24T12:00:00Z", raw_text=f"Ad {i}")
        temp_db.insert_post(p)
        blk = build_chained_evidence_block(temp_db, p.post_uid, p.channel_id, p.message_id, p.timestamp_utc, p.raw_text)
        temp_db.record_evidence_block(blk)

    blocks = temp_db.get_all_evidence_blocks()

    # Tamper with block 2 canonical_json payload
    blocks[1]["canonical_json"] = '{"channel":"ch_tamper","message_id":"2","post_uid":"telegram_ch_tamper_2","text":"Tampered Legit Content","timestamp_utc":"2026-11-24T12:00:00Z"}'

    valid, msg, broken_idx = verify_evidence_chain(blocks)
    assert valid is False
    assert "Tampering detected at block 2" in msg
