"""Database store for PS02 Hackathon participant dataset.

Maintains an isolated SQLite database (data/participant_dataset.db) strictly
separated from the synthetic demo and live operations database (data/osint_monitor.db).

Stores ONLY aggregate metrics, channel/platform breakdowns, and SHA-256 hashes.
NO raw user messages, citizen handles, or personal/payment details are stored.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator

DEFAULT_PARTICIPANT_DB_PATH = Path("data/participant_dataset.db")
IST = timezone(timedelta(hours=5, minutes=30))


class ParticipantDatasetStore:
    """Isolated transactional store for participant dataset aggregate analytics."""

    def __init__(self, db_path: Path = DEFAULT_PARTICIPANT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create isolated schema tables if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS dataset_batches (
                batch_id TEXT PRIMARY KEY,
                archive_name TEXT NOT NULL,
                archive_sha256 TEXT NOT NULL,
                archive_size_bytes INTEGER NOT NULL,
                imported_at_ist TEXT NOT NULL,
                total_records INTEGER NOT NULL,
                status TEXT NOT NULL,
                audit_summary_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_batch_sha256 ON dataset_batches(archive_sha256);

            CREATE TABLE IF NOT EXISTS telegram_channel_aggregates (
                batch_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                channel_folder TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                total_messages INTEGER NOT NULL,
                total_service INTEGER NOT NULL,
                total_photos INTEGER NOT NULL,
                blank_text_count INTEGER NOT NULL,
                forward_count INTEGER NOT NULL,
                reply_count INTEGER NOT NULL,
                edit_count INTEGER NOT NULL,
                date_start_ist TEXT,
                date_end_ist TEXT,
                PRIMARY KEY (batch_id, channel_folder),
                FOREIGN KEY (batch_id) REFERENCES dataset_batches(batch_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS social_platform_aggregates (
                batch_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                total_posts INTEGER NOT NULL,
                images_referenced INTEGER NOT NULL,
                images_found INTEGER NOT NULL,
                posts_with_hashtags INTEGER NOT NULL,
                total_likes INTEGER NOT NULL,
                total_comments INTEGER NOT NULL,
                PRIMARY KEY (batch_id, platform),
                FOREIGN KEY (batch_id) REFERENCES dataset_batches(batch_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS hourly_timeline_aggregates (
                batch_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                platform_or_channel TEXT NOT NULL,
                hour_bucket_ist TEXT NOT NULL,
                record_count INTEGER NOT NULL,
                PRIMARY KEY (batch_id, source_type, platform_or_channel, hour_bucket_ist),
                FOREIGN KEY (batch_id) REFERENCES dataset_batches(batch_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_timeline_hour ON hourly_timeline_aggregates(batch_id, hour_bucket_ist);

            CREATE TABLE IF NOT EXISTS poster_verification_records (
                batch_id TEXT NOT NULL,
                poster_name TEXT NOT NULL,
                expected_sha256 TEXT NOT NULL,
                actual_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                PRIMARY KEY (batch_id, poster_name),
                FOREIGN KEY (batch_id) REFERENCES dataset_batches(batch_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS dataset_quality_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                code TEXT NOT NULL,
                severity TEXT NOT NULL,
                count INTEGER NOT NULL,
                detail TEXT NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES dataset_batches(batch_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS lexicon_aggregates (
                batch_id TEXT NOT NULL,
                category TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (batch_id, category),
                FOREIGN KEY (batch_id) REFERENCES dataset_batches(batch_id) ON DELETE CASCADE
            );
            """)
            conn.commit()

    def get_batch_by_hash(self, archive_sha256: str) -> Optional[Dict[str, Any]]:
        """Retrieve existing batch metadata by archive SHA-256 for idempotency checking."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM dataset_batches WHERE archive_sha256 = ? ORDER BY imported_at_ist DESC LIMIT 1",
                (archive_sha256,)
            ).fetchone()
            if row:
                return dict(row)
        return None

    def get_latest_batch(self) -> Optional[Dict[str, Any]]:
        """Retrieve the most recently imported dataset batch."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM dataset_batches ORDER BY imported_at_ist DESC LIMIT 1"
            ).fetchone()
            if row:
                return dict(row)
        return None

    def list_batches(self) -> List[Dict[str, Any]]:
        """List all imported dataset batches with high-level stats."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT batch_id, archive_name, archive_sha256, archive_size_bytes, imported_at_ist, total_records, status "
                "FROM dataset_batches ORDER BY imported_at_ist DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def save_batch(
        self,
        batch_id: str,
        archive_name: str,
        archive_sha256: str,
        archive_size_bytes: int,
        audit_result: Dict[str, Any],
        parsed_data: Dict[str, Any],
    ) -> str:
        """Atomically persist parsed aggregate records inside a single transaction."""
        now_ist = datetime.now(IST).isoformat()
        total_records = parsed_data.get("totals", {}).get("combined_records", 0)

        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                # 1. Insert or replace batch header
                conn.execute("""
                INSERT OR REPLACE INTO dataset_batches 
                (batch_id, archive_name, archive_sha256, archive_size_bytes, imported_at_ist, total_records, status, audit_summary_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    batch_id,
                    archive_name,
                    archive_sha256,
                    archive_size_bytes,
                    now_ist,
                    total_records,
                    "SUCCESS",
                    json.dumps(audit_result),
                ))

                # 2. Telegram channels
                for ch in parsed_data.get("telegram_channels", []):
                    conn.execute("""
                    INSERT OR REPLACE INTO telegram_channel_aggregates
                    (batch_id, channel_id, channel_folder, channel_name, total_messages, total_service, total_photos, blank_text_count, forward_count, reply_count, edit_count, date_start_ist, date_end_ist)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        batch_id,
                        ch["channel_id"],
                        ch["channel_folder"],
                        ch["channel_name"],
                        ch["total_messages"],
                        ch["total_service"],
                        ch["total_photos"],
                        ch["blank_text_count"],
                        ch["forward_count"],
                        ch["reply_count"],
                        ch["edit_count"],
                        ch["date_start_ist"],
                        ch["date_end_ist"],
                    ))

                # 3. Social platforms
                for sp in parsed_data.get("social_platforms", []):
                    conn.execute("""
                    INSERT OR REPLACE INTO social_platform_aggregates
                    (batch_id, platform, total_posts, images_referenced, images_found, posts_with_hashtags, total_likes, total_comments)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        batch_id,
                        sp["platform"],
                        sp["total_posts"],
                        sp["images_referenced"],
                        sp["images_found"],
                        sp["posts_with_hashtags"],
                        sp["total_likes"],
                        sp["total_comments"],
                    ))

                # 4. Hourly timeline
                for (src_type, plat_ch, hour_str), cnt in parsed_data.get("hourly_distribution", {}).items():
                    conn.execute("""
                    INSERT OR REPLACE INTO hourly_timeline_aggregates
                    (batch_id, source_type, platform_or_channel, hour_bucket_ist, record_count)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        batch_id,
                        src_type,
                        plat_ch,
                        hour_str,
                        cnt,
                    ))

                # 5. Poster verifications
                for p in audit_result.get("counts", {}).get("poster_details", []):
                    conn.execute("""
                    INSERT OR REPLACE INTO poster_verification_records
                    (batch_id, poster_name, expected_sha256, actual_sha256, status)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        batch_id,
                        p["image"],
                        p["expected_sha256"],
                        p["actual_sha256"],
                        p["status"],
                    ))

                # 6. Quality findings
                conn.execute("DELETE FROM dataset_quality_findings WHERE batch_id = ?", (batch_id,))
                for f in audit_result.get("findings", []):
                    conn.execute("""
                    INSERT INTO dataset_quality_findings (batch_id, code, severity, count, detail)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        batch_id,
                        f["code"],
                        f.get("severity", "error"),
                        f.get("count", 1),
                        f.get("detail", ""),
                    ))

                # 7. Lexicon aggregates
                for cat, count in audit_result.get("counts", {}).get("lexicon_categories", {}).items():
                    conn.execute("""
                    INSERT OR REPLACE INTO lexicon_aggregates (batch_id, category, count)
                    VALUES (?, ?, ?)
                    """, (batch_id, cat, count))

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return batch_id

    # Analytics query methods for Dashboard
    def get_platform_breakdown(self, batch_id: str) -> List[Dict[str, Any]]:
        """Returns post counts across Telegram and Social platforms."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT 'Telegram' as platform, SUM(total_messages) as total_posts, SUM(total_photos) as images_found
            FROM telegram_channel_aggregates WHERE batch_id = ?
            UNION ALL
            SELECT platform, total_posts, images_found
            FROM social_platform_aggregates WHERE batch_id = ?
            ORDER BY total_posts DESC
            """, (batch_id, batch_id)).fetchall()
            return [dict(r) for r in rows]

    def get_telegram_channel_summary(self, batch_id: str) -> List[Dict[str, Any]]:
        """Returns Telegram channel aggregates."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT channel_folder, channel_name, total_messages, total_service, total_photos, blank_text_count, forward_count, edit_count, date_start_ist, date_end_ist
            FROM telegram_channel_aggregates WHERE batch_id = ?
            ORDER BY total_messages DESC
            """, (batch_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_social_platform_summary(self, batch_id: str) -> List[Dict[str, Any]]:
        """Returns Social Media platform aggregates."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT platform, total_posts, images_referenced, images_found, posts_with_hashtags, total_likes, total_comments
            FROM social_platform_aggregates WHERE batch_id = ?
            ORDER BY total_posts DESC
            """, (batch_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_timeline_series(self, batch_id: str) -> List[Dict[str, Any]]:
        """Returns hourly counts sorted chronologically."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT hour_bucket_ist, source_type, SUM(record_count) as total_count
            FROM hourly_timeline_aggregates WHERE batch_id = ?
            GROUP BY hour_bucket_ist, source_type
            ORDER BY hour_bucket_ist ASC
            """, (batch_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_poster_records(self, batch_id: str) -> List[Dict[str, Any]]:
        """Returns poster verification details."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT poster_name, expected_sha256, actual_sha256, status
            FROM poster_verification_records WHERE batch_id = ?
            ORDER BY poster_name ASC
            """, (batch_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_quality_findings(self, batch_id: str) -> List[Dict[str, Any]]:
        """Returns data quality findings."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT code, severity, count, detail
            FROM dataset_quality_findings WHERE batch_id = ?
            ORDER BY id ASC
            """, (batch_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_lexicon_categories(self, batch_id: str) -> List[Dict[str, Any]]:
        """Returns slang lexicon categories."""
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT category, count FROM lexicon_aggregates WHERE batch_id = ?
            ORDER BY count DESC
            """, (batch_id,)).fetchall()
            return [dict(r) for r in rows]
