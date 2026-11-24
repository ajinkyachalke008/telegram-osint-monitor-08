"""Scripted Demo Post Injector for Evaluator Live Demonstration."""
import time
from typing import Dict, Any, Optional

from core.db import Database
from core.models import PostRecord, IdentifierRecord, AlertRecord, now_utc_iso
from core.normalizer import normalize_text
from addons.extractors import extract_all_entities
from addons.scorer import RuleScorer
from addons.evidence import build_chained_evidence_block

SCRIPTED_DEMO_POST_TEXT = (
    "Fresh ICICI current account and ATM card available for rent. "
    "High limit load, zero dispute. Commission 15% daily. "
    "Ping @fast_cash_hub or UPI mule.syndicate@ybl or Call +919000011111."
)
SCRIPTED_DEMO_CHANNEL = "t.me/delhi_classifieds_demo"


def inject_scripted_demo_post(db: Optional[Database] = None) -> Dict[str, Any]:
    """Ingest one fixed post containing mule.syndicate@ybl through the full pipeline.
    
    Pipeline stages:
    1. Text Normalization
    2. Entity & Payment Extraction (channel handle excluded from seller identifiers)
    3. Classification & Threat Risk Scoring
    4. Post Insertion (with unique runtime message ID)
    5. Identifier upsert & cross-channel edge linking
    6. SHA-256 Chained Evidence Block Generation & Recording
    7. Actionable Alert Creation
    8. Audit Log Recording
    
    Returns:
        Dict with post_uid, alert_id, block_height, current_hash, category, risk_level, channel_id.
    """
    db = db or Database()
    if db.is_operational or db.db_path.name == "operational.db":
        raise PermissionError("FATAL: Injection of scripted demo posts is strictly prohibited on operational.db!")
    scorer = RuleScorer()
    
    timestamp_utc = now_utc_iso()
    runtime_suffix = int(time.time() * 1000)
    message_id = f"scripted_{runtime_suffix}"
    
    post = PostRecord(
        platform="telegram",
        channel_id=SCRIPTED_DEMO_CHANNEL,
        message_id=message_id,
        timestamp_utc=timestamp_utc,
        raw_text=SCRIPTED_DEMO_POST_TEXT,
        ingestion_source="VERIFIED-SYNTHETIC"
    )
    
    # 1. Normalization
    post.normalized_text = normalize_text(post.raw_text)
    
    # 2. Extraction & Classification / Risk scoring
    extracted = extract_all_entities(post.normalized_text, channel_handle=post.channel_id)
    score_res = scorer.score(post.normalized_text, identifiers=extracted)
    post.category = score_res.primary_category or "bank_account"
    post.risk_level = score_res.risk_level
    post.threat_score = score_res.total_score
    
    # 3. Post Insertion
    db.insert_post(post)
    
    # 4. Identifier Linking (excluding channel's own handle)
    channel_slug = post.channel_id.strip().lower().lstrip('@')
    if "t.me/" in channel_slug:
        channel_slug = channel_slug.split("t.me/")[-1].strip("/@")

    for ent in extracted.get("all_flat", []):
        val = ent["value"]
        etype = ent["type"]
        val_clean = str(val).strip().lower().lstrip('@')
        if "t.me/" in val_clean:
            val_clean = val_clean.split("t.me/")[-1].strip("/@")

        if etype in ("Username", "TelegramLink") and val_clean == channel_slug:
            continue

        ident_id = f"{etype.lower()}:{val}"
        db.upsert_identifier(
            IdentifierRecord(
                identifier_id=ident_id,
                type=etype,
                raw_value=val,
                normalized_value=val,
                first_seen=post.timestamp_utc,
                last_seen=post.timestamp_utc
            ),
            channel_id=post.channel_id
        )
        db.link_post_identifier(post.post_uid, ident_id)
        db.upsert_edge(post.channel_id, ident_id, "mentions")
        
    # 5. Evidence Block
    ev_block = build_chained_evidence_block(
        db, post.post_uid, post.channel_id, post.message_id, post.timestamp_utc, post.raw_text
    )
    db.record_evidence_block(ev_block)
    
    # 6. Actionable Alert Creation
    alert_id = f"ALT-{ev_block.current_hash[:10].upper()}"
    alert = AlertRecord(
        alert_id=alert_id,
        post_uid=post.post_uid,
        category=post.category,
        risk_level=post.risk_level,
        threat_score=post.threat_score,
        matched_terms=score_res.matched_terms,
        status="new"
    )
    db.create_alert(alert)
    
    # 7. Audit Log
    db.log_audit("inject_scripted_demo_post", {
        "post_uid": post.post_uid,
        "alert_id": alert_id,
        "block_height": ev_block.block_height,
        "current_hash": ev_block.current_hash,
        "target_upi": "mule.syndicate@ybl",
        "channel_id": post.channel_id,
        "timestamp": timestamp_utc
    })
    
    return {
        "post_uid": post.post_uid,
        "alert_id": alert_id,
        "block_height": ev_block.block_height,
        "current_hash": ev_block.current_hash,
        "raw_text": post.raw_text,
        "channel_id": post.channel_id,
        "category": post.category,
        "risk_level": post.risk_level,
        "threat_score": post.threat_score
    }
