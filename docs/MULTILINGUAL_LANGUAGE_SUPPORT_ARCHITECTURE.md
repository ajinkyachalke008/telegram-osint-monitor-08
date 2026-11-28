# Multilingual Language Support Architecture

## 1. Executive Summary & Objective

The **Telegram OSINT Monitor (PS02)** detection engine has been upgraded to provide native, first-class multilingual intelligence across three linguistic registers:
1. **English (EN):** Existing dictionary, regex boundaries, and semantic models preserved 100%.
2. **Hindi — Devanagari Script (HI):** Native Devanagari script processing, Unicode NFKC normalization, nukta character folding, danda punctuation mapping, and matra preservation.
3. **Hinglish — Romanised Hindi (HI-LATN):** Phonetic variations, repeated character normalization (`kattaaaa` -> `katta`), colloquial particles, and approved alias resolution.
4. **Mixed-Language / Code-Switching (MIXED):** Robust character- and token-level script classification supporting inter-sentential and intra-sentential code-switching.

---

## 2. Architecture Overview

```
                                  [Raw Incoming Post]
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │   Script & Language Tag Detection     │
                       │     (core/multilingual.py)            │
                       │   - Devanagari Character Analysis     │
                       │   - Latin & Hinglish Grammar Tokens   │
                       │   -> LanguageTag (EN/HI/HI-LATN/MIXED)│
                       └───────────────────┬───────────────────┘
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │     Deterministic Normalization       │
                       │   - NFKC Unicode Normalization        │
                       │   - Nukta Folding (क़->क, फ़->फ, ज़->ज)   │
                       │   - Danda Mapping (।/॥ -> .)          │
                       │   - Zero-Width Removal (ZWJ / ZWNJ)   │
                       │   - Repeated Character Collapse       │
                       │   - Phonetic Alias Standardization    │
                       └───────────────────┬───────────────────┘
                                           │
                   ┌───────────────────────┴───────────────────────┐
                   ▼                                               ▼
┌───────────────────────────────────────┐       ┌───────────────────────────────────────┐
│     Multilingual RuleScorer           │       │       Hybrid ML Classifier            │
│       (addons/scorer.py)              │       │      (models/classifier.py)           │
│ - Lexicon (slang_en, slang_hi, etc.)  │       │ - Multilingual TF-IDF n-grams (1-3)   │
│ - Unicode Token Boundary Matching     │       │ - Sentence-Transformers Embedding Head│
│ - Concept Deduplication (1 per post)  │       │ - Multilingual Hard-Negative Filtering│
│ - Single Multiplier Application       │       │ - Police Advisory & Notice Suppressor │
│ - Advisory False-Positive Suppressor  │       │ - Language Metadata & Script Weights  │
└──────────────────┬────────────────────┘       └──────────────────┬────────────────────┘
                   │                                               │
                   └───────────────────────┬───────────────────────┘
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │   Calibrated Classification Result    │
                       │   - Category, Confidence, Risk Level  │
                       │   - Language Tag & Script Breakdown   │
                       │   - Explainable Matched Terms & Span  │
                       │   - RFC-8785 Evidentiary Audit Trail  │
                       └───────────────────────────────────────┘
```

---

## 3. Core Normalization Pipeline

### 3.1 Script & Language Detection (`core/multilingual.py`)
- Evaluates Unicode character ranges:
  - Devanagari: `[\u0900-\u097F]`
  - Latin: `[a-zA-Z]`
- Analyzes Hinglish grammatical markers (e.g., `chahiye`, `milega`, `karo`, `hai`, `kisi`, `apna`, `bina`).
- Emits structured `LanguageTag` (`EN`, `HI`, `HI_LATN`, `MIXED`, `UNKNOWN`) and fractional script distribution.

### 3.2 Devanagari Unicode Normalization
- **NFKC Normalization:** Canonical decomposition followed by canonical composition to standardize glyph representations.
- **Nukta Folding:** Folded to base characters (`क़` -> `क`, `फ़` -> `फ`, `ज़` -> `ज`, `ड़` -> `ड`, `ढ़` -> `ढ`, `य़` -> `य`), resolving colloquial keyboard variations without altering semantic content.
- **Danda Punctuation:** Replaces Devanagari single danda (`।`) and double danda (`॥`) with standard sentence-terminating periods.
- **Zero-Width Character Cleanup:** Strips zero-width joiners (`\u200D`) and non-joiners (`\u200C`) that bad actors use for algorithmic evasion.

### 3.3 Hinglish Phonetic Normalization
- **Repetition Collapse:** Collapses 3+ identical consecutive characters (`kattaaaaa` -> `katta`, `tamanchaaaa` -> `tamancha`, `farziii` -> `farzi`).
- **Phonetic Alias Registry:** Deterministic lookup mapping common spelling variants to canonical stems:
  - `nakalee` / `nakly` -> `nakli`
  - `farjee` / `farji` -> `farzi`
  - `jaali` -> `jali`
  - `dastavej` -> `dastavez`
  - `tamanchaa` -> `tamancha`
  - `banduk` / `bandooq` -> `bandook`
  - `hatiyar` / `hathyar` -> `hathiyar`
  - `aslah` -> `asla`
  - `gaavti katta` -> `gavti katta`
  - `chaalu sim` -> `chalu sim`

---

## 4. Detection Engine Architectural Enhancements

### 4.1 Unicode Token Boundaries
Standard ASCII regex `\b` fails on Devanagari script transitions. The engine employs Unicode-aware lookbehind and lookahead patterns:
```python
pattern = re.compile(rf"(?i)(?<![\u0900-\u097F\w]){re.escape(term_str)}(?![\u0900-\u097F\w])")
```
This guarantees exact-token matching for both English, Hinglish, and native Devanagari without false substring triggers.

### 4.2 Concept-Level Deduplication
When a suspicious advertisement repeats multiple surface forms of the same concept (e.g. `desi katta`, `tamancha`, `कट्टा`, `देसी कट्टा`), scoring each surface form individually squanders calibration and inflates false alarms.
- **Mechanism:** All matched terms are preserved in `ScoreResult.matched_terms` for complete legal explainability and audit trail.
- **Scoring:** The base concept weight is added exactly **once** per canonical concept cluster (e.g. `country_pistol`, `firearm_rifle`, `fake_aadhar`, `mule_account`).

### 4.3 Double Multiplier Bug Fix
- **Root Cause:** Previous revisions applied `category["weight_multiplier"]` during regex compilation in `_compile_patterns()`, and then multiplied `cat_raw_score * multiplier` again in `score()`, squaring the multiplier.
- **Resolution:** Base weights are compiled without multiplying by the category multiplier. The multiplier is applied exactly once in `cat_weighted_score = cat_raw_score * multiplier`.

### 4.4 Public Awareness & Advisory False-Positive Suppression
Legitimate cyber police advisories, bank warnings, and public awareness messages frequently contain illegal trade keywords (e.g., *"सावधान रहें: कभी किसी को अपना बैंक खाता या OTP शेयर न करें। साइबर हेल्पलाइन 1930"*).
- The engine checks `check_awareness_context(text)` against curated English, Hindi, and Hinglish public advisory markers.
- If verified as an official advisory:
  - Risk level is suppressed to `Clean` or `Low`.
  - `is_actionable` is set to `False`.
  - Forensic explainability clearly states: *"Classified as Clean: Legitimate advisory/notice disclaimers detected."*

---

## 5. Model Evaluation & AI4Bharat IndicXlit Analysis

### 5.1 AI4Bharat IndicXlit Evaluation Summary
- **Capability:** Neural sequence-to-sequence transliteration across 22 Indic languages using heavy PyTorch models (~1.2 GB model weights, Fairseq compilation dependencies).
- **Architectural Trade-Off:**
  1. *Air-Gap / Offline Readiness:* Hackathon demonstration and secure deployment require deterministic, lightweight, zero-cloud execution with zero model-download failure risks.
  2. *Deterministic Integrity:* Neural transliteration models can hallucinate or alter non-standard slang terms (e.g. transforming `tamancha` or `315 bore piece` into unrelated phonetics).
  3. *Latency:* Neural inference adds 45–120ms per post; deterministic Unicode normalization and alias matching executes in <1.5ms per post.
- **Adopted Design:** Deterministic, curated Unicode normalization and phonetic alias mapping as the primary, air-gapped engine. Transliteration weights may be toggled as an optional secondary plugin where heavy GPU infrastructure is available.

---

## 6. Statutory Compliance & Evidence Integrity

- **Original Raw Text Preservation:** `posts.raw_text` is permanently stored unchanged to guarantee evidentiary integrity under Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA).
- **RFC-8785 Proof of Custody:** Cryptographic SHA-256 evidence blocks are calculated over canonicalized JSON containing the raw text and exact timestamps.
- **Statutory Disclaimer:**
  > *"A keyword match is a search result, not proof of wrongdoing. Context, provenance, integrity and independent verification are necessary before any legal or operational reliance."*
