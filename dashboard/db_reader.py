"""Database and Data Source Reader for OSINT Threat Dashboard.

Architecture Note (ONE Database Path):
The system uses ONE unified application database path everywhere:
    `data/osint_monitor.db` (core.db.DEFAULT_DB_PATH)
Used by: Dashboard pages, Ingestion worker, Evidence verifier, Link analysis.

External Source Note:
The path `~/.local/share/tgsherlock/accounts/*/tgsherlock.db` is strictly an
upstream daemon database read-only input adapter (ingestion.adapters.TGSherlockAdapter)
for ingesting raw Telegram messages into `data/osint_monitor.db`. It is NEVER
accessed directly for dashboard queries, graph analytics, or evidence seals.
"""
import json
import sqlite3
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.db import Database, DEFAULT_DB_PATH
from addons.extractors import extract_all_entities
from addons.scorer import RuleScorer
from addons.evidence import build_evidence_record, normalize_utc_timestamp
from addons.importer import DataImporter

SAMPLE_DATA_PATH = Path(__file__).parent.parent / "sample_data" / "synthetic_posts.json"


def load_unified_posts(db: Optional[Database] = None, limit: int = 500) -> List[Dict[str, Any]]:
    """
    Read posts directly from the single unified OSINT monitor SQLite DB (data/osint_monitor.db).
    """
    target_db = db or Database(DEFAULT_DB_PATH)
    posts = []
    with target_db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT p.post_uid, p.platform, p.channel_id, p.message_id, p.timestamp_utc,
                   p.raw_text, p.media_path, p.category, p.risk_level, p.threat_score,
                   p.ingestion_source, e.current_hash, e.canonical_json
            FROM posts p
            LEFT JOIN evidence e ON p.post_uid = e.post_uid
            ORDER BY p.timestamp_utc DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        for r in rows:
            extracted = target_db.get_post_identifiers(r["post_uid"])
            posts.append({
                "platform": r["platform"],
                "source": r["channel_id"],
                "post_id": r["message_id"],
                "timestamp": r["timestamp_utc"],
                "text": r["raw_text"],
                "image_path": r["media_path"],
                "extracted": {"all_flat": [{"value": i["normalized_value"], "type": i["type"]} for i in extracted]},
                "risk_level": r["risk_level"],
                "total_score": r["threat_score"],
                "primary_category": r["category"],
                "is_actionable": r["risk_level"] in ("High", "Medium"),
                "ingestion_source": r["ingestion_source"],
                "evidence_hash": r["current_hash"],
            })
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
    limit: int = 500,
    db: Optional[Database] = None,
) -> List[Dict[str, Any]]:
    """
    Unified data loader for Streamlit dashboard.
    source_type: 'auto' | 'unified' | 'synthetic' | 'custom'
    Always routes to ONE database path: data/osint_monitor.db.
    """
    if source_type == "custom" and uploaded_file and uploaded_file.exists():
        importer = DataImporter()
        return importer.import_file(uploaded_file)
        
    if source_type == "synthetic":
        return load_synthetic_demo_posts()
        
    # 'auto' or 'unified': Load from unified OSINT database
    db_posts = load_unified_posts(db=db, limit=limit)
    if db_posts:
        return db_posts
    return load_synthetic_demo_posts()
