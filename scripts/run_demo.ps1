# Windows PowerShell One-Click Demo Runner for TGSherlock OSINT Monitor
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 🛡️ TGSherlock OSINT Threat Intelligence System " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$VENV_PY = ".\.venv\Scripts\python.exe"
$STREAMLIT = ".\.venv\Scripts\streamlit.exe"

if (-not (Test-Path $VENV_PY)) {
    Write-Host "Error: Virtual environment not found at .venv. Please set up Python venv first." -ForegroundColor Red
    exit 1
}

Write-Host "`n[1/4] Generating Seeded Demo Dataset..." -ForegroundColor Yellow
& $VENV_PY scripts/generate_demo_data.py

Write-Host "`n[2/4] Ingesting Demo Dataset through Full Pipeline (Normalizer -> ML -> Hash Chain -> Graph)..." -ForegroundColor Yellow
& $VENV_PY -c "
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

Write-Host "`n[3/4] Verifying Evidence Ledger Cryptographic Integrity..." -ForegroundColor Yellow
& $VENV_PY addons/verify_evidence.py

Write-Host "`n[4/4] Launching Multipage Streamlit Dashboard..." -ForegroundColor Green
Write-Host "Dashboard will open at: http://localhost:8501" -ForegroundColor Cyan
& $STREAMLIT run dashboard/app.py --server.port 8501
