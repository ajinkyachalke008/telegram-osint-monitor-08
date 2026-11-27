import json, tempfile, zipfile
from pathlib import Path
import importlib.util

spec=importlib.util.spec_from_file_location("preflight","scripts/ps02_preflight.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_archive_limits_and_path_safety():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"unsafe.zip"
        with zipfile.ZipFile(p,"w") as z: z.writestr("../escape.txt","bad")
        with zipfile.ZipFile(p) as z:
            try: m.safe_zip(z)
            except ValueError: pass
            else: assert False, "unsafe path should be rejected"
