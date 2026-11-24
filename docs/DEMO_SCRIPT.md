# TGSherlock OSINT Threat Intelligence - 4-Minute Demonstration Script

This script provides an exact, minute-by-minute walkthrough designed for hackathon judges and law enforcement evaluators.

---

## Evaluation Summary
- **Total Duration:** 4 Minutes (240 Seconds)
- **Start Command:** Run `python scripts/run_demo.py` (or `./scripts/run_demo` / `scripts\run_demo.bat`)
- **Dashboard URL:** `http://localhost:8501`
- **Key Message:** Public broadcast monitoring only, zero channel joining, leads not proof, and Section 63 BSA 2023 evidence generation.

---

## Minute-by-Minute Walkthrough

### ⏱️ Minute 0:00 – 0:45 | Home Overview & 6-Step Tour
- **Where to Click:** Land on `http://localhost:8501` (Home Overview).
- **What to Observe:**
  - Notice the **Data Provenance Banner** at the top (`VERIFIED-SYNTHETIC` active stream, `LIVE` web previews, `IMPORTED` dumps, `UNVERIFIED` candidate feeds).
  - Observe the top 5 KPI cards: Total Posts, Actionable Threats (High), Extracted Identifiers, Cross-Channel Syndicates, Sealed Evidence Blocks.
  - Inspect the **Ledger Chain-Head Hash** box showing the latest SHA-256 digest (`Block #12`).
  - Point out the **"Reset Demo State"** button in the left sidebar (allows judges to wipe and reseed the demonstration instantly).
- **Talking Points:**
  > *"TGSherlock is a dedicated OSINT engine for detecting illicit Indian cybercrime trades—specifically mule bank accounts, unlicensed weapons, fake KYC credentials, and contraband. We operate exclusively on public broadcast channels with zero channel joining, and every post is cryptographically sealed for judicial admissibility."*

---

### ⏱️ Minute 0:45 – 1:30 | Step 1: Live Threat Alerts (`1_🚨_Live_Alerts.py`)
- **Where to Click:** In the sidebar or 6-Step Tour on Home, click **"1_🚨_Live_Alerts"**.
- **What to Observe:**
  - The page displays incoming alerts ranked by risk level (`[HIGH]` in neon red, `[MEDIUM]` in gold).
  - Observe the auto-refresh fragment: every 5 seconds, the background replay worker injects simulated posts. When an alert arrives, a toast notification pops up: `🚨 New threat alert received!`.
  - Look at the entity pill badges: notice extracted UPI IDs (e.g., `mule.syndicate@ybl 🚨(2+ Chans)`), Indian phone numbers (`+919876543210`), and usernames (`@fast_cash_hub`).
  - Notice the channel's own handle is excluded from seller identifiers.
- **What to Click:** Expand **"⚙️ Triage & Analyst Action for Alert"**:
  - Change status from `new` to `confirmed`.
  - Enter Analyst Note: `"Verified mule recruiter linked to Delhi classifieds."`
  - Click **"Save Verdict"** -> page updates and writes an immutable audit record.
- **Talking Points:**
  > *"Live alerts stream directly into analyst triage cards. The system extracts financial payment handles (UPI, IFSC, crypto) and phone numbers, normalizing Devanagari numerals. When an actor appears in multiple channels, the system automatically flags them with a cross-channel syndicate badge."*

---

### ⏱️ Minute 1:30 – 2:15 | Step 2: Evidence Seal & Section 63 BSA 2023 Dossier (`2_🔍_Alert_Detail.py`)
- **Where to Click:** In the sidebar, click **"2_🔍_Alert_Detail"**.
- **What to Select:** In the dropdown, select the alert containing `mule.syndicate@ybl` (`delhi_classifieds_demo`).
- **What to Observe:**
  - **Left Column:** Shows the raw post text, metadata, and the **Financial Ad Analysis** flagging `MULE RECRUITMENT PATTERN DETECTED` with character offsets.
  - **Image OCR Capability Status:** Honestly shows `OCR DISABLED` because the host environment does not have the external Google Tesseract binary installed. Highlight that we never fake OCR outputs.
  - **Right Column:** Shows RFC-8785 Canonical JSON, Previous Hash, and Current Hash.
- **What to Click:** Click **"🛡️ Verify Cryptographic Seal Live"**:
  - Green banner appears: `✅ EVIDENCE VERIFIED: SHA-256 seal matches exactly. Block #1 is tamper-evident and chained to parent.`
- **What to Click:** Click **"📥 Export Section 63 BSA 2023 Evidence Package (PDF)"**:
  - Open or view the generated PDF. Point out the statutory notice:
    > *"Evidence package prepared to support a Section 63 BSA 2023 certificate (must be signed by the responsible person and an expert). Not legal advice."*
  - Point out the Chain-Head Hash and RFC-8785 JSON table embedded inside the PDF.

---

### ⏱️ Minute 2:15 – 3:00 | Step 3 & 4: Syndicate Link Analysis & Coordinated Campaigns
- **Where to Click:** In the sidebar, click **"3_🕸️_Entity_Graph"**.
- **What to Observe:**
  - Interactive multi-relational network graph.
  - Trace the central red node: `mule.syndicate@ybl`.
  - Notice it connects across **3 distinct public broadcast channels**:
    1. `t.me/delhi_classifieds_demo`
    2. `t.me/mumbai_trade_network`
    3. `t.me/mule_accounts_market`
  - The channel handles are blue broadcast nodes, not misclassified as sellers.
- **Where to Click:** In the sidebar, click **"4_🔁_Coordinated_Campaigns"**.
- **What to Observe:**
  - MinHash Jaccard similarity groups near-duplicate marketing templates broadcast simultaneously across different channels.
- **Talking Points:**
  > *"Criminal syndicates rarely restrict operations to a single channel. By correlating extracted payment handles and running MinHash clustering on ad copy, TGSherlock links disparate channels into a single unified syndicate dossier."*

---

### ⏱️ Minute 3:00 – 3:30 | Step 5 & 6: Multi-Platform Data Ingestion (`6_📁_Data_Ingestion.py`)
- **Where to Click:** In the sidebar, click **"6_📁_Data_Ingestion"**.
- **What to Click:** Click **"Browse files"** and select `sample_data/demo_import.csv` (or `sample_data/demo_import.json`).
- **What to Observe:**
  - The upload preview displays columns: `platform`, `source`, `post_id`, `timestamp`, `text`.
  - Column mappings auto-populate correctly.
- **What to Click:** Click **"🚀 Ingest into Unified Database & Pipeline"**:
  - Success message and balloons appear!
  - 4 new threat records are ingested, normalized, scored, and sealed in SQLite.
- **What to Verify:** Click back to **"1_🚨_Live_Alerts"**:
  - The newly imported posts (corporate bank accounts, Delhi arms deals) now appear in the Live Alerts triage feed with `[IMPORTED]` badges.

---

### ⏱️ Minute 3:30 – 4:00 | Step 7: Responsible Use & Model Benchmarks (`8_⚖️` & `7_📈`)
- **Where to Click:** In the sidebar, click **"8_⚖️_Responsible_Use_and_Audit"**.
- **What to Observe:**
  - **Analyst Lexicon Feedback Loop:** Select `drugs`, term `maal`, change weight from `5.0` to `7.5`, enter analyst ID, and click "Submit Feedback Weight Adjustment".
  - Weight updates immediately in `lexicon_feedback.yaml` with **ZERO model retraining on Telegram data**.
  - Show the permanent audit table below recording all analyst actions.
- **Where to Click:** Click **"7_📈_Model_Metrics"**.
- **What to Observe:**
  - Highlights Model A (TF-IDF: 95.56% accuracy, 1.67 ms latency) as the active production default.
  - Shows Model B (MiniLM-L12: 94.89% accuracy, 32.67 ms latency).
  - Explicit disclosure: Embeddings are not claimed to be better unless verified on human-written data.
  - Points out that `data/test_human_written.jsonl` contains 40 placeholder rows ready for judge/user verification.
- **Conclusion:**
  > *"TGSherlock combines strict legal compliance, zero channel infiltration, and cryptographic chain-of-custody to deliver actionable cybercrime intelligence for Indian law enforcement."*
