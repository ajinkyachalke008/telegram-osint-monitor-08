"""90-Second Real Demo Verification with Playwright Screenshots & Toast Detection."""
import os
import sys
import time
import subprocess
import threading
from queue import Queue, Empty
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db import Database, DEFAULT_DB_PATH
from scripts.generate_demo_data import seed_demo_database

SCREENSHOT_DIR = PROJECT_ROOT / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 76)
    print(" 90-SECOND REAL DEMO VERIFICATION & PLAYWRIGHT TEST")
    print("=" * 76)

    # 1. Reset DB & seed baseline
    print("[1/5] Resetting database and seeding baseline demonstration records...")
    db = Database(DEFAULT_DB_PATH)
    count = seed_demo_database(db=db, reset=True)
    print(f"      Seeded {count} baseline posts.")

    # 2. Start replay worker (one post every ~5s)
    print("[2/5] Starting replay worker (interval=5.0s, loop=True)...")
    replay_cmd = [
        sys.executable,
        "-u",
        str(PROJECT_ROOT / "ingestion" / "replay.py"),
        "--interval", "5.0",
        "--loop"
    ]
    replay_proc = subprocess.Popen(
        replay_cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    replay_lines = []
    log_queue = Queue()

    def read_replay_output():
        for line in iter(replay_proc.stdout.readline, ''):
            clean_l = line.strip()
            if clean_l:
                replay_lines.append(clean_l)
                log_queue.put(clean_l)
        replay_proc.stdout.close()

    t_reader = threading.Thread(target=read_replay_output, daemon=True)
    t_reader.start()

    # 3. Start Streamlit dashboard with DEMO_MODE=1
    print("[3/5] Starting Streamlit dashboard on port 8501 with DEMO_MODE=1...")
    env = os.environ.copy()
    env["DEMO_MODE"] = "1"
    dashboard_cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        str(PROJECT_ROOT / "dashboard" / "app.py"),
        "--server.port", "8501",
        "--server.headless", "true"
    ]
    dashboard_proc = subprocess.Popen(
        dashboard_cmd,
        cwd=str(PROJECT_ROOT),
        env=env
    )

    print("      Waiting 4 seconds for Streamlit dashboard to bind...")
    time.sleep(4.0)

    # 4. Playwright Browser Automation
    print("[4/5] Launching Playwright Chromium headless...")
    toast_fired = False
    toast_messages = []
    initial_alerts_count = 0
    t60_alerts_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("      Navigating to http://localhost:8501 ...")
        page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        time.sleep(2.0)

        # Navigate to Live Alerts page
        print("      Navigating to Live Threat Alerts page...")
        live_link = page.locator("a:has-text('Live Threat Alerts'), a[href*='Live_Alerts'], span:has-text('Live Alerts')").first
        if live_link.count() > 0:
            live_link.click()
            time.sleep(3.0)
        else:
            page.goto("http://localhost:8501/Live_Alerts", wait_until="networkidle", timeout=30000)
            time.sleep(3.0)

        try:
            page.wait_for_selector("h1:has-text('Live Threat Alerts')", timeout=10000)
        except Exception:
            pass

        # Time t = 0
        t0_path = SCREENSHOT_DIR / "live_alerts_t0.png"
        page.screenshot(path=str(t0_path), full_page=True)
        print(f"      📸 Captured t=0s screenshot: {t0_path.name}")

        # Check initial alerts on page
        t0_text = page.inner_text("body")
        for line in t0_text.splitlines():
            if "Found" in line and "alerts matching" in line:
                print(f"      [t=0s Page State]: {line.strip()}")
                break

        start_time = time.time()
        print("\n[5/5] Monitoring streaming execution for 90 seconds...")
        print("------------------------------------------------------------------------")
        print(" LIVE REPLAY WORKER LOG OUTPUT & TOAST SURVEILLANCE:")
        print("------------------------------------------------------------------------")

        t60_captured = False

        while True:
            elapsed = time.time() - start_time

            # Drain log queue
            while not log_queue.empty():
                try:
                    msg = log_queue.get_nowait()
                    print(f"[{elapsed:04.1f}s WORKER] {msg}")
                except Empty:
                    break

            # Check for toast notification in DOM
            toasts = page.locator(".stToast, [data-testid='stToast'], div:has-text('New threat alert received')").all()
            for t in toasts:
                try:
                    t_text = t.inner_text()
                    if t_text and t_text not in toast_messages:
                        toast_fired = True
                        toast_messages.append(t_text)
                        print(f"[{elapsed:04.1f}s TOAST DETECTED 🔔] {t_text}")
                except Exception:
                    pass

            # Capture t=60s screenshot
            if elapsed >= 60.0 and not t60_captured:
                t60_path = SCREENSHOT_DIR / "live_alerts_t60.png"
                page.screenshot(path=str(t60_path), full_page=True)
                print(f"[{elapsed:04.1f}s] 📸 Captured t=60s screenshot: {t60_path.name}")
                t60_text = page.inner_text("body")
                for line in t60_text.splitlines():
                    if "Found" in line and "alerts matching" in line:
                        print(f"[{elapsed:04.1f}s Page State]: {line.strip()}")
                        break
                t60_captured = True

            if elapsed >= 90.0:
                print(f"[{elapsed:04.1f}s] Reached 90s surveillance window. Concluding test.")
                break

            time.sleep(1.0)

        browser.close()

    # Clean shutdown
    print("\nTerminating background demo processes...")
    try:
        replay_proc.terminate()
        dashboard_proc.terminate()
    except Exception:
        pass

    print("=" * 76)
    print(" 90-SECOND DEMO SURVEILLANCE SUMMARY")
    print("=" * 76)
    print(f"Total Replay Worker Log Lines: {len(replay_lines)}")
    print(f"Toast Notification Fired:     {'YES 🔔' if toast_fired else 'NO ❌'}")
    if toast_messages:
        print(f"Captured Toast Messages:     {toast_messages}")
    print(f"Screenshot at t=0s:           {SCREENSHOT_DIR / 'live_alerts_t0.png'}")
    print(f"Screenshot at t=60s:          {SCREENSHOT_DIR / 'live_alerts_t60.png'}")
    print("=" * 76)


if __name__ == "__main__":
    main()
