"""Dataset parsing module for PS02 Hackathon dataset.

Strictly aggregate-only parser for:
1. Telegram channel JSON exports (messages vs service records)
2. Social media CSV posts (with Asia/Kolkata IST timezone parsing)
3. Poster SHA-256 verification records
4. Slang lexicon categories

NO raw text, author usernames, phone numbers, or mule account identifiers are retained.
"""

import csv
import json
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

IST = timezone(timedelta(hours=5, minutes=30))


def parse_ist_timestamp(ts_str: Any) -> Optional[datetime]:
    """Parse various timestamp formats into Asia/Kolkata timezone-aware datetime."""
    if not ts_str:
        return None
    s = str(ts_str).strip()
    if not s:
        return None
        
    # Unix timestamp
    if s.isdigit():
        try:
            return datetime.fromtimestamp(int(s), tz=IST)
        except Exception:
            pass

    # Standard ISO or datetime formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=IST)
        except ValueError:
            continue
            
    # Fallback ISO with possible Z or offset
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=IST)
        return dt.astimezone(IST)
    except Exception:
        return None


def parse_participant_dataset(source_path: Path) -> Dict[str, Any]:
    """Parse entire participant dataset into structured aggregate series and counts."""
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    from ps02_dataset.preflight import safe_zip, discover_root_prefix, REQUIRED, csv_rows

    z = zipfile.ZipFile(source_path)
    names = safe_zip(z)
    rootprefix = discover_root_prefix(names, REQUIRED)
    read = lambda rel: z.read(rootprefix + rel)
    files = lambda d: [n[len(rootprefix):] for n in names if n.startswith(rootprefix + d + "/") and not n.endswith("/")]

    # Available image names
    all_images = {Path(p).name.lower() for p in files("03_images") if Path(p).suffix.lower() in (".jpg", ".jpeg", ".png")}
    all_images.update({Path(p).name.lower() for p in files("02_social_media") if Path(p).suffix.lower() in (".jpg", ".jpeg", ".png")})

    # 1. Telegram parsing
    tg_files = [n for n in files("01_telegram_exports") if n.endswith(".json")]
    telegram_channel_aggregates = []
    hourly_distribution: Dict[Tuple[str, str, str], int] = {}  # (source_type, platform_or_channel, hour_str) -> count

    total_tg_messages = 0
    total_tg_services = 0
    total_tg_photos = 0

    for f in tg_files:
        obj = json.loads(read(f))
        ch_folder = Path(f).parent.name
        ch_name = obj.get("name", ch_folder)
        records = obj.get("messages", [])

        ch_messages = 0
        ch_services = 0
        ch_photos = 0
        blank_text = 0
        forward_cnt = 0
        reply_cnt = 0
        edit_cnt = 0
        dates: List[datetime] = []

        for r in records:
            r_type = r.get("type", "message")
            dt = parse_ist_timestamp(r.get("date")) or parse_ist_timestamp(r.get("date_unixtime"))
            if dt:
                dates.append(dt)
                hour_bucket = dt.strftime("%Y-%m-%d %H:00")
                key = ("Telegram", ch_name, hour_bucket)
                hourly_distribution[key] = hourly_distribution.get(key, 0) + 1

            if r_type == "message":
                ch_messages += 1
                total_tg_messages += 1
                if r.get("photo"):
                    ch_photos += 1
                    total_tg_photos += 1
                if not r.get("text"):
                    blank_text += 1
                if r.get("forwarded_from"):
                    forward_cnt += 1
                if r.get("reply_to_message_id"):
                    reply_cnt += 1
                if r.get("edited"):
                    edit_cnt += 1
            else:
                ch_services += 1
                total_tg_services += 1

        date_start = min(dates).isoformat() if dates else ""
        date_end = max(dates).isoformat() if dates else ""

        telegram_channel_aggregates.append({
            "channel_id": str(obj.get("id", ch_folder)),
            "channel_folder": ch_folder,
            "channel_name": ch_name,
            "total_messages": ch_messages,
            "total_service": ch_services,
            "total_photos": ch_photos,
            "blank_text_count": blank_text,
            "forward_count": forward_cnt,
            "reply_count": reply_cnt,
            "edit_count": edit_cnt,
            "date_start_ist": date_start,
            "date_end_ist": date_end,
        })

    # 2. Social Media parsing
    social_files = [n for n in files("02_social_media") if n.endswith(".csv")]
    platform_aggregates: Dict[str, Dict[str, Any]] = {}
    total_social_posts = 0

    for f in social_files:
        rows = csv_rows(read(f))
        for r in rows:
            total_social_posts += 1
            plat = r.get("platform", "Unknown").strip()
            if plat not in platform_aggregates:
                platform_aggregates[plat] = {
                    "platform": plat,
                    "total_posts": 0,
                    "images_referenced": 0,
                    "images_found": 0,
                    "posts_with_hashtags": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "locations": {},
                }
            
            p_data = platform_aggregates[plat]
            p_data["total_posts"] += 1
            
            # Likes & comments
            try:
                p_data["total_likes"] += int(r.get("likes", 0) or 0)
            except Exception:
                pass
            try:
                p_data["total_comments"] += int(r.get("comments", 0) or 0)
            except Exception:
                pass

            # Hashtags
            ht = r.get("hashtags", "").strip()
            if ht:
                p_data["posts_with_hashtags"] += 1

            # Image resolution
            img_ref = r.get("image_file", "").strip()
            if img_ref and img_ref.lower() != "none":
                p_data["images_referenced"] += 1
                if Path(img_ref).name.lower() in all_images:
                    p_data["images_found"] += 1

            # Location tag (coarse aggregate)
            loc = r.get("location_tag", "").strip()
            if loc:
                p_data["locations"][loc] = p_data["locations"].get(loc, 0) + 1

            # Timestamp parsing
            dt = parse_ist_timestamp(r.get("posted_at_ist"))
            if dt:
                hour_bucket = dt.strftime("%Y-%m-%d %H:00")
                key = ("SocialMedia", plat, hour_bucket)
                hourly_distribution[key] = hourly_distribution.get(key, 0) + 1

    # 3. Posters index parsing
    idx_files = [n for n in files("03_images") if n.endswith(".csv")]
    poster_records = []
    if idx_files:
        p_rows = csv_rows(read(idx_files[0]))
        for r in p_rows:
            poster_records.append({
                "image": r.get("image", "").strip(),
                "sha256": r.get("sha256", "").strip(),
            })

    # 4. Lexicon parsing
    lex_files = [n for n in files("04_lexicon") if n.endswith(".csv")]
    lexicon_records = []
    for f in lex_files:
        for lr in csv_rows(read(f)):
            lexicon_records.append({
                "category": lr.get("category", "").strip(),
                "language_or_script": lr.get("language_or_script", "").strip(),
                "source": lr.get("source", "").strip(),
            })

    return {
        "telegram_channels": telegram_channel_aggregates,
        "social_platforms": list(platform_aggregates.values()),
        "hourly_distribution": hourly_distribution,
        "posters": poster_records,
        "lexicon": lexicon_records,
        "totals": {
            "telegram_messages": total_tg_messages,
            "telegram_services": total_tg_services,
            "telegram_photos": total_tg_photos,
            "social_posts": total_social_posts,
            "combined_records": total_tg_messages + total_social_posts,
        }
    }
