# Telegram OSINT Monitor

A research and hackathon demonstration for **public-source, multi-platform threat-intelligence triage**. The application ingests exported or publicly available posts, extracts candidate identifiers, applies explainable rules, correlates repeated content, and preserves basic evidence-integrity metadata for analyst review.

> **Status and intended use:** This repository is a prototype/hackathon system, not an operational law-enforcement platform. Detection results are leads for human review, not proof of criminal conduct or identity. Do not use it to access private groups, contact people listed in samples, or take enforcement action based only on an automated score.

## Current capabilities

- Telegram Desktop JSON export ingestion and generic CSV/JSON import.
- Public Telegram preview and local TGSherlock read-only adapters.
- Unicode normalization, Hindi/English number normalization, homoglyph handling, and rule-based threat scoring.
- Candidate extraction for phones, context-labelled bank-account numbers, Telegram export account IDs, UPI-style identifiers, IFSCs, cryptocurrency addresses, Telegram handles/links, location mentions and prices.
- SQLite storage, source provenance, shared-identifier linking, alerts and a SHA-256 evidence chain.
- Streamlit dashboard for alerts, evidence review, entity graph, text similarity, geographic mentions, data ingestion, metrics, responsible use and channel discovery.
- Optional OCR through Tesseract (English, Hindi and Marathi, where language packs are installed).
- PS02 dataset audit/import workflow, including Telegram Desktop exports, social-post JSON, attachment hashes and OCR analysis.

## Run locally

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

The dashboard uses the repository's SQLite database at `data/osint_monitor.db` by default. Keep local databases, account sessions and credentials out of Git.

### Optional OCR

Install the Tesseract system executable and the language data files for `eng`, `hin` and `mar`. The application reports OCR as disabled when the required executable is not available; it does not fabricate extracted text.

## PS02 hackathon dataset

The PS02 page is available from the Streamlit multipage navigation as **PS02 Dataset Studio**.

1. Upload the complete `PS02_demo_data` ZIP.
2. Review the archive audit, channel inventory, media checks and warnings.
3. Choose whether to run OCR.
4. Explicitly select **Import 1,850 primary posts** to write the Telegram and social posts into SQLite.

Imported records use the provenance label `HACKATHON_SAMPLE`. The same archive is idempotent on re-import. The parser deliberately excludes the separate masked complaint/reference CSVs and the real-world reference-channel list from posts, alerts, scoring and entity correlation. The supplied starter lexicon is presented as analyst reference data; context-dependent terms are not automatically promoted wholesale into high-confidence detection rules.

The dataset should be supplied locally by the organizers. Do not commit the ZIP, extracted records, the masked complaint repository, OCR output containing sensitive information, or real credentials to this repository.

For CLI audit/import of an already extracted dataset:

```bash
python -m ingestion.ps02_dataset /path/to/PS02_demo_data --no-ocr
python -m ingestion.ps02_dataset /path/to/PS02_demo_data --import-db
```

## Tests

```bash
pytest -q
```

## Data handling and provenance

The post ledger distinguishes source classes such as `LIVE`, `IMPORTED`, `VERIFIED-SYNTHETIC` and `HACKATHON_SAMPLE`. These labels describe how records entered the application; they do not certify the truth of their content.

Original message text is retained separately from normalized/combined analysis text. PS02 source metadata is preserved in `source_metadata_json`; attachment and metadata SHA-256 digests are included in new evidence blocks when available. Hashing can help detect later changes, but a local mutable SQLite database is not an independently anchored or legally certified chain of custody.

Location displays represent locations mentioned in message text or structured post tags. They are not device GPS, IP location, or verified physical presence. Shared handles, payment identifiers, message templates and image hashes are investigative correlation signals only; shared content does not prove common ownership.

## Known limitations

- The judge-only PS02 answer key is not part of the supplied archive; precision, recall and official ground-truth accuracy cannot be calculated from this package alone.
- The current ingestion worker uses rule-based scoring. The separate ML classifier is not automatically part of the PS02 worker pipeline.
- OCR quality depends on source image quality and installed Tesseract language packs; empty or poor OCR results must remain visible as limitations.
- Exact SHA-256 image matching finds byte-identical files, not visually similar or recompressed variants.
- Text similarity, pHash image candidates and entity graphs are exploratory; their clusters need analyst validation and must not be presented as confirmed criminal networks. Context-labelled bank-account candidates can help test cross-source links, but extraction does not verify account ownership or account status.
- Geographic results are reported mentions/tags, not physical tracking.
- Authentication, access controls, independent evidence anchoring, retention governance and production security require further work before any operational deployment.

## Repository structure

```text
addons/        Extractors, scoring, OCR, evidence and reporting
core/          Data models, database and normalization
dashboard/     Streamlit application and analysis pages
discovery/     Public-channel discovery utilities
ingestion/     Adapters, worker, replay and PS02 dataset reader
data/          SQLite schema and local runtime data (not uploaded)
docs/          Project documentation, limitations and demo guidance
tests/         Unit and integration tests
```

## Responsible use

Only use data you are authorized to process and public sources within applicable terms and law. Do not attempt to access private communications, bypass access controls, contact handles or payment identifiers found in sample data, or deanonymize individuals. Treat every automated alert as an unverified lead requiring independent human assessment.
