# PS02 Participant Dataset Demo — Architecture Contract

## Design
Create a dedicated, offline, aggregate-only path beside the existing Streamlit application. Do not pass the participant archive through the current threat-extraction worker: that path extracts and links personal/payment identifiers. That behaviour is not needed to demonstrate real use of the committee dataset.

## Responsibilities
- Preflight: bounded ZIP inspection, optional root discovery, required-folder checks, JSON/CSV structure validation, aggregate counts, timestamp checks, attachment reference checks and poster manifest hashes.
- Parser: Telegram JSON records and actual social CSV schema, tolerant of BOM and malformed files.
- Import: dry-run first, explicit user action, stable keys, idempotent re-import, transaction rollback.
- Store: dedicated SQLite DB (for example `data/participant_demo.sqlite3`) leaving `data/osint_monitor.db` unchanged.
- UI: new “PS02 Participant Dataset” page with upload, preflight, preview, import, batch provenance, charts and aggregate report export.
- Launcher: new nondestructive command. Existing `scripts/run_demo.py` resets/reseeds the legacy DB and must not be used for a preservation-sensitive judges run unless safely changed.

## Aggregate-only fields
Store only what is needed: batch ID, safe relative source filename, platform/record type, opaque stable record key, parsed timestamp, allowed aggregate categories, attachment-present flag and import timestamp. Never store raw text, authors, handles, phone/payment details or personal contacts in the participant demo store.

## Data rules
- Telegram: separate messages and service records; aggregate blank text, edit/forward flags and photo references if supported by source fields.
- Social: use post IDs only for deduplication; platform and IST timestamps for time-series aggregation; hashtags/location tags only as safe aggregates. Never display author/text.
- Images: path-safe reference checking; no external OCR or image upload. Prefer counts, not thumbnails.
- Poster manifest: compare local bytes to declared SHA-256 and report matched/missing/mismatch independently.
- Lexicon: validate/count rows only; do not train models or modify current lexicon from participant text.

## UI states
No dataset → upload → preflight running → pass/warn/fail → dry-run preview → explicit import → success summary → aggregate insights. Include empty/error states and actual progress, not staged/fake values.

## Acceptance
- Both Telegram and social files contribute to analytics.
- All counts are computed from uploaded bytes at runtime.
- Source/batch labels shown on every chart.
- Re-import is idempotent.
- Dry-run has no writes.
- Legacy DB/pages remain unchanged and usable.
- ZIP, raw files and participant DB remain local and gitignored.
