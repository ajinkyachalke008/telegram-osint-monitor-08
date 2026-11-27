"""Dry-run and transactional importer for PS02 Hackathon dataset.

Enforces:
1. Zero DB writes during dry-run
2. Transactional execution with rollback on failure
3. Duplicate import detection (idempotent re-import)
4. Batch provenance preservation
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from ps02_dataset.preflight import audit
from ps02_dataset.parser import parse_participant_dataset
from ps02_dataset.store import ParticipantDatasetStore, DEFAULT_PARTICIPANT_DB_PATH

IST = timezone(timedelta(hours=5, minutes=30))


def run_dry_run(source_path: Path) -> Dict[str, Any]:
    """Execute read-only preflight validation and parse preview with zero DB writes."""
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {source_path}")

    # 1. Structural preflight audit
    audit_res = audit(source_path)

    # 2. Parse aggregates in memory
    parsed_res = parse_participant_dataset(source_path)

    return {
        "mode": "dry_run",
        "timestamp_ist": datetime.now(IST).isoformat(),
        "source": str(source_path.name),
        "audit": audit_res,
        "preview": {
            "telegram_channels_count": len(parsed_res.get("telegram_channels", [])),
            "social_platforms_count": len(parsed_res.get("social_platforms", [])),
            "total_messages": parsed_res.get("totals", {}).get("telegram_messages", 0),
            "total_services": parsed_res.get("totals", {}).get("telegram_services", 0),
            "total_social_posts": parsed_res.get("totals", {}).get("social_posts", 0),
            "combined_records": parsed_res.get("totals", {}).get("combined_records", 0),
            "poster_hashes_verified": audit_res.get("counts", {}).get("poster_hashes_verified", 0),
            "poster_index_rows": audit_res.get("counts", {}).get("poster_index_rows", 0),
            "lexicon_rows": audit_res.get("counts", {}).get("lexicon_rows", 0),
        },
        "passed": audit_res.get("passed", False),
    }


def run_import(
    source_path: Path,
    store: Optional[ParticipantDatasetStore] = None,
    force_reimport: bool = False,
) -> Dict[str, Any]:
    """Execute safe transactional import with duplicate prevention and audit receipt."""
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {source_path}")

    if store is None:
        store = ParticipantDatasetStore(DEFAULT_PARTICIPANT_DB_PATH)

    # 1. Preflight audit
    audit_res = audit(source_path)
    archive_sha256 = audit_res.get("archive_metadata", {}).get("sha256", "")
    archive_size = audit_res.get("archive_metadata", {}).get("size_bytes", 0)
    archive_name = source_path.name

    # 2. Check for existing batch (Idempotency check)
    existing_batch = store.get_batch_by_hash(archive_sha256)
    if existing_batch and not force_reimport:
        return {
            "status": "already_imported",
            "message": "Archive already imported with identical SHA-256 digest (idempotent no-op).",
            "batch_id": existing_batch["batch_id"],
            "imported_at_ist": existing_batch["imported_at_ist"],
            "total_records": existing_batch["total_records"],
            "archive_sha256": archive_sha256,
            "is_duplicate": True,
            "audit": audit_res,
        }

    # 3. Parse dataset into aggregate representations
    parsed_res = parse_participant_dataset(source_path)

    # 4. Generate stable batch identifier
    hash_prefix = archive_sha256[:8] if archive_sha256 else "offline"
    ts_compact = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    batch_id = f"BATCH-PS02-{hash_prefix}-{ts_compact}"

    # 5. Persist inside atomic transaction
    saved_id = store.save_batch(
        batch_id=batch_id,
        archive_name=archive_name,
        archive_sha256=archive_sha256,
        archive_size_bytes=archive_size,
        audit_result=audit_res,
        parsed_data=parsed_res,
    )

    return {
        "status": "imported",
        "message": f"Successfully imported batch {saved_id} into isolated database.",
        "batch_id": saved_id,
        "imported_at_ist": datetime.now(IST).isoformat(),
        "total_records": parsed_res.get("totals", {}).get("combined_records", 0),
        "archive_sha256": archive_sha256,
        "is_duplicate": False,
        "audit": audit_res,
        "summary": {
            "telegram_messages": parsed_res.get("totals", {}).get("telegram_messages", 0),
            "telegram_services": parsed_res.get("totals", {}).get("telegram_services", 0),
            "social_posts": parsed_res.get("totals", {}).get("social_posts", 0),
            "poster_hashes_verified": audit_res.get("counts", {}).get("poster_hashes_verified", 0),
        }
    }
