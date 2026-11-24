# Requirements Traceability Matrix (R1 – R6)

This document establishes the completed verification and audit tracking for all functional requirements of the **Telegram & Social Media Illegal Trade Monitor**.

---

## 1. Traceability Matrix

| Req ID | Requirement Description | Implementation Files | Automated Test(s) | Demo / Operational Step | Status | Evidence from Test Run & Environment Audit |
|---|---|---|---|---|---|---|
| **R1** | **Data Collection**<br>Collector for public Telegram channels + CSV/JSON import for other platforms. Unified SQLite DB in WAL mode + replay mode. | `core/db.py`<br>`data/schema.sql`<br>`ingestion/adapters.py`<br>`ingestion/worker.py`<br>`ingestion/replay.py`<br>`discovery/finder.py` | `tests/test_unified_db.py`<br>`tests/test_addons.py::test_importer_csv`<br>`tests/test_addons.py::test_importer_json` | Ingest live records from TGSherlock DB (`~/.local/share/tgsherlock`), poll watchlist via `tgq preview`, or upload CSV/JSON in Page 6. | **Done** | Unified SQLite database `data/osint_monitor.db` in WAL mode handles idempotent upserts with `UNIQUE(platform, channel_id, message_id)`. Replay stream tested at adjustable speed. 12 demo posts ingested and verified. |
| **R2** | **Illegal-Sale Classifier**<br>Curated slang+emoji lexicon + machine learning; flags drugs, arms, fake documents, bank accounts, ATM cards. | `core/normalizer.py`<br>`addons/lexicon.yaml`<br>`addons/scorer.py`<br>`models/classifier.py`<br>`eval/evaluate_model.py`<br>`addons/slang_suggester.py` | `tests/test_normalizer.py`<br>`tests/test_classifier.py`<br>`tests/test_addons.py::test_scorer_*` | Multi-page alerts display category badges, confidence %, and human-readable `why_flagged` explainability traces. | **Done** | Evaluated on 3,010 synthetic samples (80% train, 20% test). Achieved **94.19% accuracy**, **0.943 Macro F1**, and **0.941 Weighted F1** with 0% false positives on hard negatives (bank notices, licensed pharmacies). Zero Telegram data used for model training. Metrics recorded in `docs/METRICS.md`. |
| **R3** | **Financial-Ad Detector**<br>Buy/sell/rent of savings/current accounts, ATM/credit cards, net-banking kits, SIM cards; risk classification + evidence. | `addons/financial_detector.py` | `tests/test_financial_detector.py` | Page 2 shows structured breakdown: Intent, Instrument, Incentive signals, Mule Recruitment flag, and character offset spans. | **Done** | Detects intent (buy/sell/rent/recruit), instruments (savings, current, corporate, ATM, net-banking kit, SIM, crypto), signals (commission, KYC-less, high-limit), and extracts exact evidentiary character spans for court admissibility. All 6 tests passing. |
| **R4** | **Identifier Extraction**<br>Phone numbers, UPI IDs, wallet addresses, usernames, locations from text (and images where feasible). | `addons/extractors.py`<br>`addons/ocr_extractor.py` | `tests/test_addons.py::test_*`<br>`tests/test_extractors_extended.py`<br>`tests/test_demo_and_ocr.py` | Alerts and Seller Dossiers display extracted UPIs, phones, Base58Check crypto wallets, IFSCs, PIN codes, and locations. | **Done** | NPCI-verified UPI handles (rejects emails), 10-digit/Devanagari/word-form phones (`90000 11111`), TRON Base58Check double-SHA256 checksum validation, Indian gazetteer coordinates/PIN codes, price extractions, and OCR image fallback. All 14 tests passing. |
| **R5** | **Link Analysis**<br>Repeated/coordinated ads (text + image similarity); same identifier linked across channels in an entity graph. | `dashboard/graph.py`<br>`dashboard/similarity.py` | `tests/test_dashboard.py`<br>`tests/test_graph_persistence.py` | Page 3 renders interactive Plotly entity graph, highlights cross-channel actors in bold red, lists syndicates, and generates Seller Dossiers. Page 4 clusters campaigns. | **Done** | Persists graph edges to SQLite `entities_edges`. Computes degree and betweenness centrality. Groups connected syndicates. Generates deep Seller Profiles with all linked channels and co-occurring contacts. MinHash (datasketch) Jaccard clustering and pHash (imagehash) duplicate flyer grouping verified. |
| **R6** | **Alert Dashboard & Evidence**<br>Alerts with evidence snapshot per post: text, time, channel, hash. | `dashboard/app.py`<br>`dashboard/pages/*.py`<br>`addons/evidence.py`<br>`addons/verify_evidence.py` | `tests/test_hash_chain.py`<br>`tests/test_addons.py::test_evidence_*` | Multipage Streamlit app at `http://localhost:8501`. Page 1: Alerts & triage workflow. Page 2: RFC-8785 JSON viewer & live hash verify button. | **Done** | Multipage Streamlit dashboard: Home overview + 8 dedicated pages. Cryptographic evidence ledger with block height indexing, RFC-8785 canonical serialization, and chaining (`current_hash = SHA256(canonical_json + prev_hash)`). Verified unbroken chain across all 12 blocks using `addons/verify_evidence.py`. |

---

## 2. Test Execution Evidence (Final Complete Suite)

Executed on: **2026-11-24 12:55:44 UTC+5:30**  
Environment: **Windows 11, Python 3.15.2, pytest-9.2.0**

```text
============================= test session starts =============================
platform win32 -- Python 3.15.2, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\AJINKYA CHALKE\Desktop\rajasthan hackthon ps2
plugins: anyio-4.16.0
collected 59 items

tests/test_addons.py::test_upi_extraction_valid_handles PASSED           [  1%]
tests/test_addons.py::test_upi_extraction_rejects_emails PASSED          [  3%]
tests/test_addons.py::test_phone_extraction_standard_formats PASSED      [  5%]
tests/test_addons.py::test_phone_extraction_devanagari_numerals PASSED   [  6%]
tests/test_addons.py::test_ifsc_extraction PASSED                        [  8%]
tests/test_addons.py::test_crypto_extraction PASSED                      [ 10%]
tests/test_addons.py::test_username_and_tme_links PASSED                 [ 11%]
tests/test_addons.py::test_location_extraction PASSED                    [ 13%]
tests/test_addons.py::test_scorer_drugs_category PASSED                  [ 15%]
tests/test_addons.py::test_scorer_bank_account_mule PASSED               [ 16%]
tests/test_addons.py::test_scorer_arms_category PASSED                   [ 18%]
tests/test_addons.py::test_scorer_clean_message PASSED                   [ 20%]
tests/test_addons.py::test_canonical_json_determinism PASSED             [ 22%]
tests/test_addons.py::test_evidence_tamper_verification PASSED           [ 23%]
tests/test_addons.py::test_importer_csv PASSED                           [ 25%]
tests/test_addons.py::test_importer_json PASSED                          [ 27%]
tests/test_classifier.py::test_synthetic_data_exists PASSED              [ 28%]
tests/test_classifier.py::test_blatant_illegal_drug_ad_classified_high PASSED [ 30%]
tests/test_classifier.py::test_mule_account_ad_classified_high PASSED    [ 32%]
tests/test_classifier.py::test_hard_negative_bank_notice_classified_clean PASSED [ 33%]
tests/test_classifier.py::test_hard_negative_pharmacy_classified_clean PASSED [ 35%]
tests/test_classifier.py::test_hard_negative_shooting_sports PASSED      [ 37%]
tests/test_classifier.py::test_slang_suggester_candidate_extraction PASSED [ 38%]
tests/test_dashboard.py::test_synthetic_data_loading PASSED              [ 40%]
tests/test_dashboard.py::test_cross_channel_entity_graph PASSED          [ 42%]
tests/test_dashboard.py::test_minhash_ad_campaign_clustering PASSED      [ 44%]
tests/test_demo_and_ocr.py::test_generate_demo_dataset PASSED            [ 45%]
tests/test_demo_and_ocr.py::test_ocr_extractor_fallback PASSED           [ 47%]
tests/test_discovery.py::test_load_keywords PASSED                       [ 49%]
tests/test_discovery.py::test_extract_forward_origins PASSED             [ 50%]
tests/test_discovery.py::test_score_channel_posts PASSED                 [ 52%]
tests/test_discovery.py::test_save_watchlist_csv PASSED                  [ 54%]
tests/test_extractors_extended.py::test_phone_spelled_words PASSED       [ 55%]
tests/test_extractors_extended.py::test_phone_spaced_and_dotted PASSED   [ 57%]
tests/test_extractors_extended.py::test_tron_wallet_checksum PASSED      [ 59%]
tests/test_extractors_extended.py::test_locations_with_lat_lon_and_pincodes PASSED [ 61%]
tests/test_extractors_extended.py::test_price_extractions PASSED         [ 62%]
tests/test_financial_detector.py::test_mule_recruitment_pattern_detection PASSED [ 64%]
tests/test_financial_detector.py::test_corporate_netbanking_kit_sale PASSED [ 66%]
tests/test_financial_detector.py::test_atm_card_rent_intent PASSED       [ 67%]
tests/test_financial_detector.py::test_pre_activated_sim_cards PASSED    [ 69%]
tests/test_financial_detector.py::test_exact_evidence_spans_captured PASSED [ 71%]
tests/test_financial_detector.py::test_benign_security_advisory_suppressed PASSED [ 72%]
tests/test_graph_persistence.py::test_graph_centrality_and_cross_channel_detection PASSED [ 74%]
tests/test_graph_persistence.py::test_graph_persistence_to_db PASSED     [ 76%]
tests/test_graph_persistence.py::test_seller_profile_generation PASSED   [ 77%]
tests/test_hash_chain.py::test_hash_chain_sequential_linking PASSED      [ 79%]
tests/test_hash_chain.py::test_hash_chain_tamper_detection PASSED        [ 81%]
tests/test_normalizer.py::test_zero_width_and_control_removal PASSED     [ 83%]
tests/test_normalizer.py::test_homoglyph_folding PASSED                  [ 84%]
tests/test_normalizer.py::test_spaced_out_letters_collapse PASSED        [ 86%]
tests/test_normalizer.py::test_devanagari_digits_folding PASSED          [ 88%]
tests/test_normalizer.py::test_number_words_conversion PASSED            [ 89%]
tests/test_normalizer.py::test_emoji_mapping PASSED                      [ 91%]
tests/test_normalizer.py::test_full_evasion_normalization PASSED         [ 93%]
tests/test_unified_db.py::test_db_wal_mode_and_init PASSED               [ 94%]
tests/test_unified_db.py::test_idempotent_post_insertion PASSED          [ 96%]
tests/test_unified_db.py::test_cross_channel_identifier_linking PASSED   [ 98%]
tests/test_unified_db.py::test_evidence_hash_chain_storage PASSED        [100%]

============================= 59 passed in 2.79s ==============================
```

---

## 3. Cryptographic Ledger Verification Proof

Executed on: **2026-11-24 12:59:39 UTC+5:30**  
Command: `.\.venv\Scripts\python.exe addons/verify_evidence.py --db data/osint_monitor.db`

```text
Loaded 12 evidence blocks from data\osint_monitor.db
SUCCESS: All 12 evidence blocks cryptographically verified with unbroken chain
```

---

## 4. Provenance Classification of Features
- **LIVE:** Real public Telegram channel collection via TGSherlock daemon (`127.0.0.1:8765`) and `tgq preview` public broadcast scraper.
- **IMPORTED:** External CSV/JSON dumps ingested via `addons/importer.py` / `ingestion/adapters.py` (Page 6).
- **SIMULATED:** Seeded multi-platform dataset in `sample_data/demo_multiplatform_dataset.json` and synthetic training data in `data/train_synthetic.jsonl` replayed to demonstrate cross-channel attribution offline.
