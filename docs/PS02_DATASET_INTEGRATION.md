# PS02 dataset audit and integration

## Scope and provenance

The PS02 package README describes 1,850 primary advertisement/community posts: 1,500 Telegram Desktop messages across 13 exports and 350 social-media posts. The supplied records identify themselves as synthetic hackathon material. Treat each alert as an unverified lead.

The audit and importer cover only:
- `01_telegram_exports/*/result.json` and referenced Telegram photos;
- `02_social_media/posts.json` (preferred) or `posts.csv`, plus referenced images;
- `03_images/images_index.csv` and its master posters for file/hash audit;
- `04_lexicon/starter_slang_lexicon.csv` as analyst reference material.

The `posts.json` social export is used in preference to the equivalent CSV. Do not ingest both. The `05_reference/real_reported_channels.csv` file is background-only; those public references are not monitored or contacted. The additional `Suspect_Repository_masked` complaint/reference CSVs are not part of the README's 1,850 primary posts and are deliberately excluded from post ingestion, scoring, alerts and entity graphing. The judge-only `99_answer_key` was not present in the uploaded archive.

## Archive audit snapshot

The inspected archive contained:

| Measure | Observed |
|---|---:|
| Telegram export folders | 13 |
| Telegram message records | 1,500 |
| Telegram photo references | 199 |
| Telegram forwarded messages | 42 |
| Telegram edited messages | 40 |
| Telegram messages with empty text | 63 |
| Social posts | 350 |
| Social platforms represented | 5 |
| Social image references | 92 |
| Indexed master posters | 18 |
| Poster SHA-256 index mismatches | 0 |
| JPEG copies in archive | 309 |
| Distinct exact image byte hashes | 18 |
| Starter lexicon rows | 37 |
| Real-channel reference rows | 8 |
| Extra masked complaint/reference CSVs | 6 files / 1,613 rows |

All 199 Telegram and 92 social image references resolved during the archive audit. The 309 JPEG files contained 18 unique file hashes, so many entries are exact duplicate copies rather than independent images. The six extra masked CSV files had 1,363 distinct acknowledgement numbers and 250 repeated acknowledgement rows; their complaint narratives are not reproduced in this report.

Telegram exports contain 13 non-message service records in addition to the 1,500 message records. Telegram text may be a string or an array of text/entity segments. The adapter reconstructs the text in order and preserves the original entity segments in source metadata. Where `date_unixtime` is available it is the timestamp authority; social `posted_at_ist` values are interpreted in `Asia/Kolkata` before conversion to UTC.

## Import design

The dedicated adapter is `ingestion/ps02_dataset.py`. It:
1. Validates the archive and rejects path traversal, symlink members, invalid CRC and archives over the configured uncompressed-size limit.
2. Locates the `PS02_demo_data` root and fingerprints the primary post, media and starter-lexicon files.
3. Parses Telegram exports and social JSON without forcing either source into a lossy generic CSV mapping.
4. Resolves attachment paths within the correct export/platform directory and calculates SHA-256 hashes.
5. Runs optional OCR through the existing `OCRExtractor`; OCR results are cached by exact image hash within a reader run.
6. Preserves sender, source, forwarding, edits, text entities, hashtags, location tags, engagement counts, media paths, OCR status and the dataset fingerprint in `source_metadata_json`.
7. Sends the original text and source metadata through the normal ingestion worker with provenance `HACKATHON_SAMPLE`.

The worker uses OCR text and social hashtags as supplemental analysis input while preserving the original source text separately. A context-labelled bank-account extractor recognises values immediately following labels such as `a/c` or `account number`, enabling the README-described PS01/PS02 candidate cross-link; it does not validate account ownership, account status or beneficial control. Telegram Desktop `from_id` values that match the exported `user<number>` form are also linked as `TelegramAccount` source identifiers, allowing the supplied group sender references to be compared across exports; these IDs identify an export-level platform account reference, not a real-world person. Media SHA-256 is retained as a media signal and in the evidence payload; it is not inserted as a person/account identifier in the seller graph. Evidence blocks created for new records optionally bind the media SHA-256 and a hash of source metadata. Existing evidence payloads remain verifiable because the new fields are optional.

The posts table gains `source_metadata_json`. Existing SQLite databases are migrated on initialization using `PRAGMA table_info` plus `ALTER TABLE` when the column is missing. Re-import of the same archive is idempotent through the existing `(platform, channel_id, message_id)` uniqueness constraint.

## Dashboard and analysis changes

- **PS02 Dataset Studio** (page 10) accepts the ZIP, validates and inventories it, exposes the starter lexicon for analyst reference, separates masked/reference records, and requires a deliberate import action.
- Entity graph and coordinated-campaign pages now load up to 5,000 posts, covering the 1,850 primary sample instead of truncating at the prior 200/250 row caps.
- Campaign analysis adds exact media SHA-256 reuse groups and an adjustable pHash visual-candidate review. The pHash output is only a visual shortlist requiring manual comparison; neither exact nor perceptual matches establish common ownership.
- Geographic mapping includes social `location_tag` source metadata and additional Rajasthan cities. The dashboard labels results as reported mentions/tags, not physical tracking.
- The entity graph includes a separate forwarded-from evidence view. Forward labels are not added as identity edges or treated as authenticated source chains.
- Alert detail displays selected source metadata, forwarding/edit context, OCR text and stored media digest.

## Normalization and starter lexicon

The text normalizer now handles common leetspeak variants such as `g@nja`, `ch@ras` and `p!st0l`, dotted acronyms such as `A.T.M`, and compound emoji codes in the starter lexicon. It attempts to protect usernames, email addresses, UPI-style handles and pure numeric identifiers from accidental modification.

Only more specific starter terms and semantic emoji tokens were added to the automatic lexicon. Generic items such as `maal`, `stuff`, `limit`, `kit`, `goli` and `desi` are context-dependent and should not be bulk-promoted as high-confidence indicators. The complete supplied lexicon remains available as reference data.

## Running the importer

From the repository root:

```bash
python -m ingestion.ps02_dataset /path/to/PS02_demo_data --no-ocr
python -m ingestion.ps02_dataset /path/to/PS02_demo_data --import-db
python -m streamlit run dashboard/app.py
```

Alternatively, upload the ZIP in the Streamlit page **PS02 Dataset Studio** and choose the import action. OCR requires the system Tesseract executable and the relevant language packs. The UI reports the actual OCR engine/status and does not claim OCR success when the dependency is unavailable.

## Evaluation constraints and interpretation

The uploaded package did not include the judge-only answer key. The README's advertised category/difficulty counts and seeded campaign links are dataset-design notes, not an available row-level ground-truth label file. Do not report precision, recall, F1, false-positive rate or official benchmark performance from this archive unless the authorized answer key is supplied and mapped carefully.

The sample is useful for functional demonstration and regression tests, not independent operational validation. Shared phones, context-labelled bank-account candidates, UPI-style values, usernames, forwarded content, text templates and image hashes are correlation signals, not proof that accounts share an operator. The sample itself warns that synthetic identifiers must not be contacted.

## Known technical limits

- OCR operates on referenced media; quality varies and blank/garbled OCR text must remain a visible limitation.
- Exact SHA-256 groups only identify byte-identical image files. Re-encoded or visually similar variants require a separately validated perceptual comparison.
- The current worker uses rule-based scoring. The repository's separate ML classifier is not implicitly part of this import path.
- Social `location_tag` and message text mentions are source-provided clues, not GPS or IP location.
- The SQLite hash chain is locally stored and mutable by a sufficiently privileged local operator. It is not an independently anchored forensic storage system.
- This prototype is not an operational law-enforcement platform. Human review, security controls, retention policy, source legality and legal evidence certification remain necessary.
