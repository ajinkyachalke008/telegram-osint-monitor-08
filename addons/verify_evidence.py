"""Standalone CLI Tool to Verify Cryptographic Chain of Custody Ledger."""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import Database, DEFAULT_DB_PATH
from addons.evidence import verify_evidence_chain


def main():
    parser = argparse.ArgumentParser(description="Verify cryptographic integrity of OSINT evidence chain.")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    db = Database(db_path)
    blocks = db.get_all_evidence_blocks()

    print("=" * 72)
    print(" CRYPTOGRAPHIC EVIDENCE CHAIN VERIFICATION (RFC-8785 SHA-256)")
    print(f" Database: {db_path}")
    print(f" Total Blocks Found: {len(blocks)}")
    print("=" * 72)

    is_valid, msg, count = verify_evidence_chain(blocks)

    if is_valid:
        print(f"Verification Status: SUCCESS (100% Cryptographic Match) ✅")
        print(f"Chain Integrity:    {msg}")
        if blocks:
            head = max(blocks, key=lambda b: b.get("block_height", b.block_height if hasattr(b, "block_height") else 0))
            genesis = min(blocks, key=lambda b: b.get("block_height", b.block_height if hasattr(b, "block_height") else 0))
            head_h = head.get("block_height", getattr(head, "block_height", 0))
            head_hash = head.get("current_hash", getattr(head, "current_hash", ""))
            genesis_hash = genesis.get("current_hash", getattr(genesis, "current_hash", ""))
            print("-" * 72)
            print(f"Genesis Block (#1) Hash:   {genesis_hash}")
            print(f"Chain Head Block Height:   #{head_h}")
            print(f"Chain Head SHA-256 Hash:   {head_hash}")
            print("-" * 72)
        print("Tamper Status: UNBROKEN & VALID")
        print("=" * 72)
        sys.exit(0)
    else:
        print(f"INTEGRITY FAILURE: {msg}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
