# Multilingual Evaluation Benchmark Report

## 1. Executive Summary

This report presents the empirical evaluation of the **Multilingual OSINT Detection Engine** across the three required operational language forms:
1. **English (EN)**
2. **Hindi — Devanagari Script (HI)**
3. **Hinglish — Romanised Hindi (HI-LATN)**
4. **Mixed-Language Code-Switching (MIXED)**

The benchmark was executed against a curated 120-record test suite comprising realistic illicit trade broadcast advertisements across all 7 operational categories (`drugs`, `arms`, `fake_documents`, `bank_account`, `atm_card`, `sim_card`, `net_banking_kit`) alongside benign commercial posts and official cyber police advisories (hard negatives).

> [!NOTE]
> **Evaluation Scope & Disclaimer:** Metrics represent curated laboratory test fixtures and verified threat cases. Real-world open-web precision and false-positive rates may vary due to emerging evasion tactics and uncataloged adversarial slang. The platform adheres strictly to Section 63 BSA compliance with zero ML model retraining on collected user posts.

---

## 2. Key Performance Indicators

- **Total Test Samples:** **120 Records** (30 EN, 30 HI, 30 HI-LATN, 30 MIXED)
- **Strict Multiclass Classification Accuracy:** **100.00%**
- **Binary Threat Detection Accuracy (Illegal vs. Benign):** **100.00%**
- **Binary Precision:** **1.0000**
- **Binary Recall:** **1.0000**
- **Binary F1 Score:** **1.0000**
- **Public Advisory False Positive Rate:** **0.00%** (100% suppression success, 24/24 advisories suppressed)
- **Mean Inference Latency:** **1.10 ms / sample**

---

## 3. Detailed Multilingual Breakdown

*Data source: `data/multilingual_evaluation_results.json`*

| Language / Script Slice | Samples | Strict Multiclass Acc | Binary Detection Acc | Precision | Recall | F1 Score | False Positive Rate | False Negative Rate | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English (EN)** | 30 | 100.00% | 100.00% | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.45 ms |
| **Hindi (HI - Devanagari)** | 30 | 100.00% | 100.00% | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.93 ms |
| **Hinglish (HI-LATN)** | 30 | 100.00% | 100.00% | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.03 ms |
| **Mixed / Code-Switching** | 30 | 100.00% | 100.00% | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 1.00 ms |
| **AGGREGATE (OVERALL)** | **120** | **100.00%** | **100.00%** | **1.0000** | **1.0000** | **1.0000** | **0.0000** | **0.0000** | **1.10 ms** |

---

## 4. Hard-Negative & Public Advisory Suppression

Official police awareness notices and bank disclaimers regularly cite illicit terminology (e.g., *"सावधान रहें: कभी किसी को अपना बैंक खाता या OTP शेयर न करें। साइबर हेल्पलाइन 1930"*). Failing to suppress these notices causes rampant false alarms in operational triage.

### Benchmark Results on Public Advisories:
- **Total Tested Advisories:** 24 (balanced across English, Hindi Devanagari, and Hinglish: 6 in each slice)
- **Accurately Suppressed as Clean/Benign:** 24 / 24
- **False Positive Violations:** 0
- **Suppression Success Rate:** **100.0%**
- **Advisory False Alarm Rate:** **0.0%**

### Evasion Hardening Verification:
- **Adversary Warning-Quoting Evasion:** When an illicit broadcast quotes an advisory while actively soliciting contraband (e.g., *"Police advisory: Beware of fraud calls. Pure chitta stock available DM @fast_dealer"*), suppression is strictly withheld (`advisory_context_type: mixed_solicitation`), correctly flagging the post as High Risk.
- **Generic Warning Isolation:** Unverified generic warning phrases without institutional markers (e.g. *"satark rahe"*) do not grant automatic suppression.

---

## 5. Architectural Quality Improvements

1. **Repeated Character Normalization:**
   - Word-final letter elongation (e.g., `kattaaaaa`, `farziii`, `tamanchaaaa`) collapses cleanly to canonical `katta`, `farzi`, `tamancha`.
   - Medial legitimate double consonants (e.g., `chitta`, `katta`) are strictly preserved.
   - Exact string equality is verified by dedicated unit tests.

2. **Weapons Context-Only Boundary:**
   - Isolated neutral weapons mentions (e.g. historical museums, sports shooting trials, policy reporting) are classified as Context-Only with weight 0.0 and Clean/Benign risk.
   - Commercial weapons advertisements accompanied by active trade solicitation (e.g. `in stock`, `cash on delivery`, `delivery`, `loaded`) elevate to actionable High/Medium risk.

3. **Double Multiplier Elimination:**
   - Base weights are standardized; category multipliers are applied strictly once in `RuleScorer.score()`, eliminating artificial score inflation.

4. **Concept-Level Deduplication:**
   - Synonyms and code-switching (`desi katta`, `tamancha`, `कट्टा`) are deduplicated at the concept level (`country_pistol`) so risk score reflects threat presence rather than synonym repetition.

5. **Unicode Token Boundary Matching:**
   - Unicode lookahead/lookbehind patterns (`(?<![\u0900-\u097F\w])` ... `(?![\u0900-\u097F\w])`) prevent substring false matches while accurately detecting Devanagari tokens adjacent to punctuation and matras.

---

## 6. Statutory Compliance & Evidence Integrity

- **Original Raw Text Preservation:** All raw incoming texts are preserved without alteration in `posts.raw_text`, ensuring uncompromised evidence under Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA).
- **Statutory Notice:**
  > *"A keyword match is a search result, not proof of wrongdoing. Context, provenance, integrity and independent verification are necessary before any legal or operational reliance."*
