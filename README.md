# TGSherlock OSINT Threat Intelligence & Cross-Channel Attribution Engine

An open-source intelligence (OSINT) and law-enforcement analytical platform designed to monitor **public Telegram channels** for illicit sales (narcotics, unlicensed firearms, forged documents, mule bank accounts, cloned ATM cards, and fake KYC SIM cards), attribute seller identifiers across disparate channels, detect coordinated spam/ad campaigns, and produce forensically verifiable evidence packages.

---

## Architecture Diagram

```text
                               +--------------------------------------------+
                               |     Public Telegram Network (Broadcast)    |
                               +--------------------------------------------+
                                      |                              |
               [Direct Live WebSocket / MTProto]        [Zero-Auth Web Preview t.me/s/]
                                      |                              |
                                      v                              v
                      +-------------------------------+  +-----------------------------+
                      |     TGSherlock Base Core      |  |    tgq-cli Discovery Engine  |
                      |  (Local Web Panel :8765)      |  | (Snowball Expansion d <= 2) |
                      +-------------------------------+  +-----------------------------+
                                      |                              |
                                      v                              v
                         ~/.local/share/tgsherlock/             watchlist.csv
                              (SQLite Database)                      |
                                      |                              |
                                      +--------------+---------------+
                                                     |
                                                     v
                                      +-------------------------------+
                                      |     addons/ Detection Suite   |
                                      +-------------------------------+
                                      | • extractors.py (UPI, Phone,  |
                                      |   IFSC, Crypto, Devanagari)   |
                                      | • lexicon.yaml (Slang Rules)  |
                                      | • scorer.py (Weighted Risk)   |
                                      | • evidence.py (RFC-8785 Hash) |
                                      | • importer.py (Multi-Platform)|
                                      +-------------------------------+
                                                     |
                                                     v
                                      +-------------------------------+
                                      | dashboard/ Streamlit Platform |
                                      +-------------------------------+
                                      | • Threat Radar & Alerts       |
                                      | • NetworkX + Plotly Link Graph|
                                      | • MinHash / pHash Ad Clusters |
                                      | • Forensics & Evidence Export |
                                      +-------------------------------+
```

---

## Core Capabilities

1. **Multi-Lingual Illicit Slang Scorer (`addons/lexicon.yaml`, `scorer.py`):**
   - 7 primary threat categories: `drugs`, `arms`, `fake_documents`, `bank_account`, `atm_card`, `sim_card`, `net_banking_kit`.
   - Multi-lingual terminology covering English, Hinglish, Marathi, coded words (`c0ke`, `420`, `315 piece`), and emoji indicators (`🍁`, `🔫`, `🪪`, `💳`, `🏦`).
   - Risk scoring with transparent explainability tags (`High`, `Medium`, `Low`).

2. **Specialized Financial & Contact Extractors (`addons/extractors.py`):**
   - **UPI IDs:** Pattern matching validated against an authoritative registry of real NPCI and bank PSP handles (`@okaxis`, `@ybl`, `@paytm`, `@oksbi`, etc.), strictly rejecting email domains (`gmail.com`, `yahoo.com`, `proton.me`).
   - **Indian Phone Numbers:** Formats for `+91`, 10-digit mobiles, and native **Devanagari numeral** normalization (`०१२३४५६७८९` → `0123456789`).
   - **Financial Codes & Wallets:** IFSC validation, Crypto wallets (BTC, ETH/EVM, TRX/TRC20, Solana), and `@usernames`.

3. **Forensic Chain of Custody (`addons/evidence.py`):**
   - Formulates RFC-8785 canonical JSON from `(channel, message_id, timestamp_utc, text)`.
   - Generates deterministic SHA-256 evidence digests and media hashes for tamper-proof judicial reporting.

4. **Link Analysis & Cross-Channel Attribution (`dashboard/graph.py`):**
   - Constructs interactive bipartite entity networks linking posts, channels, and identifiers.
   - Automatically detects and highlights cross-channel syndicates (actors operating in $\ge 2$ distinct channels).

5. **Coordinated Campaign & Repeated-Ad Detection (`dashboard/similarity.py`):**
   - **MinHash (datasketch):** Groups templated marketing copy and mule-recruitment spam broadcasted across disparate channels.
   - **Perceptual Hash (imagehash pHash):** Identifies near-duplicate promotional flyers, rate cards, and payment QR posters.

6. **Channel Discovery & Snowball Expansion (`discovery/finder.py`):**
   - Uses `tgq-cli` to inspect public web previews (`t.me/s/`) without requiring an active account or credentials.
   - Performs snowball expansion (depth $\le 2$) via forward origins (`fwd_from`) to map out criminal affiliate networks and generate ranked `watchlist.csv`.

---

## Quickstart & Run Instructions (Windows PowerShell)

### 1. Prerequisites
- Python 3.11+ (Python 3.15 installed)
- PowerShell 5.1+

### 2. Environment Setup
```powershell
# Create and activate virtual environment
python -m venv .venv

# Install dependencies (already installed in workspace)
.\.venv\Scripts\python.exe -m pip install -e tgsherlock
.\.venv\Scripts\python.exe -m pip install pyyaml pytest streamlit networkx plotly datasketch imagehash pillow pandas tgq-cli
```

### 3. Start TGSherlock Core Server
Runs the local base monitoring panel:
```powershell
.\.venv\Scripts\python.exe -m tgsherlock --no-browser --port 8765
```
Access at: `http://127.0.0.1:8765`

### 4. Launch the Streamlit OSINT Analytics Dashboard
Launches the full link analysis, threat radar, and graph dashboard:
```powershell
.\.venv\Scripts\streamlit.exe run dashboard/app.py
```
Access at: `http://localhost:8501`

### 5. Run Automated Channel Discovery (Snowball Expansion)
Discovers public illicit channels and generates a ranked `watchlist.csv`:
```powershell
.\.venv\Scripts\python.exe discovery/finder.py
```

### 6. Run the Verification Test Suite
Execute the full 23-test unit test suite covering extractors, scorer, evidence hashing, graph construction, and discovery:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 3-Minute Hackathon Demo Script (Pitch & Presentation)

### [0:00 - 0:45] The Problem & The Solution
> *"Judges, cyber-enabled financial fraud in India is fueled by an underground ecosystem on Telegram: mule bank accounts for rent, fake KYC SIM cards, forged Aadhar biometric bypasses, and illicit arms. Because these channels are fragmented, criminals believe they are anonymous. Today, we present our OSINT Threat Intelligence & Cross-Channel Attribution Engine. We monitor strictly public broadcast channels, ingest seller identifiers, and link their operations across the entire network."*

### [0:45 - 1:30] Live Threat Radar & Identifier Extraction
- Open **Tab 1: Live Threat Alerts & Evidence** (`http://localhost:8501`).
- Point out the metrics: Flagged posts, High-risk alerts, Cross-channel syndicates, and Coordinated ad campaigns.
- Show an alert card (e.g. Current account mule recruitment):
  > *"Notice how our engine extracts verified UPI IDs like `demo.seller@ybl` while cleanly rejecting email domains like `gmail.com`. It also decodes Devanagari numerals in Marathi and Hindi WhatsApp numbers, scores the post as HIGH RISK based on multi-lingual slang, and creates an immutable SHA-256 evidence digest for law enforcement evidence submission."*

### [1:30 - 2:15] Cross-Channel Attribution Network Graph
- Switch to **Tab 2: Entity Link Analysis (Graph)**.
- Point out the interactive Plotly network:
  > *"Here is the crown jewel of our system: Cross-Channel Attribution. Individual posts appear disconnected on Telegram. But when we map the graph, the red alert node immediately reveals that `demo.seller@ybl` and phone `+91 90000 00000` are operating simultaneously across 'Public Deals Hub', 'Dark Deals All India', and 'Crypto P2P Cashout Network'. In one click, an investigator can see the entire syndicate hierarchy."*

### [2:15 - 2:45] Coordinated Campaigns & Repeated Ads
- Switch to **Tab 3: Coordinated Campaigns**.
- Show the MinHash cluster:
  > *"Criminal syndicates use automated bots to blast templated ads across dozens of channels. Using MinHash LSH text similarity and pHash image duplicate grouping, our system clusters coordinated campaigns instantly, proving that multiple disparate channels belong to a single threat actor ring."*

### [2:45 - 3:00] Discovery & Admissible Evidence Export
- Switch to **Tab 4: Evidence Chain of Custody & Export**.
- Demonstrate the **Tamper Verification** button and one-click **Download Forensic JSON (RFC-8785)** / **HTML Dossier**.
  > *"Every flagged record is cryptographically verifiable and ready for court presentation. Combined with our `tgq-cli` snowball channel discovery, we provide law enforcement with an end-to-end, privacy-compliant intelligence pipeline. Thank you!"*

---

## Safety & Compliance
- **Public Channels Only:** Operates exclusively on publicly accessible broadcast channels and public web previews (`t.me/s/`). Never enumerates private groups or initiates contact.
- **Credential Hygiene:** API ID, hash, and Telegram session files are strictly isolated and ignored in `.gitignore`.
- **Demo Data:** All synthetic test data utilizes RFC-compliant demo placeholders (e.g. `demo.seller@ybl`, `90000 00000`).
- **No Model Training:** Uses rule-based scoring and statistical similarity algorithms; does not fine-tune or train models on Telegram data.
