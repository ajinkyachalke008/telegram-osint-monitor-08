"""Verification script to prove the complete OSINT intelligence flow:
Flagged post -> Extracted identifiers -> Cryptographic evidence hash verification -> Cross-channel graph (3+ channels).
"""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import Database
from addons.evidence import canonical_json

def main():
    db = Database()
    print("=================================================================")
    print(" 1. FLAGGED POST & THREAT ALERT")
    print("=================================================================")
    alerts = db.list_alerts(limit=5)
    if not alerts:
        print("No alerts found in DB.")
        return

    sample = alerts[0]
    print(f"Alert ID:       {sample['alert_id']}")
    print(f"Post UID:       {sample['post_uid']}")
    print(f"Channel:        {sample['channel_id']} ({sample['platform']})")
    print(f"Category:       {sample['category']}")
    print(f"Risk Level:     {sample['risk_level']} (Threat Score: {sample['threat_score']:.1f}/10)")
    print(f"Timestamp:      {sample['timestamp_utc']}")
    print(f"Raw Text:       {sample['raw_text'][:120]}...")

    print("\n=================================================================")
    print(" 2. EXTRACTED ACTIONABLE IDENTIFIERS")
    print("=================================================================")
    post_uid = sample['post_uid']
    idents = db.get_post_identifiers(post_uid)
    for i in idents:
        print(f"  • [{i['type']}] {i['normalized_value']} (channel_count: {i['channel_count']}, cross_channel: {bool(i['cross_channel'])})")

    print("\n=================================================================")
    print(" 3. CRYPTOGRAPHIC EVIDENCE SEAL & HASH CHAIN INTEGRITY")
    print("=================================================================")
    with db.get_connection() as conn:
        ev = conn.execute("SELECT * FROM evidence WHERE post_uid = ?", (post_uid,)).fetchone()
    if ev:
        print(f"Block Height:   #{ev['block_height']}")
        print(f"Current Hash:   {ev['current_hash']}")
        print(f"Previous Hash:  {ev['prev_hash']}")
        payload = f"{ev['canonical_json']}:{ev['prev_hash']}"
        computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        is_valid = (computed == ev['current_hash'])
        print(f"Re-computed:    {computed}")
        print(f"Chain Validity: {'TAMPER-EVIDENT VALID (100% MATCH)' if is_valid else 'FAILED'}")

    print("\n=================================================================")
    print(" 4. CROSS-CHANNEL GRAPH SYNDICATE (IDENTIFIER IN 3+ CHANNELS)")
    print("=================================================================")
    cross_actors = db.list_cross_channel_identifiers()
    found_3plus = False
    for ca in cross_actors:
        linked = ca.get('linked_channels', [])
        if len(linked) >= 3 or ca.get('channel_count', 0) >= 3:
            found_3plus = True
            print(f"🚨 IDENTIFIER OPERATING IN 3+ CHANNELS:")
            print(f"   Identifier Value: {ca['normalized_value']} ({ca['type']})")
            print(f"   Channel Count:    {len(linked)} distinct public channels")
            print(f"   Linked Channels:  {linked}")
            print(f"   First Seen:       {ca['first_seen']}")
            print(f"   Last Seen:        {ca['last_seen']}")

    if not found_3plus:
        print("No identifier active in 3+ channels found yet.")

if __name__ == "__main__":
    main()
