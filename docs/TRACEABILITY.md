# Requirements Traceability Matrix (R1 – R6)

This document establishes the audit baseline and implementation tracking for all functional requirements of the **Telegram & Social Media Illegal Trade Monitor**.

---

## 1. Traceability Matrix

| Req ID | Requirement Description | Implementation Files | Automated Test(s) | Demo / Operational Step | Status | Evidence from Test Run & Environment Audit |
|---|---|---|---|---|---|---|
| **R1** | **Data Collection**<br>Collector for public Telegram channels + CSV/JSON import for other platforms. | `discovery/finder.py`<br>`dashboard/db_reader.py`<br>`addons/importer.py`<br>`tgsherlock/src/tgsherlock/tg.py` | `tests/test_discovery.py`<br>`tests/test_addons.py::test_importer_csv`<br>`tests/test_addons.py::test_importer_json` | Ingest live records from TGSherlock DB (`~/.local/share/tgsherlock`) and preview public channels via `tgq preview`. | **Partial** | Verified 4 discovery tests & 2 importer tests passing. Live TGSherlock daemon connected at port 8765 (`account: 5624251936`). Needs unified single SQLite DB (`data/osint_monitor.db`), stream replay mode, and worker process. |
| **R2** | **Illegal-Sale Classifier**<br>Curated slang+emoji lexicon + machine learning; flags drugs, arms, fake documents, bank accounts, ATM cards. | `addons/lexicon.yaml`<br>`addons/scorer.py` | `tests/test_addons.py::test_scorer_drugs_category`<br>`tests/test_addons.py::test_scorer_bank_account_mule`<br>`tests/test_addons.py::test_scorer_arms_category`<br>`tests/test_addons.py::test_scorer_clean_message` | Rule-based scoring categorizes posts into 7 threat categories with explainable matched terms chips. | **Partial** | Curated lexicon with English/Hinglish/Marathi slang and weights verified passing. Needs text normalizer layer (NFKC, homoglyphs, leetspeak, spaced letters), synthetic ML embedding model + logistic regression, `eval/` benchmark metrics, and slang suggestion tool. |
| **R3** | **Financial-Ad Detector**<br>Buy/sell/rent of savings/current accounts, ATM/credit cards, net-banking kits, SIM cards; risk classification + evidence. | `addons/scorer.py` (bank_account, atm_card, sim_card, net_banking_kit) | `tests/test_addons.py::test_scorer_bank_account_mule` | Categorizes mule recruitment ads and generates weighted risk score. | **Partial** | Mule patterns detected in rule scorer. Needs dedicated modular detector returning JSON: intent, instrument, signals, mule-recruitment pattern flag, and exact text span evidence. |
| **R4** | **Identifier Extraction**<br>Phone numbers, UPI IDs, wallet addresses, usernames, locations from text (and images where feasible). | `addons/extractors.py` | `tests/test_addons.py::test_upi_extraction_valid_handles`<br>`tests/test_addons.py::test_upi_extraction_rejects_emails`<br>`tests/test_addons.py::test_phone_extraction_standard_formats`<br>`tests/test_addons.py::test_phone_extraction_devanagari_numerals`<br>`tests/test_addons.py::test_ifsc_extraction`<br>`tests/test_addons.py::test_crypto_extraction`<br>`tests/test_addons.py::test_username_and_tme_links`<br>`tests/test_addons.py::test_location_extraction` | Alerts display extracted UPIs, normalized phones, crypto addresses, and locations as badge chips. | **Partial** | 8 extractor tests passing. Validates NPCI UPI handles and rejects email domains. Handles Devanagari numerals. Needs phonetic word-form numbers ("nine eight seven..."), TRON/BTC checksum validation, Indian gazetteer coordinates/pincodes, and OCR text extraction. |
| **R5** | **Link Analysis**<br>Repeated/coordinated ads (text + image similarity); same identifier linked across channels in an entity graph. | `dashboard/graph.py`<br>`dashboard/similarity.py` | `tests/test_dashboard.py::test_cross_channel_entity_graph`<br>`tests/test_dashboard.py::test_minhash_ad_campaign_clustering` | Interactive NetworkX Plotly graph highlights cross-channel nodes; MinHash tab groups templated ad copy. | **Partial** | Graph highlights multi-channel actors (e.g. `demo.seller@ybl` across 3 channels); MinHash text clusters passing. Needs SQLite graph edge persistence, network centrality metrics, connected components, and unified seller dossier. |
| **R6** | **Alert Dashboard & Evidence**<br>Alerts with evidence snapshot per post: text, time, channel, hash. | `dashboard/app.py`<br>`addons/evidence.py` | `tests/test_addons.py::test_canonical_json_determinism`<br>`tests/test_addons.py::test_evidence_tamper_verification` | Streamlit dashboard serves threat feed, evidence card, and CSV/JSON/HTML export. | **Partial** | Streamlit running live on port 8501. Deterministic SHA-256 evidence hashing verified. Needs hash chain (`prev_hash`), standalone ledger verifier (`verify_evidence.py`), alert workflow status, multi-page layout, and location map. |

---

## 2. Test Execution Evidence (Baseline Run)

Executed on: **2026-11-24 12:24:29 UTC+5:30**  
Environment: **Windows 11, Python 3.15.2, pytest-9.2.0**

```text
============================= test session starts =============================
platform win32 -- Python 3.15.2, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\AJINKYA CHALKE\Desktop\rajasthan hackthon ps2
collected 23 items

tests/test_addons.py::test_upi_extraction_valid_handles PASSED           [  4%]
tests/test_addons.py::test_upi_extraction_rejects_emails PASSED          [  8%]
tests/test_addons.py::test_phone_extraction_standard_formats PASSED      [ 13%]
tests/test_addons.py::test_phone_extraction_devanagari_numerals PASSED   [ 17%]
tests/test_addons.py::test_ifsc_extraction PASSED                        [ 21%]
tests/test_addons.py::test_crypto_extraction PASSED                      [ 26%]
tests/test_addons.py::test_username_and_tme_links PASSED                 [ 30%]
tests/test_addons.py::test_location_extraction PASSED                    [ 34%]
tests/test_addons.py::test_scorer_drugs_category PASSED                  [ 39%]
tests/test_addons.py::test_scorer_bank_account_mule PASSED               [ 43%]
tests/test_addons.py::test_scorer_arms_category PASSED                   [ 47%]
tests/test_addons.py::test_scorer_clean_message PASSED                   [ 52%]
tests/test_addons.py::test_canonical_json_determinism PASSED             [ 56%]
tests/test_addons.py::test_evidence_tamper_verification PASSED           [ 60%]
tests/test_addons.py::test_importer_csv PASSED                           [ 65%]
tests/test_addons.py::test_importer_json PASSED                          [ 69%]
tests/test_dashboard.py::test_synthetic_data_loading PASSED              [ 73%]
tests/test_dashboard.py::test_cross_channel_entity_graph PASSED          [ 78%]
tests/test_dashboard.py::test_minhash_ad_campaign_clustering PASSED      [ 82%]
tests/test_discovery.py::test_load_keywords PASSED                       [ 86%]
tests/test_discovery.py::test_extract_forward_origins PASSED             [ 91%]
tests/test_discovery.py::test_score_channel_posts PASSED                 [ 95%]
tests/test_discovery.py::test_save_watchlist_csv PASSED                  [100%]

============================= 23 passed in 2.18s ==============================
```

---

## 3. Provenance Classification of Features
- **LIVE:** Real public Telegram channel collection via TGSherlock authorized session and `tgq preview` public web scraper.
- **IMPORTED:** External CSV/JSON dumps ingested via `addons/importer.py` / `ingestion/adapters.py`.
- **SIMULATED:** Synthetic seed posts in `sample_data/synthetic_posts.json` replayed to demonstrate cross-channel attribution offline.
