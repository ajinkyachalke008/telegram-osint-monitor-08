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

    print(f"Loaded {len(blocks)} evidence blocks from {db_path}")
    is_valid, msg, count = verify_evidence_chain(blocks)

    if is_valid:
        print(f"SUCCESS: {msg}")
        sys.exit(0)
    else:
        print(f"INTEGRITY FAILURE: {msg}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
