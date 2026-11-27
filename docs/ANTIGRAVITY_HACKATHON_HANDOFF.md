# PS02 Hackathon Dataset-First Build Brief

> **Read this before changing code.** This is the working handoff for Antigravity. The deadline is the next-day hackathon demonstration, so prioritize a reliable, explainable end-to-end demo over adding more features.

## Mission

Prepare the existing **Telegram OSINT Monitor (PS02)** for judging by making the committee-provided dataset the centre of the demonstration, while preserving the existing application and its previous demo path.

The desired result is one project with two clearly separated demonstrations:

1. **PS02 committee-dataset demonstration:** a real local workflow that reads the supplied archive, validates its structure and assets, and presents accurate aggregate analytics in the existing Streamlit application.
2. **Existing application demonstration:** preserve the pre-existing dashboard and synthetic/sample workflow. Keep its provenance clearly labelled; do not mix sample records with committee data or describe sample records as committee data.

Do not create a parallel replacement app. Extend the existing repository and follow its conventions.

## Repository and current-state facts

Repository: `ajinkyachalke008/telegram-osint-monitor-08`  
Default branch: `main`  
The earlier preflight contribution (PR #3) has already been merged into `main`. It added:

- `scripts/ps02_preflight.py`
- `docs/PS02_PREFLIGHT.md`
- `tests/test_ps02_preflight.py`
- `docs/PS02_Aggregate_Audit_Summary.json`

Relevant existing code:

| Area | Current location | What to know |
|---|---|---|
| Streamlit entry point | `dashboard/app.py` | Existing multipage dashboard entry point |
| Existing dashboard pages | `dashboard/pages/` | Pages 1–9 already exist |
| Generic CSV/JSON import UI | `dashboard/pages/6_📁_Data_Ingestion.py` | Not a ready-made importer for the committee archive |
| Generic CSV/JSON mapper | `ingestion/adapters.py` | `FileImporterAdapter` / `CSVJSONImporter` expects generic source/text fields |
| Existing processing worker | `ingestion/worker.py` | Runs normalization, identifier extraction, scoring, and identifier/edge persistence |
| Existing demo replay | `ingestion/replay.py` | Replays the repository's synthetic sample posts |
| Existing one-command demo | `scripts/run_demo.py`, `scripts/run_demo.sh` | May reset/reseed the DB and start synthetic replay; do not use as the committee-dataset importer |
| Aggregate preflight | `scripts/ps02_preflight.py` | Structural aggregate QA only; not a full application importer |
| Tests | `tests/` | Preserve and run the existing suite |

### Important integration mismatch

Do **not** route the committee archive through `PipelineWorker.process_raw_post()` or the old generic import button as a shortcut. The worker currently invokes entity extraction and persists identifier links/edges. The committee dataset's social CSV schema also differs from the generic mapper: it has fields such as `author`, `posted_at_ist`, and `image_file`, rather than the generic `source`, `timestamp`, and `image_path` names. Telegram JSON exports are structured exports, not necessarily flat generic post rows.

Build a dedicated dataset reader and a separate dataset demonstration page. Reuse existing validation utilities where appropriate, but do not pass raw committee records into the old worker.

## Dataset facts to use

The uploaded participant archive was previously inventoried. The profile is recorded in [PS02_DATASET_PROFILE.json](PS02_DATASET_PROFILE.json). These are aggregate audit counts, not ground-truth labels:

- **Telegram:** 13 JSON exports; 1,500 message records; 13 service records; 199 photo references.
- Telegram message-level observations included 63 empty-text messages, 40 edit-metadata records, and 42 forwarded records. These are overlapping record attributes; do not add them together as if they were disjoint groups.
- **Social media:** 350 CSV posts across Instagram (126), Facebook (88), X (48), YouTube comments (36), and ShareChat (52).
- **Images:** 92 social-media image files and 18 poster files.
- **Poster integrity:** all 18 poster files matched the supplied SHA-256 index in the previous structural audit.
- **Lexicon:** 37 rows.
- **Content-record total:** 1,850 = 1,500 Telegram messages + 350 social posts. The 13 Telegram service records are separate and are not included in this content-record total.

Social CSV fields observed in the archive:

`post_id`, `platform`, `author`, `posted_at_ist`, `text`, `hashtags`, `image_file`, `location_tag`, `likes`, `comments`.

The participant archive did **not** include a judge-only answer key. Do not invent labels or claim accuracy, precision, recall, F1, campaign-linkage correctness, or model superiority from this dataset. The previous audit establishes structural counts and the supplied poster hash matches only; it does not authenticate the real-world truth of any record.

## Required implementation shape

### 1. Local-only dataset staging

Use a local, ignored path such as:

`data/participant/PS02_demo_data/`

or keep the supplied ZIP under:

`data/participant/`

Support an extracted directory and, where practical, the ZIP archive directly. Resolve the path from an environment variable such as `PS02_DATASET_PATH`; do not hardcode a developer-specific absolute path.

Never commit the participant archive, extracted records, or original media. The repository's `.gitignore` is being updated for the expected local staging paths. Confirm the ignore rule works before running `git add`.

### 2. Dedicated aggregate-only reader

Prefer a focused module such as `ingestion/ps02_dataset_reader.py` (first search for existing reusable helpers). It should:

- Validate the expected folders: `01_telegram_exports`, `02_social_media`, `03_images`, and `04_lexicon`.
- Read Telegram JSON exports safely; distinguish message records from service records.
- Read social CSV files with UTF-8 BOM handling and validate the expected columns.
- Parse `posted_at_ist` as the dataset's India-local timestamp field; report invalid/missing timestamps without silently inventing dates.
- Count blank-text records, forwarded/edit metadata, and photo references without displaying their raw content.
- Check whether referenced image files exist, reporting counts and missing-reference totals.
- Verify the poster files against the provided SHA-256 index; report verified/failed/missing counts.
- Count lexicon rows without displaying the lexicon terms in the public demo view.
- Produce a deterministic aggregate report with a dataset provenance label and clear validation findings.
- Validate ZIP paths and size limits before reading members. Do not extract untrusted ZIP paths directly to arbitrary filesystem locations.
- Fail clearly with an actionable message if the archive is absent, incomplete, malformed, or has an unexpected root folder.

The reader must not return or persist row-level personal or target information. It should not write records to the existing operational SQLite pipeline.

### 3. New dataset-first Streamlit page

Add a separate page under `dashboard/pages/` (pages 1–9 already exist; choose the next available page number, for example `10_📦_PS02_Dataset_Demo.py`).

Build the page around the **actual committee archive** and the aggregate report. Include:

- A clear `HACKATHON PROVIDED DATASET · LOCAL · UNVERIFIED` provenance/status label.
- KPI cards for total content records, Telegram messages, social posts, platforms, media assets, and poster hash verification.
- A platform-distribution bar chart using the actual CSV counts.
- A time-distribution chart from valid `posted_at_ist` values, with an explicit IST label and sensible date bucketing.
- A data-quality section: empty-text count, service-record count, timestamp errors, missing attachment references, and poster-hash results.
- A media/asset integrity section with totals only.
- A lexicon inventory count, not an exposed list of terms.
- A refresh/revalidate action and clear error states.
- A visible explanation that this page reads the committee archive locally and does not mix it with synthetic sample data.

Do not render raw message text, author names, usernames, handles, phone numbers, email addresses, UPI IDs, wallet addresses, exact location tags, or row-level exports. Do not build target profiles, identity graphs, payment/contact networks, or cross-platform person matching from this archive. Do not add a CSV export of individual rows.

### 4. Preserve the existing application

- Do not delete or replace pages 1–9, the existing worker, the existing sample data, or the existing demo scripts.
- Do not silently change the existing sample/synthetic path into a committee-data path.
- Keep the committee dataset reader separate from the worker and existing DB.
- A dataset demo should not reset, reseed, or mutate `data/osint_monitor.db`.
- Where the existing app displays sample/synthetic data, keep its provenance badge accurate.
- Make the new page usable at desktop and narrow/mobile widths; avoid fixed-width layouts and overflowing tables.

### 5. Correct inaccurate presentation material

The current `README.md` appears to describe an unrelated crypto trading terminal called **OpenTerminal**. It must be corrected to describe this actual repository and its verified capabilities before the judge presentation. Remove unsupported badges/claims such as unrelated market feeds, "all complete", "zero mock data", or production-ready statements unless verified.

The existing `docs/DEMO_SCRIPT.md` contains stale scripted examples, specific personal/payment identifiers, and strong legal/evidence claims. Do not repeat those examples or claims. Replace or clearly supersede it with the truthful dataset-first runbook in [PS02_HACKATHON_DEMO_RUNBOOK.md](PS02_HACKATHON_DEMO_RUNBOOK.md). Describe hashes as integrity checks; do not call a dataset hash match proof that its contents are authentic or legally admissible.

## Build order — deadline priority

1. **Baseline:** inspect `git status`, read `AGENTS.md`, `README.md`, relevant modules and tests. Run the current test suite before changes and record existing failures separately.
2. **Dataset path:** stage the archive locally; run `scripts/ps02_preflight.py`; fix or extend the preflight only when the observed dataset requires it. Do not claim it passes until it has actually run against the archive on the laptop.
3. **Reader and tests:** implement the focused aggregate reader and fixture-based tests. Do not use the committee's raw archive as a committed test fixture.
4. **Dashboard:** add the new dataset page and verify that the UI numbers come from the reader report, not hardcoded constants.
5. **Old-demo regression:** confirm the previous application pages and synthetic demo still operate independently.
6. **Judge polish:** correct README/demo guide, verify labels and errors, capture fresh screenshots, and rehearse the exact runbook.

Do not spend the deadline adding new ML models, live scrapers, OCR pipelines, external API dependencies, or new operational targeting features. A stable, fully demonstrated dataset workflow is more valuable than unverified scope.

## Commands and verification

From the repository root (Windows PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
$env:PS02_DATASET_PATH = "data/participant/PS02_demo_data"
python scripts/ps02_preflight.py --dataset $env:PS02_DATASET_PATH --output data/participant/preflight-report.json
python -m streamlit run dashboard/app.py
```

From the repository root (macOS/Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
export PS02_DATASET_PATH="data/participant/PS02_demo_data"
python scripts/ps02_preflight.py --dataset "$PS02_DATASET_PATH" --output data/participant/preflight-report.json
python -m streamlit run dashboard/app.py
```

Use the actual extracted path or ZIP path supplied on the laptop. The preflight JSON is an aggregate report and should remain in the ignored local participant-data directory. Run the test suite again after implementation. Record every command and its real result. Never describe an unrun test, screen, ingestion, or feature as passing.

**Caution:** Do not launch `scripts/run_demo.py` or `scripts/run_demo.sh` as the first dataset-demo command. Existing demo scripts may reset/reseed the database and start synthetic replay. Use the Streamlit entry point directly for the new dataset page, and verify the old demo separately.

## Definition of done

- [ ] A clean laptop checkout can locate the committee dataset using a documented local path.
- [ ] The structural preflight runs against the actual supplied archive and reports its observed counts.
- [ ] The new dataset page reads the archive locally and all visible metrics are derived from the report.
- [ ] The five-platform breakdown and IST time chart use actual valid records.
- [ ] Poster SHA-256 checks run against the actual supplied files and manifest.
- [ ] Missing/corrupt data produces clear errors rather than fake success or placeholder metrics.
- [ ] No row-level personal identifiers, raw text, profiles, or cross-platform identity links appear in the dataset page/report.
- [ ] The prior dashboard/demo path is preserved and clearly labelled as its real source.
- [ ] Existing tests and new tests are run; failures are recorded rather than hidden.
- [ ] README and judge runbook accurately describe what was demonstrated.
- [ ] Fresh screenshots are captured from the running application, not mockups.

## Copy/paste execution instruction for Antigravity

You are taking over the existing PS02 repository for a next-day hackathon demonstration. Read this entire file, `AGENTS.md`, [PS02_DATASET_PROFILE.json](PS02_DATASET_PROFILE.json), [PS02_DATASET_ACCEPTANCE_CHECKLIST.md](PS02_DATASET_ACCEPTANCE_CHECKLIST.md), and [PS02_HACKATHON_DEMO_RUNBOOK.md](PS02_HACKATHON_DEMO_RUNBOOK.md) before editing. Work from the current repository state and preserve all existing changes. First run `git status --short --branch` and `python -m pytest -q`; report the baseline. Then implement the local-only, aggregate-only committee dataset reader and a separate Streamlit dataset demo page, reusing existing code where safe. Do not route committee records through `ingestion/worker.py`, do not expose raw identifiers or row-level content, do not modify the operational DB, and do not commit the source archive. Make the dataset page fully functional with the real local archive, retain the previous sample demo, correct the unrelated/stale README and judge demo guide, add tests, run the complete suite, capture real screenshots, and report exact verified versus unverified results. Do not stop at documentation or a mock UI: complete the implementation and run it on the actual archive once it is present on this machine.
