"""PS02 dataset validation and ingestion adapter.

Imports only the 1,500 Telegram Desktop messages and 350 social posts described
in the PS02 README. Real-world reference-channel records and the separate masked
complaint repository are audited as reference material and are never ingested.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import zipfile
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, Iterator, List, Optional, Tuple

PROVENANCE = "HACKATHON_SAMPLE"
IST = timezone(timedelta(hours=5, minutes=30), name="IST")
MAX_ARCHIVE_BYTES = 250 * 1024 * 1024


class PS02DatasetError(ValueError):
    """Invalid, incomplete or unsafe PS02 dataset."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_child(base: Path, relative: str) -> Path:
    """Resolve a dataset-relative path and reject traversal outside its root."""
    normalized = str(relative or "").replace("\\", "/").strip()
    rel = PurePosixPath(normalized)
    win_rel = PureWindowsPath(normalized)
    if not normalized or rel.is_absolute() or win_rel.is_absolute() or win_rel.drive or any(part in ("", ".", "..") for part in rel.parts):
        raise PS02DatasetError("Unsafe dataset-relative path.")
    root = base.resolve()
    target = (root / Path(*rel.parts)).resolve()
    if os.path.commonpath((str(root), str(target))) != str(root):
        raise PS02DatasetError("Dataset path escapes its permitted folder.")
    return target


def find_dataset_root(path: Path | str) -> Path:
    path = Path(path).resolve()
    if (path / "01_telegram_exports").is_dir() and (path / "02_social_media").is_dir():
        return path
    candidate = path / "PS02_demo_data"
    if (candidate / "01_telegram_exports").is_dir():
        return candidate
    matches = [item for item in path.glob("**/PS02_demo_data")
               if item.is_dir() and (item / "01_telegram_exports").is_dir()]
    if len(matches) == 1:
        return matches[0]
    raise PS02DatasetError("PS02_demo_data root not found (expected 01_telegram_exports and 02_social_media).")


def safe_extract_zip(archive_path: Path | str, destination: Path | str,
                     max_uncompressed_bytes: int = MAX_ARCHIVE_BYTES) -> Path:
    """CRC-check and safely unpack a ZIP, rejecting traversal and symlinks."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            total = sum(item.file_size for item in entries)
            if total > max_uncompressed_bytes:
                raise PS02DatasetError(f"Archive exceeds the {max_uncompressed_bytes:,}-byte extraction limit.")
            corrupt = archive.testzip()
            if corrupt:
                raise PS02DatasetError(f"ZIP CRC check failed for {corrupt}.")
            root = destination.resolve()
            for item in entries:
                rel = PurePosixPath(item.filename.replace("\\", "/"))
                win_rel = PureWindowsPath(item.filename)
                if rel.is_absolute() or win_rel.is_absolute() or win_rel.drive or any(part in ("", ".", "..") for part in rel.parts):
                    raise PS02DatasetError("ZIP contains an unsafe member path.")
                mode = (item.external_attr >> 16) & 0xFFFF
                if (mode & 0o170000) == 0o120000:
                    raise PS02DatasetError("ZIP symlink entries are not supported.")
                target = (root / Path(*rel.parts)).resolve()
                if os.path.commonpath((str(root), str(target))) != str(root):
                    raise PS02DatasetError("ZIP member escapes the extraction directory.")
            archive.extractall(root)
    except zipfile.BadZipFile as exc:
        raise PS02DatasetError("Uploaded file is not a valid ZIP archive.") from exc
    return find_dataset_root(destination)


def flatten_telegram_text(value: Any) -> str:
    """Flatten Telegram Desktop text entities without dropping text segments."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return "" if value is None else str(value)


def to_utc_iso(value: Any, *, unix_epoch: bool = False, naive_timezone=IST) -> str:
    if value is None or str(value).strip() == "":
        raise PS02DatasetError("A post record is missing its timestamp.")
    try:
        if unix_epoch:
            parsed = datetime.fromtimestamp(int(value), tz=timezone.utc)
        elif isinstance(value, datetime):
            parsed = value
        else:
            parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=naive_timezone)
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError, OverflowError, OSError) as exc:
        raise PS02DatasetError(f"Invalid timestamp: {value!r}") from exc


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PS02DatasetError(f"Could not read {path.name}: {exc}") from exc


def dataset_fingerprint(root: Path) -> str:
    """Fingerprint primary post, media and lexicon data; exclude reference repositories."""
    digest = hashlib.sha256()
    for dirname in ("01_telegram_exports", "02_social_media", "03_images", "04_lexicon"):
        folder = root / dirname
        if not folder.exists():
            continue
        for path in sorted((p for p in folder.rglob("*") if p.is_file()),
                           key=lambda p: p.relative_to(root).as_posix()):
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


class PS02DatasetReader:
    """Read, audit and import primary PS02 posts while preserving provenance."""

    def __init__(self, root: Path | str, ocr_enabled: bool = True, ocr_extractor: Any = None):
        self.root = find_dataset_root(root)
        self.ocr_enabled = bool(ocr_enabled)
        self.ocr_extractor = ocr_extractor
        self.ocr_cache: Dict[str, Dict[str, Any]] = {}
        self.dataset_id = dataset_fingerprint(self.root)

    def _ocr(self, path: Optional[Path], media_hash: Optional[str]) -> Dict[str, Any]:
        if not self.ocr_enabled or not path or not media_hash:
            return {"success": False, "text": "", "engine": "NOT_REQUESTED",
                    "languages": None, "error": None}
        if media_hash in self.ocr_cache:
            return dict(self.ocr_cache[media_hash])
        if self.ocr_extractor is None:
            try:
                from addons.ocr_extractor import OCRExtractor
                self.ocr_extractor = OCRExtractor()
            except Exception:
                self.ocr_extractor = False
        if not self.ocr_extractor:
            result = {"success": False, "text": "", "engine": "OCR DISABLED",
                      "languages": None, "error": "OCR engine could not be initialized."}
        else:
            result = self.ocr_extractor.extract_text(path, lang="eng+hin+mar")
        self.ocr_cache[media_hash] = dict(result)
        return result

    def _asset(self, base: Path, relative: Any) -> Tuple[Optional[str], Optional[str]]:
        if not relative:
            return None, None
        path = safe_child(base, str(relative))
        if not path.is_file():
            return None, None
        return str(path), sha256_file(path)

    def telegram_posts(self) -> Iterator[Dict[str, Any]]:
        exports = sorted((self.root / "01_telegram_exports").glob("*/result.json"))
        if not exports:
            raise PS02DatasetError("No Telegram Desktop result.json exports were found.")
        for export in exports:
            payload = read_json(export)
            if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
                raise PS02DatasetError(f"Unexpected Telegram export structure: {export}")
            display_name = str(payload.get("name") or export.parent.name).strip()
            source_id = str(payload.get("id") or "").strip()
            if not source_id:
                raise PS02DatasetError(f"Missing Telegram channel ID in {export}.")
            for message in payload["messages"]:
                if not isinstance(message, dict) or message.get("type") != "message":
                    continue
                msg_id = str(message.get("id") or "").strip()
                if not msg_id:
                    raise PS02DatasetError(f"Message without ID in {export.parent.name}.")
                timestamp = message.get("date_unixtime")
                timestamp_utc = to_utc_iso(timestamp, unix_epoch=True) if timestamp else to_utc_iso(message.get("date"))
                photo_rel = str(message.get("photo") or "").replace("\\", "/")
                media_path, media_hash = self._asset(export.parent, photo_rel)
                ocr = self._ocr(Path(media_path) if media_path else None, media_hash)
                metadata = {
                    "schema": "telegram_desktop_export", "dataset_id": self.dataset_id,
                    "provenance": PROVENANCE, "source_display": display_name,
                    "source_id": source_id, "export_type": payload.get("type"),
                    "sender_name": message.get("from"), "sender_id": message.get("from_id"),
                    "forwarded_from": message.get("forwarded_from"),
                    "source_date": message.get("date"),
                    "source_date_unixtime": str(timestamp or ""),
                    "edited_at": message.get("edited"),
                    "edited_unixtime": str(message.get("edited_unixtime") or ""),
                    "text_entities": message.get("text_entities") or [],
                    "media_relative_path": photo_rel or None,
                    "media_width": message.get("width"), "media_height": message.get("height"),
                    "media_sha256": media_hash, "ocr_text": ocr.get("text", "") or "",
                    "ocr_success": bool(ocr.get("success")), "ocr_engine": ocr.get("engine"),
                    "ocr_languages": ocr.get("languages"), "ocr_error": ocr.get("error"),
                }
                yield {
                    "platform": f"Telegram [PS02:{self.dataset_id[:8]}]",
                    "channel_id": f"Telegram:{source_id}", "message_id": msg_id,
                    "timestamp_utc": timestamp_utc, "raw_text": flatten_telegram_text(message.get("text")),
                    "media_path": media_path, "media_hash": media_hash, "source_metadata": metadata,
                }

    def social_posts(self) -> Iterator[Dict[str, Any]]:
        folder = self.root / "02_social_media"
        json_path, csv_path = folder / "posts.json", folder / "posts.csv"
        rows = read_json(json_path) if json_path.exists() else read_csv(csv_path)
        if not isinstance(rows, list):
            raise PS02DatasetError("Social posts must be a JSON array or CSV table.")
        for row in rows:
            if not isinstance(row, dict):
                continue
            platform = str(row.get("platform") or "Social").strip()
            author = str(row.get("author") or "Unknown").strip()
            post_id = str(row.get("post_id") or "").strip()
            if not post_id:
                raise PS02DatasetError("Social-media post is missing post_id.")
            timestamp = to_utc_iso(row.get("posted_at_ist"))
            image_rel = str(row.get("image_file") or "").replace("\\", "/")
            media_path, media_hash = self._asset(folder, image_rel)
            ocr = self._ocr(Path(media_path) if media_path else None, media_hash)
            hashtags = row.get("hashtags") or ""
            if isinstance(hashtags, list):
                hashtags = " ".join(str(tag) for tag in hashtags)
            location_tag = str(row.get("location_tag") or "")
            analysis_text = " ".join(part for part in (str(hashtags), str(ocr.get("text") or "")) if part).strip()
            metadata = {
                "schema": "ps02_social_media_post", "dataset_id": self.dataset_id,
                "provenance": PROVENANCE, "source_platform": platform, "source_display": author,
                "author": author, "posted_at_ist": str(row.get("posted_at_ist") or ""),
                "hashtags": str(hashtags), "location_tag": location_tag,
                "likes": _safe_int(row.get("likes")), "comments": _safe_int(row.get("comments")),
                "media_relative_path": image_rel or None, "media_sha256": media_hash,
                "ocr_text": ocr.get("text", "") or "", "ocr_success": bool(ocr.get("success")),
                "ocr_engine": ocr.get("engine"), "ocr_languages": ocr.get("languages"),
                "ocr_error": ocr.get("error"), "analysis_text": analysis_text,
            }
            yield {
                "platform": f"{platform} [PS02:{self.dataset_id[:8]}]",
                "channel_id": f"{platform}:{author}", "message_id": post_id,
                "timestamp_utc": timestamp, "raw_text": str(row.get("text") or ""),
                "media_path": media_path, "media_hash": media_hash, "source_metadata": metadata,
            }

    def iter_posts(self) -> Iterator[Dict[str, Any]]:
        yield from self.telegram_posts()
        yield from self.social_posts()

    def ocr_status(self) -> Dict[str, Any]:
        if not self.ocr_enabled:
            return {"enabled": False, "engine": "NOT_REQUESTED"}
        if self.ocr_extractor is None:
            try:
                from addons.ocr_extractor import OCRExtractor
                self.ocr_extractor = OCRExtractor()
            except Exception:
                self.ocr_extractor = False
        if not self.ocr_extractor:
            return {"enabled": True, "engine": "OCR DISABLED"}
        return {"enabled": True, **self.ocr_extractor.get_detection_status()}

    def audit(self) -> Dict[str, Any]:
        telegram_exports = sorted((self.root / "01_telegram_exports").glob("*/result.json"))
        telegram_channels, telegram_total = [], 0
        telegram_photos, missing_telegram, forwarded, edited, empty_text = 0, [], 0, 0, 0
        entity_types = Counter()
        for export in telegram_exports:
            payload = read_json(export)
            if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
                raise PS02DatasetError(f"Unexpected Telegram export structure: {export}")
            messages = [m for m in payload["messages"] if isinstance(m, dict) and m.get("type") == "message"]
            senders = {str(m.get("from_id") or m.get("actor_id") or "") for m in messages}
            channel_photos = channel_forwards = channel_edits = channel_empty = 0
            for message in messages:
                telegram_total += 1
                if not flatten_telegram_text(message.get("text")).strip():
                    empty_text += 1
                    channel_empty += 1
                if message.get("forwarded_from"):
                    forwarded += 1
                    channel_forwards += 1
                if message.get("edited") or message.get("edited_unixtime"):
                    edited += 1
                    channel_edits += 1
                for entity in message.get("text_entities") or []:
                    if isinstance(entity, dict):
                        entity_types[str(entity.get("type") or "unknown")] += 1
                photo = str(message.get("photo") or "").replace("\\", "/")
                if photo:
                    telegram_photos += 1
                    channel_photos += 1
                    if not safe_child(export.parent, photo).is_file():
                        missing_telegram.append(f"{export.parent.name}/{photo}")
            telegram_channels.append({
                "folder": export.parent.name, "name": payload.get("name") or export.parent.name,
                "type": payload.get("type") or "unknown", "source_id": str(payload.get("id") or ""),
                "posts": len(messages), "service_events": len(payload["messages"]) - len(messages),
                "senders": len(senders), "photo_references": channel_photos,
                "empty_text_posts": channel_empty, "forwarded_posts": channel_forwards,
                "edited_posts": channel_edits,
            })

        social_dir = self.root / "02_social_media"
        social_json = social_dir / "posts.json"
        social = read_json(social_json) if social_json.exists() else read_csv(social_dir / "posts.csv")
        if not isinstance(social, list):
            raise PS02DatasetError("Social posts must be an array/table.")
        social_platforms = Counter(str(r.get("platform") or "Unknown") for r in social)
        social_photos, missing_social = 0, []
        for row in social:
            image_ref = str(row.get("image_file") or "").replace("\\", "/")
            if image_ref:
                social_photos += 1
                if not safe_child(social_dir, image_ref).is_file():
                    missing_social.append(image_ref)

        index_rows = read_csv(self.root / "03_images" / "images_index.csv")
        poster_mismatches, poster_hashes = [], set()
        for row in index_rows:
            name = str(row.get("image") or "")
            path = safe_child(self.root / "03_images" / "posters", name)
            if not path.is_file():
                poster_mismatches.append(f"{name}: missing")
            elif sha256_file(path) != str(row.get("sha256") or "").lower():
                poster_mismatches.append(f"{name}: SHA-256 mismatch")
            else:
                poster_hashes.add(sha256_file(path))

        lexicon_count = len(read_csv(self.root / "04_lexicon" / "starter_slang_lexicon.csv"))
        reference_count = len(read_csv(self.root / "05_reference" / "real_reported_channels.csv"))
        image_files = list(self.root.rglob("*.jpg")) + list(self.root.rglob("*.jpeg"))
        unique_image_hashes = {sha256_file(path) for path in image_files}
        masked_dir = self.root / "Suspect_Repository_masked"
        masked_files = sorted(masked_dir.glob("*.csv")) if masked_dir.exists() else []
        masked_rows, ack_counts = 0, Counter()
        for path in masked_files:
            rows = read_csv(path)
            masked_rows += len(rows)
            for row in rows:
                ack = str(row.get("Acknowledgement No") or "").strip()
                if ack:
                    ack_counts[ack] += 1
        warnings = []
        if telegram_total + len(social) != 1850:
            warnings.append(f"README advertises 1,850 primary posts; found {telegram_total + len(social)}.")
        if missing_telegram or missing_social:
            warnings.append("Some post-linked media files are missing.")
        if poster_mismatches:
            warnings.append("One or more poster files do not match their indexed SHA-256.")
        if masked_files:
            warnings.append("Masked complaint/reference CSVs are excluded from posts, scoring and entity graph.")
        if not (self.root / "99_answer_key").exists():
            warnings.append("Judge-only answer key is absent; no ground-truth performance metrics are available.")
        return {
            "dataset_id": self.dataset_id, "provenance": PROVENANCE,
            "telegram_export_count": len(telegram_exports), "telegram_posts": telegram_total,
            "telegram_channels": telegram_channels, "telegram_photo_references": telegram_photos,
            "missing_telegram_photos": missing_telegram, "telegram_forwarded_posts": forwarded,
            "telegram_edited_posts": edited, "telegram_empty_text_posts": empty_text,
            "telegram_text_entity_types": dict(entity_types), "social_posts": len(social),
            "social_platforms": dict(social_platforms), "social_photo_references": social_photos,
            "missing_social_photos": missing_social, "total_posts": telegram_total + len(social),
            "poster_count": len(index_rows), "poster_hash_mismatches": poster_mismatches,
            "verified_poster_hashes": len(poster_hashes), "starter_lexicon_terms": lexicon_count,
            "reference_channel_rows": reference_count, "jpeg_file_count": len(image_files),
            "unique_image_hashes": len(unique_image_hashes), "masked_repository_files": len(masked_files),
            "masked_repository_rows": masked_rows,
            "masked_repository_unique_acknowledgements": len(ack_counts),
            "masked_repository_repeated_acknowledgement_rows": sum(n - 1 for n in ack_counts.values() if n > 1),
            "answer_key_present": (self.root / "99_answer_key").exists(), "warnings": warnings,
        }

    def import_into_worker(self, worker: Any) -> Dict[str, Any]:
        from core.models import ChannelRecord
        inserted = duplicates = failures = ocr_successes = 0
        errors: List[Dict[str, str]] = []
        channels_seen = set()
        total = 0
        for record in self.iter_posts():
            total += 1
            metadata = record["source_metadata"]
            if metadata.get("ocr_success"):
                ocr_successes += 1
            channel_id = record["channel_id"]
            if channel_id not in channels_seen:
                channels_seen.add(channel_id)
                worker.db.upsert_channel(ChannelRecord(
                    channel_id=channel_id, platform=record["platform"],
                    username=str(metadata.get("author") or ""),
                    title=str(metadata.get("source_display") or channel_id),
                    first_seen=record["timestamp_utc"], last_seen=record["timestamp_utc"],
                ))
            try:
                ok = worker.process_raw_post(
                    platform=record["platform"], channel_id=channel_id,
                    message_id=record["message_id"], timestamp_utc=record["timestamp_utc"],
                    raw_text=record["raw_text"], ingestion_source=PROVENANCE,
                    media_path=record["media_path"], media_hash=record["media_hash"],
                    source_metadata=metadata,
                )
                if ok:
                    inserted += 1
                else:
                    duplicates += 1
            except Exception as exc:
                failures += 1
                if len(errors) < 50:
                    errors.append({"source": channel_id, "message_id": record["message_id"],
                                   "error": str(exc)[:400]})
        report = {
            "dataset": "PS02_demo_data", "dataset_id": self.dataset_id, "provenance": PROVENANCE,
            "total_records": total, "inserted": inserted, "duplicates": duplicates,
            "failures": failures, "ocr_successes": ocr_successes,
            "ocr_engine": self.ocr_status().get("engine"),
            "masked_repository_ingested": False, "reference_channels_ingested": False,
            "errors": errors,
        }
        try:
            worker.db.log_audit("ps02_dataset_import", report)
        except Exception:
            pass
        return report


def _safe_int(value: Any) -> Optional[int]:
    try:
        return None if value is None or str(value).strip() == "" else int(value)
    except (ValueError, TypeError):
        return None


def load_starter_lexicon(root: Path | str) -> List[Dict[str, str]]:
    root = find_dataset_root(root)
    return read_csv(root / "04_lexicon" / "starter_slang_lexicon.csv")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audit/import the PS02 hackathon dataset.")
    parser.add_argument("dataset", help="Extracted PS02_demo_data folder or parent folder.")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR.")
    parser.add_argument("--import-db", action="store_true", help="Import primary PS02 posts into SQLite.")
    args = parser.parse_args()
    reader = PS02DatasetReader(args.dataset, ocr_enabled=not args.no_ocr)
    print(json.dumps(reader.audit(), ensure_ascii=False, indent=2))
    if args.import_db:
        from core.db import Database
        from ingestion.worker import IngestionWorker
        print(json.dumps(reader.import_into_worker(IngestionWorker(db=Database())),
                         ensure_ascii=False, indent=2))
