"""One-Command Demonstration Launcher for telegram-osint-monitor-08 OSINT Monitor.

Performs:
1. Database reset (data/osint_monitor.db) & initial baseline demo data seeding
2. Spawns background streaming replay worker (one post every ~5s)
3. Spawns Streamlit OSINT dashboard on port 8501
4. Automatically opens web browser to http://localhost:8501
5. Gracefully handles shutdown on Ctrl+C
"""
import os
import sys
import time
import signal
import subprocess
import webbrowser
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db import Database, DEFAULT_DB_PATH
from scripts.generate_demo_data import seed_demo_database


def main():
    print("=" * 76)
    print("       🛡️  telegram-osint-monitor-08 Threat Intelligence - 1-Command Demo")
    print("=" * 76)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Database:     {DEFAULT_DB_PATH}")

    # 1. Reset database and seed baseline demo records
    print("\n[1/4] 🔄 Resetting database & seeding baseline demo records...")
    db = Database(DEFAULT_DB_PATH)
    count = seed_demo_database(db=db, reset=True)
    print(f"      ✅ Seeded {count} baseline posts with RFC-8785 SHA-256 evidence chain.")

    # 2. Spawn background replay worker (one post every ~5s)
    print("\n[2/4] 📡 Starting streaming replay worker (1 post every ~5s)...")
    replay_cmd = [
        sys.executable,
        str(PROJECT_ROOT / "ingestion" / "replay.py"),
        "--interval", "5.0",
        "--loop"
    ]
    replay_proc = subprocess.Popen(
        replay_cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(f"      ✅ Replay worker running in background (PID: {replay_proc.pid})")

    # 3. Spawn Streamlit dashboard (with DEMO_MODE=1)
    print("\n[3/4] 🚀 Starting Streamlit OSINT Dashboard on http://localhost:8501 ...")
    dashboard_cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        str(PROJECT_ROOT / "dashboard" / "app.py"),
        "--server.port", "8501",
        "--server.headless", "true"
    ]
    dashboard_env = os.environ.copy()
    dashboard_env["DEMO_MODE"] = "1"
    dashboard_proc = subprocess.Popen(
        dashboard_cmd,
        cwd=str(PROJECT_ROOT),
        env=dashboard_env
    )
    print(f"      ✅ Dashboard process started (PID: {dashboard_proc.pid})")

    # 4. Open browser
    print("\n[4/4] 🌐 Opening browser to http://localhost:8501 ...")
    time.sleep(2.5)
    webbrowser.open("http://localhost:8501")

    print("\n" + "=" * 76)
    print("  🎉 DEMO IS LIVE! Press Ctrl+C at any time to shut down gracefully.")
    print("=" * 76 + "\n")

    def handle_exit(sig, frame):
        print("\n[telegram-osint-monitor-08] Shutting down demo processes...")
        try:
            replay_proc.terminate()
            dashboard_proc.terminate()
        except Exception:
            pass
        print("[telegram-osint-monitor-08] Demo shutdown complete.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        dashboard_proc.wait()
    except KeyboardInterrupt:
        handle_exit(None, None)


if __name__ == "__main__":
    main()
