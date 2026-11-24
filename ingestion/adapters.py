"""Ingestion Adapters for TGSherlock, tgq Public Previews, and External File Imports."""
import csv
import json
import logging
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator

from core.models import PostRecord, ChannelRecord, now_utc_iso

log = logging.getLogger("ingestion.adapters")

TGSHERLOCK_DATA_DIR = Path.home() / ".local" / "share" / "tgsherlock" / "accounts"
VENV_TGQ = Path(__file__).parent.parent / ".venv" / "Scripts" / "tgq.exe"
TGQ_CMD = str(VENV_TGQ) if VENV_TGQ.exists() else "tgq"

COLUMN_ALIASES = {
    "platform": ["platform", "app", "network", "service"],
    "source": ["source", "channel", "channel_title", "chat_title", "group", "forum"],
    "post_id": ["post_id", "msg_id", "message_id", "id", "item_id"],
    "timestamp": ["timestamp", "date", "created_at", "time", "captured_at"],
    "text": ["text", "message", "content", "body", "caption"],
    "image_path": ["image_path", "media_path", "media", "image", "attachment"],
}


class TGSherlockAdapter:
    """Read-only adapter for local TGSherlock SQLite accounts."""

    def __init__(self, accounts_dir: Optional[Path] = None):
        self.accounts_dir = accounts_dir or TGSHERLOCK_DATA_DIR

    def find_active_db(self) -> Optional[Path]:
        if not self.accounts_dir.exists():
            return None
        dbs = list(self.accounts_dir.glob("*/tgsherlock.db"))
        if not dbs:
            return None
        dbs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return dbs[0]

    def read_recent_posts(self, limit: int = 100, db_path: Optional[Path] = None) -> List[PostRecord]:
        target_db = db_path or self.find_active_db()
        if not target_db or not target_db.exists():
            return []

        posts = []
        uri = f"file:{target_db.as_posix()}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True, timeout=10)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, chat_id, chat_title, msg_id, sender_name, date, text, media, media_path
                FROM messages
                ORDER BY id DESC LIMIT ?
                """,
                (limit,)
            ).fetchall()

            for r in rows:
                channel_name = r["chat_title"] or f"Chat_{r['chat_id']}"
                posts.append(PostRecord(
                    platform="Telegram",
                    channel_id=channel_name,
                    message_id=str(r["msg_id"] or r["id"]),
                    timestamp_utc=r["date"] or now_utc_iso(),
                    raw_text=r["text"] or "",
                    media_path=r["media_path"],
                    ingestion_source="LIVE"
                ))
            conn.close()
        except Exception as exc:
            log.warning("Could not read TGSherlock DB: %s", exc)
        return posts


class TGQPreviewAdapter:
    """Adapter for zero-credential public web previews using tgq preview."""

    def __init__(self, executable: str = TGQ_CMD):
        self.executable = executable

    def fetch_channel_posts(self, channel_name: str, limit: int = 25) -> List[PostRecord]:
        clean_name = re.sub(r"^(?:https?://)?(?:t\.me|telegram\.me)/(?:s/)?", "", channel_name).strip("/@")
        if not clean_name:
            return []

        cmd = [self.executable, "preview", clean_name]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            posts = []
            for line in proc.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    posts.append(PostRecord(
                        platform="Telegram",
                        channel_id=clean_name,
                        message_id=str(data.get("id", 0)),
                        timestamp_utc=data.get("date") or now_utc_iso(),
                        raw_text=data.get("text", "") or "",
                        ingestion_source="LIVE"
                    ))
                except json.JSONDecodeError:
                    continue
            return posts[-limit:] if posts else []
        except Exception as exc:
            log.warning("tgq preview error for %s: %s", clean_name, exc)
            return []


class FileImporterAdapter:
    """Multi-platform CSV/JSON file importer with validation, error report, and --dry-run."""

    def __init__(self):
        pass

    def validate_and_map_row(self, raw_row: Dict[str, Any], default_platform: str = "External") -> Tuple[Optional[PostRecord], List[str]]:
        """Map raw dict to PostRecord, returning (record, errors)."""
        errors = []
        lower_keys = {str(k).strip().lower(): k for k in raw_row.keys()}
        mapped = {"platform": default_platform, "source": "", "post_id": "", "timestamp": now_utc_iso(), "text": "", "image_path": None}

        for canonical, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in lower_keys:
                    val = raw_row[lower_keys[alias]]
                    if val is not None:
                        mapped[canonical] = val
                    break

        if not mapped["source"]:
            errors.append("Missing required 'source' (channel/group) column.")
        if not mapped["text"]:
            errors.append("Empty message 'text'.")

        if errors:
            return None, errors

        post = PostRecord(
            platform=str(mapped["platform"]).strip(),
            channel_id=str(mapped["source"]).strip(),
            message_id=str(mapped["post_id"] or int(datetime.now().timestamp())),
            timestamp_utc=str(mapped["timestamp"]),
            raw_text=str(mapped["text"]),
            media_path=mapped.get("image_path"),
            ingestion_source="IMPORTED"
        )
        return post, []

    def import_file(self, filepath: Path, default_platform: str = "External", dry_run: bool = False) -> Dict[str, Any]:
        """
        Process CSV or JSON file.
        Returns detailed report: {total, valid, invalid, dry_run, errors, posts}
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        raw_rows = []
        suffix = filepath.suffix.lower()

        if suffix in (".csv", ".tsv"):
            with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                raw_rows = list(reader)
        elif suffix == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for k in ("posts", "messages", "data", "items"):
                        if k in data and isinstance(data[k], list):
                            raw_rows = data[k]
                            break
                    else:
                        raw_rows = [data]
                elif isinstance(data, list):
                    raw_rows = data
        else:
            raise ValueError(f"Unsupported extension: {suffix}. Must be CSV or JSON.")

        valid_posts = []
        row_errors = []

        for idx, row in enumerate(raw_rows):
            post, errs = self.validate_and_map_row(row, default_platform=default_platform)
            if post:
                valid_posts.append(post)
            else:
                row_errors.append({"row_index": idx + 1, "errors": errs, "sample": str(row)[:100]})

        report = {
            "file": str(filepath),
            "total_rows": len(raw_rows),
            "valid_count": len(valid_posts),
            "invalid_count": len(row_errors),
            "dry_run": dry_run,
            "errors": row_errors,
            "posts": valid_posts,
        }
        return report
