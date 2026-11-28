# Multilingual Engine Test Matrix

## 1. Scope & Execution Summary

- **Total Dedicated Multilingual Engine Tests:** 22 tests (`tests/test_multilingual_engine.py`)
- **Total Repository Test Suite:** 128 tests across all modules
- **Status:** **100% PASSED (0 Failures, 0 Regressions)**
- **Test Framework:** Pytest 9.2.0 on Python 3.15.2
- **Execution Time:** ~23 seconds for full test suite

---

## 2. Dedicated Multilingual Engine Test Verification Matrix

| Test ID | Function / Component | Language / Script Target | Test Description & Verifications | Status |
| :--- | :--- | :--- | :--- | :---: |
| `TEST-ML-01` | `detect_language_and_script` | English (EN) | Validates pure English script & token distribution (`> 80% en`) | **PASS** |
| `TEST-ML-02` | `detect_language_and_script` | Hindi (HI) | Validates pure Devanagari script detection (`> 80% hi`) | **PASS** |
| `TEST-ML-03` | `detect_language_and_script` | Hinglish (HI-LATN) | Validates Latin script with Hindi grammatical particles | **PASS** |
| `TEST-ML-04` | `detect_language_and_script` | Mixed / Code-Switching | Validates hybrid Latin-Devanagari sentences | **PASS** |
| `TEST-ML-05` | `normalize_devanagari` | Hindi (Devanagari) | Nukta character decomposition & folding (`क़ट्टा फ़र्ज़ी` -> `कट्टा फर्जी`) | **PASS** |
| `TEST-ML-06` | `normalize_devanagari` | Hindi (Devanagari) | Devanagari danda punctuation replacement (`।`/`॥` -> `. `) | **PASS** |
| `TEST-ML-07` | `normalize_hinglish_slang` | Hinglish (HI-LATN) | Exact equality for repeated characters (`kattaaaaa` == `katta`, `farziii` == `farzi`, legitimate `chitta` == `chitta`) | **PASS** |
| `TEST-ML-08` | `normalize_hinglish_slang` | Hinglish (HI-LATN) | Verifies normalized spelling matches lexicon terms (`kattaaaaa` -> `arms`, `farziiii` -> `fake_documents`) | **PASS** |
| `TEST-ML-09` | `normalize_hinglish_slang` | Hinglish (HI-LATN) | Phonetic alias mapping (`nakalee` -> `nakli`, `farjee` -> `farzi`, `dastavej` -> `dastavez`) | **PASS** |
| `TEST-ML-10` | `normalize_multilingual` | Mixed / Audit | Verifies audit dataclass with raw text preservation for Section 63 BSA | **PASS** |
| `TEST-ML-11` | `RuleScorer` | Hindi (Devanagari) | Arms category detection with Devanagari terms (`देसी कट्टा`, `कट्टा`, `गोली`) | **PASS** |
| `TEST-ML-12` | `RuleScorer` | Hindi (Devanagari) | Drugs category detection with Devanagari terms (`एमडीएमए`, `चरस`) | **PASS** |
| `TEST-ML-13` | `RuleScorer` | Multilingual | Concept-level deduplication across synonyms (`desi katta, tamancha and कट्टा` scored once) | **PASS** |
| `TEST-ML-14` | `RuleScorer` | Architecture / Scorer | Single multiplier verification (`cat_weighted_score == cat_raw_score * multiplier`) | **PASS** |
| `TEST-ML-15` | `check_awareness_context` | English (EN) | Hard negative suppression on English police advisory -> Clean/Low | **PASS** |
| `TEST-ML-16` | `check_awareness_context` | Hindi (Devanagari) | Hard negative suppression on Hindi cyber notice -> Clean/Low | **PASS** |
| `TEST-ML-17` | `check_awareness_context` | Hinglish (HI-LATN) | Hard negative suppression on Hinglish advisory -> Clean/Low | **PASS** |
| `TEST-ML-18` | `HybridClassifier` | Full Pipeline | Multilingual metadata emission (`language`, `detected_scripts`, `risk_level`) | **PASS** |
| `TEST-ML-19` | `evaluate_awareness_context` | Mixed Evasion | Quoted police advisory accompanied by drug/arms trade cues is NOT suppressed | **PASS** |
| `TEST-ML-20` | `evaluate_awareness_context` | Generic Warning | Generic warning phrase in isolation without institutional backing is NOT suppressed | **PASS** |
| `TEST-ML-21` | `RuleScorer` / `Classifier` | Neutral Context | Neutral isolated weapon mention (museum/shooting sport) -> Context-Only, 0.0 score, Clean | **PASS** |
| `TEST-ML-22` | `RuleScorer` / `Classifier` | Active Solicitation | Weapons mention with trade cues -> Full weight, Actionable High/Medium Risk | **PASS** |

---

## 3. Full Repository Test Suite Coverage

| Test Module | Scope & Functionality | Tests | Status |
| :--- | :--- | :---: | :---: |
| `tests/test_multilingual_engine.py` | Complete Multilingual engine (EN, HI, HI-LATN, MIXED) | 22 | **PASS** |
| `tests/test_normalizer.py` | Normalizer, NFKC, homoglyphs, Devanagari digits, emojis | 7 | **PASS** |
| `tests/test_addons.py` | Scorer, extractors, canonical JSON, evidence tamper check, OCR, PDF export | 22 | **PASS** |
| `tests/test_classifier.py` | HybridClassifier, hard negatives, TF-IDF inference, slang suggester | 7 | **PASS** |
| `tests/test_discovery.py` | Channel discovery, keyword loading, forward origins, scoring | 4 | **PASS** |
| `tests/test_financial_detector.py` | Financial ad detection, intent classification, entity extraction | 9 | **PASS** |
| `tests/test_extractors_extended.py` | Financial handles, UPI, phone, crypto, IFSC, t.me links | 8 | **PASS** |
| `tests/test_hash_chain.py` | Cryptographic evidence hash chain, RFC-8785 canonical JSON | 6 | **PASS** |
| `tests/test_ps02_search_catalog.py`| Committee search catalog, 10 categories, Indian languages | 19 | **PASS** |
| `tests/test_ps02_dataset.py` | Isolated participant database, preflight audit, aggregations | 8 | **PASS** |
| `tests/test_instagram_source.py` | Instagram monitor, air-gapped forensic fixtures | 8 | **PASS** |
| `tests/test_graph_persistence.py` | Graph database relations, channel networks, posters | 8 | **PASS** |
| `tests/test_unified_db.py` | SQLite schema, alerts, posts, audit logs | 7 | **PASS** |
| **TOTAL** | **Entire Test Suite** | **128** | **100% PASS** |
