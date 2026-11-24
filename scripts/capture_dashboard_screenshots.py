"""Automated Headless Screenshot Capture for Streamlit Pages.

Captures high-resolution PNG screenshots of all 9 dashboard views:
1. Home Overview
2. Live Alerts Feed & Triage
3. Forensic Alert Detail & Hash Seal Verifier
4. Entity Knowledge Graph
5. Coordinated Campaigns
6. Geographic Hotspot Map
7. Multi-Platform Data Ingestion
8. Model Metrics & Benchmarks
9. Responsible Use & Audit Log
"""
import sys
import time
from pathlib import Path

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("00_home_overview.png", "http://localhost:8501/"),
    ("01_live_alerts.png", "http://localhost:8501/Live_Alerts"),
    ("02_alert_detail.png", "http://localhost:8501/Alert_Detail"),
    ("03_entity_graph.png", "http://localhost:8501/Entity_Graph"),
    ("04_coordinated_campaigns.png", "http://localhost:8501/Coordinated_Campaigns"),
    ("05_geographic_map.png", "http://localhost:8501/Geographic_Map"),
    ("06_data_ingestion.png", "http://localhost:8501/Data_Ingestion"),
    ("07_model_metrics.png", "http://localhost:8501/Model_Metrics"),
    ("08_responsible_use_and_audit.png", "http://localhost:8501/Responsible_Use_and_Audit"),
]

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed.")
        return

    print("Launching Chromium headless...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        for filename, url in PAGES:
            target_path = SCREENSHOTS_DIR / filename
            print(f"Navigating to {url}...")
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
                # Wait for streamlit stApp rendering
                time.sleep(2)
                page.screenshot(path=str(target_path), full_page=True)
                print(f"  📸 Saved screenshot: {target_path}")
            except Exception as e:
                print(f"  ❌ Error capturing {url}: {e}")

        browser.close()
    print("\nAll screenshots captured successfully into docs/screenshots/")

if __name__ == "__main__":
    main()
