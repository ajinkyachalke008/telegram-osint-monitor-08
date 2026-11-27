# PS02 Dataset Demo Acceptance Checklist

Use this checklist during Antigravity implementation and the final laptop rehearsal. Tick an item only after observing it work on the actual archive.

## A. Repository safety and baseline

- [ ] Read `AGENTS.md` and the PS02 handoff documents.
- [ ] Run `git status --short --branch`; preserve any existing local work.
- [ ] Run `python -m pytest -q` before code changes and record the baseline result.
- [ ] Confirm the participant archive and extracted source data are ignored by Git.
- [ ] Confirm no committee archive, raw export, original media, credentials, or secrets are staged.
- [ ] Do not merge committee data into the synthetic sample database.

## B. Local dataset discovery

- [ ] Dataset can be supplied as an extracted directory or supported ZIP path.
- [ ] Path is configurable through `PS02_DATASET_PATH`; there is no developer-specific absolute path.
- [ ] Missing dataset produces a clear instruction showing the expected path.
- [ ] Expected top-level folders are checked: Telegram exports, social media, images, and lexicon.
- [ ] ZIP member paths, duplicate names, entry count, per-member size, and total size are validated before reading.
- [ ] Malformed JSON/CSV and unsupported file layout produce useful errors.

## C. Structural data checks

- [ ] Telegram JSON exports are parsed without treating service records as messages.
- [ ] Telegram message/service counts are shown separately.
- [ ] Empty-text, edit-metadata, forwarded, and photo-reference counts are reported without displaying source content.
- [ ] Social CSV headers are validated against the actual participant schema.
- [ ] All five platform totals are computed from CSV rows, not hardcoded.
- [ ] `posted_at_ist` timestamps are parsed and invalid/missing values are counted.
- [ ] Image references are checked for existence; missing references are counted.
- [ ] Poster SHA-256 index rows are compared with the actual local poster files.
- [ ] Lexicon row count is computed without exposing the term list.
- [ ] The report contains aggregate counts and non-sensitive error codes only.

## D. Dataset-first dashboard page

- [ ] A dedicated page is added under `dashboard/pages/`; existing pages 1–9 remain.
- [ ] Page provenance reads `HACKATHON PROVIDED DATASET · LOCAL · UNVERIFIED`.
- [ ] Main content total is computed from message/post records and excludes service records.
- [ ] KPI values come from the parser report, not fixed placeholder constants.
- [ ] Platform chart uses the actual five-platform breakdown.
- [ ] Time chart labels the timezone as IST and excludes invalid timestamps transparently.
- [ ] Asset/integrity area shows image totals and actual poster hash pass/fail counts.
- [ ] Data-quality area shows missing/invalid counts and explains their meaning.
- [ ] Refresh/revalidate works; stale cached results are not presented as fresh.
- [ ] Empty, missing, and malformed inputs produce useful error states.
- [ ] Layout works on normal desktop width and a narrow/mobile viewport.
- [ ] The page does not display raw message text, authors, handles, contact/payment IDs, wallet addresses, exact location tags, or row-level exports.
- [ ] The page does not build target profiles, identity graphs, or cross-platform identity matches.
- [ ] The page does not write participant records into the operational SQLite database.

## E. Tests and regression

- [ ] Unit tests use small synthetic fixtures, not the real committee archive.
- [ ] Tests cover valid directory and ZIP layouts.
- [ ] Tests cover ZIP path traversal and archive-size limits.
- [ ] Tests cover Telegram message/service separation and malformed JSON.
- [ ] Tests cover social schema, platform counting, and timestamp parsing.
- [ ] Tests cover empty text and overlapping metadata counts.
- [ ] Tests cover missing media references and poster hash pass/fail cases.
- [ ] Test asserts the generated report contains no row-level source values or identifiers.
- [ ] Run focused PS02 tests.
- [ ] Run full `python -m pytest -q` and record the actual result.
- [ ] Run the dashboard and validate the new page from a clean checkout.
- [ ] Run the old demo separately and confirm the existing sample workflow was not broken.

## F. Judge readiness

- [ ] README title and content describe Telegram OSINT Monitor, not OpenTerminal or a crypto trading terminal.
- [ ] Stale demo guide content has been corrected or superseded.
- [ ] Every claim in the judge walkthrough is observable in the running app.
- [ ] Screenshots are captured from the running page, not generated mockups.
- [ ] Dataset page is visibly distinct from sample/synthetic pages.
- [ ] The team can explain the data counts, poster hash check, limitations, and missing answer key.
- [ ] No model accuracy, real-world attribution, or legal admissibility claim is made without appropriate validation.
- [ ] The full demo is rehearsed from the documented commands with no hidden setup steps.

## Final report required from Antigravity

Provide a compact table with each feature, evidence, command or screenshot, and status: **verified**, **partially verified**, **not verified**, or **blocked**. Include the full test summary, actual archive path used (not personal file contents), actual parsed counts, any remaining issues, and the exact branch/commit pushed. Never mark a feature complete just because code was written.
