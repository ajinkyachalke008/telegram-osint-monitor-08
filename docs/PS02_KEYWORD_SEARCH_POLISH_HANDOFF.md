# PS02 Keyword Search & Evidence Preview — Antigravity Build Handoff

**Priority:** P0 — next-day hackathon demo  
**Repository:** https://github.com/ajinkyachalke008/telegram-osint-monitor-08  
**Base branch:** `main`  
**Base commit inspected:** `612212bb83d064f164f3707dd64e484bdd1fb7f7`  
**Purpose:** Add one polished, real, dataset-backed search workflow without replacing or breaking the existing application.

## 1. Mission

Extend the existing Telegram OSINT Monitor with a **local PS02 Keyword Explorer** for the committee-provided participant ZIP. The primary demo should let a judge type a phrase such as **“fake Aadhaar card”**, see matching records from the supplied archive, identify the Telegram **chat/channel source**, timestamp and matched terms, and preview a photo attached to a matching record.

This must be a real search of the supplied ZIP—not hardcoded cards or synthetic results. Preserve the existing aggregate dataset page and all earlier application pages.

## 2. Read these files first

- `AGENTS.md`
- `docs/ANTIGRAVITY_HACKATHON_HANDOFF.md`
- `docs/PS02_DATASET_PROFILE.json`
- `docs/PS02_DATASET_ACCEPTANCE_CHECKLIST.md`
- `docs/PS02_DATASET_DEMO_ARCHITECTURE.md`
- `docs/PS02_HACKATHON_DEMO_RUNBOOK.md`
- `dashboard/pages/10_📊_PS02_Dataset_Insights.py`
- `ps02_dataset/preflight.py`
- `ps02_dataset/parser.py`
- `ps02_dataset/importer.py`
- `ps02_dataset/store.py`
- `tests/test_ps02_dataset.py`

Work from the **current `main` branch**. PR #3, #13 and #14 are already merged. Several older feature/handoff branches are behind `main`; do not reset the workspace to one of those stale branches and do not copy their old trees over the current project.

## 3. What already exists (verified in current main)

- Streamlit multipage app; preserve the existing pages and their current database.
- Page 10, `dashboard/pages/10_📊_PS02_Dataset_Insights.py`, is the committee dataset intake, preflight, dry-run, transactional import and aggregate-insights page.
- Dataset-specific modules already exist:
  - `ps02_dataset/preflight.py`
  - `ps02_dataset/parser.py`
  - `ps02_dataset/importer.py`
  - `ps02_dataset/store.py`
- The parser is intentionally aggregate-only: it counts records and media but does **not** retain raw post text or per-message search rows.
- The old alert pages (Pages 1–2) query the legacy `osint_monitor.db`; they are **not** searching the committee participant archive.
- The existing ingestion worker extracts identifiers and writes legacy records/links. Do not route the participant ZIP through that worker.

Therefore, the requested participant-data search is **not currently implemented**. Add it as a separate, explicit feature. Do not pretend the existing aggregate chart page is already a message search engine.

## 4. Participant ZIP facts (recomputed from the uploaded archive)

The uploaded archive is `PS02_demo_data-20261127T071007Z-1-001.zip`. Keep the archive and all extracted contents local; never commit them.

| Item | Observed |
|---|---:|
| Telegram JSON exports | 13 |
| Telegram message records | 1,500 |
| Telegram service records | 13 (separate from messages) |
| Telegram photo references | 199 |
| Telegram photo files resolved inside the archive | 199 / 199 |
| Social CSV posts | 350 |
| Social image references / files | 92 / 92 |
| Poster images | 18 |
| Poster SHA-256 comparisons against the supplied index | 18 matched in the previous archive audit |
| Starter lexicon CSV rows | 37 |

Telegram exports have top-level chat fields such as `name` and `id`. Message rows also contain sender fields `from` and `from_id`. Social rows include `author`, `text`, `posted_at_ist`, `platform` and `image_file`.

**Important query observation:** the literal phrase `fake Aadhaar card` did not occur in the Telegram or social text I checked. The token `aadhaar` did occur in **81 Telegram messages** and **12 social posts**. Treat those as broad keyword matches only; do not label every Aadhaar mention as fake or illicit. The actual search must recompute all results from the file at runtime.

The ZIP also contains an additional `Suspect_Repository_masked` folder with six CSV files that is not described in the dataset README folder map. **Exclude this undocumented folder from the demo search/import.** Do not inspect, render, or join it to the Telegram/social data unless the committee supplies explicit scope and permission.

## 5. Required UX

Prefer a new page such as `dashboard/pages/11_🔎_PS02_Keyword_Explorer.py`, linked naturally from Page 10. Keep Page 10's aggregate-only promise unchanged.

### Search controls

- Main search input: keyword or phrase, e.g. `fake Aadhaar card`.
- Search scope: Telegram, social media, or both.
- Source filter: all Telegram chats or one of the exported **chat/channel names**.
- Optional chat filter: the export-level chat ID only, clearly labelled **Chat ID**.
- Date range filter using the dataset's local time convention, visibly labelled **IST**.
- `Has attached image` filter.
- Exact phrase mode and an optional **Expand terms** mode. Show the exact expanded terms/tokens being searched so results are explainable.
- A clear search button and reset control; do not run expensive ZIP scans on every keystroke.

### Results

Each result card may show:
- source platform;
- Telegram chat/channel title (or social platform);
- message/post date and time in IST;
- matched term(s) highlighted;
- a short text excerpt with contact/identity values redacted;
- attached image preview when an image is actually referenced and resolves inside the selected archive;
- a source-file label such as the export folder name.

Do not invent results, timestamps, chat names, attachment links or match explanations. Use an honest no-results state. Sort deterministically (newest first by valid IST timestamp, with a stable fallback).

### Image previews

- Telegram `photo` paths are relative to the corresponding export folder; social `image_file` paths are relative to the social-media folder.
- Resolve each path against the ZIP member list, reject absolute paths and `..`, and verify the member exists before reading it.
- Render from ZIP bytes in memory (for example, `BytesIO`); do not blindly extract arbitrary archive paths.
- Show a clear missing/unsupported-image state rather than a broken image.
- Label previews as **attachments from the supplied demo archive**, not proof of an event or identity.
- First version is text-index search. Do not claim image-only posts are searchable by their visual text unless local OCR is implemented, tested and clearly identified as OCR output. Do not send images to external OCR/API services.

## 6. Search and privacy boundaries

The distinction in the Telegram schema matters:

- **Allowed source filter:** top-level chat/channel `name` and top-level chat/channel `id`.
- **Do not implement:** individual sender `from` / `from_id` lookup, Telegram user/author username lookup, user dossiers, member enumeration, cross-channel person tracking or identity graphs from this archive.
- Do not display or persist social `author` values.
- Do not render raw phone numbers, email addresses, Telegram handles/links, UPI/payment identifiers, bank/account numbers, wallet addresses or other personal contact details. Redact them from result excerpts and never use them as search pivots or graph edges.
- No contacting, joining, purchasing, scraping, outreach or live Telegram lookups. This is an offline file-demo only.
- A keyword hit is a **search hit**, not a verified offence or a claim about the author. Avoid labels such as “criminal”, “seller confirmed” or “fraudster”.
- Do not persist the raw text, sender fields, or individual search results in SQLite, logs, exports, caches or screenshots. Search should be ephemeral/in-memory for the active local session. The existing participant aggregate database remains aggregate-only.
- Do not route these records through `PipelineWorker.process_raw_post()`, the legacy classifier, financial detector, identifier extractors or entity graph.
- No model training/fine-tuning on committee participant records.

Use safe ZIP/path validation helpers already present in `ps02_dataset/preflight.py` rather than creating a weaker duplicate. Avoid adding new dependencies unless essential.

## 7. Keyword expansion

Use the committee starter lexicon as a reference, and keep the search-term groups transparent and editable in one clearly named project config/module. Include categories that reflect the README's dataset description (for example, drugs, arms, fake documents, bank-account sale, ATM-card sale and SIM-card sale), but never imply that a category label is ground truth.

For a phrase such as `fake Aadhaar card`:
1. Exact mode should honestly report zero literal phrase matches if there are none.
2. Expanded mode may search the configured Aadhaar-related aliases and show which alias matched.
3. Clearly separate exact matches from broader term matches. A broad `aadhaar` match is not proof that a post advertises a fake document.
4. Do not silently broaden every query into unrelated high-volume terms.

Do not hardcode the observed 81 / 12 counts; compute them from the selected archive every time.

## 8. Required verification

Add focused tests for:
- Telegram JSON text represented as either a string or Telegram entity-list structure;
- case-insensitive and Unicode-normalized matching;
- exact phrase versus expanded-term behavior;
- chat-name/chat-ID filters and date-range filtering;
- sender `from` / `from_id` are never returned or searchable;
- sensitive values are redacted from result excerpts;
- Telegram and social image references resolve only inside their intended ZIP directories;
- traversal/absolute ZIP paths and missing image members are rejected;
- service records are excluded from normal message-result cards;
- no raw text or sender/contact fields are written to the participant SQLite database;
- empty results, malformed records and invalid timestamps fail gracefully.

Run the existing suite plus the new tests. Test against the actual uploaded ZIP from a local path (copy it to the documented local input location only on the developer machine). Confirm:
- 1,500 Telegram message records;
- 13 service records;
- 350 social records;
- 199 Telegram photo references and 92 social image references;
- query counts are computed, not hardcoded;
- a known keyword search returns only real matching rows from the selected ZIP;
- a matched row with a valid photo shows that archive image;
- exact `fake Aadhaar card` and expanded `aadhaar` results are reported separately.

Also smoke-test the Streamlit page at desktop and mobile widths. Keep the result cards readable, with no horizontal overflow.

## 9. Small UI/data-quality polish to check while touching Page 10

- Replace any hardcoded `199 / 199` or `92 / 92` media metrics with values computed from the current audit/import result.
- Review the automatic-import fallback in Page 10. The visible workflow says preflight → dry-run → explicit import; do not silently perform an import that bypasses that user action.
- Avoid absolute claims such as “100% privacy compliant” or “statutory compliance” unless independently established. Prefer factual wording: “local processing”, “aggregate store”, “no external service used by this page”.
- Do not change the existing legacy database schema or reset/reseed the legacy database during the participant-dataset demo.

## 10. Demo acceptance flow

1. Open Page 10 and select/upload the committee ZIP.
2. Run preflight and show the actual results.
3. Run dry-run; show zero database writes.
4. Import only after the explicit confirmation/button and show the separate aggregate dataset batch.
5. Open Page 11 Keyword Explorer.
6. Search `fake Aadhaar card` in exact mode; explain the honest no-literal-phrase result.
7. Toggle expanded terms; search `aadhaar`; show the actual match count, chat/channel source and IST timestamp.
8. Open a result that has an attached photo and preview the archive image.
9. Explain that the sender's personal identity/contact information is intentionally not exposed and that a keyword hit is not a finding of guilt.
10. Briefly show the existing pages separately, preserving their original provenance labels.

**Done means:** a real, fast, local keyword search over the supplied ZIP; source/channel-level context; safe attachment previews; redacted content; no sender profiling; no raw participant text persisted; tests passing; no regression to existing app functionality.
