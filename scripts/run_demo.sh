#!/usr/bin/env bash
# Portable Shell One-Click Demo Runner for telegram-osint-monitor-08 OSINT Monitor
set -e

echo "=========================================================="
echo " 🛡️ telegram-osint-monitor-08 Threat Intelligence System "
echo "=========================================================="

VENV_PY="./.venv/bin/python"
STREAMLIT="./.venv/bin/streamlit"

# Check Windows fallback if on WSL/Git Bash
if [ ! -f "$VENV_PY" ]; then
    VENV_PY="./.venv/Scripts/python.exe"
    STREAMLIT="./.venv/Scripts/streamlit.exe"
fi

if [ ! -f "$VENV_PY" ]; then
    echo "Error: Python executable not found in .venv."
    exit 1
fi

echo ""
echo "[1/4] Generating Seeded Demo Dataset..."
$VENV_PY scripts/generate_demo_data.py

echo ""
echo "[2/4] Ingesting Demo Dataset through Full Pipeline..."
$VENV_PY -c "
from core.db import Database
from ingestion.worker import PipelineWorker
from ingestion.adapters import CSVJSONImporter
from pathlib import Path
db = Database()
worker = PipelineWorker(db=db)
importer = CSVJSONImporter(db=db, worker=worker)
res = importer.import_file(Path('sample_data/demo_multiplatform_dataset.json'))
print(f'Ingestion Complete: {res}')
"

echo ""
echo "[3/4] Verifying Evidence Ledger Cryptographic Integrity..."
$VENV_PY addons/verify_evidence.py

echo ""
echo "[4/4] Launching Multipage Streamlit Dashboard..."
echo "Dashboard will open at: http://localhost:8501"
$STREAMLIT run dashboard/app.py --server.port 8501
