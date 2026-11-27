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

# Enforce DEMO_MODE=1 for demonstration script
os.environ["DEMO_MODE"] = "1"

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

    # 1. Database initialization (preserves existing DB if --no-reset or NO_RESET=1)
    no_reset = "--no-reset" in sys.argv or os.environ.get("NO_RESET") == "1"
    db = Database(DEFAULT_DB_PATH)
    if no_reset:
        print("\n[1/4] 🛡️ Preserving existing database (--no-reset mode active)...")
        print(f"      ✅ Database {DEFAULT_DB_PATH} preserved without reset.")
    else:
        print("\n[1/4] 🔄 Resetting database & seeding baseline demo records...")
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
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(f"      ✅ Replay worker running in background (PID: {replay_proc.pid})")

    # 3. Spawn Streamlit dashboard engine (with DEMO_MODE=1)
    print("\n[3/5] 🚀 Starting Streamlit Intelligence Engine on http://localhost:8501 ...")
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
    print(f"      ✅ Intelligence Engine started (PID: {dashboard_proc.pid})")

    # 4. Check & Spawn Unified Web Panel on http://127.0.0.1:8765
    print("\n[4/5] 🌐 Starting Unified OSINT Web Panel on http://127.0.0.1:8765 ...")
    panel_proc = None
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_port_8765_open = False
    try:
        s.connect(("127.0.0.1", 8765))
        is_port_8765_open = True
        s.close()
    except Exception:
        pass

    if not is_port_8765_open:
        panel_cmd = [sys.executable, "-m", "tgsherlock", "--no-browser", "--port", "8765"]
        panel_proc = subprocess.Popen(panel_cmd, cwd=str(PROJECT_ROOT))
        print(f"      ✅ Unified Web Panel started (PID: {panel_proc.pid})")
    else:
        print("      ✅ Unified Web Panel is already active on port 8765.")

    # 5. Open Unified Browser App
    print("\n[5/5] 🚀 Opening Unified Application in Browser at http://127.0.0.1:8765 ...")
    time.sleep(2.5)
    webbrowser.open("http://127.0.0.1:8765")

    print("\n" + "=" * 76)
    print("  🎉 UNIFIED APPLICATION IS LIVE at http://127.0.0.1:8765!")
    print("  Press Ctrl+C at any time to shut down gracefully.")
    print("=" * 76 + "\n")

    def handle_exit(sig, frame):
        print("\n[telegram-osint-monitor-08] Shutting down demo processes...")
        try:
            replay_proc.terminate()
            dashboard_proc.terminate()
            if panel_proc:
                panel_proc.terminate()
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
