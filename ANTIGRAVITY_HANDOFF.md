# Antigravity Handoff — PS02 Hackathon Dataset Demo

**Priority:** P0 — the presentation is tomorrow.  
**Repository:** https://github.com/ajinkyachalke008/telegram-osint-monitor-08  
**Work branch:** `feat/ps02-hackathon-handoff-v2`  
**Default branch:** `main`

## Mission

Make the EXISTING Telegram & Social Media Illegal Trade Monitor demonstrate genuine, reproducible use of the hackathon committee's participant-provided PS02 dataset. Do not build a replacement app and do not throw away existing working pages. Preserve the prior project, add a separate dataset-focused path, and verify it end-to-end.

The committee explicitly permits use of its provided dataset. This is the primary focus of tomorrow's demo: select the ZIP, run validation, preview real counts, import safely, and show interactive aggregate insights computed from those exact files.

## Repository reality — read before changing code

The repository root README currently describes an unrelated “OpenTerminal” crypto-trading terminal and is stale/mismatched. DO NOT use it as the product specification. The actual application is the Telegram / social media project documented in:
- `docs/DEMO_SCRIPT.md`
- `docs/HONEST_STATUS.md`
- `docs/LIMITATIONS.md`
- `docs/TRACEABILITY.md`
- `docs/JUDGES_QA.md`
- `dashboard/app.py`
- `dashboard/pages/6_📁_Data_Ingestion.py`
- `ingestion/adapters.py`
- `ingestion/worker.py`
- `core/db.py`
- `scripts/run_demo.py`

Existing app: Streamlit multipage dashboard, 9 pages, CSV/JSON generic ingestion, SQLite storage, synthetic replay, hash-chained evidence for legacy demo records. Existing Page 6 is a generic row importer and does NOT understand the participant archive's folder structure and social CSV schema without adaptation.

Existing preflight QA tool merged in PR #3:
- `scripts/ps02_preflight.py`
- `docs/PS02_PREFLIGHT.md`
- `docs/PS02_Aggregate_Audit_Summary.json`
- `tests/test_ps02_preflight.py`

PR #3 was merged to main on 2026-11-27 (merge commit begins `9d90df7`). The preflight implementation is a simplified port and has only a shallow test in the repository. Review it, test it, and improve it if necessary; do not assume it validates every requirement.

## Participant dataset snapshot (audit reference only)

The uploaded participant archive was `PS02_demo_data-20261127T071007Z-1-001.zip`. It is NOT in GitHub and must remain local. The user must provide it from their laptop or upload it through the application. Do not expect the archive to exist in a clean clone.

Prior offline inspection found these reference totals (recompute them at runtime; these numbers are not substitutes for running the actual ZIP):

| Component | Reference count |
|---|---:|
| Telegram JSON exports | 13 |
| Telegram message records | 1,500 |
| Telegram service records | 13 |
| Telegram photo references | 199 |
| Social posts | 350 |
| Social image files | 92 |
| Poster images | 18 |
| Poster SHA-256 matches in supplied index | 18 / 18 |
| Lexicon CSV rows | 37 |
| Telegram + social message/post records | 1,850 |

Telegram JSON includes service records, empty text, edit/forward metadata and attachment references. Do not count all JSON records as plain messages. Social CSV includes columns such as `post_id`, `platform`, `author`, `posted_at_ist`, `text`, `hashtags`, `image_file`, `location_tag`, `likes`, and `comments`. The private judge answer key was not included in the participant ZIP. No ground-truth precision/recall or linkage accuracy can be claimed.

## What to build — must-have

### A. Dataset intake
- Add a clearly named “PS02 Participant Dataset” experience, preferably a new Streamlit page or an obvious distinct section.
- Accept the actual supplied ZIP directly. Also support an extracted directory if practical.
- Find the optional top-level folder correctly; validate required folders and file structure.
- Show filename, archive size, number of files, file types and clear validation result.
- Provide dry-run / preview before database writes.
- Provide a deliberate Import button; do not import automatically on upload.

### B. Dataset-specific parsing
- Telegram JSON exports: count message vs service records separately; count blank text and media/photo references. Defensively handle malformed files individually.
- Social CSV: use actual `posted_at_ist` schema and timezone, handle UTF-8 BOM and CSV quoting, count by platform, parse timestamps as Asia/Kolkata without silently converting naive local times to UTC.
- Images: validate relative file references safely and report present/missing counts; prevent absolute paths and `..` traversal.
- Poster manifest: compute SHA-256 from image bytes and report matched, missing, mismatch separately.
- Lexicon: validate expected CSV columns and count rows; do not train or update a model from it.
- Show number of skipped rows/files grouped by reason, not their raw contents.

### C. Real aggregate insights from those files
Build useful, well-labelled visualizations based on actual runtime parsed data:
- Platform coverage and record counts
- Posts by time/day (IST explicitly)
- Telegram message/service/empty-text/forward/edit statistics, where the source structure supports it
- Image/poster attachment availability
- Aggregate location-tag counts only (no precise coordinates; suppress small groups if needed)
- Data quality summary: missing/invalid timestamps, missing required fields, duplicate IDs, unresolved image refs and poster hash results
- Source-file coverage and import batch provenance

All displayed charts must carry a visible “Hackathon-provided PS02 participant dataset” source label. Do not mix these counts with synthetic replay.

### D. Safe storage and repeatable import
- Use a new dedicated SQLite database (e.g. `data/participant_demo.sqlite3`) or a clearly isolated table namespace. Preferred: separate SQLite DB, leaving existing `data/osint_monitor.db` unchanged.
- Store only fields required for aggregate analysis: batch ID, safe source-relative file name, source platform/type, stable opaque record key, timestamp (if valid), aggregate categorical fields, attachment-present flag, import timestamp. Do not store/display raw post text, author names, contact/payment values or usernames in this dataset demo path.
- Idempotency: reimporting the same archive/records must not double-count. A changed archive with same filename must be detected as a different batch.
- Dry-run must not write to DB.
- Use transactions and roll back a failed batch.
- Add a local archive hash for batch identity if appropriate; do not publish it as a cross-environment tracking identifier.
- Never reset/delete the existing legacy DB. Never change its schema unless essential and backward compatible.

### E. Existing project must remain intact
- Keep existing dashboard pages and normal workflows functioning.
- Clearly separate the participant dataset from synthetic replay, optional live intake and any existing imported data.
- Do not let the participant archive flow into the current `PipelineWorker.process_raw_post` path, because it extracts personal/payment identifiers and creates cross-channel links.
- Existing synthetic demo capability may remain for a brief “existing feature” segment, but label it “synthetic demo data” and do not claim those results came from the participant archive.
- Audit `scripts/run_demo.py`: it resets the DB and seeds demo records before launching. Do not use this destructively for a judge run. Add a nondestructive launcher or safe flag; default must preserve existing DB.

## Privacy and integrity boundaries

The participant content is potentially sensitive. This demo should demonstrate dataset use through data engineering and aggregate analysis, not target people:
- No raw post text, authors, usernames/handles, phone numbers, UPI/payment IDs, wallet addresses, personal contacts or individual-level records in the new UI/reports/logs/screenshots.
- Do not extract, persist, correlate or render actionable identifiers from participant data.
- No person/seller dossiers, cross-platform person identity graph, or targeting list from participant data.
- No automated guilt/criminality labels. At most, explain that legacy classifier flags are unverified triage hints and only use clearly labelled synthetic fixtures for that segment.
- No private group joins, DMs, member enumeration, outreach or external scraping as part of this dataset flow.
- Do not upload participant data to external APIs, model providers, analytics services or public websites.
- Do not train/fine-tune models on participant-provided messages or social posts.
- Keep ZIP, extracted raw files and participant DB local and gitignored. Never commit any participant data or raw-content reports.
- Manifest hash success establishes byte match against a supplied manifest only; it does not prove source authenticity, truth, author identity or wrongdoing.
- Do not claim judge-answer-key accuracy; no judge key was in the provided participant archive.

## Safety / ZIP engineering
- Reject absolute and traversal paths, duplicate entries and suspicious paths.
- Enforce maximum archive entry count, total uncompressed size and per-file size; consider compression ratio limits.
- Never extract archive members blindly. Read members using validated names or safe extraction into a temporary isolated directory.
- Catch malformed JSON/CSV per file; one bad file should not crash the entire preflight.
- Avoid printing source row values in exceptions/logs.
- Resolve image paths only relative to dataset root and verify resolved paths remain inside it.

## Demo quality and workflow
Make the flow obvious, calm and visually polished:
1. Existing app opens with a clear route into the participant dataset demo.
2. User selects ZIP.
3. Preflight shows actual counts and warnings.
4. User reviews dry-run.
5. User clicks Import.
6. App displays inserted/duplicate/skipped/error counts and batch ID.
7. Dataset Insights shows charts from that same batch.
8. Refresh/re-import demonstrates no duplicate inflation.
9. Existing pages remain available and clearly labelled.

Use responsive Streamlit layout, uncluttered metric cards, sensible chart legends, readable labels, loading states, helpful errors and a clear no-dataset state. Do not create fake progress or fake successful outcomes.

## Recommended architecture

Suggested names are flexible. Keep the implementation isolated:
- `ps02_dataset/preflight.py`: ZIP/directory validation and aggregate inventory
- `ps02_dataset/parser.py`: Telegram JSON and social CSV schema parser
- `ps02_dataset/store.py`: dedicated SQLite DB / schema
- `ps02_dataset/importer.py`: dry-run and transactional idempotent ingest
- `dashboard/pages/10_📊_PS02_Dataset_Insights.py`: upload, preflight, import and visualizations
- `scripts/run_ps02_dataset_demo.py`: nondestructive launcher
- `tests/test_ps02_dataset_*.py`: isolated fixture tests
- `.gitignore`: participant ZIP, extracted folders, participant DB, generated sensitive reports

Do not force these exact paths if the repository has a more suitable convention.

## Mandatory tests and commands

Tests should cover:
- ZIP traversal, absolute paths, duplicate entries, size/count limits
- ZIP with or without top-level root folder
- valid/malformed Telegram JSON
- social CSV BOM, quoting, schema and IST timestamps
- safe relative image path and missing attachments
- poster manifest matched/missing/mismatch
- dry-run is read-only
- idempotent repeated import
- transactional rollback on error
- aggregate expected counts on synthetic fixtures
- legacy DB remains readable and not reset
- dashboard page imports / smoke launch

Run and record actual output:
```bash
python -m compileall core ingestion dashboard scripts tests
pytest -q
python scripts/ps02_preflight.py --dataset /path/to/PS02_demo_data.zip --output /tmp/ps02_preflight.json
```
Also test the newly implemented importer on the actual participant ZIP locally, if the ZIP is available. The archive is not stored in GitHub. Never claim tests passed unless they were run.

## Demo story (3–4 minutes)

- 0:00–0:30: explain the challenge and that this is the committee-provided dataset.
- 0:30–1:10: upload ZIP and show structural preflight; all counts are live computed, not hardcoded.
- 1:10–2:20: explore platform distribution, IST timeline, attachment coverage and data quality.
- 2:20–3:10: show one existing project feature running on its own synthetic fixture, with source badge visible.
- 3:10–4:00: show batch provenance, idempotent re-import, integrity caveat and responsible-use limitations.

## Urgent prioritization

**P0:** inspect and launch existing app; actual ZIP parser; dry-run; separate safe import store; aggregate charts; nondestructive launch; tests; one-page operator instructions.

**P1:** polished responsive UI, aggregate report download, screenshots, concise README correction after all checks.

Do not spend time on refactoring everything, external services, new ML models or personal-targeting functionality.

## Final report required from Antigravity

Before stopping, provide:
- changed file list
- commands executed
- exact test totals and failures
- actual ZIP counts measured locally
- current launch command and URL
- how to select/place the ZIP
- confirmation the legacy DB was not reset or modified
- known limitations / any incomplete P0 requirement
- exact commit SHA and branch

Do not merge into main without owner approval. Do not force-push or overwrite user changes.
