#!/usr/bin/env python3
"""CLI wrapper for PS02 dataset preflight inspection.

Aggregate-only structural preflight for participant-facing PS02 demo data.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ps02_dataset.preflight import audit, safe_zip

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
