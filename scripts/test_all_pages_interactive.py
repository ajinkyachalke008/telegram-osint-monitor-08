"""Deep interactive verification of all 11 dashboard pages using Streamlit AppTest."""
import os
import sys
from pathlib import Path

# Enforce DEMO_MODE=1 for full data verification
os.environ["DEMO_MODE"] = "1"

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest

PAGES = [
    ("Home Overview", "dashboard/app.py"),
    ("Page 1: Live Alerts", "dashboard/pages/1_🚨_Live_Alerts.py"),
    ("Page 2: Alert Detail", "dashboard/pages/2_🔍_Alert_Detail.py"),
    ("Page 3: Entity Graph", "dashboard/pages/3_🕸️_Entity_Graph.py"),
    ("Page 4: Coordinated Campaigns", "dashboard/pages/4_🔁_Coordinated_Campaigns.py"),
    ("Page 5: Geographic Map", "dashboard/pages/5_🗺️_Geographic_Map.py"),
    ("Page 6: Data Ingestion", "dashboard/pages/6_📁_Data_Ingestion.py"),
    ("Page 7: Model Metrics", "dashboard/pages/7_📈_Model_Metrics.py"),
    ("Page 8: Responsible Use & Audit", "dashboard/pages/8_⚖️_Responsible_Use_and_Audit.py"),
    ("Page 9: Channel Discovery", "dashboard/pages/9_🔭_Channel_Discovery.py"),
    ("Page 10: PS02 Dataset Insights", "dashboard/pages/10_📊_PS02_Dataset_Insights.py"),
]

results = []
all_ok = True

print("=" * 80)
print(" 🔬 STABILITY & INTERACTION VERIFICATION — ALL 11 DASHBOARD PAGES")
print("=" * 80)

for name, rel_path in PAGES:
    print(f"\n▶ Testing: {name} ({rel_path})...")
    file_path = ROOT / rel_path
    if not file_path.exists():
        print(f"❌ File missing: {rel_path}")
        all_ok = False
        results.append((name, False, "File missing", []))
        continue

    try:
        at = AppTest.from_file(str(file_path), default_timeout=25)
        at.run()
        if at.exception:
            exc_msgs = [f"{e.value}: {e.message}" for e in at.exception]
            print(f"❌ Initial render failed with {len(at.exception)} exception(s):")
            for m in exc_msgs:
                print(f"   • {m}")
            all_ok = False
            results.append((name, False, "Render exception", exc_msgs))
            continue

        interactions_tested = []

        # Page-specific interaction tests
        if "1_🚨" in rel_path:
            # Change risk filter
            if at.multiselect:
                at.multiselect[0].select("Low")
                at.run()
                interactions_tested.append("risk_filter_select")
            if at.selectbox:
                at.selectbox[0].select("reviewing")
                at.run()
                interactions_tested.append("status_filter_select")

        elif "2_🔍" in rel_path:
            if at.selectbox:
                # Select alert
                opts = at.selectbox[0].options
                if opts:
                    at.selectbox[0].select(opts[0])
                    at.run()
                    interactions_tested.append(f"alert_select({opts[0][:20]}...)")
            if at.button:
                # Click verify cryptographic seal
                verify_btns = [b for b in at.button if "Verify Cryptographic Seal" in b.label]
                if verify_btns:
                    verify_btns[0].click().run()
                    interactions_tested.append("verify_cryptographic_seal_button")

        elif "3_🕸️" in rel_path:
            if at.radio:
                # Change label mode
                radio = at.radio[0]
                for opt in radio.options:
                    radio.set_value(opt).run()
                    assert not at.exception, f"Error selecting {opt}"
                interactions_tested.append("radio_label_modes_all_tested")

        elif "4_🔁" in rel_path:
            if at.slider:
                at.slider[0].set_value(0.70).run()
                interactions_tested.append("slider_threshold_set_0.70")

        elif "8_⚖️" in rel_path:
            if at.slider:
                at.slider[0].set_value(5.0).run()
                interactions_tested.append("slider_term_weight_set_5.0")

        elif "9_🔭" in rel_path:
            if at.tabs:
                interactions_tested.append("tabs_rendered")

        elif "10_📊" in rel_path:
            if at.tabs:
                interactions_tested.append(f"{len(at.tabs)} tabs verified")
            # Click preflight
            preflight_btn = [b for b in at.button if "1. Run Preflight Audit" in b.label]
            if preflight_btn:
                preflight_btn[0].click().run()
                interactions_tested.append("btn_run_preflight_audit")
            # Click dry run
            dry_btn = [b for b in at.button if "2. Dry-Run Preview" in b.label]
            if dry_btn:
                dry_btn[0].click().run()
                interactions_tested.append("btn_dry_run_preview")

        if at.exception:
            exc_msgs = [f"{e.value}: {e.message}" for e in at.exception]
            print(f"❌ Interactive step failed:")
            for m in exc_msgs:
                print(f"   • {m}")
            all_ok = False
            results.append((name, False, "Interaction exception", exc_msgs))
        else:
            print(f"✅ PASSED cleanly. Interactions tested: {', '.join(interactions_tested) or 'Load & Layout'}")
            results.append((name, True, "OK", interactions_tested))

    except Exception as e:
        print(f"❌ CRITICAL EXCEPTION on {name}: {e}")
        all_ok = False
        results.append((name, False, str(e), []))

print("\n" + "=" * 80)
print(f" SUMMARY: {'ALL 11 PAGES PASSED' if all_ok else 'SOME PAGES FAILED'}")
print("=" * 80)
for name, ok, status, acts in results:
    icon = "✅" if ok else "❌"
    print(f"{icon} {name:<35} | {status:<20} | Actions: {acts}")

if not all_ok:
    sys.exit(1)
