"""Evidence and Cryptographic Hash Chain Ledger for Law Enforcement OSINT Analysis.

Features:
- RFC-8785 deterministic canonical JSON serialization
- Cryptographic hash-chaining (current_hash = SHA256(canonical_payload + prev_hash))
- Block height indexing
- Tamper detection and chain validation routines
- PDF, JSON, and CSV export utilities
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List

from core.models import EvidenceBlock, now_utc_iso

GENESIS_PREV_HASH = "0" * 64


def canonical_json(data: Dict[str, Any]) -> str:
    """
    Produce RFC-8785 deterministic canonical JSON:
    - Sorted keys
    - Minimal whitespace (no trailing spaces or indentations)
    - UTF-8 representation
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_sha256(content: Union[str, bytes]) -> str:
    """Compute standard SHA-256 hex digest of string or byte buffer."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def hash_media_file(file_path: Optional[Union[str, Path]]) -> Optional[str]:
    """Compute SHA-256 hash of media attachment file on disk."""
    if not file_path:
        return None
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return None

    sha256 = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def normalize_utc_timestamp(dt: Union[str, datetime, None]) -> str:
    """Normalize timestamps to strict ISO-8601 UTC with 'Z' suffix."""
    if dt is None:
        return now_utc_iso()
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    dt_str = str(dt).strip()
    if dt_str.endswith("Z"):
        return dt_str
    try:
        parsed = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return dt_str


def build_evidence_record(
    channel: str,
    message_id: Union[int, str],
    timestamp: Union[str, datetime],
    text: str,
    matched_terms: Optional[list] = None,
    extracted_identifiers: Optional[dict] = None,
    media_path: Optional[Union[str, Path]] = None,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct a single-block evidence dictionary (backward compatible)."""
    ts_utc = normalize_utc_timestamp(timestamp)
    norm_channel = str(channel).strip()
    norm_msg_id = int(message_id) if str(message_id).isdigit() else str(message_id)
    norm_text = text or ""

    core_tuple = {
        "channel": norm_channel,
        "message_id": norm_msg_id,
        "text": norm_text,
        "timestamp_utc": ts_utc,
    }
    canonical_str = canonical_json(core_tuple)
    evidence_hash = compute_sha256(canonical_str)
    media_hash = hash_media_file(media_path)

    record = {
        "evidence_id": f"EV-{evidence_hash[:16].upper()}",
        "evidence_hash": evidence_hash,
        "canonical_payload": canonical_str,
        "core": core_tuple,
        "media": {
            "path": str(media_path) if media_path else None,
            "sha256": media_hash,
        },
        "analysis": {
            "category": category,
            "risk_level": risk_level,
            "matched_terms": matched_terms or [],
            "extracted_identifiers": extracted_identifiers or {},
        },
        "captured_at_utc": now_utc_iso(),
    }
    return record


def build_chained_evidence_block(
    db: Any,
    post_uid: str,
    channel: str,
    message_id: Union[int, str],
    timestamp: Union[str, datetime],
    text: str
) -> EvidenceBlock:
    """
    Construct a new EvidenceBlock chained cryptographically to the prior block:
    current_hash = SHA256(canonical_json + prev_hash)
    """
    ts_utc = normalize_utc_timestamp(timestamp)
    core_tuple = {
        "channel": str(channel).strip(),
        "message_id": str(message_id),
        "post_uid": str(post_uid),
        "text": text or "",
        "timestamp_utc": ts_utc,
    }
    canonical_str = canonical_json(core_tuple)

    # Fetch latest block from database
    latest_block = db.get_latest_evidence_block()
    if latest_block:
        prev_hash = latest_block["current_hash"]
        block_height = latest_block["block_height"] + 1
    else:
        prev_hash = GENESIS_PREV_HASH
        block_height = 1

    # Chained hash computation
    chained_payload = f"{canonical_str}:{prev_hash}"
    current_hash = compute_sha256(chained_payload)
    evidence_id = f"EV-BLK{block_height:06d}-{current_hash[:10].upper()}"

    return EvidenceBlock(
        evidence_id=evidence_id,
        post_uid=post_uid,
        canonical_json=canonical_str,
        current_hash=current_hash,
        prev_hash=prev_hash,
        block_height=block_height,
        generated_at_utc=now_utc_iso()
    )


def verify_evidence_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify single evidence record integrity."""
    core = record.get("core")
    if not core:
        return False, "Missing core fields in evidence record"
    expected_hash = record.get("evidence_hash")
    if not expected_hash:
        return False, "Missing evidence hash"

    recomputed = compute_sha256(canonical_json(core))
    if recomputed != expected_hash:
        return False, f"Hash mismatch: record={expected_hash}, recomputed={recomputed} (tampering detected)"
    return True, "Cryptographic integrity verified"


def verify_evidence_chain(blocks: List[Dict[str, Any]]) -> Tuple[bool, str, int]:
    """
    Verify the entire unbroken cryptographic chain of evidence blocks.
    Returns (is_valid, message, verified_count).
    """
    if not blocks:
        return True, "Chain is empty (valid)", 0

    expected_prev = GENESIS_PREV_HASH
    for idx, block in enumerate(blocks):
        height = block["block_height"]
        cur_hash = block["current_hash"]
        prev_hash = block["prev_hash"]
        canonical_str = block["canonical_json"]

        # 1. Height check
        if height != idx + 1:
            return False, f"Broken sequence at block index {idx}: expected height {idx+1}, got {height}", idx

        # 2. Previous hash linkage check
        if prev_hash != expected_prev:
            return False, f"Broken hash chain at block {height}: expected prev_hash {expected_prev}, got {prev_hash}", idx

        # 3. Recompute chained hash
        recomputed = compute_sha256(f"{canonical_str}:{prev_hash}")
        if recomputed != cur_hash:
            return False, f"Tampering detected at block {height}: expected {cur_hash}, recomputed {recomputed}", idx

        expected_prev = cur_hash

    return True, f"All {len(blocks)} evidence blocks cryptographically verified with unbroken chain", len(blocks)
