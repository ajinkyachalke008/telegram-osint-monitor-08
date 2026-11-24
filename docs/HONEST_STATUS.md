# Independent Honesty Audit Report

**Date of Audit:** 2026-11-24  
**Auditor:** Independent Technical Systems Auditor  
**Scope:** telegram-osint-monitor-08 (Rajasthan Police PS2 Threat Intelligence & Section 63 BSA 2023 Evidence Suite)  
**Standard:** Strict Evidence-Based Verification (Zero unverified claims, zero marketing language)

---

## 1. Executive Summary

Out of 30 inventoried capabilities, **2 (6.7%) are LIVE-VERIFIED**, **2 (6.7%) are IMPORTED-VERIFIED**, **20 (66.7%) are SYNTHETIC-ONLY**, **4 (13.3%) are MOCK/STUB**, **2 (6.7%) are CODE-ONLY**, and **0 are BROKEN or MISSING**.

### Category Breakdown

| Status Category | Count | Percentage | Definition |
| :--- | :---: | :---: | :--- |
| **LIVE-VERIFIED** | 2 | 6.7% | Ran against real external data or a real service in this session; raw output captured. |
| **IMPORTED-VERIFIED** | 2 | 6.7% | Ran on real files/databases supplied from prior actual user sessions. |
| **SYNTHETIC-ONLY** | 20 | 66.7% | Functional logic verified, but operates strictly on synthetic or hand-crafted mock data. |
| **MOCK/STUB** | 4 | 13.3% | Returns placeholder/canned data, simulated delays, or graceful fallback reporting disabled. |
| **CODE-ONLY** | 2 | 6.7% | Server daemon processes and UI scaffolding verified via local port binding (HTTP 200 is not external data verification). |
| **BROKEN** | 0 | 0.0% | Code exists but contains logic/key errors that fail during execution (previous graph decorator defect fixed). |
| **MISSING** | 0 | 0.0% | Claimed in documentation but completely absent from the codebase. |
| **TOTAL** | **30** | **100.0%** | Comprehensive system inventory |

---

## 2. Master Capability Verification Table

| ID | Capability Name | Status Category | Real-Data Risk (Deterministic vs Statistical) | File Reference | Verification Command & Concrete Raw Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CAP-01** | Telegram Public Web Preview Scraper | **LIVE-VERIFIED** | **Deterministic function** (HTTP client + BeautifulSoup DOM parsing). Zero statistical risk; bounded by Telegram Web markup changes. | `ingestion/adapters.py`, `.venv/Scripts/tgq.exe` | **CMD:** `.venv\Scripts\tgq.exe preview --limit 5 telegram`<br>**OUTPUT:** `Retrieved 5 real live messages from @telegram: Msg #460 (2026-08-26T19:12:34+00:00) "For all the info from today's update..."`. Ran live against real Telegram servers. |
| **CAP-02** | Operational Live Ingestion Pipeline | **LIVE-VERIFIED** | **Hybrid** (Deterministic DB insertion & SHA-256 chaining; statistical ML classification). Risk of false positives on slang. | `scripts/run_operational_ingestion.py`, `core/db.py` | **CMD:** `python scripts/run_operational_ingestion.py`<br>**OUTPUT:** Ingested 30 live real posts from `@telegram`, `@durov`, and `@tginfo` into `data/operational.db`. Extracted 6 real identifiers, generated 30 unbroken SHA-256 evidence blocks, 0 false positive alerts. |
| **CAP-03** | TGSherlock SQLite Historical Bridge | **IMPORTED-VERIFIED** | **Deterministic function** (Direct SQLite query). Zero statistical risk. | `ingestion/adapters.py` | **CMD:** `TGSherlockAdapter().read_recent_posts(limit=3)`<br>**OUTPUT:** Read 10 real messages from channel `@study` captured by actual Telegram account in `~/.local/share/tgsherlock/accounts/[REDACTED_ACCOUNT_ID]/tgsherlock.db`. |
| **CAP-04** | Multi-Platform CSV/JSON Dump Ingest | **IMPORTED-VERIFIED** | **Deterministic function** (Schema aliasing and CSV/JSON dict parsing). Zero statistical risk. | `ingestion/adapters.py` | **CMD:** `FileImporterAdapter().import_file(Path('sample_data/demo_dataset.csv'))`<br>**OUTPUT:** `total_rows: 15, valid_count: 15, invalid_count: 0`. Successfully mapped external columns, extracted entities, and scored records. |
| **CAP-05** | Text Normalizer (Unicode/Leetspeak) | **SYNTHETIC-ONLY** | **Deterministic function** (Regex character substitution and Unicode NFKC normalization). Zero statistical risk. | `core/normalizer.py` | **CMD:** `normalize_text('FR3SH 1C1C1 B@NK KH@T@ CALL +91 98765 43210')`<br>**OUTPUT:** Folded homoglyphs and whitespace in synthetic test string. |
| **CAP-06** | Identifier & Entity Extractors | **SYNTHETIC-ONLY** | **Deterministic function** (Strict regexes and checksum validators). Risk of false negatives if evasion patterns bypass regex. | `addons/extractors.py` | **CMD:** `extract_all_entities('Send 5000 USDT to 0x71C... or UPI mule.syndicate@ybl')`<br>**OUTPUT:** `{'upis': ['mule.syndicate@ybl'], 'crypto_wallets': [('0x71C...', 'ETH/EVM', True)]}`. |
| **CAP-07** | Financial Ad & Mule Intent Scorer | **SYNTHETIC-ONLY** | **Rule-based heuristic** (Dictionary keyword matching). Risk of context blindness and polysemy errors. | `addons/financial_detector.py` | **CMD:** `FinancialAdDetector().detect('Rent your khata 10,000 commission')`<br>**OUTPUT:** `is_ad=True, intent='recruit', risk='High', spans=6`. |
| **CAP-08** | Hybrid Cybercrime ML Classifier | **SYNTHETIC-ONLY** | **Statistical model** (TF-IDF + Logistic Regression). Risk of false positives and false negatives on novel dialects and unseen slang. | `models/classifier.py` | **CMD:** `HybridClassifier().classify('Pure mdma and charas in Mumbai')`<br>**OUTPUT:** `category='drugs', risk='High', confidence=0.853`. Model trained on synthetic dataset `data/train_synthetic.jsonl`. |
| **CAP-09** | Sentence Transformer Embedding Head | **SYNTHETIC-ONLY** | **Statistical model** (paraphrase-multilingual-MiniLM-L12-v2). High compute latency; statistical semantic transfer risk. | `models/classifier.py` | **CMD:** `is_sentence_transformers_available()`<br>**OUTPUT:** `True`. Inference functional, but trained exclusively on synthetic data. |
| **CAP-10** | Slang & Keyword Suggester | **SYNTHETIC-ONLY** | **Statistical heuristic** (Frequency counts and stopword filtering). Risk of extracting irrelevant high-frequency tokens. | `addons/slang_suggester.py` | **CMD:** `SlangSuggester().extract_candidates(posts, min_count=2)`<br>**OUTPUT:** Extracted candidate slang tokens from synthetic posts; filters existing lexicon terms. |
| **CAP-11** | RFC-8785 Canonical JSON Serialization | **SYNTHETIC-ONLY** | **Deterministic function** (Strict key sorting and float formatting). Zero statistical risk. | `addons/evidence.py` | **CMD:** `canonical_json({'b':2, 'a':1})`<br>**OUTPUT:** `{"a":1,"b":2}`, SHA-256: `61c6a506...`. |
| **CAP-12** | Tamper-Evident SHA-256 Hash Chain | **SYNTHETIC-ONLY** | **Deterministic function** (SHA-256 sequential hashing). Zero statistical risk; verification detects post-hoc DB alterations. | `scripts/verify_evidence.py` | **CMD:** `python scripts/verify_evidence.py`<br>**OUTPUT:** Verified all evidence blocks with unbroken hash chain. |
| **CAP-13** | End-to-End Flow Proof Verification | **SYNTHETIC-ONLY** | **Deterministic workflow** (Pipeline orchestration). Zero statistical risk. | `scripts/verify_flow_proof.py` | **CMD:** `python scripts/verify_flow_proof.py`<br>**OUTPUT:** `100% SUCCESS`: Traced post -> category -> entities -> block #1 -> channels. |
| **CAP-14** | Section 63 BSA 2023 PDF Exporter | **SYNTHETIC-ONLY** | **Deterministic function** (ReportLab PDF compilation). Zero statistical risk; document layout strictly programmatic. | `addons/pdf_exporter.py` | **CMD:** `generate_evidence_pdf(alert, ev, idents)`<br>**OUTPUT:** Compiled 4,570-byte valid PDF document with SHA-256 hash seal and statutory certificate disclaimer. |
| **CAP-15** | MinHash Jaccard Ad Campaign Cluster | **SYNTHETIC-ONLY** | **Statistical approximation** (MinHash LSH). Risk of false cluster mergers or missed duplicates on short texts. | `dashboard/similarity.py` | **CMD:** `find_text_ad_clusters(posts, threshold=0.5)`<br>**OUTPUT:** Discovered 3 ad template clusters across synthetic posts in `demo.db`. |
| **CAP-16** | Perceptual Image Hash (pHash) Cluster | **SYNTHETIC-ONLY** | **Deterministic image transform** (DCT frequency decomposition). Risk of collisions on simple geometric graphics. | `dashboard/similarity.py` | **CMD:** `compute_image_phash(img)`<br>**OUTPUT:** `IMAGEHASH_AVAILABLE=True`. Tested perceptual hashing on sample image flyer. |
| **CAP-17** | Syndicate Entity Knowledge Graph | **SYNTHETIC-ONLY** | **Deterministic graph construction** (NetworkX bipartite projection). Fixed node/edge matching logic. | `dashboard/graph.py` | **CMD:** `build_entity_graph(posts)`<br>**OUTPUT:** Constructed NetworkX graph linking channels, posts, and identifiers with cross-channel highlighting. |
| **CAP-18** | Syndicate Community Detection | **SYNTHETIC-ONLY** | **Deterministic graph algorithm** (Connected components). Zero statistical risk; topological partitioning only. | `dashboard/graph.py` | **CMD:** `get_connected_syndicates(G)`<br>**OUTPUT:** Grouped graph into connected syndicate components from post links. |
| **CAP-19** | Geographic Hotspot STD Mapping | **SYNTHETIC-ONLY** | **Deterministic lookup** (Indian STD/telecom prefix dictionary). Risk that mobile number location does not match crime site. | `dashboard/pages/5_🗺️_Geographic_Map.py` | **CMD:** Inferred cities (Jaipur, Mewat, Mumbai, Delhi) from synthetic phone prefixes. |
| **CAP-20** | Channel Discovery Snowball Engine | **SYNTHETIC-ONLY** | **Rule-based heuristic** (Forward origin parsing + keyword density). Risk of trailing into irrelevant channels. | `discovery/finder.py` | **CMD:** `score_channel_posts(sample_posts, scorer)`<br>**OUTPUT:** Calculated threat scores and extracted forward origins on mock post fixtures. |
| **CAP-21** | Dynamic Model Metrics Benchmark Engine | **SYNTHETIC-ONLY** | **Statistical evaluation** (Held-out synthetic benchmarking). Accuracy on synthetic data does not guarantee real-world generalization. | `eval/evaluate_model.py`, `dashboard/pages/7_📈_Model_Metrics.py` | **CMD:** `python eval/evaluate_model.py`<br>**OUTPUT:** Generated `data/model_evaluation_results.json` (`timestamp_utc: 2026-11-24T13:27:32Z`, TF-IDF accuracy: **95.56%**, Embedding accuracy: **94.89%**, 0.0% FPR). Read dynamically by Page 7. |
| **CAP-22** | Audit Trail Compliance Logging | **SYNTHETIC-ONLY** | **Deterministic function** (SQLite insert). Zero statistical risk. | `core/db.py` | **CMD:** `Database.log_audit('demo_action')`<br>**OUTPUT:** Writes action, timestamp, and details JSON to local SQLite table `audit_log`. |
| **CAP-23** | Synthetic Replay Stream Worker | **SYNTHETIC-ONLY** | **Deterministic simulation** (Sleep-delayed JSON generator). Zero real external data. | `ingestion/replay.py` | **CMD:** `run_replay()`<br>**OUTPUT:** Simulates live Telegram traffic by looping synthetic posts with delays. Strictly blocked on `operational.db`. |
| **CAP-24** | Dynamic Provenance Watermark & DB Segregator | **SYNTHETIC-ONLY** | **Deterministic function** (Row provenance count check). Zero statistical risk. | `dashboard/provenance_banner.py`, `core/db.py` | **CMD:** `get_default_db_path()`<br>**OUTPUT:** Routes to `operational.db` by default (no watermark) and `demo.db` when `DEMO_MODE=1` (displays prominent red watermark: `⚠️ SIMULATED DATA — NOT REAL CRIMINAL EVIDENCE`). |
| **CAP-25** | Multilingual OCR Image Extractor | **MOCK/STUB** | **Statistical computer vision** (Tesseract LSTM neural OCR). Currently disabled on this host. | `addons/ocr_extractor.py` | **CMD:** `detect_tesseract_binary()`<br>**OUTPUT:** `None`. Tesseract executable is not installed on this host. OCR reports disabled/fallback; does not extract real image text. |
| **CAP-26** | Scripted Demo Post Injector | **MOCK/STUB** | **Deterministic mock injection** (Hardcoded test string). Zero real external data. | `ingestion/demo_injector.py` | **CMD:** `inject_scripted_demo_post(db)`<br>**OUTPUT:** Injects hardcoded post containing `mule.syndicate@ybl`. Gated behind `DEMO_MODE=1`; raises `PermissionError` on `operational.db`. |
| **CAP-27** | Reset Demo State Action | **MOCK/STUB** | **Deterministic mock reset** (Table wipe and re-seed). Zero real external data. | `dashboard/demo_sidebar.py`, `core/db.py` | **CMD:** `db.wipe_all_data()`<br>**OUTPUT:** Wipes and reseeds synthetic records. Gated behind `DEMO_MODE=1`; raises `PermissionError` on `operational.db`. |
| **CAP-28** | Human-Written Benchmark Split | **MOCK/STUB** | **Statistical benchmark placeholder**. Unpopulated. | `data/test_human_written.jsonl` | **CMD:** File inspection<br>**OUTPUT:** Contains 40 unfilled placeholder rows (`PLACEHOLDER_TEXT_01`...). Evaluator skips them. |
| **CAP-29** | TGSherlock Web Panel UI Host | **CODE-ONLY** | **Runtime Infrastructure** (FastAPI / Uvicorn server). Port binding check is not external data verification. | `tgsherlock/src/tgsherlock/server.py` | **CMD:** `urllib.request.urlopen('http://127.0.0.1:8765/api/status')`<br>**OUTPUT:** `HTTP 200: {"version":"2026.11.3.144","authorized":true}`. Server daemon listening on port 8765. |
| **CAP-30** | Streamlit Dashboard UI Host | **CODE-ONLY** | **Runtime Infrastructure** (Streamlit web server). Port binding check is not external data verification. | `dashboard/app.py` | **CMD:** `urllib.request.urlopen('http://localhost:8501/?embed=true')`<br>**OUTPUT:** `HTTP 200: server:uvicorn, cache-control:no-cache`. Dashboard server listening on port 8501. |

---

## 3. Planned / Not Built Features

The following capabilities were conceived or mentioned in early project proposals but are **NOT BUILT** or intentionally out of scope:

1. **Automated Telegram Account Farm Registration**: Not built. Account creation requires manual phone/QR verification.
2. **Private Invite-Only Channel Infiltration**: Not built. System enforces strict public broadcast domain boundaries.
3. **Automated FIR / Police Station Case Management System (CCTNS) API Sync**: Not built. Evidence is exported as standalone PDFs and JSON files; no direct integration with state CCTNS police servers exists.
4. **Hardware Security Module (HSM) Cryptographic Chain Anchoring**: Not built. The evidence ledger resides in a local SQLite file without hardware-backed private key signing.
5. **Speech-to-Text / Audio Note Transcriber**: Not built. Audio and voice messages posted on Telegram are not transcribed.
6. **Live Multi-Channel MTProto Parallel Scraper**: Not built for MTProto. TGSherlock monitors accounts synchronously; multi-channel background polling operates via public web previews (`tgq preview`).

---

## 4. List of Mock, Simulation, and Synthetic Components

The following components return canned data, simulate activity, or rely on synthetic records:

1. **Synthetic Replay Worker (`ingestion/replay.py`)**: Simulates live Telegram traffic by feeding synthetic messages on an adjustable timer. Strictly barred from running on `operational.db`.
2. **Scripted Demo Injector (`ingestion/demo_injector.py`)**: Injects a fixed post containing `mule.syndicate@ybl` to demonstrate detection. Gated behind `DEMO_MODE=1`; raises `PermissionError` on `operational.db`.
3. **Reset Demo State (`dashboard/demo_sidebar.py`)**: A demo reset feature that purges the database and re-seeds synthetic records. Gated behind `DEMO_MODE=1`; raises `PermissionError` on `operational.db`.
4. **Synthetic Training & Evaluation Datasets**:
   - `data/train_synthetic.jsonl` (3,010 generated cybercrime ad templates).
   - `data/test_heldout_novel_templates.jsonl` (450 generated novel held-out test records).
   - `data/test_human_written.jsonl` (40 unfilled placeholder entries).
5. **Synthetic Database Content (`data/demo.db`)**: 27 baseline synthetic posts with `ingestion_source = 'VERIFIED-SYNTHETIC'`.
6. **OCR Fallback (`addons/ocr_extractor.py`)**: Tesseract OCR binary is missing from the host environment, causing OCR to report disabled mode.
7. **Discovery Watchlist (`discovery/watchlist.csv`)**: Pre-populated with synthetic channel handles for evaluation walkthroughs.

---

## 5. What a Police Officer Can Rely On Today vs What Must Not Be Relied On

### What an Officer CAN Rely On:
1. **Deterministic Entity & Identifier Extraction**: Phone numbers, UPI handles, IFSC codes, and cryptocurrency wallet addresses (ETH, BTC, TRON) are extracted via deterministic regular expressions and cryptographic checksums (e.g. Luhn, Base58Check, EIP-55).
2. **Local MTProto Telegram Account Ingestion**: If an investigator logs into Telegram via TGSherlock on port 8765, real messages from joined groups and public channels are genuinely collected and stored in local SQLite without external cloud transmission.
3. **Real-Data Public Web Preview Ingestion (`tgq preview`)**: Can collect live, unauthenticated broadcast posts from public channels (e.g. `@telegram`, `@durov`, `@tginfo`) directly into `data/operational.db`.
4. **Evidence Hash Chain Linkage**: The evidence ledger computes RFC-8785 canonical JSON and SHA-256 digests chained sequentially (`prev_hash`).
5. **Section 63 BSA Evidence Package Export**: The system formats captured records into a forensic summary package with SHA-256 hash anchors.

### What an Officer MUST NOT Rely On:
1. **The 95.56% Accuracy Score in Real Investigations**: This accuracy was measured exclusively on synthetic text generated by python scripts (`data/test_heldout_novel_templates.jsonl`). Real criminals employ evolving regional dialects, voice notes, code words, and image flyers that will exhibit different error rates and false negatives.
2. **Automated Live Channel Scraping as a Full Coverage Solution**: `tgq preview` only reads web previews (`t.me/s/`) for public broadcast channels. It cannot view private channels, invite-only groups, or accounts with active anti-scraping blocks.
3. **OCR Image Evidence**: The OCR engine is currently disabled because Tesseract is not installed on this machine. Images will not be parsed for text.
4. **Section 63 BSA PDF as an Automatic Legal Admissibility Guarantee**: Evidence package to support a Section 63 BSA certificate (signed by the person in charge and an expert). Not legal advice.
5. **Immediate Tampering Detection on Local Storage**: Chain verification detects changes only when run, and cannot detect a fully rebuilt chain unless the chain-head hash is stored elsewhere.

---

## 6. Machine Learning Models & Training Ground Truth

| Model Property | Reality / Actual Status |
| :--- | :--- |
| **Training Data** | 3,010 synthetic records generated by `scripts/generate_synthetic_training.py`. **Zero real Telegram messages were used to train or fine-tune models** (in compliance with Telegram Terms of Service). |
| **Evaluation Data** | 450 synthetic records generated by `scripts/generate_novel_heldout_eval.py`. |
| **Accuracy on Novel Held-Out Set** | **95.56%** for Model A (TF-IDF + Logistic Regression, 1.52 ms latency); **94.89%** for Model B (Multilingual MiniLM-L12 Embeddings, 56.42 ms latency). Evaluated dynamically at `2026-11-24T13:27:32Z` in `data/model_evaluation_results.json`. |
| **Real-World Benchmark** | `data/test_human_written.jsonl` currently has **0 real labeled records** (contains 40 placeholders). Real-world accuracy, precision, and recall are **UNKNOWN**. |
| **False Positive Rate** | Measured at 0.0% on 100 crafted synthetic hard negatives (bank security notices, pharmacy tips). Real-world false positive rate on colloquial Hindi/Hinglish chat is **UNKNOWN**. |

---

## 7. Security and Privacy Basics

1. **Access Control**: **UNAUTHENTICATED**. Neither the TGSherlock web console (port 8765) nor the Streamlit dashboard (port 8501) requires a password or session token. Anyone with network or localhost access can access all screens, read messages, and trigger actions.
2. **Secrets Protection**: All real account identifiers and phone numbers have been sanitized with `[REDACTED_ACCOUNT_ID]` and `[REDACTED_PHONE]`. No API keys or session secrets are hardcoded in git.
3. **Database Segregation**: Operational investigations default to `data/operational.db` (clean, zero seeds, reset strictly prohibited). Demo features operate only on `data/demo.db` when `DEMO_MODE=1` with persistent simulated data watermarks.
4. **Data Retention**: **INDEFINITE**. There is no automated TTL or data purge mechanism. Stored messages and extracted personal identifiers remain in SQLite permanently until manual deletion.
5. **Audit Trail**: Operational actions are written to local SQLite `audit_log`. Because SQLite is a local file without append-only hardware protection, an administrator with local root access can modify or delete audit rows.

---

## 8. Manual Steps to Obtain Real-Data Proof

To elevate additional components from `SYNTHETIC-ONLY` to `LIVE-VERIFIED` for police authorities, the operator must execute the following steps:

1. **Telegram Live Authentication**:
   - Open `http://127.0.0.1:8765/#/settings`.
   - Connect a valid Telegram test account using phone number or QR code.
2. **Real Channel Target Monitoring**:
   - Navigate to `Live Monitor` and add a real public channel (e.g. `@telegram` or a public regional trade group).
   - Let the live monitor capture at least 10 real messages.
3. **Populate Human-Written Benchmark**:
   - Edit `data/test_human_written.jsonl` and replace the 40 placeholders with real human-written cybercrime ad samples and benign messages.
   - Run `python eval/evaluate_model.py` to obtain an empirically grounded accuracy score on human samples.
4. **Install Tesseract OCR**:
   - Install Tesseract-OCR binary on Windows (`C:\Program Files\Tesseract-OCR\tesseract.exe`) to activate the image extractor.
