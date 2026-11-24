"""Unified SQLite Database Manager for OSINT Threat Intelligence System.

Operates in SQLite WAL mode with foreign keys enabled.
Supports idempotent ingestion, cryptographic evidence hash chaining,
channel metrics, entity graph edge tracking, and audit logging.
"""
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

from core.models import (
    ChannelRecord,
    PostRecord,
    IdentifierRecord,
    EvidenceBlock,
    AlertRecord,
    now_utc_iso,
)

def get_default_db_path() -> Path:
    """Return operational.db by default, or demo.db when DEMO_MODE=1."""
    data_dir = Path(__file__).parent.parent / "data"
    if os.environ.get("DEMO_MODE", "0") in ("1", "true", "True"):
        return data_dir / "demo.db"
    return data_dir / "operational.db"


DEFAULT_DB_PATH = get_default_db_path()
SCHEMA_PATH = Path(__file__).parent.parent / "data" / "schema.sql"
GENESIS_HASH = "0" * 64


class Database:
    def __init__(self, db_path: Optional[Union[Path, str]] = None):
        if db_path is None:
            self.db_path = get_default_db_path()
        elif isinstance(db_path, str):
            self.db_path = Path(db_path)
        else:
            self.db_path = db_path
        self.is_operational = self.db_path.name == "operational.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def wipe_all_data(self):
        """Wipes data tables. Strictly prohibited on operational.db; permitted on demo.db only when DEMO_MODE=1."""
        if self.is_operational or self.db_path.name == "operational.db":
            raise PermissionError("FATAL: Database reset/wipe is strictly prohibited on operational.db!")
        if self.db_path.name == "demo.db" and os.environ.get("DEMO_MODE") != "1":
            raise PermissionError("FATAL: Database reset on demo.db is only permitted when DEMO_MODE=1!")
        with self._lock, self.get_connection() as conn:
            for tbl in ["alerts", "evidence", "post_identifiers", "identifiers", "entities_edges", "posts", "channels", "feedback"]:
                conn.execute(f"DELETE FROM {tbl}")
            conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Create a thread-safe connection with Row factory and WAL enabled."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Initialize database tables and indexes from schema.sql."""
        with self._lock, self.get_connection() as conn:
            if SCHEMA_PATH.exists():
                schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
                conn.executescript(schema_sql)
            conn.commit()

    def init_db(self):
        """Public alias to initialize database tables."""
        self._init_db()

    def reset_db(self):
        """Wipe all database tables and recreate clean schema. Strictly prohibited on operational.db!"""
        if self.is_operational or self.db_path.name == "operational.db":
            raise PermissionError("FATAL: Database reset/wipe is strictly prohibited on operational.db!")
        if self.db_path.name == "demo.db" and os.environ.get("DEMO_MODE") != "1":
            raise PermissionError("FATAL: Database reset on demo.db is only permitted when DEMO_MODE=1!")
        with self._lock, self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = OFF")
            tables = ["alerts", "post_identifiers", "evidence", "identifiers", "posts", "edges", "channels", "audit_log"]
            for t in tables:
                conn.execute(f"DROP TABLE IF EXISTS {t}")
            conn.commit()
        self._init_db()

    # ---------------------------------------------------------------------------
    # Audit Log
    # ---------------------------------------------------------------------------
    def log_audit(self, action: str, details: Optional[Dict[str, Any]] = None):
        with self._lock, self.get_connection() as conn:
            conn.execute(
                "INSERT INTO audit_log(action, details_json, timestamp) VALUES(?, ?, ?)",
                (action, json.dumps(details or {}, ensure_ascii=False), now_utc_iso())
            )
            conn.commit()

    # ---------------------------------------------------------------------------
    # Channel Management
    # ---------------------------------------------------------------------------
    def upsert_channel(self, channel: ChannelRecord):
        with self._lock, self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO channels(channel_id, platform, username, title, subscribers, first_seen, last_seen, risk_level, threat_score, is_monitored)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    username = excluded.username,
                    title = excluded.title,
                    subscribers = CASE WHEN excluded.subscribers > 0 THEN excluded.subscribers ELSE channels.subscribers END,
                    last_seen = excluded.last_seen,
                    risk_level = excluded.risk_level,
                    threat_score = excluded.threat_score
                """,
                (
                    channel.channel_id, channel.platform, channel.username, channel.title,
                    channel.subscribers, channel.first_seen, channel.last_seen,
                    channel.risk_level, channel.threat_score, 1 if channel.is_monitored else 0
                )
            )
            conn.commit()

    def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,)).fetchone()
            return dict(row) if row else None

    def list_channels(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM channels ORDER BY threat_score DESC, last_seen DESC").fetchall()
            return [dict(r) for r in rows]

    # ---------------------------------------------------------------------------
    # Post Ingestion (Idempotent)
    # ---------------------------------------------------------------------------
    def insert_post(self, post: PostRecord) -> bool:
        """Insert post idempotently. Returns True if newly inserted, False if duplicate."""
        with self._lock, self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO posts(post_uid, platform, channel_id, message_id, timestamp_utc,
                                  raw_text, normalized_text, media_path, media_hash,
                                  category, risk_level, threat_score, ingestion_source, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(platform, channel_id, message_id) DO NOTHING
                """,
                (
                    post.post_uid, post.platform, post.channel_id, str(post.message_id),
                    post.timestamp_utc, post.raw_text, post.normalized_text,
                    post.media_path, post.media_hash, post.category, post.risk_level,
                    post.threat_score, post.ingestion_source, post.created_at
                )
            )
            inserted = cur.rowcount > 0
            if inserted:
                # Update channel last_seen
                conn.execute(
                    "UPDATE channels SET last_seen = ? WHERE channel_id = ?",
                    (post.timestamp_utc, post.channel_id)
                )
            conn.commit()
            return inserted

    def get_post(self, post_uid: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM posts WHERE post_uid = ?", (post_uid,)).fetchone()
            return dict(row) if row else None

    def list_posts(self, limit: int = 200, category: Optional[str] = None, risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM posts WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        query += " ORDER BY timestamp_utc DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(r) for r in rows]

    # ---------------------------------------------------------------------------
    # Identifier Management & Linking
    # ---------------------------------------------------------------------------
    def upsert_identifier(self, ident: IdentifierRecord, channel_id: str):
        with self._lock, self.get_connection() as conn:
            # Check existing
            row = conn.execute(
                "SELECT identifier_id, channel_count, first_seen FROM identifiers WHERE type = ? AND normalized_value = ?",
                (ident.type, ident.normalized_value)
            ).fetchone()

            if row:
                ident_id = row["identifier_id"]
                # Count distinct channels this identifier is linked to
                cnt_row = conn.execute(
                    """
                    SELECT COUNT(DISTINCT p.channel_id) as cnt
                    FROM post_identifiers pi
                    JOIN posts p ON pi.post_uid = p.post_uid
                    WHERE pi.identifier_id = ?
                    """,
                    (ident_id,)
                ).fetchone()
                ch_count = max(row["channel_count"], (cnt_row["cnt"] if cnt_row else 1))
                is_cross = 1 if ch_count >= 2 else 0

                conn.execute(
                    """
                    UPDATE identifiers SET
                        last_seen = ?,
                        channel_count = ?,
                        cross_channel = ?
                    WHERE identifier_id = ?
                    """,
                    (ident.last_seen, ch_count, is_cross, ident_id)
                )
            else:
                conn.execute(
                    """
                    INSERT INTO identifiers(identifier_id, type, raw_value, normalized_value, channel_count, first_seen, last_seen, cross_channel)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ident.identifier_id, ident.type, ident.raw_value, ident.normalized_value,
                        ident.channel_count, ident.first_seen, ident.last_seen, 1 if ident.cross_channel else 0
                    )
                )
            conn.commit()

    def link_post_identifier(self, post_uid: str, identifier_id: str, source: str = "text"):
        with self._lock, self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO post_identifiers(post_uid, identifier_id, extraction_source)
                VALUES(?, ?, ?)
                ON CONFLICT(post_uid, identifier_id) DO NOTHING
                """,
                (post_uid, identifier_id, source)
            )
            # Re-evaluate cross_channel count
            conn.execute(
                """
                UPDATE identifiers
                SET channel_count = (
                    SELECT COUNT(DISTINCT p.channel_id)
                    FROM post_identifiers pi
                    JOIN posts p ON pi.post_uid = p.post_uid
                    WHERE pi.identifier_id = identifiers.identifier_id
                ),
                cross_channel = CASE WHEN (
                    SELECT COUNT(DISTINCT p.channel_id)
                    FROM post_identifiers pi
                    JOIN posts p ON pi.post_uid = p.post_uid
                    WHERE pi.identifier_id = identifiers.identifier_id
                ) >= 2 THEN 1 ELSE 0 END
                WHERE identifier_id = ?
                """,
                (identifier_id,)
            )
            conn.commit()

    def get_identifier(self, identifier_id_or_val: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM identifiers WHERE identifier_id = ? OR normalized_value = ?",
                (identifier_id_or_val, identifier_id_or_val)
            ).fetchone()
            return dict(row) if row else None

    def get_post_identifiers(self, post_uid: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT i.*, pi.extraction_source
                FROM post_identifiers pi
                JOIN identifiers i ON pi.identifier_id = i.identifier_id
                WHERE pi.post_uid = ?
                """,
                (post_uid,)
            ).fetchall()
            return [dict(r) for r in rows]

    def list_cross_channel_identifiers(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT i.*, GROUP_CONCAT(DISTINCT p.channel_id) as linked_channels
                FROM identifiers i
                JOIN post_identifiers pi ON i.identifier_id = pi.identifier_id
                JOIN posts p ON pi.post_uid = p.post_uid
                WHERE i.cross_channel = 1
                GROUP BY i.identifier_id
                ORDER BY i.channel_count DESC
                """
            ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["linked_channels"] = d["linked_channels"].split(",") if d.get("linked_channels") else []
                results.append(d)
            return results

    # ---------------------------------------------------------------------------
    # Evidence Ledger (Hash Chain)
    # ---------------------------------------------------------------------------
    def get_latest_evidence_block(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM evidence ORDER BY block_height DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def record_evidence_block(self, evidence: EvidenceBlock):
        with self._lock, self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO evidence(evidence_id, post_uid, canonical_json, current_hash, prev_hash, block_height, generated_at_utc)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(post_uid) DO NOTHING
                """,
                (
                    evidence.evidence_id, evidence.post_uid, evidence.canonical_json,
                    evidence.current_hash, evidence.prev_hash, evidence.block_height,
                    evidence.generated_at_utc
                )
            )
            conn.commit()

    def get_all_evidence_blocks(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM evidence ORDER BY block_height ASC").fetchall()
            return [dict(r) for r in rows]

    # ---------------------------------------------------------------------------
    # Alerts Management & Workflow
    # ---------------------------------------------------------------------------
    def create_alert(self, alert: AlertRecord) -> bool:
        """Create alert with deduplication. Returns True if created, False if duplicate."""
        with self._lock, self.get_connection() as conn:
            # Check if an alert already exists for this post_uid
            dup = conn.execute("SELECT alert_id FROM alerts WHERE post_uid = ?", (alert.post_uid,)).fetchone()
            if dup:
                return False

            # Check if an identical alert already exists for the same channel, normalized text and category
            cur_post = conn.execute("SELECT channel_id, normalized_text FROM posts WHERE post_uid = ?", (alert.post_uid,)).fetchone()
            if cur_post:
                norm_text = cur_post["normalized_text"]
                channel_id = cur_post["channel_id"]
                existing_content = conn.execute(
                    """
                    SELECT a.alert_id FROM alerts a
                    JOIN posts p ON a.post_uid = p.post_uid
                    WHERE p.channel_id = ? AND p.normalized_text = ? AND a.category = ?
                    LIMIT 1
                    """,
                    (channel_id, norm_text, alert.category)
                ).fetchone()
                if existing_content:
                    return False

            conn.execute(
                """
                INSERT INTO alerts(alert_id, post_uid, category, risk_level, threat_score, matched_terms_json, status, analyst_notes, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.alert_id, alert.post_uid, alert.category, alert.risk_level,
                    alert.threat_score, json.dumps(alert.matched_terms, ensure_ascii=False),
                    alert.status, alert.analyst_notes, alert.created_at
                )
            )
            conn.commit()
            return True

    def update_alert_status(self, alert_id: str, status: str, notes: str = ""):
        with self._lock, self.get_connection() as conn:
            conn.execute(
                "UPDATE alerts SET status = ?, analyst_notes = ? WHERE alert_id = ?",
                (status, notes, alert_id)
            )
            conn.commit()

    def list_alerts(self, status: Optional[str] = None, risk_level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
        SELECT a.*, p.channel_id, p.platform, p.timestamp_utc, p.raw_text, p.media_path, p.media_hash,
               e.evidence_id, e.current_hash, e.prev_hash, e.block_height
        FROM alerts a
        JOIN posts p ON a.post_uid = p.post_uid
        LEFT JOIN evidence e ON a.post_uid = e.post_uid
        WHERE 1=1
        """
        params = []
        if status:
            query += " AND a.status = ?"
            params.append(status)
        if risk_level:
            query += " AND a.risk_level = ?"
            params.append(risk_level)
        query += " ORDER BY a.created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["matched_terms"] = json.loads(d.get("matched_terms_json") or "[]")
                results.append(d)
            return results

    # ---------------------------------------------------------------------------
    # Graph Edges
    # ---------------------------------------------------------------------------
    def upsert_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        with self._lock, self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO entities_edges(source_id, target_id, relation, weight, created_at)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(source_id, target_id, relation) DO UPDATE SET weight = excluded.weight
                """,
                (source_id, target_id, relation, weight, now_utc_iso())
            )
            conn.commit()

    def get_all_edges(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM entities_edges").fetchall()
            return [dict(r) for r in rows]
