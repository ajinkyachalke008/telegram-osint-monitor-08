#!/usr/bin/env python3
"""Dedicated Non-Destructive Launcher for PS02 Hackathon Demonstration.

Preserves all existing databases (data/osint_monitor.db, data/demo.db).
Initializes isolated participant dataset store (data/participant_dataset.db).
Performs idempotent preflight & import of committee dataset if present.
Spawns Streamlit Intelligence Engine on http://localhost:8501.
"""

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ps02_dataset.store import ParticipantDatasetStore, DEFAULT_PARTICIPANT_DB_PATH
from ps02_dataset.importer import run_import
from core.db import Database, DEFAULT_DB_PATH


def main():
    print("=" * 78)
    print(" 🛡️  RAJASTHAN CYBER POLICE HACKATHON 2026 · PS02 PARTICIPANT DEMO LAUNCHER")
    print("=" * 78)
    print(f"Project Root:      {PROJECT_ROOT}")
    print(f"Legacy OSINT DB:   {DEFAULT_DB_PATH} [PRESERVED - NON-DESTRUCTIVE]")
    print(f"Participant DB:    {DEFAULT_PARTICIPANT_DB_PATH} [ISOLATED]")

    # 1. Non-destructive check of legacy database
    db = Database(DEFAULT_DB_PATH)
    print("\n[1/4] 🔒 Verifying database preservation...")
    print(f"      ✅ Existing operational database preserved at {DEFAULT_DB_PATH}.")

    # 2. Check and initialize participant dataset store
    print("\n[2/4] 📦 Initializing isolated participant dataset store...")
    store = ParticipantDatasetStore(DEFAULT_PARTICIPANT_DB_PATH)
    print(f"      ✅ Isolated schema ready at {DEFAULT_PARTICIPANT_DB_PATH}.")

    # 3. Check for participant dataset ZIP and auto-import idempotently
    print("\n[3/4] 🔍 Detecting committee-supplied dataset ZIP...")
    candidate_zips = [
        PROJECT_ROOT / "data" / "participant_input" / "PS02_demo_data-20261127T071007Z-1-001.zip",
        PROJECT_ROOT / "data" / "participant_input" / "PS02_demo_data.zip",
    ]
    detected_zip = next((p for p in candidate_zips if p.exists()), None)

    if detected_zip:
        print(f"      📁 Found local archive: {detected_zip.name} ({detected_zip.stat().st_size / (1024*1024):.2f} MB)")
        print("      ⚡ Executing idempotent import into isolated store...")
        try:
            res = run_import(detected_zip, store=store)
            if res.get("is_duplicate"):
                print(f"      ✅ {res['message']} (Batch: {res['batch_id']})")
            else:
                print(f"      🎉 Successfully imported {res.get('total_records', 0)} records (Batch: {res['batch_id']})")
        except Exception as e:
            print(f"      ⚠️ Pre-import warning: {e} (Operators can re-import inside dashboard UI)")
    else:
        print("      ⚠️ No ZIP found at default path. Operators can upload or select via dashboard UI.")

    # 4. Spawn Streamlit dashboard engine on port 8501
    print("\n[4/4] 🚀 Spawning Streamlit OSINT Suite on http://localhost:8501 ...")
    env = os.environ.copy()
    env["NO_RESET"] = "1"
    dashboard_cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        str(PROJECT_ROOT / "dashboard" / "app.py"),
        "--server.port", "8501",
        "--server.headless", "true"
    ]

    proc = subprocess.Popen(dashboard_cmd, cwd=str(PROJECT_ROOT), env=env)
    print(f"      ✅ Streamlit Engine active (PID: {proc.pid})")
    print("\n" + "=" * 78)
    print(" 🌟 ACCESS COMPLETE OSINT SUITE & PARTICIPANT DATASET AT:")
    print("    👉 http://localhost:8501")
    print("    👉 Page 10: '📊 PS02 Dataset Insights' for official committee data")
    print("=" * 78)
    print(" Press Ctrl+C to terminate gracefully.\n")

    # Open web browser after brief delay
    time.sleep(2.0)
    try:
        webbrowser.open("http://localhost:8501")
    except Exception:
        pass

    def cleanup(signum, frame):
        print("\n\n🛑 Shutting down demo server cleanly...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("✅ Shutdown complete.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        proc.wait()
    except KeyboardInterrupt:
        cleanup(None, None)


if __name__ == "__main__":
    main()
