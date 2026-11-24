"""Database and Data Source Reader for OSINT Threat Dashboard.

Safely accesses:
1. TGSherlock SQLite database (in read-only mode using URI file:...mode=ro)
2. Synthetic Hackathon Sample Data (sample_data/synthetic_posts.json)
3. Uploaded External CSV/JSON dumps (via importer.py)
"""
import json
import sqlite3
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from addons.extractors import extract_all_entities
from addons.scorer import RuleScorer
from addons.evidence import build_evidence_record, normalize_utc_timestamp
from addons.importer import DataImporter

# Default TGSherlock accounts directory
TGSHERLOCK_DATA_DIR = Path.home() / ".local" / "share" / "tgsherlock" / "accounts"
SAMPLE_DATA_PATH = Path(__file__).parent.parent / "sample_data" / "synthetic_posts.json"


def find_tgsherlock_db() -> Optional[Path]:
    """Locate the most recently modified active TGSherlock SQLite database."""
    if not TGSHERLOCK_DATA_DIR.exists():
        return None
    db_candidates = list(TGSHERLOCK_DATA_DIR.glob("*/tgsherlock.db"))
    if not db_candidates:
        return None
    # Sort by modification time descending
    db_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return db_candidates[0]


def load_tgsherlock_posts(db_path: Optional[Path] = None, limit: int = 500) -> List[Dict[str, Any]]:
    """
    Read posts directly from TGSherlock SQLite DB in strict read-only mode,
    enriching each post with Phase 1 extractors, scorer, and evidence hash.
    """
    target_db = db_path or find_tgsherlock_db()
    if not target_db or not target_db.exists():
        return []

    scorer = RuleScorer()
    posts = []

    # Read-only SQLite URI with WAL support
    uri_path = f"file:{target_db.as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(uri_path, uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Query messages with alerts or entities
        sql = """
        SELECT m.id, m.chat_id, m.chat_title, m.msg_id, m.sender_id, m.sender_name,
               m.sender_username, m.date, m.text, m.media, m.media_path, m.risk, m.source
        FROM messages m
        ORDER BY m.id DESC
        LIMIT ?
        """
        rows = cur.execute(sql, (limit,)).fetchall()

        for r in rows:
            text = r["text"] or ""
            source = r["chat_title"] or f"Chat_{r['chat_id']}"
            extracted = extract_all_entities(text)
            score_res = scorer.score(text, identifiers=extracted)

            evidence = build_evidence_record(
                channel=source,
                message_id=r["msg_id"] or r["id"],
                timestamp=r["date"],
                text=text,
                matched_terms=score_res.matched_terms,
                extracted_identifiers=extracted,
                media_path=r["media_path"],
                category=score_res.primary_category,
                risk_level=score_res.risk_level,
            )

            posts.append({
                "platform": "Telegram (Live)",
                "source": source,
                "post_id": r["msg_id"] or r["id"],
                "timestamp": normalize_utc_timestamp(r["date"]),
                "text": text,
                "image_path": r["media_path"],
                "extracted": extracted,
                "risk_level": score_res.risk_level,
                "total_score": score_res.total_score,
                "primary_category": score_res.primary_category,
                "is_actionable": score_res.is_actionable,
                "matched_terms": score_res.matched_terms,
                "evidence": evidence,
            })
        conn.close()
    except Exception as exc:
        print(f"Error reading TGSherlock DB: {exc}")
        return []

    return posts


def load_synthetic_demo_posts() -> List[Dict[str, Any]]:
    """Load the pre-packaged synthetic demo dataset for hackathon offline evaluations."""
    if not SAMPLE_DATA_PATH.exists():
        return []
    importer = DataImporter()
    return importer.import_from_json(SAMPLE_DATA_PATH, default_platform="Telegram (Synthetic Demo)")


def load_dashboard_data(
    source_type: str = "auto",
    uploaded_file: Optional[Path] = None,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """
    Unified data loader for Streamlit dashboard.
    source_type: 'auto' | 'live' | 'synthetic' | 'custom'
    """
    if source_type == "custom" and uploaded_file and uploaded_file.exists():
        importer = DataImporter()
        return importer.import_file(uploaded_file)
        
    if source_type == "synthetic":
        return load_synthetic_demo_posts()
        
    if source_type == "live":
        return load_tgsherlock_posts(limit=limit)
        
    # 'auto': Try live TGSherlock DB first; if empty, fallback to synthetic demo data
    live_posts = load_tgsherlock_posts(limit=limit)
    if live_posts:
        return live_posts
    return load_synthetic_demo_posts()
