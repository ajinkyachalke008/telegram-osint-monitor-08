"""Verify all Streamlit multipage application files for runtime exceptions using AppTest."""
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

PAGES_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "pages"
APP_FILE = Path(__file__).resolve().parent.parent / "dashboard" / "app.py"

files_to_test = [APP_FILE] + sorted(list(PAGES_DIR.glob("*.py")))

all_passed = True
print("=== VERIFYING STREAMLIT MULTIPAGE APPLICATION ===")

for p in files_to_test:
    print(f"\nTesting page: {p.name}...")
    try:
        at = AppTest.from_file(str(p), default_timeout=15).run()
        if at.exception:
            print(f"❌ ERROR on page {p.name}:")
            for ex in at.exception:
                print(f"   Exception: {ex.value}")
                print(f"   Message: {ex.message}")
            all_passed = False
        else:
            print(f"✅ PASSED: {p.name} rendered cleanly with 0 exceptions.")
            # Print a few rendered elements
            titles = [t.value for t in at.title]
            subheaders = [s.value for s in at.subheader]
            print(f"   Rendered Title(s): {titles}")
            if subheaders:
                print(f"   Subheaders: {subheaders[:2]}")
    except Exception as e:
        print(f"❌ CRITICAL FAILURE launching {p.name}: {e}")
        all_passed = False

if all_passed:
    print(f"\n🎉 ALL {len(files_to_test)} STREAMLIT DASHBOARD PAGES VERIFIED CLEANLY WITH 0 EXCEPTIONS!")
else:
    print("\n⚠️ SOME PAGES ENCOUNTERED ERRORS. FIX REQUIRED.")
    sys.exit(1)
