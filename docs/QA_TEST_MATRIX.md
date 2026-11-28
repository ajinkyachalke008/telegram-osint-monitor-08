# PS02 Hackathon QA Test Matrix

This matrix documents all executed automated unit, integration, UI, and security verification tests across the entire codebase.

**Execution Environment:** Windows 11, Python 3.15.2, Pytest 9.2.0, Streamlit AppTest, Playwright Chromium
**Total Tests Executed:** 121 (105 Pytest + 12 Streamlit AppTest + 4 Playwright Viewports)
**Total Passed:** 121 / 121 (100% Pass Rate)
**Total Failed:** 0

---

## 1. Automated Test Suite Matrix (`pytest`)

| Test ID | Component | Test Case | Expected Result | Actual Result | Status | Evidence |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `TC-ADD-01` | `addons/extractors` | Valid UPI handle extraction | Extracts UPI handles cleanly | Handles extracted matching regex | **PASS** | `test_addons.py::test_upi_extraction_valid_handles` |
| `TC-ADD-02` | `addons/extractors` | Rejection of email as UPI | Rejects valid emails from UPI match | Cleanly excluded emails | **PASS** | `test_addons.py::test_upi_extraction_rejects_emails` |
| `TC-ADD-03` | `addons/extractors` | Standard phone number formats | Extracts +91, 0, dashed phone numbers | Correct phone normalization | **PASS** | `test_addons.py::test_phone_extraction_standard_formats` |
| `TC-ADD-04` | `addons/extractors` | Devanagari numerals phone | Folds Devanagari digits to ASCII phone | Cleanly normalized phone | **PASS** | `test_addons.py::test_phone_extraction_devanagari_numerals` |
| `TC-ADD-05` | `addons/extractors` | IFSC bank code extraction | Extracts standard 11-char IFSC | Matches valid bank IFSCs | **PASS** | `test_addons.py::test_ifsc_extraction` |
| `TC-ADD-06` | `addons/extractors` | Crypto address extraction | Identifies BTC/ETH/TRX addresses | Matches crypto wallets | **PASS** | `test_addons.py::test_crypto_extraction` |
| `TC-ADD-07` | `addons/extractors` | Telegram username & t.me links | Extracts handle and t.me link | Correct handle extraction | **PASS** | `test_addons.py::test_username_and_tme_links` |
| `TC-ADD-08` | `addons/extractors` | Channel own handle exclusion | Excludes channel handle from seller IDs | Excluded own handle | **PASS** | `test_addons.py::test_channel_own_handle_excluded_from_seller_identifiers` |
| `TC-ADD-09` | `addons/extractors` | Rajasthan location extraction | Extracts cities, districts, pincodes | Matches Rajasthan entities | **PASS** | `test_addons.py::test_location_extraction` |
| `TC-ADD-10` | `addons/scorer` | Threat scoring: drugs | Assigns High/Critical score for drugs | Correct threat category | **PASS** | `test_addons.py::test_scorer_drugs_category` |
| `TC-ADD-11` | `addons/scorer` | Threat scoring: mule account | Identifies bank account rental intent | High threat score | **PASS** | `test_addons.py::test_scorer_bank_account_mule` |
| `TC-ADD-12` | `addons/scorer` | Threat scoring: arms | Identifies arms procurement signals | High threat score | **PASS** | `test_addons.py::test_scorer_arms_category` |
| `TC-ADD-13` | `addons/scorer` | Threat scoring: clean message | Scores benign message as Clean/Low | Threat score 0.0 | **PASS** | `test_addons.py::test_scorer_clean_message` |
| `TC-ADD-14` | `addons/evidence` | RFC-8785 canonical determinism | Canonical JSON produces stable hash | Deterministic SHA-256 | **PASS** | `test_addons.py::test_canonical_json_determinism` |
| `TC-ADD-15` | `addons/evidence` | Tamper verification | Modified record fails hash check | Tamper flag triggered | **PASS** | `test_addons.py::test_evidence_tamper_verification` |
| `TC-ADD-16` | `addons/importer` | Generic CSV importer | Parses generic CSV into raw posts | Records parsed | **PASS** | `test_addons.py::test_importer_csv` |
| `TC-ADD-17` | `addons/importer` | Generic JSON importer | Parses generic JSON array into raw posts | Records parsed | **PASS** | `test_addons.py::test_importer_json` |
| `TC-ADD-18` | `addons/slang` | Slang feedback loop | Learns emerging slang terms | Candidate list generated | **PASS** | `test_addons.py::test_lexicon_feedback_loop` |
| `TC-ADD-19` | `addons/ocr` | OCR honesty policy | Falls back gracefully without tesseract | Graceful bypass, no crash | **PASS** | `test_addons.py::test_ocr_honesty_policy` |
| `TC-ADD-20` | `addons/pdf` | PDF Section 63 BSA export | Generates courtroom evidence PDF | PDF byte stream created | **PASS** | `test_addons.py::test_pdf_export_section_63_evidence_package` |
| `TC-ADD-21` | `addons/preview` | TG preview message ID real | Extracts Telegram web message IDs | Parsed message ID | **PASS** | `test_addons.py::test_tgq_preview_message_id_extraction_real_format` |
| `TC-ADD-22` | `addons/preview` | TG preview message fallback | Fallback extraction on irregular URLs | Parsed fallback ID | **PASS** | `test_addons.py::test_tgq_preview_message_id_fallbacks` |
| `TC-CLS-01` | `models/classifier` | Synthetic data existence | Confirms training files exist | All 3 JSONL files present | **PASS** | `test_classifier.py::test_synthetic_data_exists` |
| `TC-CLS-02` | `models/classifier` | Blatant illegal drug ad | Classifies illicit drug ad as high | Score >= 0.85 | **PASS** | `test_classifier.py::test_blatant_illegal_drug_ad_classified_high` |
| `TC-CLS-03` | `models/classifier` | Mule account ad | Classifies bank account sale as high | Score >= 0.85 | **PASS** | `test_classifier.py::test_mule_account_ad_classified_high` |
| `TC-CLS-04` | `models/classifier` | Hard negative: bank notice | Benign bank security advisory clean | Score < 0.30 | **PASS** | `test_classifier.py::test_hard_negative_bank_notice_classified_clean` |
| `TC-CLS-05` | `models/classifier` | Hard negative: pharmacy | Licensed medical pharmacy clean | Score < 0.30 | **PASS** | `test_classifier.py::test_hard_negative_pharmacy_classified_clean` |
| `TC-CLS-06` | `models/classifier` | Hard negative: shooting sports | Olympic shooting sports clean | Score < 0.30 | **PASS** | `test_classifier.py::test_hard_negative_shooting_sports` |
| `TC-CLS-07` | `models/slang` | Slang candidate extraction | Extracts frequency-based candidates | Correct candidates returned | **PASS** | `test_classifier.py::test_slang_suggester_candidate_extraction` |
| `TC-DSH-01` | `dashboard/app` | Synthetic data loading | Loads demo records into dashboard | Loaded demo records | **PASS** | `test_dashboard.py::test_synthetic_data_loading` |
| `TC-DSH-02` | `dashboard/graph` | Cross-channel entity graph | Identifies shared nodes across channels | Graph nodes linked | **PASS** | `test_dashboard.py::test_cross_channel_entity_graph` |
| `TC-DSH-03` | `dashboard/similarity` | MinHash campaign clustering | Clusters syndicated message copies | High Jaccard similarity | **PASS** | `test_dashboard.py::test_minhash_ad_campaign_clustering` |
| `TC-DEM-01` | `scripts/demo` | Demo dataset generator | Generates valid demo records | Records generated cleanly | **PASS** | `test_demo_and_ocr.py::test_generate_demo_dataset` |
| `TC-DEM-02` | `addons/ocr` | OCR fallback behavior | Returns empty text when OCR disabled | No unhandled exception | **PASS** | `test_demo_and_ocr.py::test_ocr_extractor_fallback` |
| `TC-DIS-01` | `discovery/finder` | Keyword loading | Loads discovery seed keywords | Keywords dictionary loaded | **PASS** | `test_discovery.py::test_load_keywords` |
| `TC-DIS-02` | `discovery/finder` | Forward origin extraction | Identifies original forwarded channels | Extracted origin channel | **PASS** | `test_discovery.py::test_extract_forward_origins` |
| `TC-DIS-03` | `discovery/finder` | Channel post scoring | Computes suspicious score for channel | Score computed accurately | **PASS** | `test_discovery.py::test_score_channel_posts` |
| `TC-DIS-04` | `discovery/finder` | Watchlist CSV persistence | Saves identified channels to CSV | CSV exported cleanly | **PASS** | `test_discovery.py::test_save_watchlist_csv` |
| `TC-EXT-01` | `addons/extractors` | Spelled-out phone numbers | Normalizes "nine eight two..." words | Extracted digit string | **PASS** | `test_extractors_extended.py::test_phone_spelled_words` |
| `TC-EXT-02` | `addons/extractors` | Spaced & dotted phone numbers | Normalizes "982.90.12345" | Normalized 10-digit number | **PASS** | `test_extractors_extended.py::test_phone_spaced_and_dotted` |
| `TC-EXT-03` | `addons/extractors` | Tron wallet checksum | Validates Base58Check TRC-20 wallet | Validated TRON address | **PASS** | `test_extractors_extended.py::test_tron_wallet_checksum` |
| `TC-EXT-04` | `addons/extractors` | Locations with lat/lon/pincode | Extracts geographic coordinates | Coordinates matched | **PASS** | `test_extractors_extended.py::test_locations_with_lat_lon_and_pincodes` |
| `TC-EXT-05` | `addons/extractors` | Price extractions | Extracts INR/USDT price mentions | Currency & amount parsed | **PASS** | `test_extractors_extended.py::test_price_extractions` |
| `TC-FIN-01` | `addons/financial` | Mule recruitment pattern | Identifies "need current account rent" | Mule pattern flagged | **PASS** | `test_financial_detector.py::test_mule_recruitment_pattern_detection` |
| `TC-FIN-02` | `addons/financial` | Corporate netbanking kit sale | Identifies corporate kit sale | Corporate kit pattern flagged | **PASS** | `test_financial_detector.py::test_corporate_netbanking_kit_sale` |
| `TC-FIN-03` | `addons/financial` | ATM card rent intent | Identifies ATM card rental ads | ATM intent flagged | **PASS** | `test_financial_detector.py::test_atm_card_rent_intent` |
| `TC-FIN-04` | `addons/financial` | Pre-activated SIM cards | Identifies pre-activated SIM sales | SIM sale flagged | **PASS** | `test_financial_detector.py::test_pre_activated_sim_cards` |
| `TC-FIN-05` | `addons/financial` | Evidence span capture | Records exact substring offsets | Spans recorded | **PASS** | `test_financial_detector.py::test_exact_evidence_spans_captured` |
| `TC-FIN-06` | `addons/financial` | Benign advisory suppression | Suppresses official police warnings | Benign notice suppressed | **PASS** | `test_financial_detector.py::test_benign_security_advisory_suppressed` |
| `TC-GRP-01` | `core/db` | Graph centrality & cross-channel | Computes degree centrality | Central nodes identified | **PASS** | `test_graph_persistence.py::test_graph_centrality_and_cross_channel_detection` |
| `TC-GRP-02` | `core/db` | Graph persistence to DB | Persists nodes & edges to SQLite | Records saved in SQLite | **PASS** | `test_graph_persistence.py::test_graph_persistence_to_db` |
| `TC-GRP-03` | `core/db` | Seller profile generation | Synthesizes composite seller profile | Profile generated | **PASS** | `test_graph_persistence.py::test_seller_profile_generation` |
| `TC-GRP-04` | `core/db` | Cross-channel decoration | Decorates cross-channel nodes | Badges applied | **PASS** | `test_graph_persistence.py::test_load_graph_from_db_decorates_cross_channel_nodes` |
| `TC-HSH-01` | `addons/evidence` | Evidence ledger genesis | Creates initial hash chain link | Genesis hash created | **PASS** | `test_hash_chain.py::test_evidence_ledger_genesis` |
| `TC-HSH-02` | `addons/evidence` | Hash chain sequential linkage | Previous hash equals prior link SHA | SHA-256 chain unbroken | **PASS** | `test_hash_chain.py::test_evidence_ledger_sequential_linkage` |
| `TC-HSH-03` | `addons/evidence` | Tamper detection on record | Modifying payload breaks integrity | Verification returns False | **PASS** | `test_hash_chain.py::test_evidence_ledger_tamper_detection` |
| `TC-HSH-04` | `addons/evidence` | Section 63 BSA certificate export | Exports verifiable courtroom PDF | PDF generated with hashes | **PASS** | `test_hash_chain.py::test_section_63_evidence_export` |
| `TC-INS-01` | `instagram_source` | Submodule & license preserved | Retains upstream license files | MIT license file present | **PASS** | `test_instagram_source.py::test_submodule_and_license_preserved` |
| `TC-INS-02` | `instagram_source` | Localhost service binding | Restricts bridge to 127.0.0.1 | Local binding enforced | **PASS** | `test_instagram_source.py::test_localhost_service_binding` |
| `TC-INS-03` | `instagram_source` | CSV parser valid records | Parses Instagram activity rows | Records parsed into schema | **PASS** | `test_instagram_source.py::test_csv_parser_valid_records` |
| `TC-INS-04` | `instagram_source` | Formula injection defense | Strips `=,+,-,@` spreadsheet prefixes | Sanitized cell values | **PASS** | `test_instagram_source.py::test_formula_injection_defense` |
| `TC-INS-05` | `instagram_source` | Malformed CSV handling | Handles empty & truncated rows | Skips bad rows gracefully | **PASS** | `test_instagram_source.py::test_malformed_csv_handling` |
| `TC-INS-06` | `instagram_source` | Meta JSON export parser | Parses Instagram JSON export files | Extracted target records | **PASS** | `test_instagram_source.py::test_meta_json_export_parser` |
| `TC-INS-07` | `instagram_source` | Isolated storage CRUD | Persists targets to isolated DB | Saved to instagram_intel.db | **PASS** | `test_instagram_source.py::test_isolated_storage_crud_and_idempotency` |
| `TC-INS-08` | `dashboard/page11` | Page 11 rendering | Renders Instagram Intelligence UI | Renders without exception | **PASS** | `test_instagram_source.py::test_page_11_rendering` |
| `TC-LIV-01` | `ingestion/worker` | Operational pipeline E2E | Ingests, scores, and alerts post | Full pipeline pass | **PASS** | `test_live_ingestion_e2e.py::test_operational_pipeline_end_to_end` |
| `TC-NRM-01` | `core/normalizer` | Zero-width character removal | Strips ZWSP, ZWNJ, and controls | Cleaned text | **PASS** | `test_normalizer.py::test_zero_width_and_control_removal` |
| `TC-NRM-02` | `core/normalizer` | Homoglyph folding | Folds Cyrillic/Greek lookalikes | Folded to Latin ASCII | **PASS** | `test_normalizer.py::test_homoglyph_folding` |
| `TC-NRM-03` | `core/normalizer` | Spaced-out letters collapse | Collapses "d r u g s" to "drugs" | Collapsed token | **PASS** | `test_normalizer.py::test_spaced_out_letters_collapse` |
| `TC-NRM-04` | `core/normalizer` | Devanagari digits folding | Folds १२३४ to 1234 | Folded to ASCII digits | **PASS** | `test_normalizer.py::test_devanagari_digits_folding` |
| `TC-NRM-05` | `core/normalizer` | Number words conversion | Converts "nine eight" to "98" | Converted to numbers | **PASS** | `test_normalizer.py::test_number_words_conversion` |
| `TC-NRM-06` | `core/normalizer` | Emoji mapping | Maps 🍁 to cannabis, 💊 to pills | Normalized emoji keywords | **PASS** | `test_normalizer.py::test_emoji_mapping` |
| `TC-NRM-07` | `core/normalizer` | Full evasion normalization | Normalizes multi-layer obfuscation | Extracted plain terms | **PASS** | `test_normalizer.py::test_full_evasion_normalization` |
| `TC-PS0-01` | `ps02/preflight` | Safe ZIP security | Blocks directory traversal (`..`) | Raises ValueError on traversal | **PASS** | `test_ps02_dataset.py::test_safe_zip_security` |
| `TC-PS0-02` | `ps02/preflight` | Root prefix discovery | Discovers optional top-level folder | Returns prefix string | **PASS** | `test_ps02_dataset.py::test_discover_root_prefix` |
| `TC-PS0-03` | `ps02/parser` | Parse IST timestamp | Parses ISO string with +05:30 | Correct timezone offset | **PASS** | `test_ps02_dataset.py::test_parse_ist_timestamp` |
| `TC-PS0-04` | `ps02/importer` | Dry-run & idempotent import | Dry-run = 0 writes, 2nd run = 0 adds | Idempotent, zero duplicate | **PASS** | `test_ps02_dataset.py::test_dry_run_and_idempotent_import_on_actual_zip` |
| `TC-PS0-05` | `ps02/preflight` | Archive limits & path safety | Rejects oversized ZIP archives | Bounds strictly enforced | **PASS** | `test_ps02_preflight.py::test_archive_limits_and_path_safety` |
| `TC-PS0-06` | `ps02/catalog` | Catalog loads 10 categories | Loads all 10 official categories | Exactly 10 categories found | **PASS** | `test_ps02_search_catalog.py::test_catalog_loads_10_categories` |
| `TC-PS0-07` | `ps02/catalog` | Weapons category terms | 16 ordinary contextual terms only | Matches 16 exact terms | **PASS** | `test_ps02_search_catalog.py::test_weapons_firearms_category_terms` |
| `TC-PS0-08` | `ps02/catalog` | Case-insensitive matching | Matches uppercase, lowercase, mixed | Matches "KATTE", "Katta" | **PASS** | `test_ps02_search_catalog.py::test_case_insensitive_matching` |
| `TC-PS0-09` | `ps02/catalog` | Exact phrase vs broad search | Contiguous tokens vs single tokens | Differentiates phrase/token | **PASS** | `test_ps02_search_catalog.py::test_exact_phrase_vs_broad_search` |
| `TC-PS0-10` | `ps02/catalog` | Marathi variants matching | Matches "gavti katta", "banduk" | Correct Marathi match | **PASS** | `test_ps02_search_catalog.py::test_marathi_variants_matching` |
| `TC-PS0-11` | `ps02/catalog` | False-positive suppression | "spray gun" does not match weapon | Benign homonym suppressed | **PASS** | `test_ps02_search_catalog.py::test_false_positive_suppression` |
| `TC-PS0-12` | `ps02/catalog` | Comprehensive PII sanitization | Redacts phone, email, UPI, usernames | Scrubbed with [REDACTED_*] | **PASS** | `test_ps02_search_catalog.py::test_comprehensive_pii_sanitization` |
| `TC-PS0-13` | `ps02/catalog` | Statutory disclaimer content | Exact mandatory legal statement | String matches verbatim | **PASS** | `test_ps02_search_catalog.py::test_disclaimer_content` |
| `TC-PS0-14` | `ps02/catalog` | Synthetic fixture: fraud | Matches cyber fraud fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[general_fraud_forgery]` |
| `TC-PS0-15` | `ps02/catalog` | Synthetic fixture: phishing | Matches bank impersonation fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[phishing_impersonation]` |
| `TC-PS0-16` | `ps02/catalog` | Synthetic fixture: OTP/KYC | Matches secret banking OTP fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[otp_kyc_credentials]` |
| `TC-PS0-17` | `ps02/catalog` | Synthetic fixture: UPI card | Matches QR payment scam fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[upi_payment_card]` |
| `TC-PS0-18` | `ps02/catalog` | Synthetic fixture: identity | Matches duplicate certificate fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[identity_document]` |
| `TC-PS0-19` | `ps02/catalog` | Synthetic fixture: loan fee | Matches instant loan fee fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[loan_job_advance_fee]` |
| `TC-PS0-20` | `ps02/catalog` | Synthetic fixture: lottery | Matches lottery circulation fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[investment_lottery]` |
| `TC-PS0-21` | `ps02/catalog` | Synthetic fixture: delivery | Matches courier scam fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[marketplace_delivery]` |
| `TC-PS0-22` | `ps02/catalog` | Synthetic fixture: extortion | Matches malware threat fixture | Category detected | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[extortion_malware]` |
| `TC-PS0-23` | `ps02/catalog` | Synthetic fixture: weapons | Matches unlicensed firearm fixture | Category detected (Context) | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[weapons_firearm_context-1]` |
| `TC-PS0-24` | `ps02/catalog` | Synthetic fixture: Marathi | Matches gavti katta & banduk | Category detected (Context) | **PASS** | `test_ps02_search_catalog.py::test_all_10_categories_synthetic_fixtures[weapons_firearm_context-2]` |
| `TC-PS0-25` | `ps02/catalog` | Attachment bytes safety | Reads ZIP bytes safely, blocks `..` | Traversal rejected | **PASS** | `test_ps02_search_catalog.py::test_attachment_bytes_retrieval_and_safety` |
| `TC-PS0-26` | `ps02/catalog` | Genuine offline dataset search | Matches `aadhaar` in genuine ZIP | Found genuine matches | **PASS** | `test_ps02_search_catalog.py::test_offline_committee_dataset_genuine_search` |
| `TC-UDB-01` | `core/db` | WAL mode & DB initialization | Sets WAL journal mode and tables | WAL pragma verified | **PASS** | `test_unified_db.py::test_db_wal_mode_and_init` |
| `TC-UDB-02` | `core/db` | Idempotent post insertion | Re-inserting post returns False | Idempotent no-op | **PASS** | `test_unified_db.py::test_idempotent_post_insertion` |
| `TC-UDB-03` | `core/db` | Cross-channel linking | Links seller IDs across channels | Creates edge in SQLite | **PASS** | `test_unified_db.py::test_cross_channel_identifier_linking` |
| `TC-UDB-04` | `core/db` | Evidence hash chain storage | Persists hash chain entry to DB | Stored in evidence_ledger | **PASS** | `test_unified_db.py::test_evidence_hash_chain_storage` |
| `TC-UDB-05` | `core/db` | Alert dedup per channel | Deduplicates alerts within window | Duplicate alert suppressed | **PASS** | `test_unified_db.py::test_alert_dedup_per_channel` |
| `TC-UDB-06` | `core/db` | Scripted demo injection | Injects demo records for rehearsals | Injected into demo.db | **PASS** | `test_unified_db.py::test_inject_scripted_demo_post` |
| `TC-UDB-07` | `core/db` | Operational DB protection | Protects operational.db from reset | Operational DB intact | **PASS** | `test_unified_db.py::test_operational_db_protected_from_reset_and_injection` |
| `TC-UDB-08` | `core/db` | Default DB path selection | Selects correct DB based on env | Correct DB path returned | **PASS** | `test_unified_db.py::test_default_db_path_selection` |

---

## 2. Interactive Streamlit AppTest Suite Matrix

| Test ID | Page File | Component | Action / Interaction Tested | Result | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `TC-APP-00` | `dashboard/app.py` | Home Overview | Initial load & KPI banner render | Loaded cleanly | **PASS** |
| `TC-APP-01` | `dashboard/pages/1_🚨_Live_Alerts.py` | Live Alerts | Risk filter multiselect (`Low`), Status select (`reviewing`) | Filtered table updated | **PASS** |
| `TC-APP-02` | `dashboard/pages/2_🔍_Alert_Detail.py` | Alert Detail | Alert selection dropdown, Verify Seal button click | Seal verified green | **PASS** |
| `TC-APP-03` | `dashboard/pages/3_🕸️_Entity_Graph.py` | Entity Graph | Pyvis HTML canvas loading, physics layout options | Canvas loaded | **PASS** |
| `TC-APP-04` | `dashboard/pages/4_🔁_Coordinated_Campaigns.py` | Coordinated Campaigns | Similarity threshold slider adjustment (0.70) | Clustered table updated | **PASS** |
| `TC-APP-05` | `dashboard/pages/5_🗺️_Geographic_Map.py` | Geographic Map | Folium map rendering, district hotspot layer | Map layer rendered | **PASS** |
| `TC-APP-06` | `dashboard/pages/6_📁_Data_Ingestion.py` | Data Ingestion | Generic file upload drag-and-drop render | Upload target ready | **PASS** |
| `TC-APP-07` | `dashboard/pages/7_📈_Model_Metrics.py` | Model Metrics | Confusion matrix, PR curve rendering | Metrics displayed | **PASS** |
| `TC-APP-08` | `dashboard/pages/8_⚖️_Responsible_Use_and_Audit.py` | Responsible Use & Audit | Term weight tuning slider adjustment (5.0) | Weight updated | **PASS** |
| `TC-APP-09` | `dashboard/pages/9_🔭_Channel_Discovery.py` | Channel Discovery | Tab switching, watchlist table render | Tabs rendered | **PASS** |
| `TC-APP-10` | `dashboard/pages/10_📊_PS02_Dataset_Insights.py` | PS02 Insights & Explorer | Tabs 1-6, Run Preflight button, Dry-run preview button | Preflight & dry-run passed | **PASS** |
| `TC-APP-11` | `dashboard/pages/11_📸_Instagram_Intelligence.py` | Instagram Intelligence | Control panel load, target profile status card | UI rendered cleanly | **PASS** |

---

## 3. Playwright Multi-Viewport Responsive Matrix

| Test ID | Viewport Name | Dimensions | Target URL | Overflow Delta | Interaction Tested | Status |
| :--- | :--- | :---: | :--- | :---: | :--- | :---: |
| `TC-PW-01` | Desktop | 1920 × 1080 | `/PS02_Dataset_Insights` | 0 px | Tab 6 click, preset chip `desi katta`, exact disclaimer render | **PASS** |
| `TC-PW-02` | Laptop | 1366 × 768 | `/PS02_Dataset_Insights` | 0 px | Tab 6 click, preset chip `desi katta`, exact disclaimer render | **PASS** |
| `TC-PW-03` | Tablet | 768 × 1024 | `/PS02_Dataset_Insights` | 0 px | Tab 6 click, preset chip `desi katta`, exact disclaimer render | **PASS** |
| `TC-PW-04` | Mobile | 390 × 844 | `/PS02_Dataset_Insights` | 0 px | Tab 6 click, preset chip `tamancha`, touch wrap layout | **PASS** |
