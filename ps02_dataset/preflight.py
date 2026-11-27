#!/usr/bin/env python3
"""Aggregate-only structural preflight for participant-facing PS02 demo data.

No text, usernames, payment/contact identifiers, profile data, or cross-platform
relationships are extracted or emitted. ZIP members are inspected in place.
"""

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from datetime import datetime, timezone, timedelta

REQUIRED = (
    "01_telegram_exports",
    "02_social_media",
    "03_images",
    "04_lexicon",
)

MAX_ENTRIES = 20000
MAX_MEMBER = 128 * 1024 * 1024  # 128 MB per member
MAX_TOTAL = 1024 * 1024 * 1024   # 1 GB total uncompressed

IST = timezone(timedelta(hours=5, minutes=30))


def safe_zip(z: zipfile.ZipFile) -> Set[str]:
    """Validate archive entry bounds and path safety against zip-slip and bombs."""
    infos = z.infolist()
    if len(infos) > MAX_ENTRIES:
        raise ValueError(f"Archive entry limit exceeded: {len(infos)} > {MAX_ENTRIES}")
    
    total = 0
    names = set()
    for i in infos:
        n = i.filename.replace("\\", "/")
        p = Path(n)
        
        # Security checks: no absolute paths, no directory traversal, no duplicate names
        if p.is_absolute() or ".." in n.split("/") or n in names:
            raise ValueError(f"Unsafe ZIP member path detected: {n}")
            
        if not i.is_dir() and i.file_size > MAX_MEMBER:
            raise ValueError(f"Oversized ZIP member ({i.file_size} bytes): {n}")
            
        names.add(n)
        total += i.file_size
        if total > MAX_TOTAL:
            raise ValueError(f"Archive uncompressed size limit exceeded ({total} bytes)")
            
    return names


def discover_root_prefix(names: Set[str], required: Tuple[str, ...] = REQUIRED) -> str:
    """Discover root prefix inside ZIP archive containing all required folders."""
    # Case 1: Required folders are directly at root of ZIP
    if all(any(n.startswith(d + "/") for n in names) for d in required):
        return ""
        
    # Case 2: Required folders are inside a single top-level folder (e.g. PS02_demo_data/)
    top_dirs = {n.split("/")[0] for n in names if "/" in n}
    for p in top_dirs:
        prefix = f"{p}/"
        if all(any(n.startswith(f"{prefix}{d}/") for n in names) for d in required):
            return prefix
            
    # Case 3: Nested candidate search
    for p in top_dirs:
        sub_dirs = {n.split("/")[1] for n in names if n.startswith(f"{p}/") and len(n.split("/")) > 2}
        for sub in sub_dirs:
            prefix = f"{p}/{sub}/"
            if all(any(n.startswith(f"{prefix}{d}/") for n in names) for d in required):
                return prefix

    raise ValueError(f"Dataset root containing required folders {required} not found in ZIP")


def csv_rows(data: bytes) -> List[Dict[str, str]]:
    """Decode and parse CSV bytes safely handling UTF-8 BOM."""
    text = data.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(text.splitlines()))


def audit(source: Path) -> Dict[str, Any]:
    """Execute complete aggregate-only preflight audit on dataset ZIP or directory."""
    findings: List[Dict[str, Any]] = []
    counts: Dict[str, Any] = {}
    platforms: Dict[str, int] = {}
    poster_verified = 0
    poster_mismatch = 0
    poster_missing = 0
    
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(f"Dataset source path does not exist: {source}")

    file_size_bytes = source.stat().st_size if source.is_file() else 0
    file_sha256 = ""
    
    def note(code: str, count: int, detail: str, severity: str = "error"):
        if count:
            findings.append({"code": code, "severity": severity, "count": count, "detail": detail})

    if source.is_dir():
        root = source
        if not all((root / d).is_dir() for d in REQUIRED):
            roots = [p for p in root.iterdir() if p.is_dir() and all((p / d).is_dir() for d in REQUIRED)]
            if len(roots) != 1:
                raise ValueError("Dataset root containing required directories not found")
            root = roots[0]
        read = lambda rel: (root / rel).read_bytes()
        files = lambda d: [p.relative_to(root).as_posix() for p in (root / d).rglob("*") if p.is_file()]
    else:
        # Compute archive SHA-256
        hasher = hashlib.sha256()
        with open(source, "rb") as sf:
            while chunk := sf.read(1024 * 1024):
                hasher.update(chunk)
        file_sha256 = hasher.hexdigest()

        z = zipfile.ZipFile(source)
        names = safe_zip(z)
        rootprefix = discover_root_prefix(names, REQUIRED)
        read = lambda rel: z.read(rootprefix + rel)
        files = lambda d: [n[len(rootprefix):] for n in names if n.startswith(rootprefix + d + "/") and not n.endswith("/")]

    # Check required folders
    for d in REQUIRED:
        found_files = files(d)
        if not found_files:
            note("required_folder_empty", 1, f"Required folder {d} has no files", "error")

    # 1. Telegram exports audit
    telegram_files = [n for n in files(REQUIRED[0]) if n.endswith(".json")]
    msgs = services = photos = empty_text = forward_count = reply_count = edit_count = 0
    telegram_channels = []
    telegram_photos_found = 0
    telegram_photos_missing = 0

    all_tg_photo_files = {p for p in files(REQUIRED[0]) if p.endswith(".jpg") or p.endswith(".png")}

    for f in telegram_files:
        try:
            obj = json.loads(read(f))
            records = obj.get("messages", [])
            ch_name = obj.get("name", Path(f).parent.name)
            ch_msgs = sum(1 for r in records if r.get("type") == "message")
            ch_services = sum(1 for r in records if r.get("type") != "message")
            ch_photos = 0
            
            ch_dir = str(Path(f).parent).replace("\\", "/")
            for r in records:
                if r.get("type") == "message" and r.get("photo"):
                    ch_photos += 1
                    photo_rel = r.get("photo")
                    expected_path = f"{ch_dir}/{photo_rel}" if not photo_rel.startswith(ch_dir) else photo_rel
                    if expected_path in all_tg_photo_files or any(p.endswith(Path(photo_rel).name) for p in all_tg_photo_files):
                        telegram_photos_found += 1
                    else:
                        telegram_photos_missing += 1

            msgs += ch_msgs
            services += ch_services
            photos += ch_photos
            empty_text += sum(1 for r in records if r.get("type") == "message" and not r.get("text"))
            forward_count += sum(1 for r in records if r.get("forwarded_from"))
            reply_count += sum(1 for r in records if r.get("reply_to_message_id"))
            edit_count += sum(1 for r in records if r.get("edited"))

            telegram_channels.append({
                "channel_folder": Path(f).parent.name,
                "name": ch_name,
                "total_records": len(records),
                "messages": ch_msgs,
                "services": ch_services,
                "photos": ch_photos,
            })
        except Exception as e:
            note("malformed_telegram_json", 1, f"Failed to parse {f}: {e}", "error")

    counts.update({
        "telegram_exports": len(telegram_files),
        "telegram_messages": msgs,
        "telegram_service_records": services,
        "telegram_photo_references": photos,
        "telegram_photos_found": telegram_photos_found,
        "telegram_photos_missing": telegram_photos_missing,
        "telegram_empty_text_records": empty_text,
        "telegram_forwarded_records": forward_count,
        "telegram_reply_records": reply_count,
        "telegram_edited_records": edit_count,
        "telegram_channels_summary": telegram_channels,
    })

    # 2. Social Media CSV audit
    social_csv_files = [n for n in files(REQUIRED[1]) if n.endswith(".csv")]
    social_posts = 0
    social_with_images = 0
    social_image_refs_found = 0
    social_image_refs_missing = 0
    all_social_image_files = {Path(p).name.lower() for p in files(REQUIRED[1]) if Path(p).suffix.lower() in (".jpg", ".jpeg", ".png")}

    for f in social_csv_files:
        try:
            rows = csv_rows(read(f))
            social_posts += len(rows)
            for r in rows:
                p_name = r.get("platform", "unknown").strip()
                platforms[p_name] = platforms.get(p_name, 0) + 1
                img_ref = r.get("image_file", "").strip()
                if img_ref and img_ref.lower() != "none":
                    social_with_images += 1
                    img_filename = Path(img_ref).name.lower()
                    if img_filename in all_social_image_files:
                        social_image_refs_found += 1
                    else:
                        social_image_refs_missing += 1
        except Exception as e:
            note("malformed_social_csv", 1, f"Failed to parse {f}: {e}", "error")

    counts.update({
        "social_csv_files": len(social_csv_files),
        "social_posts": social_posts,
        "platform_counts": platforms,
        "social_posts_with_image_ref": social_with_images,
        "social_image_refs_found": social_image_refs_found,
        "social_image_refs_missing": social_image_refs_missing,
        "social_images_in_archive": len(all_social_image_files),
    })

    # 3. Poster images & SHA-256 manifest verification
    poster_files = [f for f in files(REQUIRED[2] + "/posters") if Path(f).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    idx_files = [n for n in files(REQUIRED[2]) if n.endswith(".csv")]
    poster_index_rows = 0
    poster_details = []

    if idx_files:
        try:
            rows = csv_rows(read(idx_files[0]))
            poster_index_rows = len(rows)
            for r in rows:
                name = r.get("image", "").strip()
                digest = r.get("sha256", "").strip()
                match_status = "missing"
                actual_sha256 = ""
                if name and digest:
                    target_path = f"{REQUIRED[2]}/posters/{name}"
                    try:
                        poster_bytes = read(target_path)
                        actual_sha256 = hashlib.sha256(poster_bytes).hexdigest().lower()
                        if actual_sha256 == digest.lower():
                            poster_verified += 1
                            match_status = "verified"
                        else:
                            poster_mismatch += 1
                            match_status = "mismatch"
                    except Exception:
                        poster_missing += 1
                        match_status = "missing"

                poster_details.append({
                    "image": name,
                    "expected_sha256": digest,
                    "actual_sha256": actual_sha256,
                    "status": match_status,
                })

            counts["poster_index_rows"] = poster_index_rows
            counts["poster_hashes_verified"] = poster_verified
            counts["poster_hashes_mismatch"] = poster_mismatch
            counts["poster_hashes_missing"] = poster_missing
            counts["poster_details"] = poster_details
            
            if poster_mismatch > 0:
                note("poster_hash_mismatch", poster_mismatch, f"{poster_mismatch} poster images failed SHA-256 match")
            if poster_missing > 0:
                note("poster_missing_file", poster_missing, f"{poster_missing} poster manifest files not found in archive")
        except Exception as e:
            note("poster_manifest_error", 1, f"Error reading poster index {idx_files[0]}: {e}")
            
    counts["poster_files"] = len(poster_files)

    # 4. Slang Lexicon audit
    lex_files = [n for n in files(REQUIRED[3]) if n.endswith(".csv")]
    lexicon_rows = 0
    lexicon_categories = {}
    for f in lex_files:
        try:
            l_rows = csv_rows(read(f))
            lexicon_rows += len(l_rows)
            for lr in l_rows:
                cat = lr.get("category", "general").strip()
                lexicon_categories[cat] = lexicon_categories.get(cat, 0) + 1
        except Exception as e:
            note("malformed_lexicon_csv", 1, f"Error reading lexicon {f}: {e}")
    counts["lexicon_files"] = len(lex_files)
    counts["lexicon_rows"] = lexicon_rows
    counts["lexicon_categories"] = lexicon_categories

    # 5. Combined totals
    counts["total_message_and_post_records"] = msgs + social_posts
    counts["total_raw_records"] = msgs + services + social_posts

    # Compile report
    passed = len([f for f in findings if f["severity"] == "error"]) == 0
    report = {
        "report_version": 1,
        "scope": "aggregate_only_offline",
        "timestamp_ist": datetime.now(IST).isoformat(),
        "archive_metadata": {
            "source_name": source.name,
            "source_path": str(source.resolve()),
            "size_bytes": file_size_bytes,
            "sha256": file_sha256,
        },
        "counts": counts,
        "findings": findings,
        "passed": passed,
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PS02 Dataset Preflight Auditor")
    parser.add_argument("--dataset", required=True, help="Path to PS02 demo dataset ZIP or folder")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    try:
        res = audit(Path(args.dataset))
    except Exception as e:
        print(f"Preflight failed: {e}")
        raise SystemExit(2)

    out_text = json.dumps(res, indent=2)
    if args.output:
        Path(args.output).write_text(out_text + "\n", encoding="utf-8")
        print(f"Wrote preflight audit to {args.output}")
    else:
        print(out_text)

    has_errors = any(f.get("severity") == "error" for f in res.get("findings", []))
    raise SystemExit(1 if has_errors else 0)
