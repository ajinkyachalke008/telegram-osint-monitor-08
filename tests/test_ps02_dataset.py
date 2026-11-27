"""Comprehensive tests for PS02 Dataset Preflight, Parser, Store, and Importer."""

import json
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from ps02_dataset.preflight import (
    safe_zip,
    discover_root_prefix,
    audit,
    MAX_ENTRIES,
    MAX_MEMBER,
)
from ps02_dataset.parser import parse_ist_timestamp, parse_participant_dataset
from ps02_dataset.store import ParticipantDatasetStore
from ps02_dataset.importer import run_dry_run, run_import


def test_safe_zip_security():
    """Verify safe_zip rejects directory traversal and illegal paths."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "malicious.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("../etc/passwd", "evil")
        with zipfile.ZipFile(p) as z:
            with pytest.raises(ValueError, match="Unsafe ZIP member path"):
                safe_zip(z)


def test_discover_root_prefix():
    """Verify root discovery handles top-level and direct directories."""
    names_direct = {
        "01_telegram_exports/ch1/result.json",
        "02_social_media/posts.csv",
        "03_images/images_index.csv",
        "04_lexicon/starter_slang_lexicon.csv",
    }
    assert discover_root_prefix(names_direct) == ""

    names_prefixed = {
        "PS02_demo_data/01_telegram_exports/ch1/result.json",
        "PS02_demo_data/02_social_media/posts.csv",
        "PS02_demo_data/03_images/images_index.csv",
        "PS02_demo_data/04_lexicon/starter_slang_lexicon.csv",
    }
    assert discover_root_prefix(names_prefixed) == "PS02_demo_data/"


def test_parse_ist_timestamp():
    """Verify timestamp parsing assigns Asia/Kolkata timezone (+05:30)."""
    dt = parse_ist_timestamp("2026-10-27 22:46:22")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.hour == 22
    assert dt.utcoffset().total_seconds() == 19800  # +05:30

    # Unix timestamp
    dt_unix = parse_ist_timestamp("1788234137")
    assert dt_unix is not None
    assert dt_unix.utcoffset().total_seconds() == 19800

    # Invalid timestamp
    assert parse_ist_timestamp("") is None
    assert parse_ist_timestamp("not_a_date") is None


def test_dry_run_and_idempotent_import_on_actual_zip():
    """Verify dry-run performs 0 DB writes and import is fully idempotent."""
    zip_path = Path("data/participant_input/PS02_demo_data-20261127T071007Z-1-001.zip")
    if not zip_path.exists():
        pytest.skip("Local participant ZIP not available in environment")

    with tempfile.TemporaryDirectory() as d:
        test_db_path = Path(d) / "test_participant.db"
        store = ParticipantDatasetStore(test_db_path)

        # 1. Test Dry-Run: must not write anything to DB
        dry_res = run_dry_run(zip_path)
        assert dry_res["mode"] == "dry_run"
        assert dry_res["passed"] is True
        assert dry_res["preview"]["total_messages"] == 1500
        assert dry_res["preview"]["total_services"] == 13
        assert dry_res["preview"]["total_social_posts"] == 350
        assert dry_res["preview"]["combined_records"] == 1850
        assert dry_res["preview"]["poster_hashes_verified"] == 18

        # Verify DB is still completely empty
        assert store.get_latest_batch() is None

        # 2. Test Import 1: must persist records cleanly
        imp_res_1 = run_import(zip_path, store=store)
        assert imp_res_1["status"] == "imported"
        assert imp_res_1["is_duplicate"] is False
        batch_id = imp_res_1["batch_id"]

        # Check DB state
        latest = store.get_latest_batch()
        assert latest is not None
        assert latest["batch_id"] == batch_id
        assert latest["total_records"] == 1850

        # Check platforms
        breakdown = store.get_platform_breakdown(batch_id)
        platforms_dict = {b["platform"]: b["total_posts"] for b in breakdown}
        assert platforms_dict["Telegram"] == 1500
        assert platforms_dict["Instagram"] == 126
        assert platforms_dict["Facebook"] == 88
        assert platforms_dict["ShareChat"] == 52
        assert platforms_dict["X"] == 48
        assert platforms_dict["YouTube comment"] == 36

        # Check posters
        posters = store.get_poster_records(batch_id)
        assert len(posters) == 18
        assert all(p["status"] == "verified" for p in posters)

        # Check privacy / security constraint: verify NO raw message text in database!
        conn = sqlite3.connect(test_db_path)
        try:
            cursor = conn.cursor()
            tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            for tbl in tables:
                col_names = [col[1] for col in cursor.execute(f"PRAGMA table_info({tbl})").fetchall()]
                assert "raw_text" not in col_names
                assert "author_name" not in col_names
                assert "phone_number" not in col_names
                assert "upi_id" not in col_names
        finally:
            conn.close()

        # 3. Test Import 2 (Idempotency): must recognize existing batch and NOT double-insert
        imp_res_2 = run_import(zip_path, store=store)
        assert imp_res_2["status"] == "already_imported"
        assert imp_res_2["is_duplicate"] is True
        assert imp_res_2["batch_id"] == batch_id

        # Verify record totals remain exact, not doubled!
        breakdown_after = store.get_platform_breakdown(batch_id)
        platforms_after = {b["platform"]: b["total_posts"] for b in breakdown_after}
        assert platforms_after["Telegram"] == 1500
        assert platforms_after["Instagram"] == 126
