<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,20,24&height=200&section=header&fontSize=0&animation=fadeIn" width="100%" />

<h1>OpenTerminal Order Flow Intelligence — Tradfye Terminal clone</h1>

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&duration=3500&pause=1000&color=00F5A0&center=true&vCenter=true&width=820&lines=All+market+data+is+real+and+live;No+mock+data%2C+no+fabricated+constants%2C+no+synthetic+candles;ALL+COMPLETE+%E2%80%94+Stages+0%E2%80%935+done" alt="Typing SVG" /></a>

<br/>

![Status](https://img.shields.io/badge/Status-ALL%20COMPLETE-00F5A0?style=for-the-badge)
![Stages](https://img.shields.io/badge/Stages-0%E2%80%935-8A2BE2?style=for-the-badge)
![TypeScript](https://img.shields.io/badge/TypeScript-0%20errors-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Build](https://img.shields.io/badge/Build-passes-2ea44f?style=for-the-badge)
![Data](https://img.shields.io/badge/Market%20data-real%20and%20live-FF3B3B?style=for-the-badge)
![Mock](https://img.shields.io/badge/mock%20data-0-success?style=for-the-badge)

![Binance](https://img.shields.io/badge/Binance-F0B90B?style=for-the-badge&logo=binance&logoColor=black)
![Bybit](https://img.shields.io/badge/Bybit-17181B?style=for-the-badge&logoColor=F7A600)
![Deribit](https://img.shields.io/badge/Deribit-0B0E11?style=for-the-badge)
![WebSocket](https://img.shields.io/badge/WebSocket-live-010101?style=for-the-badge&logo=socketdotio&logoColor=white)
![GitHub](https://img.shields.io/badge/pushed%20to-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaf49c.gif" width="100%">

> Production-quality read-only order flow intelligence module built into the existing OpenTerminal (quant-hub-008) application, reverse-engineered from Tradfye Terminal (tradfye.com/terminal) using REA methodology. **All market data is real and live** — no mock data, no fabricated constants, no synthetic candles.

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaf49c.gif" width="100%">

## 📡 Status

**ALL COMPLETE** — Stages 0–5 done, all hardcoded/mock data replaced with real APIs, live crypto candles via spot WebSocket, timeframe switching working, TypeScript: 0 errors, build passes, pushed to GitHub.

| Area | Status |
|------|--------|
| Order Flow Module (Stages 0–5) | ✅ Complete |
| Real-Data Waves 1–3 (11 fixes) | ✅ Complete — zero mock/hardcoded data |
| Live Crypto Candles (spot WS) | ✅ Working from India |
| Timeframe Switching (1m–1W) | ✅ All timeframes return correct data |
| Visual Polish (chart/heatmap/screener/ticker) | ✅ Professional appearance |
| Security Hardening | ✅ CORS allowlist, rate limiting, headers |
| Server-Side Proxy (R08) | ✅ Built + verified; deploy to VPS for futures WS |
| TypeScript | ✅ 0 errors |
| Build | ✅ Passes |

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaf49c.gif" width="100%">

## ⚡ Features

All features use **real market data** from free public APIs. No mock data, no fabricated constants, no synthetic candles.

### 🧭 Order Flow Module (Stages 0–5)

| Feature | Description | File(s) |
|---------|-------------|---------|
| **Trade Tape** | Aggregated real-time trade stream; 500-trade buffer | `src/components/widgets/TradeTape.tsx` |
| **Order Book Ladder** | 20-level L2 depth visualization | `src/components/widgets/OrderBookLadder.tsx` |
| **Whale Tracker** | Detects orders ≥ **,000** notional | `src/components/widgets/WhaleFeed.tsx` |
| **Liquidation Feed** | Real-time liquidation events; 10,000-event buffer | `src/components/widgets/LiquidationFeed.tsx` |
| **Heatmap** | Resting L2 liquidity heatmap; 500ms cadence; 1440-column buffer | `HeatmapWidget.tsx`, `HeatmapCanvas.tsx` |
| **Footprint Chart** | Volume-at-price per bar with bid/ask delta; 2.0× imbalance | `FootprintCanvas.tsx` |
| **CVD / VWAP** | Cumulative Volume Delta & Volume-Weighted Average Price | `orderFlowService.ts` |
| **Decision Panel** | **9 signals**, **101 total weight** scoring (including real value signal via VAH/VAL) | `DecisionPanel.tsx` |
| **Market Regime Badge** | range / unclear / trend / volatile | `RegimeBadge.tsx` |
| **Danger Meter** | CALM / ELEVATED / HIGH (VPIN + liq velocity) | `DangerMeter.tsx` |
| **Futures Context Panel** | Funding rate, **real open interest** (Binance fapi), mark price | `FuturesContextPanel.tsx` |
| **FeedStatusBadge** | 8 connection states | `FeedStatusBadge.tsx` |
| **GEX Panel** | Flip level, **correct call/put walls**, max pain | `GEXPanel.tsx` |
| **Options Chain** | **Real Deribit options** (964 rows), expiry filter, IV/OI color coding | `OptionsChain.tsx` |
| **Bybit Fallback Adapter** | Delta orderbook, auto-failover | `BybitLinearAdapter.ts` |
| **Gamma Exposure Service** | Deribit fetch + 5s poll | `gammaExposureService.ts` |
| **Cross-Exchange Spread** | Binance vs Bybit bp spread | `CrossExchangeSpread.tsx` |
| **OHLCV Chart** | lightweight-charts candlestick + VWAP + CVD | `OHLCVChart.tsx` |

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaf49c.gif" width="100%">

### 🔄 Real-Data Improvements (Waves 1–3)

All hardcoded/mock/synthetic data replaced with real API calls:

| What | Before (mock) | After (real) | Data Source |
|------|--------------|--------------|-------------|
| **Open Interest** | Hardcoded |

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,20,24&height=120&section=footer" width="100%" /># 🛡️ telegram-osint-monitor-08: OSINT Threat Intelligence Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![RFC-8785](https://img.shields.io/badge/Evidence-RFC--8785%20SHA--256-green.svg)](https://datatracker.ietf.org/doc/html/rfc8785)

An air-gapped open-source intelligence (OSINT) and law-enforcement analytical platform designed to monitor **public Telegram channels** for illicit Indian cybercrime trades—specifically mule bank accounts, unlicensed firearms, forged documents, fake KYC SIM cards, and narcotics.

telegram-osint-monitor-08 correlates seller payment handles across disparate channels, clusters coordinated ad campaigns, and generates cryptographically sealed evidence packages prepared to support Section 63 Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023) certificates.

---

## ⚡ 5-Minute Setup on a Fresh Machine

Follow these step-by-step instructions to get telegram-osint-monitor-08 running from scratch in under 5 minutes:

### 1. Prerequisites
- **Python 3.10 to 3.15** installed on your system ([Download Python](https://www.python.org/downloads/))
- **Git** installed ([Download Git](https://git-scm.com/))
- *(Optional)* [Google Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) for multilingual image extraction (English, Hindi, Marathi). If not installed, the platform honestly marks image OCR as `OCR DISABLED` with zero fake fallbacks.

### 2. Clone Repository
```bash
git clone https://github.com/ajinkyachalke008/telegram-osint-monitor-08.git
cd telegram-osint-monitor-08
```

### 3. Create & Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux / macOS (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
# Core pipeline & dashboard (lightweight, zero PyTorch/CUDA needed, ultra-fast 1.67ms TF-IDF inference):
pip install -r requirements.txt

# (Optional) Multilingual neural sentence embeddings:
# pip install -r requirements-embeddings.txt
# Note: First-run loading of embeddings will download paraphrase-multilingual-MiniLM-L12-v2 (~470 MB) from HuggingFace Hub.
```

### 5. Launch One-Command Demo
Run the automated launcher:
```bash
python scripts/run_demo.py
```
*(On Windows, you can also simply run `scripts\run_demo.bat` or `.\scripts\run_demo.ps1`; on Linux/macOS run `./scripts/run_demo`)*

**What this command does automatically:**
1. Resets and initializes the SQLite database at `data/osint_monitor.db`
2. Seeds baseline demonstration records with RFC-8785 SHA-256 evidence blocks
3. Spawns a background streaming replay worker injecting simulated posts every ~5s
4. Spawns the Streamlit OSINT Dashboard on `http://localhost:8501`
5. Automatically opens your default web browser to the dashboard

---

## 🧪 Verification & Testing Commands

To verify system integrity and evidentiary proofs:

### 1. Run Complete Test Suite (61+ Tests)
```bash
python -m pytest -v
```
Verifies UPI extraction, Devanagari digit normalization, RFC-8785 canonical JSON hashing, channel-handle exclusion, PDF generation, and the zero-retraining lexicon feedback loop.

### 2. Verify Single Post End-to-End Forensic Trace
```bash
python scripts/verify_flow_proof.py
```
Follows post `telegram_t.me/delhi_classifieds_demo_1001` containing `mule.syndicate@ybl` through:
- Ingestion & Text Normalization
- Category & Risk Scoring (`bank_account` / `High`)
- Extracted Identifiers (Channel handle excluded)
- RFC-8785 SHA-256 Seal Validation (Block #1)
- Multi-Channel Link Graph proving the UPI operates across **3 public channels**

### 3. Run Streamlit Page Verification (AppTest)
```bash
python scripts/verify_streamlit_pages.py
```
Validates that all 10 dashboard pages initialize with 0 runtime exceptions.

---

## 🧭 System Architecture & Demonstration Tour

```text
[Public Telegram Broadcast Feeds / CSV-JSON Ingest / Demo Replay Stream]
                               │
                               ▼
    1. Text Normalization (NFKC, Homoglyphs, Leetspeak, Devanagari Digits)
                               │
                               ▼
    2. Hybrid Classifier (TF-IDF Default / MiniLM Embeddings + Hard-Negative Calibrator)
                               │
                               ▼
    3. Financial-Ad Detector (Mule Recruitment Intent, Instruments, Text Offsets)
                               │
                               ▼
    4. Actionable Extractor (UPI, Phones, Base58Check Wallets, IFSC, Usernames)
       *Strict Guard: Channel handle is never treated as a seller identifier*
                               │
                               ▼
    5. Evidence Chain Ledger (RFC-8785 Canonical JSON + Sequential SHA-256 Hashing)
                               │
                               ▼
    6. Multi-Relational Graph & Link Analysis (NetworkX Cross-Channel Bipartite Graph)
                               │
                               ▼
    7. Multi-Page Streamlit Intelligence Dashboard (Triage, Dossiers, Section 63 BSA PDF)
```

### Guided 6-Step Demonstration Workflow
Follow this sequential path through the web interface (`http://localhost:8501`):
1. **`1_🚨_Live_Alerts`:** Live streaming feed auto-refreshing every 5s with new-alert toasts, risk badges, and analyst triage.
2. **`2_🔍_Alert_Detail`:** Cryptographic ledger inspection, live hash seal verification, and Section 63 BSA 2023 evidence package export.
3. **`3_🕸️_Entity_Graph`:** Interactive bipartite network graph showing how `mule.syndicate@ybl` links 3 distinct public broadcast channels.
4. **`4_🔁_Coordinated_Campaigns`:** MinHash Jaccard clustering identifying copy-pasted ad marketing templates.
5. **`5_🗺️_Geographic_Map`:** Spatial threat map analyzing extracted regional cybercrime hotspots (Mewat, Jamtara, Delhi, Mumbai).
6. **`8_⚖️_Responsible_Use_and_Audit` & `9_🔭_Channel_Discovery`:** Analyst lexicon feedback loop (weight adjustment without ML retraining) and snowball discovery of public feeds.

---

## 📡 Data Provenance Classification Standards

Every feature and dataset in telegram-osint-monitor-08 is strictly tagged with one of four provenance levels:

| Provenance Label | Scope & Operational Boundary | Air-Gap & Compliance Rule |
| :--- | :--- | :--- |
| **`VERIFIED-SYNTHETIC`** | Automated synthetic benchmark records (450 held-out test rows, demo seed datasets) | Validated against regex extractors, classifier pipeline, and SHA-256 ledger. |
| **`IMPORTED`** | Offline investigator imports (CSV, JSON, sample police cybercell batches) | Read-only ingest; raw records preserved with cryptographic sealing. |
| **`UNVERIFIED`** | Telegram Web Preview Poller, telegram-osint-monitor-08 Daemon Intake, and Discovery Snowball Watchlist | Air-gap unverified; requires external live connection or active user session. |
| **`LIVE`** | Unauthenticated Telegram web previews or daemon sessions *only when live verified on host* | Strict public broadcast feeds only; zero channel joining or infiltration. |

---

## ⚖️ Legal & Compliance Disclosures

1. **Section 63 Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023):**
   Section 63 requires a certificate (signed by the responsible person and an expert) with a hash value; anchoring the chain head outside the DB is recommended practice, not a statutory requirement; consult legal counsel.
2. **Public Broadcast Feeds Only:**
   The system never infiltrates private channels, private groups, or encrypted 1-on-1 chats. Zero interactive behavior (no posting, reactions, DMs, or member enumeration).
3. **Investigative Leads, Not Courtroom Proof:**
   Algorithmic classifications and link graphs represent investigative intelligence leads to assist sworn cybercell officers, not autonomous courtroom proof.
4. **Zero Retraining on Telegram Data:**
   In compliance with Telegram API terms, zero models were trained on collected posts. The analyst feedback loop modifies rule weights in YAML only.

---

## 📚 Essential Documentation

- [**docs/DEMO_SCRIPT.md**](docs/DEMO_SCRIPT.md): Complete 4-minute evaluation script with exact clicks and talking points.
- [**docs/LIMITATIONS.md**](docs/LIMITATIONS.md): Intentional design boundaries, synthetic metrics, and external anchor requirements.
- [**docs/METRICS.md**](docs/METRICS.md): Side-by-side performance comparison of Model A (TF-IDF) vs Model B (MiniLM-L12).
- [**docs/TRACEABILITY.md**](docs/TRACEABILITY.md): Verification matrix mapping technical components to requirements R1 through R5.
- [**docs/JUDGES_QA.md**](docs/JUDGES_QA.md): Comprehensive answers to frequently asked technical and legal evaluation questions.
