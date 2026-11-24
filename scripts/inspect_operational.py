"""Inspect posts and entities in operational.db."""
import os
import sys
from pathlib import Path

os.environ["DEMO_MODE"] = "0"
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import Database

db = Database("data/operational.db")
posts = db.list_posts(limit=100)
evidence = db.get_all_evidence_blocks()
alerts = db.list_alerts()

print(f"=== OPERATIONAL DB SUMMARY ===")
print(f"Total Posts: {len(posts)}")
print(f"Total Evidence Blocks: {len(evidence)}")
print(f"Total Alerts: {len(alerts)}")

print("\n--- Posts Breakdown ---")
for p in posts:
    idents = [i["identifier_id"] for i in db.get_post_identifiers(p["post_uid"])]
    clean_text = p["raw_text"].replace("\n", " ")[:90]
    print(f"[@{p['channel_id']}] Msg #{p['message_id']} ({p['timestamp_utc'][:19]}) | Cat: {p['category']} | Risk: {p['risk_level']} (Score: {p['threat_score']}) | Idents: {idents}")
    print(f"     \"{clean_text}\"")

with db.get_connection() as conn:
    edges = conn.execute("SELECT * FROM entities_edges").fetchall()
    idents = conn.execute("SELECT * FROM identifiers").fetchall()

print(f"\n--- Extracted Identifiers ({len(idents)}) ---")
for i in idents:
    print(f"  - [{i['type']}] {i['identifier_id']} (Normalized: {i['normalized_value']})")

print(f"\n--- Knowledge Graph Edges ({len(edges)}) ---")
for e in edges:
    print(f"  - ({e['source_id']}) --[{e['relation']}]--> ({e['target_id']})")
