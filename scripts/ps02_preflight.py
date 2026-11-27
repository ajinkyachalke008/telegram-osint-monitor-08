#!/usr/bin/env python3
"""Aggregate-only structural preflight for participant-facing PS02 demo data.

No text, usernames, payment/contact identifiers, profile data, or cross-platform
relationships are extracted or emitted. ZIP members are inspected in place.
"""
import argparse, csv, hashlib, json, zipfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

REQUIRED=("01_telegram_exports","02_social_media","03_images","04_lexicon")
MAX_ENTRIES=20000
MAX_MEMBER=128*1024*1024
MAX_TOTAL=1024*1024*1024

def safe_zip(z):
    infos=z.infolist()
    if len(infos)>MAX_ENTRIES: raise ValueError("Archive entry limit exceeded")
    total=0; names=set()
    for i in infos:
        n=i.filename.replace("\\","/")
        p=Path(n)
        if p.is_absolute() or ".." in n.split("/") or n in names or i.is_dir() is False and i.file_size>MAX_MEMBER:
            raise ValueError("Unsafe or oversized ZIP member")
        names.add(n); total+=i.file_size
        if total>MAX_TOTAL: raise ValueError("Archive size limit exceeded")
    return names

def csv_rows(data):
    return list(csv.DictReader(data.decode("utf-8-sig").splitlines()))

def audit(source):
    findings=[]; counts={}; platforms={}; poster_verified=0
    def note(code,count,detail):
        if count: findings.append({"code":code,"severity":"error","count":count,"detail":detail})
    if source.is_dir():
        root=source
        if not all((root/d).is_dir() for d in REQUIRED):
            roots=[p for p in root.iterdir() if p.is_dir() and all((p/d).is_dir() for d in REQUIRED)]
            if len(roots)!=1: raise ValueError("Dataset root not found")
            root=roots[0]
        read=lambda rel: (root/rel).read_bytes()
        files=lambda d: [p.relative_to(root).as_posix() for p in (root/d).rglob("*") if p.is_file()]
    else:
        z=zipfile.ZipFile(source); names=safe_zip(z)
        prefixes=[n.split("/")[0] for n in names]
        rootprefix=next((p+"/" for p in set(prefixes) if all(any(n.startswith(p+d+"/") for n in names) for d in REQUIRED)), "")
        if not rootprefix: raise ValueError("Dataset root not found in ZIP")
        read=lambda rel: z.read(rootprefix+rel)
        files=lambda d: [n[len(rootprefix):] for n in names if n.startswith(rootprefix+d+"/") and not n.endswith("/")]

    for d in REQUIRED:
        if not files(d): note("required_folder_empty",1,d)
    telegram_files=[n for n in files(REQUIRED[0]) if n.endswith(".json")]
    msgs=services=photos=0
    for f in telegram_files:
        obj=json.loads(read(f)); records=obj.get("messages",[])
        msgs+=sum(1 for r in records if r.get("type")=="message")
        services+=sum(1 for r in records if r.get("type")!="message")
        photos+=sum(1 for r in records if r.get("type")=="message" and r.get("photo"))
    counts.update(telegram_exports=len(telegram_files),telegram_messages=msgs,telegram_service_records=services,telegram_photo_references=photos)
    social=[n for n in files(REQUIRED[1]) if n.endswith(".csv")]
    social_posts=0
    for f in social:
        rows=csv_rows(read(f)); social_posts+=len(rows)
        for r in rows:
            platform=r.get("platform","unknown")
            platforms[platform]=platforms.get(platform,0)+1
    counts.update(social_csv_files=len(social),social_posts=social_posts,platform_counts=platforms)
    poster_files=files(REQUIRED[2]+"/posters")
    idx=[n for n in files(REQUIRED[2]) if n.endswith(".csv") and "sha256" in n.lower()]
    if idx:
        rows=csv_rows(read(idx[0]))
        for r in rows:
            name=r.get("image",""); digest=r.get("sha256","")
            if name and digest:
                try: poster_verified+=hashlib.sha256(read(REQUIRED[2]+"/posters/"+name)).hexdigest().lower()==digest.lower()
                except Exception: pass
        counts["poster_index_rows"]=len(rows); counts["poster_hashes_verified"]=poster_verified
        note("poster_hash_mismatch",len(rows)-poster_verified,"Poster hash checks failed")
    counts["poster_files"]=len(poster_files)
    lex=[n for n in files(REQUIRED[3]) if n.endswith(".csv")]
    counts["lexicon_rows"]=sum(len(csv_rows(read(n))) for n in lex)
    report={"report_version":1,"scope":"aggregate_only_offline","counts":counts,"findings":findings,"passed":not findings}
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--dataset",required=True); ap.add_argument("--output")
    args=ap.parse_args()
    try: result=audit(Path(args.dataset))
    except Exception as e: print("Preflight failed:",str(e)); raise SystemExit(2)
    out=json.dumps(result,indent=2)
    if args.output: Path(args.output).write_text(out+"\n",encoding="utf-8")
    else: print(out)
    raise SystemExit(1 if result["findings"] else 0)
