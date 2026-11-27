# PS02 Participant Dataset Demo — Architecture Contract

## Design choice
Add a dedicated, offline, aggregate-only dataset path beside the existing application. Do not route participant messages through the legacy active threat-extraction worker. The current worker extracts and links personal/payment identifiers and produces profiles; that is not needed to prove that the supplied dataset is genuinely used.

## Components (proposed)
- `ps02_dataset/preflight.py`: bounded ZIP inspection; optional root discovery; required path checks; aggregate counts; social CSV schema/time validation; Telegram JSON structural validation; attachment reference checks; poster SHA-256 manifest checks.
- `ps02_dataset/ingest.py`: reads only fields needed for aggregate analytics; builds deterministic record keys from source-file path + stable record ID; no author/text/contact values persisted.
- `ps02_dataset/store.py`: separate SQLite file (e.g. `data/participant_demo.sqlite3`) with batches and aggregate dimensions; never use `data/osint_monitor.db` for this dataset path.
- `dashboard/pages/10_📊_PS02_Dataset_Insights.py`: upload ZIP, preflight, dry-run, explicit import, batch selector, aggregate charts, source-provenance summary and downloadable aggregate report.
- `scripts/run_ps02_dataset_demo.py`: nondestructive launcher; no DB reset, no synthetic data reseed, no TGSherlock startup and no automatic browser side-effects where avoidable.
- `tests/test_ps02_dataset_*.py`: isolated fixtures covering ZIP safety, schema, timestamps, attachments, manifest integrity, dry-run, idempotence and DB isolation.

Names are a suggested layout, not a demand to match exact filenames. Reuse repository conventions where appropriate.

## Required record handling
- Telegram: count JSON exports and message/service records separately. Track empty text, edit/forward metadata, photo references and attachments as aggregate flags/counters only.
- Social: read post ID for dedupe, platform and timestamp for grouped analytics, hashtags only as aggregate frequency if safe; do not persist or show author or text. Image references must be path-validated.
- Images/posters: validate that referenced files exist within the archive and calculate manifest hash status. Do not upload images or render potentially identifying text from posters; display aggregate thumbnails only if clearly safe and needed (prefer no images for first demo).
- Lexicon: count rows and validate required columns; do not use participant terms to train or alter models.

## UI states
1. No dataset: explain which ZIP to select.
2. Preflight running: truthful spinner.
3. Preflight passed with warnings: show warning count and clear remediation.
4. Preflight failed: show actionable safe error (no raw rows or path traversal details).
5. Dry run available: counts and skipped reason breakdown.
6. Import complete: batch ID, rows processed, records inserted/duplicates/skipped, timestamp, source archive label.
7. Existing batch selected: show its aggregate charts only.
8. Empty/no data state: clear next action.

## Import semantics
- Re-import of same source archive and same record IDs returns duplicates/skips without double counting.
- A different archive with same filename but different content must be a different batch. Compute a SHA-256 digest of the archive bytes for local batch identity; do not publish the full digest if that could reveal linkage across environments. Store it locally.
- Dry-run must not create tables/rows or write to participant DB.
- A failed import must roll back partial writes.
- Keep data local. Never include the ZIP, raw data, local SQLite file, reports containing granular sensitive dimensions, or image extracts in Git.

## Acceptance checks
- The participant ZIP upload is visibly supported.
- Observed aggregate counts are computed from the uploaded archive, not copied constants.
- Telegram and social files both contribute to the visible analytics.
- Poster manifest is checked against image bytes, with matched/missing/mismatch reported separately.
- The aggregate report is downloadable and includes source/batch, counts, validation results, run timestamp and caveats.
- A rerun is idempotent.
- The legacy app DB, pages and synthetic features remain intact.
- Unit tests and exact demo steps are written down.
