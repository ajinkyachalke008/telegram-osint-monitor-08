"""Comprehensive diagnostic and verification script for all dashboard pages and subsystems."""
import os
import sys
import json
import hashlib
import sqlite3
from pathlib import Path

# Add project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import Database, get_default_db_path, DEFAULT_DB_PATH
from addons.pdf_exporter import generate_evidence_pdf
from addons.extractors import extract_locations, extract_all_entities
from addons.financial_detector import FinancialAdDetector
from dashboard.similarity import find_text_ad_clusters
from dashboard.graph import (
    build_entity_graph,
    calculate_centrality,
    plot_entity_graph,
    get_cross_channel_identifiers,
    get_connected_syndicates,
    generate_seller_profile
)

def test_evidence_verification(mode_name, env_val):
    os.environ["DEMO_MODE"] = env_val
    db_path = get_default_db_path()
    print(f"\n--- Testing Evidence Verification for {mode_name} ({db_path.name}) ---")
    db = Database(db_path)
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT a.alert_id, e.canonical_json, e.prev_hash, e.current_hash, e.block_height "
            "FROM alerts a JOIN evidence e ON a.post_uid = e.post_uid LIMIT 5"
        ).fetchall()
        print(f"Alerts with evidence count: {len(rows)}")
        for r in rows:
            payload = f"{r['canonical_json']}:{r['prev_hash']}"
            h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            matched = (h == r["current_hash"])
            print(f"  Alert {r['alert_id']} (Block #{r['block_height']}): match={matched}")
            assert matched, f"Hash mismatch for alert {r['alert_id']}"

def test_entity_graph_subsystem():
    print("\n--- Testing Entity Graph Subsystem ---")
    os.environ["DEMO_MODE"] = "1"
    db = Database()
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT p.post_uid, p.channel_id as source, p.message_id as post_id, p.raw_text as text, "
            "p.category as primary_category, p.risk_level, p.threat_score, p.timestamp_utc as timestamp "
            "FROM posts p ORDER BY p.timestamp_utc DESC LIMIT 200"
        ).fetchall()
        posts = [dict(r) for r in rows]

    G = build_entity_graph(posts)
    calculate_centrality(G)
    cross_actors = get_cross_channel_identifiers(G)
    syndicates = get_connected_syndicates(G)
    print(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges, {len(cross_actors)} cross-channel actors, {len(syndicates)} syndicates")

    for mode in ["smart", "cross_only", "all", "hover_only"]:
        fig = plot_entity_graph(G, title="Test Graph", label_mode=mode)
        print(f"  plot_entity_graph(label_mode='{mode}'): OK ({len(fig.data)} traces)")

def test_seller_profile():
    print("\n--- Testing Seller Profile Generation ---")
    os.environ["DEMO_MODE"] = "1"
    db = Database()
    prof = generate_seller_profile("mule.syndicate@ybl", db)
    print(f"Seller profile for 'mule.syndicate@ybl': found={prof.get('found')}, channels={prof.get('channel_count')}")

def test_pdf_generation():
    print("\n--- Testing PDF Evidence Export ---")
    os.environ["DEMO_MODE"] = "1"
    db = Database()
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT a.alert_id, a.post_uid, a.category, a.risk_level, a.threat_score, a.status, "
            "p.channel_id, p.platform, p.message_id, p.timestamp_utc, p.raw_text, p.ingestion_source, "
            "e.evidence_id, e.canonical_json, e.current_hash, e.prev_hash, e.block_height, e.generated_at_utc "
            "FROM alerts a JOIN posts p ON a.post_uid = p.post_uid "
            "LEFT JOIN evidence e ON a.post_uid = e.post_uid LIMIT 1"
        ).fetchone()
        if row:
            alert = dict(row)
            idents = db.get_post_identifiers(alert["post_uid"])
            pdf_bytes = generate_evidence_pdf(
                alert=alert,
                evidence=alert,
                identifiers=idents,
                chain_head_hash="0"*64
            )
            print(f"PDF generated: {len(pdf_bytes):,} bytes")
            assert len(pdf_bytes) > 1000, "PDF export produced empty file"

if __name__ == "__main__":
    test_evidence_verification("DEMO_MODE=1", "1")
    test_entity_graph_subsystem()
    test_seller_profile()
    test_pdf_generation()
    print("\n🎉 ALL CORE DASHBOARD SUBSYSTEM TESTS PASSED WITH ZERO ERRORS!")
