import csv
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from ingestion.ps02_dataset import (
    PS02DatasetError,
    PS02DatasetReader,
    flatten_telegram_text,
    safe_child,
    safe_extract_zip,
    to_utc_iso,
)


def make_minimal_dataset(root: Path) -> Path:
    telegram_dir = root / "01_telegram_exports" / "ch01"
    telegram_dir.mkdir(parents=True)
    (telegram_dir / "photos").mkdir()
    image_bytes = b"same synthetic image bytes"
    (telegram_dir / "photos" / "poster.jpg").write_bytes(image_bytes)

    telegram = {
        "name": "Synthetic Channel",
        "type": "public_channel",
        "id": "channel123",
        "messages": [
            {"id": 1, "type": "service", "date": "2026-10-01T00:00:00", "text": "created"},
            {
                "id": 2,
                "type": "message",
                "date": "2026-10-01T12:00:00",
                "date_unixtime": "1790856000",
                "from": "Synthetic Sender",
                "from_id": "user123",
                "text": [
                    {"type": "plain", "text": "Fresh "},
                    {"type": "mention", "text": "@demo_seller"},
                    {"type": "plain", "text": " available"},
                ],
                "text_entities": [
                    {"type": "plain", "text": "Fresh "},
                    {"type": "mention", "text": "@demo_seller"},
                    {"type": "plain", "text": " available"},
                ],
                "photo": "photos/poster.jpg",
                "forwarded_from": "Another Sample Channel",
                "edited": "2026-10-01T13:00:00",
                "edited_unixtime": "1790859600",
            },
        ],
    }
    (telegram_dir / "result.json").write_text(json.dumps(telegram), encoding="utf-8")

    social_dir = root / "02_social_media"
    (social_dir / "images").mkdir(parents=True)
    (social_dir / "images" / "social.jpg").write_bytes(image_bytes)
    social_rows = [{
        "post_id": "social_1",
        "platform": "Instagram",
        "author": "sample_author",
        "posted_at_ist": "2026-10-01T12:00:00",
        "text": "Synthetic post body",
        "hashtags": "#sample #demo",
        "image_file": "images/social.jpg",
        "location_tag": "Jaipur",
        "likes": 12,
        "comments": 3,
    }]
    (social_dir / "posts.json").write_text(json.dumps(social_rows), encoding="utf-8")

    poster_dir = root / "03_images" / "posters"
    poster_dir.mkdir(parents=True)
    (poster_dir / "P01.jpg").write_bytes(image_bytes)
    poster_hash = hashlib.sha256(image_bytes).hexdigest()
    with (root / "03_images" / "images_index.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image", "sha256"])
        writer.writeheader()
        writer.writerow({"image": "P01.jpg", "sha256": poster_hash})

    lexicon_dir = root / "04_lexicon"
    lexicon_dir.mkdir(parents=True)
    with (lexicon_dir / "starter_slang_lexicon.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["term", "category"])
        writer.writeheader()
        writer.writerow({"term": "sample term", "category": "drugs"})

    reference_dir = root / "05_reference"
    reference_dir.mkdir(parents=True)
    (reference_dir / "real_reported_channels.csv").write_text("name,url\n", encoding="utf-8")
    return root


def test_flatten_telegram_text_preserves_entity_segment_order():
    value = [
        "text before ",
        {"type": "mention", "text": "@sample_user"},
        {"type": "plain", "text": " and after"},
    ]
    assert flatten_telegram_text(value) == "text before @sample_user and after"
    assert flatten_telegram_text("plain message") == "plain message"


def test_timestamp_conversion_uses_epoch_and_ist():
    assert to_utc_iso("2026-10-01T12:00:00") == "2026-10-01T06:30:00Z"
    assert to_utc_iso("1790856000", unix_epoch=True) == "2026-10-01T12:00:00Z"


def test_safe_child_rejects_path_traversal(tmp_path):
    with pytest.raises(PS02DatasetError):
        safe_child(tmp_path, "../outside.txt")


def test_safe_zip_extraction_rejects_traversal(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("../outside.txt", "blocked")
    with pytest.raises(PS02DatasetError):
        safe_extract_zip(archive, tmp_path / "unpacked")


def test_ps02_reader_audits_and_parses_both_primary_sources(tmp_path):
    root = make_minimal_dataset(tmp_path / "PS02_demo_data")
    reader = PS02DatasetReader(root, ocr_enabled=False)
    audit = reader.audit()

    assert audit["telegram_export_count"] == 1
    assert audit["telegram_posts"] == 1
    assert audit["telegram_photo_references"] == 1
    assert audit["missing_telegram_photos"] == []
    assert audit["social_posts"] == 1
    assert audit["social_photo_references"] == 1
    assert audit["missing_social_photos"] == []
    assert audit["verified_poster_hashes"] == 1
    assert audit["poster_hash_mismatches"] == []
    assert audit["total_posts"] == 2

    posts = list(reader.iter_posts())
    assert len(posts) == 2
    telegram_post = posts[0]
    assert telegram_post["raw_text"] == "Fresh @demo_seller available"
    assert telegram_post["channel_id"] == "Telegram:channel123"
    assert telegram_post["source_metadata"]["forwarded_from"] == "Another Sample Channel"
    assert telegram_post["source_metadata"]["edited_at"] == "2026-10-01T13:00:00"
    assert telegram_post["source_metadata"]["provenance"] == "HACKATHON_SAMPLE"
    assert telegram_post["media_hash"] == hashlib.sha256(b"same synthetic image bytes").hexdigest()

    social_post = posts[1]
    assert social_post["timestamp_utc"] == "2026-10-01T06:30:00Z"
    assert social_post["source_metadata"]["location_tag"] == "Jaipur"
    assert social_post["source_metadata"]["analysis_text"] == "#sample #demo"


def test_import_into_worker_keeps_hackathon_provenance_and_excludes_references(tmp_path):
    root = make_minimal_dataset(tmp_path / "PS02_demo_data")
    reader = PS02DatasetReader(root, ocr_enabled=False)

    class FakeDB:
        def __init__(self):
            self.channels = []
            self.audit_entries = []

        def upsert_channel(self, channel):
            self.channels.append(channel.channel_id)

        def log_audit(self, action, details):
            self.audit_entries.append((action, details))

    class FakeWorker:
        def __init__(self):
            self.db = FakeDB()
            self.records = []

        def process_raw_post(self, **kwargs):
            self.records.append(kwargs)
            return True

    worker = FakeWorker()
    result = reader.import_into_worker(worker)

    assert result["total_records"] == 2
    assert result["inserted"] == 2
    assert result["failures"] == 0
    assert result["masked_repository_ingested"] is False
    assert result["reference_channels_ingested"] is False
    assert {row["ingestion_source"] for row in worker.records} == {"HACKATHON_SAMPLE"}
    assert len(worker.db.channels) == 2
    assert worker.db.audit_entries[0][0] == "ps02_dataset_import"



def test_safe_child_rejects_windows_drive_paths(tmp_path):
    with pytest.raises(PS02DatasetError):
        safe_child(tmp_path, r"C:\\Windows\\system.ini")
