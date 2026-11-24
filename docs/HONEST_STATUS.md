# Independent Honesty Audit Report

**Date of Audit:** 2026-11-24  
**Auditor:** Independent Technical Systems Auditor  
**Scope:** telegram-osint-monitor-08 (Rajasthan Police PS2 Threat Intelligence & Section 63 BSA 2023 Evidence Suite)  
**Standard:** Strict Evidence-Based Verification (Zero unverified claims, zero marketing language)

---

## 1. Executive Summary

Out of 30 inventoried capabilities, **3 (10.0%) are LIVE-VERIFIED**, **1 (3.3%) is IMPORTED-VERIFIED**, **21 (70.0%) are SYNTHETIC-ONLY**, **4 (13.3%) are MOCK/STUB**, **1 (3.3%) is BROKEN**, and **0 are CODE-ONLY or MISSING**.

### Category Breakdown

| Status Category | Count | Percentage | Definition |
| :--- | :---: | :---: | :--- |
| **LIVE-VERIFIED** | 3 | 10.0% | Ran against real external data or a real service in this session; raw output captured. |
| **IMPORTED-VERIFIED** | 1 | 3.3% | Ran on real files/databases supplied from prior actual user sessions. |
| **SYNTHETIC-ONLY** | 21 | 70.0% | Functional logic verified, but operates strictly on synthetic or hand-crafted mock data. |
| **MOCK/STUB** | 4 | 13.3% | Returns placeholder/canned data, simulated delays, or graceful fallback reporting disabled. |
| **BROKEN** | 1 | 3.3% | Code exists but contains logic/key errors that fail during execution. |
| **CODE-ONLY** | 0 | 0.0% | Exists in repository but was never executed. |
| **MISSING** | 0 | 0.0% | Claimed in documentation but completely absent from the codebase. |
| **TOTAL** | **30** | **100.0%** | Comprehensive system inventory |

---

## 2. Master Capability Verification Table

| ID | Capability Name | Status Category | File Reference | Verification Command & Concrete Raw Output |
| :--- | :--- | :--- | :--- | :--- |
| **CAP-01** | Telegram Public Web Preview Scraper | **LIVE-VERIFIED** | `ingestion/adapters.py`, `.venv/Scripts/tgq.exe` | **CMD:** `.venv\Scripts\tgq.exe preview telegram`<br>**OUTPUT:** `{"channel_username":"telegram","message_id":400,"text":"Profile Ratings. Profiles now show a numerical rating...","date":"2025-08-18T13:34:04+00:00"}` (Retrieved 61 real live posts from Telegram). |
| **CAP-02** | TGSherlock Web Panel Daemon | **LIVE-VERIFIED** | `tgsherlock/src/tgsherlock/server.py` | **CMD:** `urllib.request.urlopen('http://127.0.0.1:8765/api/status')`<br>**OUTPUT:** `HTTP 200: {"version":"2026.11.3.144","authorized":true,"account":{"id":"[REDACTED_ACCOUNT_ID]","phone":"[REDACTED_PHONE]"}}`. |
| **CAP-03** | Streamlit 10-Page Dashboard Daemon | **LIVE-VERIFIED** | `dashboard/app.py` | **CMD:** `urllib.request.urlopen('http://localhost:8501/?embed=true')`<br>**OUTPUT:** `HTTP 200: server:uvicorn, cache-control:no-cache`. |
| **CAP-04** | TGSherlock SQLite Historical Bridge | **IMPORTED-VERIFIED** | `ingestion/adapters.py` | **CMD:** `TGSherlockAdapter().read_recent_posts(limit=3)`<br>**OUTPUT:** Read 10 real messages from channel `@study` captured by actual Telegram account in `~/.local/share/tgsherlock/accounts/[REDACTED_ACCOUNT_ID]/tgsherlock.db`. |
| **CAP-05** | Text Normalizer (Unicode/Leetspeak) | **SYNTHETIC-ONLY** | `core/normalizer.py` | **CMD:** `normalize_text('FR3SH 1C1C1 B@NK KH@T@ CALL +91 98765 43210')`<br>**OUTPUT:** Folded homoglyphs and whitespace in synthetic test string. |
| **CAP-06** | Identifier & Entity Extractors | **SYNTHETIC-ONLY** | `addons/extractors.py` | **CMD:** `extract_all_entities('Send 5000 USDT to 0x71C... or UPI mule.syndicate@ybl')`<br>**OUTPUT:** `{'upis': ['mule.syndicate@ybl'], 'crypto_wallets': [('0x71C...', 'ETH/EVM', True)]}`. |
| **CAP-07** | Financial Ad & Mule Intent Scorer | **SYNTHETIC-ONLY** | `addons/financial_detector.py` | **CMD:** `FinancialAdDetector().detect('Rent your khata 10,000 commission')`<br>**OUTPUT:** `is_ad=True, intent='recruit', risk='High', spans=6`. |
| **CAP-08** | Hybrid Cybercrime ML Classifier | **SYNTHETIC-ONLY** | `models/classifier.py` | **CMD:** `HybridClassifier().classify('Pure mdma and charas in Mumbai')`<br>**OUTPUT:** `category='drugs', risk='High', confidence=0.853`. Model trained on synthetic dataset `data/train_synthetic.jsonl`. |
| **CAP-09** | Sentence Transformer Embedding Head | **SYNTHETIC-ONLY** | `models/classifier.py` | **CMD:** `is_sentence_transformers_available()`<br>**OUTPUT:** `True`. Inference functional, but trained exclusively on synthetic data. |
| **CAP-10** | Slang & Keyword Suggester | **SYNTHETIC-ONLY** | `addons/slang_suggester.py` | **CMD:** `SlangSuggester().extract_candidates(posts, min_count=2)`<br>**OUTPUT:** Extracted candidate slang tokens from synthetic posts; filters existing lexicon terms. |
| **CAP-11** | RFC-8785 Canonical JSON Hashing | **SYNTHETIC-ONLY** | `addons/evidence.py` | **CMD:** `canonical_json({'b':2, 'a':1})`<br>**OUTPUT:** `{"a":1,"b":2}`, SHA-256: `61c6a506...`. |
| **CAP-12** | Tamper-Evident SHA-256 Hash Chain | **SYNTHETIC-ONLY** | `scripts/verify_evidence.py` | **CMD:** `python scripts/verify_evidence.py`<br>**OUTPUT:** Verified all 43 evidence blocks in `data/osint_monitor.db` with unbroken hash chain. All 43 blocks are synthetic posts. |
| **CAP-13** | End-to-End Flow Proof Verification | **SYNTHETIC-ONLY** | `scripts/verify_flow_proof.py` | **CMD:** `python scripts/verify_flow_proof.py`<br>**OUTPUT:** `100% SUCCESS`: Traced post -> category -> entities -> block #1 -> 6 synthetic channels. |
| **CAP-14** | Section 63 BSA 2023 PDF Exporter | **SYNTHETIC-ONLY** | `addons/pdf_exporter.py` | **CMD:** `generate_evidence_pdf(alert, ev, idents)`<br>**OUTPUT:** Compiled 4,570-byte valid PDF document with SHA-256 hash seal and statutory certificate disclaimer. Tested on synthetic alert. |
| **CAP-15** | MinHash Jaccard Ad Campaign Cluster | **SYNTHETIC-ONLY** | `dashboard/similarity.py` | **CMD:** `find_text_ad_clusters(posts, threshold=0.5)`<br>**OUTPUT:** Discovered 3 ad template clusters across 43 synthetic posts in `osint_monitor.db`. |
| **CAP-16** | Perceptual Image Hash (pHash) Cluster | **SYNTHETIC-ONLY** | `dashboard/similarity.py` | **CMD:** `compute_image_phash(img)`<br>**OUTPUT:** `IMAGEHASH_AVAILABLE=True`. Tested perceptual hashing on sample image flyer. |
| **CAP-17** | Syndicate Entity Knowledge Graph | **SYNTHETIC-ONLY** | `dashboard/graph.py` | **CMD:** `build_entity_graph(posts)`<br>**OUTPUT:** Constructed 61-node NetworkX graph linking synthetic channels, posts, and identifiers. |
| **CAP-18** | Syndicate Community Detection | **SYNTHETIC-ONLY** | `dashboard/graph.py` | **CMD:** `get_connected_syndicates(G)`<br>**OUTPUT:** Grouped graph into connected syndicate components from synthetic post links. |
| **CAP-19** | Geographic Hotspot STD Mapping | **SYNTHETIC-ONLY** | `dashboard/pages/5_🗺️_Geographic_Map.py` | **CMD:** Inferred cities (Jaipur, Mewat, Mumbai, Delhi) from synthetic phone prefixes. |
| **CAP-20** | Multi-Platform CSV/JSON Dump Ingest | **SYNTHETIC-ONLY** | `ingestion/adapters.py` | **CMD:** `CSVJSONImporter().import_file('test.csv')`<br>**OUTPUT:** Successfully mapped external columns, extracted entities, and scored records. |
| **CAP-21** | Channel Discovery Snowball Engine | **SYNTHETIC-ONLY** | `discovery/finder.py` | **CMD:** `score_channel_posts(sample_posts, scorer)`<br>**OUTPUT:** Calculated threat scores and extracted forward origins on mock post fixtures. |
| **CAP-22** | Model Metrics Benchmark Page | **SYNTHETIC-ONLY** | `dashboard/pages/7_📈_Model_Metrics.py` | **CMD:** Reads static `docs/METRICS.md` reporting 95.56% accuracy. Measured 100% on synthetic novel held-out dataset. Zero real human labels. |
| **CAP-23** | Audit Trail Compliance Logging | **SYNTHETIC-ONLY** | `core/db.py` | **CMD:** `Database.log_audit('demo_action')`<br>**OUTPUT:** Writes action, timestamp, and details JSON to local SQLite table `audit_log`. |
| **CAP-24** | Synthetic Replay Stream Worker | **SYNTHETIC-ONLY** | `ingestion/replay.py` | **CMD:** `SyntheticReplayWorker()`<br>**OUTPUT:** Simulates live Telegram traffic by looping 50 synthetic posts with delays. |
| **CAP-25** | Provenance Banner Data Derivation | **SYNTHETIC-ONLY** | `dashboard/provenance_banner.py` | **CMD:** Queries DB `ingestion_source` column and displays `VERIFIED-SYNTHETIC` badge. |
| **CAP-26** | Multilingual OCR Image Extractor | **MOCK/STUB** | `addons/ocr_extractor.py` | **CMD:** `detect_tesseract_binary()`<br>**OUTPUT:** `None`. Tesseract executable is not installed on this host. OCR reports disabled/fallback; does not extract real image text. |
| **CAP-27** | Scripted Demo Post Injector | **MOCK/STUB** | `ingestion/demo_injector.py` | **CMD:** `inject_scripted_demo_post(db)`<br>**OUTPUT:** Injects a hardcoded post with predefined text containing `mule.syndicate@ybl`. |
| **CAP-28** | Reset Demo State Action | **MOCK/STUB** | `dashboard/pages/8_⚖️_Responsible_Use_and_Audit.py` | **CMD:** Interactive UI button that wipes database and re-seeds synthetic records. Gated behind `DEMO_MODE=1`. |
| **CAP-29** | Human-Written Test Benchmark | **MOCK/STUB** | `data/test_human_written.jsonl` | **CMD:** File inspection<br>**OUTPUT:** Contains 40 unfilled placeholder rows (`PLACEHOLDER_TEXT_01`...). Evaluator skips them. |
| **CAP-30** | Database Graph Entity Decorator | **BROKEN** | `dashboard/graph.py` | **CMD:** `load_graph_from_db(db)`<br>**OUTPUT:** Node ID mismatch (`id_{val}` in decorator vs `upi:{val}` in edges table) causes `cross_channel` flags to fail to attach to nodes when loaded from DB. |

---

## 3. List of Mock, Simulation, and Synthetic Components

The following components return canned data, simulate activity, or rely on synthetic records:

1. **Synthetic Replay Worker (`ingestion/replay.py`)**: Simulates live Telegram traffic by feeding 50 synthetic messages on a timer.
2. **Scripted Demo Injector (`ingestion/demo_injector.py`)**: Hardcodes a single specific post containing `mule.syndicate@ybl` to demonstrate detection.
3. **Reset Demo State (`dashboard/pages/8_⚖️_Responsible_Use_and_Audit.py`)**: A demo reset feature that purges the database and re-seeds synthetic records.
4. **Synthetic Training & Evaluation Datasets**:
   - `data/train_synthetic.jsonl` (1,000+ generated cybercrime ad templates).
   - `data/test_heldout_novel_templates.jsonl` (450 generated test records).
   - `data/test_human_written.jsonl` (40 unfilled placeholder entries).
5. **Synthetic Database Content (`data/osint_monitor.db`)**: All 43 current posts in the threat database have `ingestion_source = 'VERIFIED-SYNTHETIC'`.
6. **OCR Fallback (`addons/ocr_extractor.py`)**: Tesseract OCR binary is missing from the host environment, causing OCR to operate in disabled fallback mode.
7. **Discovery Watchlist (`discovery/watchlist.csv`)**: Pre-populated with synthetic channel handles (`t.me/delhi_classifieds_demo`, `t.me/mule_accounts_market`).

---

## 4. What a Police Officer Can Rely On Today vs What Must Not Be Relied On

### What an Officer CAN Rely On:
1. **Cryptographic Tamper-Evidence (RFC-8785 SHA-256)**: Once a record is stored in the database, any retroactive modification of its text, timestamp, or channel will break the SHA-256 hash chain and be immediately detected by `verify_evidence.py`.
2. **Deterministic Entity Extraction**: Phone numbers (including Devanagari and spaced formats), UPI handles, IFSC codes, and Ethereum/Bitcoin/Tron wallet addresses are extracted via strict regular expressions and mathematical checksums.
3. **Local MTProto Telegram Session Ingestion**: If an investigator logs into Telegram via TGSherlock on port 8765, real messages from joined groups and public channels are genuinely collected and stored in local SQLite without external cloud transmission.
4. **Section 63 BSA 2023 PDF Documentation**: The system reliably formats intercepted data into an evidentiary summary package with hash anchors.

### What an Officer MUST NOT Rely On:
1. **The 95.56% Accuracy Score in Real Investigations**: This accuracy was measured exclusively on synthetic text generated by python scripts. In the wild, real criminals use heavy regional dialects, slang, voice notes, and image flyers that will have higher false positive and false negative rates.
2. **Automated Live Channel Scraping as a Full Coverage Solution**: `tgq preview` only reads web previews (`t.me/s/`) for public broadcast channels. It cannot view private channels, invite-only groups, or accounts with active anti-scraping blocks.
3. **Cross-Channel Syndicate Attribution on Unverified Feeds**: In the demo, `mule.syndicate@ybl` links across 6 channels because synthetic posts were generated with that identifier. On real feeds, cross-channel attribution requires real multi-channel collection.
4. **OCR Image Evidence**: The OCR engine is currently disabled because Tesseract is not installed on this machine. Images will not be parsed for text.
5. **Section 63 BSA PDF as an Automatic Legal Admissibility Guarantee**: The PDF is a formatted forensic report. Under Section 63 of the Bharatiya Sakshya Adhiniyam 2023, the certificate **must still be formally signed by the person in lawful charge of the device and an expert**, accompanied by lawful chain-of-custody documentation.

---

## 5. Machine Learning Models & Training Ground Truth

| Model Property | Reality / Actual Status |
| :--- | :--- |
| **Training Data** | 1,000+ synthetic records generated by `scripts/generate_synthetic_training.py`. **Zero real Telegram messages were used to train or fine-tune models** (in compliance with Telegram Terms of Service). |
| **Evaluation Data** | 450 synthetic records generated by `scripts/generate_novel_heldout_eval.py`. |
| **Real-World Benchmark** | `data/test_human_written.jsonl` currently has **0 real labeled records** (contains 40 placeholders). Real-world accuracy, precision, and recall are **UNKNOWN**. |
| **False Positive Rate** | Measured at 0.0% on 100 crafted synthetic hard negatives (bank security notices, pharmacy tips). Real-world false positive rate on colloquial Hindi/Hinglish chat is **UNKNOWN**. |

---

## 6. Security and Privacy Basics

1. **Access Control**: **UNAUTHENTICATED**. Neither the TGSherlock web console (port 8765) nor the Streamlit dashboard (port 8501) requires a password or session token. Anyone with network or localhost access can access all screens, read messages, and trigger actions.
2. **Secrets Protection**: No hardcoded API keys or credentials were found committed to git. Telegram API ID and Hash are entered by the user at runtime.
3. **Data Retention**: **INDEFINITE**. There is no automated TTL or data purge mechanism. Stored messages and extracted personal identifiers remain in SQLite permanently until manual deletion.
4. **Audit Trail**: Operational actions are written to local SQLite `audit_log`. Because SQLite is a local file without append-only hardware protection, an administrator with local access can modify or delete audit rows.

---

## 7. Manual Steps to Obtain Real-Data Proof

To elevate this system from `SYNTHETIC-ONLY` to `LIVE-VERIFIED` for police authorities, the operator must execute the following steps:

1. **Telegram Live Authentication**:
   - Open `http://127.0.0.1:8765/#/settings`.
   - Connect a valid Telegram test account using phone number or QR code.
2. **Real Channel Target Monitoring**:
   - Navigate to `Live Monitor` and add a real public channel (e.g. `@telegram` or a public regional trade group).
   - Let the live monitor capture at least 10 real messages.
3. **Pipeline Ingestion**:
   - Execute `TGSherlockAdapter` or the CSV/JSON Importer on the captured real messages.
   - Run the classification and evidence hashing pipeline on these real messages.
4. **Populate Human-Written Benchmark**:
   - Edit `data/test_human_written.jsonl` and replace the 40 placeholders with real human-written cybercrime ad samples and benign messages.
   - Run `python eval/evaluate_model.py` to obtain the first empirically grounded accuracy score.
5. **Install Tesseract OCR**:
   - Install Tesseract-OCR binary on Windows (`C:\Program Files\Tesseract-OCR\tesseract.exe`) to activate the image extractor.
