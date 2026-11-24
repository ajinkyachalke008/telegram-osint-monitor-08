"""Evidence and Chain of Custody Module for Law Enforcement OSINT Analysis.

Generates immutable forensic packages for flagged posts:
- Canonical JSON serialization of core evidence: (channel, message_id, timestamp_utc, text)
- Deterministic SHA-256 evidence digest
- Cryptographic hash (SHA-256) of media attachments if present
- Tamper verification routines
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Union


def canonical_json(data: Dict[str, Any]) -> str:
    """
    Produce RFC-8785 style deterministic canonical JSON:
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
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # If already a string, parse or format standard
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
    """
    Construct a forensically verifiable Evidence Record:
    Stores core immutable fields + canonical JSON hash + media hash.
    """
    ts_utc = normalize_utc_timestamp(timestamp)
    norm_channel = str(channel).strip()
    norm_msg_id = int(message_id) if str(message_id).isdigit() else str(message_id)
    norm_text = text or ""

    # The Core 4 immutable tuple for cryptographic integrity verification
    core_tuple = {
        "channel": norm_channel,
        "message_id": norm_msg_id,
        "text": norm_text,
        "timestamp_utc": ts_utc,
    }
    canonical_str = canonical_json(core_tuple)
    evidence_hash = compute_sha256(canonical_str)
    
    # Hash media if present
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
        "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return record


def verify_evidence_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verify the cryptographic integrity of an evidence record.
    Returns (is_valid, reason).
    """
    core = record.get("core")
    if not core:
        return False, "Missing core fields in evidence record"
        
    expected_hash = record.get("evidence_hash")
    if not expected_hash:
        return False, "Missing evidence hash"
        
    recomputed_canonical = canonical_json(core)
    recomputed_hash = compute_sha256(recomputed_canonical)
    
    if recomputed_hash != expected_hash:
        return False, f"Hash mismatch: record={expected_hash}, recomputed={recomputed_hash} (tampering detected)"
        
    # Check media if media file exists on disk
    media_info = record.get("media", {})
    if media_info and media_info.get("path") and media_info.get("sha256"):
        p = Path(media_info["path"])
        if p.exists() and p.is_file():
            cur_media_hash = hash_media_file(p)
            if cur_media_hash != media_info["sha256"]:
                return False, f"Media hash mismatch: expected {media_info['sha256']}, got {cur_media_hash}"
                
    return True, "Cryptographic integrity verified"
