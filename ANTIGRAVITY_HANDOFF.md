# Antigravity Handoff — PS02 Hackathon Dataset Demo

**Priority:** P0 — demo is tomorrow.  
**Repository:** https://github.com/ajinkyachalke008/telegram-osint-monitor-08  
**Branch for this work:** `feat/ps02-hackathon-dataset-demo`  
**Default branch:** `main`  
**Goal:** Make the existing Streamlit application demonstrate real, traceable use of the organiser-provided PS02 participant dataset, without pretending synthetic/demo data is real and without replacing the existing application.

## 1. Read this first — project identity and repository facts

This is the Telegram & Social Media Illegal Trade Monitor (PS02). The current `README.md` is materially stale/mismatched: it describes an unrelated crypto trading terminal called “OpenTerminal”. Do not use that README as the authoritative product specification. The relevant project documentation and code include:

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
- `scripts/ps02_preflight.py`
- `docs/PS02_PREFLIGHT.md`
- `docs/PS02_Aggregate_Audit_Summary.json`

**Do not rewrite the system from scratch.** Inspect the current code, run it, map the actual entry point and existing pages, preserve working features, and make only small reversible changes. There is already a Streamlit multipage dashboard and CSV/JSON data ingestion page.

## 2. User's hackathon instruction

The hackathon committee has explicitly allowed using the datasets provided to participants. We must therefore make the provided PS02 data a first-class part of the live demonstration, not merely show the older synthetic replay. The user wants to show that the supplied dataset is really loaded and processed by the project, while keeping all previous working project features intact.

The participant archive previously audited in this conversation is named:

`PS02_demo_data-20261127T071007Z-1-001.zip`

**The archive itself is not committed to GitHub.** It must be made available locally by the user at demo time (for example in a local `data/participant/` folder or selected through a file uploader). Do not expect it to exist in a clean clone.

Prior aggregate inventory (from an offline review of the uploaded participant archive; treat as an audit snapshot, not live application output):

| Dataset part | Observed aggregate |
|---|---:|
| Telegram exports | 13 JSON exports |
| Telegram message records | 1,500 |
| Telegram service records | 13 |
| Telegram photo references | 199 |
| Social posts | 350 |
| Social image files | 92 |
| Poster files | 18 |
| Poster SHA-256 checks | 18/18 matched in the earlier audit |
| Lexicon rows | 37 |
| Total social + Telegram message/post records | 1,850 |

Telegram JSON archives included some non-message service records, blank text and edit/forward metadata. Do not count all JSON records as message text. Social CSV data includes platform, author, posted_at_ist, text, hashtags, image_file, location_tag, likes, and comments. These aggregate numbers are expected reference values only; recompute against the actual file present at runtime and show both expected and observed only where useful. Never hardcode the counts as if they came from a fresh run.

The participant ZIP did not include the judges' private answer key. Do not claim ground-truth campaign attribution, entity-linkage precision/recall, or classifier accuracy on the judge answer key. Do not invent benchmark results.

## 3. Required product outcome for tomorrow

Deliver a real demo flow that can be run from the laptop with a single documented command and that visibly uses the participant dataset:

1. Launch the existing app without destroying existing DB contents unless the user explicitly chooses a reset.
2. Make the participant dataset discoverable via a clear “PS02 Participant Dataset” panel/page or an obvious section of Page 6 (Data Ingestion).
3. Accept the provided ZIP directly, or a safely extracted participant dataset directory. Prefer ZIP streaming/in-memory reading; do not force users to manually rearrange files.
4. Run offline structural preflight and show a clear summary: file inventory, counts by platform, Telegram message/service counts, empty-text count, attachment references, image/poster counts, lexicon rows, timestamp parse/quality summary, required folder/schema checks, duplicate IDs if checked, and poster hash verification.
5. Ingest only the supported, schema-mapped records needed for the demo. Use source-specific adapters for Telegram JSON exports and the actual social CSV schema. Do not assume the social file columns match the generic Page 6 upload defaults.
6. Display a run summary: records examined, records eligible, records skipped with reason counts, records imported, duplicate/idempotent records, and errors. Use actual run-time results.
7. Add provenance on every imported record at dataset/batch level: source dataset, platform/type, original source file (or safe relative path), import timestamp, and a batch/run ID. Do not expose sensitive values in the public UI.
8. Show useful interactive, aggregate-only visualizations derived from the participant dataset: per-platform distribution, time distribution (IST with timezone handled explicitly), category/record type counts if reliable, empty/edited/forwarded counts if reliable, attachment availability, location-tag counts only as aggregates, dataset quality checks, and source coverage.
9. Preserve the existing dashboard pages and current normal workflows. Add a clear switch/filter to distinguish participant-imported data from synthetic replay data. Never blend them silently.
10. Ensure re-running import is safe and idempotent; repeated run must not double-count or destroy existing DB.
11. Provide an explicit dry run / preview before any write. A visible “Import participant dataset” action is required.
12. Add an obvious “Dataset demo mode” label so judges know the source and limitations.

## 4. Strict scope and privacy constraints

This project processes sensitive user-generated content. For the hackathon demonstration, implement safe aggregate analytics and dataset quality checks, not operational targeting:

- Do not surface authors, usernames, phone numbers, UPI/payment IDs, wallet addresses, personal contacts, or raw message text in new participant-dataset views or exports.
- Do not extract or correlate actionable personal/payment identifiers from the supplied dataset.
- Do not build target profiles, seller dossiers, or cross-platform person identity graphs from the dataset.
- Do not infer guilt or make claims that a person/account is a criminal. Classifier output is an unverified triage hint only.
- Keep any aggregate location view at safe, high-level counts. Do not show precise coordinates or small-cell groups that may identify a person.
- Do not upload participant data to third-party APIs, model providers, analytics platforms, or external services.
- Do not train or fine-tune on participant Telegram or social content.
- Keep raw participant data local. Add it to .gitignore if a local data folder is used. Never commit the ZIP, raw exports, extracted raw files, personal identifiers, or database created from the participant dataset.
- No private-group access, channel joining, DMs, member scraping, or automated outreach.
- Treat the source dataset as a hackathon-provided demonstration dataset, not verified real-world evidence.
- Hash integrity proves file consistency against a supplied manifest, not the truth of the source content or identity of an author.

The existing application has pages for alerts, detail, entity graph, campaigns, map, ingestion, metrics, responsible use/audit, and discovery. Preserve existing pages, but do not connect the participant dataset to the existing personal-identifier graph/profiling paths. A separate aggregate-only dataset analytics path is preferred.

## 5. Technical requirements

### Dataset handling
- Inspect ZIP directory structure before implementation. Validate required paths and CSV/JSON structure against actual uploaded archive. Handle an optional top-level root folder.
- Protect against ZIP traversal, absolute paths, duplicate members, oversized members, excessive entry count, decompression bombs and corrupt archives. Do not extract paths supplied by archive without validation.
- Use bounded streaming reads. Keep reasonable size limits configurable.
- Parse JSON defensively; one bad export should create a visible file-level error without aborting the entire run.
- CSV reader must handle UTF-8 BOM, quoting, and empty values.
- Parse `posted_at_ist` as timezone-aware India time; don't silently interpret it as UTC. Preserve raw timezone metadata if the source has it.
- Validate image references using safe relative paths within archive/dataset root. Never trust absolute or `..` paths.
- Verify poster hash index entries only against files within the expected poster folder. Report matched, missing, and mismatched counts separately.
- Do not print raw row data in console logs or errors.

### Storage / isolation
- Prefer a dedicated SQLite database or separate dataset tables/namespaces for the participant demo; do not mix this content into the operational identifiers/evidence ledger.
- If a new table is needed, add schema migration/backward compatibility. Do not drop/recreate the user's existing DB.
- Batch imports should be atomic where feasible, and idempotent using stable source+record IDs.
- Add batch metadata and aggregate run metrics. Avoid raw author/text values in aggregate records.
- The default launch path must not reset or reseed any database automatically. Inspect `scripts/run_demo.py` carefully: it currently resets the database and seeds baseline demo records. Do not launch it blindly for a judges demo if preserving previous data is required. Add a safe launch option or new launcher that does not reset by default, and clearly document how the synthetic replay worker is started/stopped.

### UI
- Keep desktop and mobile layouts readable; the demo is likely desktop-first but the app should remain responsive.
- Clear progress indicators; no fake progress bars.
- Friendly validation errors with a downloadable aggregate-only JSON report.
- Keep raw text and identifiers out of new participant-dataset UI, logs, reports and screenshots.
- Label synthetic replay, participant import and any live feed distinctly.

### Tests / quality
Create tests for:
- ZIP path traversal / absolute path / duplicate file rejection
- ZIP size and entry limits
- optional root folder discovery
- Telegram JSON valid + malformed file handling
- social CSV schema, BOM and timezone parsing
- safe image relative path validation
- poster hash pass/missing/mismatch
- deduplication / re-import idempotence
- dry-run does not modify DB
- aggregate counts match fixture
- legacy DB remains readable and schema initialization preserves existing tables
- Streamlit page module imports without exception if possible

Run:
- `python -m compileall core ingestion dashboard scripts tests`
- `pytest -q`
- the repo's existing demo verification scripts where practical
- run actual participant ZIP through the new path locally (the user will provide the ZIP locally if missing).
Record exact test totals and any environment limitations. Never report tests passed unless actually run.

## 6. Demo UX / story

Suggested judges flow (about 3–4 minutes):

**0:00–0:30 — Product overview**  
Explain the existing platform and what the committee-provided data enables. Clearly label the dataset as hackathon-provided.

**0:30–1:10 — Dataset intake**  
Select the supplied ZIP. Run preflight. Show actual runtime totals and integrity checks.

**1:10–2:20 — Data insights**  
Show platform distribution, Telegram vs social coverage, posts over time (IST), image/attachment availability and dataset-quality statistics. Use interactive charts and filters with aggregate counts only.

**2:20–3:10 — Existing platform capability**  
Show one or two preserved existing features using synthetic fixtures only, clearly labeled synthetic. Do not imply participant records have been run through personal-identifier extraction or cross-person correlation.

**3:10–4:00 — Evidence, limitations and conclusion**  
Show aggregate audit report and source provenance. Explain human review, data limitations and that a participant dataset does not by itself establish truth or ground-truth labels.

Do not present synthetic UI as analysis of the committee-provided dataset. All charts must have visible source labels.

## 7. Priority order — time is short

**P0 (must work):**
1. Run the existing project locally and confirm current launch route.
2. ZIP upload and structural preflight for the exact PS02 archive.
3. Social CSV + Telegram JSON parsing with actual schema.
4. Dry-run summary with truthful counts.
5. Import into isolated, idempotent participant dataset store.
6. Aggregate dashboard and provenance panel.
7. One-command safe launch and a tested end-to-end flow.
8. Update concise operator instructions and demo script.

**P1 (only after P0 passes):**
- Responsive visual polish, concise cards, interactive charts, clear empty/error states.
- Export aggregate-only dataset quality report.
- Cache preflight results for quick rerun without re-reading images where safe.

**Do not spend time on:** complete refactor, adding new ML models, training, external APIs, new live scraping sources, or building new personal-identifier graph features.

## 8. Work discipline

- Start by reporting current git status, branch, current launcher, and exact pages/files.
- Make a short task checklist and mark it as you go.
- Run tests after each logical change.
- Keep commits small and descriptive.
- Do not force-push. Do not overwrite unrelated user changes. Do not merge to main without the owner's explicit approval.
- Before stopping, provide:
  - exact changed files
  - exact commands run
  - exact tests and results
  - any failed or skipped checks
  - launch command
  - precise dataset file placement / upload steps
  - known limitations
  - the remaining P0 items, if any

## 9. Important repository notes

- PR #3 (“Add PS02 offline dataset preflight QA tooling”) was merged into `main` on 2026-11-27. The aggregate-only script lives at `scripts/ps02_preflight.py`.
- The preflight port was simplified compared with a fuller local implementation. Its single test has not been verified in this handoff. Review and test it before relying on it. Do not assume it is sufficient for ingestion.
- Existing Page 6 (`dashboard/pages/6_📁_Data_Ingestion.py`) is a generic CSV/JSON importer using `PipelineWorker`; the participant dataset has a different directory structure and social schema, so a dedicated adapter is needed.
- Existing `scripts/run_demo.py` resets DB, seeds synthetic baseline data, starts replay, launches Streamlit and TGSherlock panel; do not use as a nondestructive judge launcher until corrected or a separate safe launcher is added.
- The `README.md` is stale and refers to an unrelated project. Update it only after the actual app startup and dataset demo are verified.
- Existing model and feature metrics are synthetic-only per `docs/HONEST_STATUS.md`, `docs/LIMITATIONS.md`, and `docs/METRICS.md`. Do not claim validated real-world detection accuracy.

**Definition of done:** a laptop user can select the committee ZIP, preview and validate it, import it without modifying the existing demo DB, see aggregate visualizations computed from that same archive, rerun without duplicates, and narrate the result truthfully in a 3–4 minute judge demo.
