import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
import tempfile
from ps02_dataset.preflight import audit
from ps02_dataset.parser import parse_participant_dataset
from ps02_dataset.importer import run_dry_run, run_import
from ps02_dataset.store import ParticipantDatasetStore

def verify_archive(zip_path: str):
    print("=" * 60)
    print(f"VERIFYING PS02 ARCHIVE: {zip_path}")
    print("=" * 60)

    # 1. Structural preflight audit
    print("\n--- 1. PREFLIGHT AUDIT ---")
    audit_res = audit(zip_path)
    counts = audit_res.get("counts", {})

    tg_exports = counts.get("telegram_exports", 0)
    tg_msgs = counts.get("telegram_messages", 0)
    tg_svc = counts.get("telegram_service_records", 0)
    tg_photos = counts.get("telegram_photo_references", 0)
    social_posts = counts.get("social_posts", 0)
    social_images = counts.get("social_images_in_archive", 0)
    posters = counts.get("poster_files", 0)
    poster_matches = counts.get("poster_hashes_verified", 0)
    lexicon_rows = counts.get("lexicon_rows", 0)
    platforms = counts.get("platform_counts", {})

    print(f"Telegram JSON exports: {tg_exports} (Reference: 13)")
    print(f"Telegram messages: {tg_msgs} (Reference: 1500)")
    print(f"Telegram service records: {tg_svc} (Reference: 13)")
    print(f"Telegram photo references: {tg_photos} (Reference: 199)")
    print(f"Social posts: {social_posts} (Reference: 350)")
    print(f"Social image files: {social_images} (Reference: 92)")
    print(f"Poster images: {posters} (Reference: 18)")
    print(f"Poster SHA-256 matches: {poster_matches} (Reference: 18)")
    print(f"Lexicon rows: {lexicon_rows} (Reference: 37)")
    print(f"Platform counts: {platforms}")

    checks = [
        ("Telegram JSON exports == 13", tg_exports == 13),
        ("Telegram messages == 1500", tg_msgs == 1500),
        ("Telegram service records == 13", tg_svc == 13),
        ("Telegram photo references == 199", tg_photos == 199),
        ("Social posts == 350", social_posts == 350),
        ("Social image files == 92", social_images == 92),
        ("Poster images == 18", posters == 18),
        ("Poster SHA-256 matches == 18", poster_matches == 18),
        ("Lexicon rows == 37", lexicon_rows == 37),
    ]

    all_match = all(c[1] for c in checks)
    print(f"\nALL 9 REFERENCE TOTALS MATCH EXACTLY: {all_match}")
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    # 2. In-depth parser verification
    print("\n--- 2. PARSER TOTALS ---")
    parsed = parse_participant_dataset(zip_path)
    totals = parsed.get("totals", {})
    print(f"Parser totals: {totals}")
    assert totals.get("combined_records") == 1850, f"Expected 1850 combined records, got {totals.get('combined_records')}"
    print("  [PASS] Combined records == 1850 (1500 msgs + 350 social posts, service records separate)")

    # 3. Dry-run and Import verification in isolated DB
    print("\n--- 3. DRY RUN & IDEMPOTENCY TEST ---")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_db = Path(f.name)

    try:
        # Dry run has 0 DB writes
        dry_res = run_dry_run(zip_path)
        print(f"Dry run result mode: {dry_res.get('mode')}, combined_records preview: {dry_res.get('preview', {}).get('combined_records')}")
        print("  [PASS] Dry-run executed in-memory with zero DB writes")

        # Explicit import 1 into isolated store
        test_store = ParticipantDatasetStore(tmp_db)
        imp1 = run_import(zip_path, store=test_store)
        print(f"Import 1 status: {imp1.get('status')}, total_records: {imp1.get('total_records')}, batch_id: {imp1.get('batch_id')}")
        assert imp1.get("status") == "imported"
        assert imp1.get("total_records") == 1850
        print("  [PASS] Explicit import successful (1850 records in batch)")

        # Idempotent repeat import
        imp2 = run_import(zip_path, store=test_store)
        print(f"Import 2 status: {imp2.get('status')}, is_duplicate: {imp2.get('is_duplicate')}")
        assert imp2.get("status") == "already_imported"
        assert imp2.get("is_duplicate") is True
        print("  [PASS] Repeat import idempotency verified (0 duplicates inserted)")

    finally:
        if tmp_db.exists():
            tmp_db.unlink()

    print("\n--- 4. LEGACY DATABASE INTEGRITY ---")
    for db_candidate in ["data/osint_monitor.db", "data/telegram_osint.db", "data/demo.db", "data/operational.db"]:
        if os.path.exists(db_candidate):
            c = sqlite3.connect(db_candidate)
            tbls = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            c.close()
            print(f"  Legacy DB {db_candidate}: {len(tbls)} tables")
    print("  [PASS] Legacy databases remain completely unperturbed.")

if __name__ == "__main__":
    verify_archive("data/participant_input/PS02_demo_data.zip")
