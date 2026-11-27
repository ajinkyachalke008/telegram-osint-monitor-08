# PS02 Hackathon Dataset-First Demo Runbook

This runbook is for the next-day judge demonstration after Antigravity completes and verifies the dedicated dataset page. Do not present an unbuilt page or unrun check as complete.

## 1. Before the demonstration

1. Clone or pull the implementation branch and make sure the committee-provided archive is available locally.
2. Keep the archive/extracted folder under `data/participant/`; it must be ignored by Git.
3. Create/activate the project virtual environment and install `requirements.txt`.
4. Run the tests and structural preflight against the actual archive.
5. Start the Streamlit app directly. Do not start the reset/replay demo launcher as the first dataset-demo step.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
$env:PS02_DATASET_PATH = "data/participant/PS02_demo_data"
python scripts/ps02_preflight.py --dataset $env:PS02_DATASET_PATH --output data/participant/preflight-report.json
python -m streamlit run dashboard/app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
export PS02_DATASET_PATH="data/participant/PS02_demo_data"
python scripts/ps02_preflight.py --dataset "$PS02_DATASET_PATH" --output data/participant/preflight-report.json
python -m streamlit run dashboard/app.py
```

Set `PS02_DATASET_PATH` to the actual extracted directory or supported archive path. The page should state clearly when it cannot find the data. Do not replace missing data with sample numbers.

## 2. Four-minute judge walkthrough

**0:00–0:30 — State the challenge and the data source**

Explain that the demo uses the committee-provided PS02 participant dataset, processed locally. Make clear that the team distinguishes committee-provided records from synthetic sample data used by the earlier demo.

**0:30–1:15 — Show dataset coverage**

On the dataset page, show the actual Telegram export count, Telegram message count, service-record count, social post count, and platform breakdown. Explain that the dashboard figures are computed from the files at runtime.

**1:15–2:00 — Show multi-platform coverage**

Show the distribution across Instagram, Facebook, X, YouTube comments, and ShareChat. Use the IST time chart to demonstrate temporal coverage. Explain that invalid timestamps are excluded from the timeline and counted in the quality panel.

**2:00–2:45 — Show media and structural integrity**

Show media file totals, photo-reference counts, missing-reference results, poster SHA-256 verification, and lexicon row count. Explain accurately: a matching hash shows that a local file matches the supplied manifest entry; it does not prove authenticity or authorship.

**2:45–3:25 — Show data quality and responsible handling**

Show empty-text and service-record counts, timestamp/attachment issues, and the local/unverified provenance label. State that no author/contact/payment details or row-level records are exposed in this aggregate demo.

**3:25–4:00 — Connect to the existing project and close**

Show the existing dashboard separately, with its true sample/synthetic provenance label, to demonstrate that the previous project has been preserved. Do not imply those sample rows came from the committee archive. Close by explaining that the participant archive has no judge-only answer key, so the team is reporting verified ingestion and data-quality behavior rather than invented model-accuracy or attribution claims.

## 3. Demo fallback

- If the participant archive is unavailable, show the clear missing-data message and switch to the previously working sample demo, clearly labelled as **synthetic/sample**.
- Do not show hardcoded committee totals as live parser output.
- Do not call a partial load a successful import.
- If poster hashes fail, show the failed count and explain the issue; do not hide or override it.
- If timestamps fail parsing, disclose the number excluded from the chart.
- Do not run `scripts/run_demo.py` or `scripts/run_demo.sh` as a fallback without understanding their reset/reseed behavior. They may reset the existing database and start synthetic replay.

## 4. Claims to avoid

Do not claim that the dataset proves a person, account, location, or activity is criminal. Do not claim that a SHA-256 manifest match proves authorship, authenticity, or legal admissibility. Do not quote model performance metrics as results on this dataset when no judge-only answer key is available. Do not describe synthetic sample events as live committee data.
