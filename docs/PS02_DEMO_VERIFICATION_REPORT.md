# PS02 Hackathon Demonstration Verification Report

**Project:** Telegram OSINT Monitor & Cybercrime Evidence Suite
**Dataset Source:** Rajasthan Police Hackathon 2026 Committee Participant Archive (`PS02_demo_data.zip`)
**Verification Date:** 2026-11-28
**Live Application URL:** `http://localhost:8501` (Dataset Insights: `http://localhost:8501/PS02_Dataset_Insights`)
**Backend API Suite:** `http://localhost:8000`

---

## 1. Committee Archive Structural Validation

The official committee archive located at `data/participant_input/PS02_demo_data.zip` was subjected to rigorous structural preflight analysis via `ps02_dataset/preflight.py`:

- **Archive Integrity:** Validated ZIP structure; zero corrupted members.
- **Entry Limits & Bounds:** 318 entries inspected in-place; within `MAX_ENTRIES` (20,000) and uncompressed size bound (1 GB).
- **Directory Traversal Protection:** All archive member paths validated against directory traversal (`..`) and absolute path injection.
- **Folder Discovery:** Automatically discovered all 4 required directories (`01_telegram_exports`, `02_social_media`, `03_images`, `04_lexicon`).

### Recomputed Exact Record Totals
| Metric | Count | Validation Status |
| :--- | :---: | :--- |
| **Telegram JSON Exports** | 13 | Verified across 13 distinct channel folders |
| **Telegram Messages** | 1,500 | Verified (content messages only) |
| **Telegram Service Records** | 13 | Verified (isolated from message stream) |
| **Telegram Photo References** | 199 | Verified (199 found in archive, 0 missing) |
| **Telegram Empty-Text Records** | 63 | Verified (photo/media only records) |
| **Telegram Forwarded Records** | 42 | Verified |
| **Telegram Edited Records** | 40 | Verified |
| **Social Media Posts (CSV)** | 350 | Verified across 5 platforms |
| — Instagram Posts | 126 | Verified |
| — Facebook Posts | 88 | Verified |
| — ShareChat Posts | 52 | Verified |
| — X (Twitter) Posts | 48 | Verified |
| — YouTube Comment Posts | 36 | Verified |
| **Social Media Images** | 92 | Verified (92 found in archive, 0 missing) |
| **Poster Image Files** | 18 | Verified (P01.jpg through P18.jpg) |
| **Poster SHA-256 Hashes** | 18 / 18 | Exact byte match against supplied index |
| **Starter Lexicon Terms** | 37 | Verified (Drugs: 18, Arms: 7, Mule: 6, SIM: 3, Docs: 2, ATM: 1) |
| **Combined Content Records** | 1,850 | 1,500 Telegram + 350 Social Posts |
| **Total Archive Records** | 1,863 | 1,850 Content + 13 Service Records |

---

## 2. Dry-Run & Import Execution Results

Execution verified using `ps02_dataset/importer.py` against isolated SQLite storage:

```
[DRY-RUN EXECUTION]
Mode: dry_run
Database Writes: 0
Combined Records Preview: 1,850
Preflight Gate: PASSED (Zero errors, zero warnings)

[EXPLICIT IMPORT 1]
Status: imported
Batch Identifier: BATCH-PS02-c0736ba6-20261128_092902
Records Persisted: 1,850
Database Target: data/participant_dataset.db (Isolated SQLite)
Legacy Database Mutation: NONE (data/osint_monitor.db untouched)

[IDEMPOTENT REPEAT IMPORT 2]
Status: already_imported
Duplicate Flag: True
Records Inserted: 0
Integrity Result: Perfect idempotency; zero duplicate record inflation.
```

---

## 3. Real Keyword Search Demonstrations

Demonstrated live on the actual committee dataset in Tab 6 of `10_📊_PS02_Dataset_Insights.py`:

### Demonstration A: Identity Document Inquiry (`aadhaar`)
- **Query Term:** `aadhaar` (Category: `identity_document`)
- **Mode:** Broad Search
- **Total Hits:** 81 matches across Telegram exports
- **Sample Record:**
  - **Source:** Telegram (`ch04_PVC_Print_Hub_All_Documents`)
  - **Channel Title:** `PVC Print Hub - All Documents`
  - **Timestamp:** `2026-10-11 22:01:06 IST`
  - **In-Memory Attachment:** `photos/photo_50@11-10-2026_22-01-06.jpg` (22,994 bytes loaded from ZIP)
  - **PII Scrubbing:** Phone numbers scrubbed to `[REDACTED_PHONE]`; payment handles scrubbed to `[REDACTED_PAYMENT_ID]`
  - **Legal Badge:** Statutory disclaimer displayed above result card.

### Demonstration B: Neutral Weapon Reference (`desi katta`)
- **Query Term:** `"desi katta"` (Category: `weapons_firearm_context`)
- **Mode:** Exact Phrase Search
- **Total Hits:** 14 matches across Instagram and Telegram
- **Sample Record:**
  - **Source:** Telegram (`ch03_RJ_Desi_Tools_Store`)
  - **Channel Title:** `RJ Desi Tools Store`
  - **Timestamp:** `2026-09-07 00:04:17 IST`
  - **Classification:** **`CONTEXT ONLY`** (0 automatic threat score)
  - **In-Memory Attachment:** `photos/photo_8@07-09-2026_00-04-17.jpg` (verified real archive bytes)
  - **Legal Badge:** Amber warning badge stating match is purely textual context.

---

## 4. Multi-Viewport Responsiveness Evidence

Verified via automated Playwright headless runner (`scripts/verify_four_viewports_playwright.py`):

| Viewport | Dimensions | Overflow Delta | Status | Screenshot Artifact |
| :--- | :---: | :---: | :---: | :--- |
| **Desktop** | 1920 × 1080 | 0 px | **PASS** | `docs/screenshots/viewport_desktop_1920x1080.png` |
| **Laptop** | 1366 × 768 | 0 px | **PASS** | `docs/screenshots/viewport_laptop_1366x768.png` |
| **Tablet** | 768 × 1024 | 0 px | **PASS** | `docs/screenshots/viewport_tablet_768x1024.png` |
| **Mobile** | 390 × 844 | 0 px | **PASS** | `docs/screenshots/viewport_mobile_390x844.png` |

---

## 5. Judge Demonstration Runbook (3–4 Minutes)

### Step 1: Launch Application Suite (0:00 - 0:30)
```powershell
# In PowerShell:
.venv\Scripts\python.exe scripts/run_demo.py --no-reset
```
- Open browser to `http://localhost:8501`.
- Explain the dual-track architecture: the existing application is preserved, while the PS02 committee dataset is processed in a dedicated, isolated workflow.

### Step 2: Open PS02 Dataset Insights (0:30 - 1:15)
- Navigate to **10. 📊 PS02 Dataset Insights** in the sidebar.
- Click **1. Run Preflight Audit** in Tab 1.
- Show live computed totals: 13 Telegram channels, 1,500 messages, 350 social posts, 18/18 verified poster SHA-256 hashes.
- Explain: counts are dynamically evaluated from archive bytes, not hardcoded.

### Step 3: Demonstrate Multi-Platform & Temporal Coverage (1:15 - 2:00)
- Review Tab 2 (Platform Analytics): Show 5-platform distribution (Instagram: 126, Facebook: 88, ShareChat: 52, X: 48, YouTube: 36).
- Review Tab 3 (Timeline & Distribution): Show hourly distribution in Indian Standard Time (IST, UTC+05:30).

### Step 4: Live Keyword Explorer & In-Memory Previews (2:00 - 3:00)
- Switch to **Tab 6: 🔎 PS02 Keyword Explorer (10 Categories)**.
- Point to the statutory evidentiary disclaimer banner.
- Click the rapid preset chip `desi katta` or `aadhaar`.
- Show:
  1. Exact matched token highlighted.
  2. Channel title and IST timestamp.
  3. Real attached photo rendered directly from in-memory archive bytes.
  4. Redacted contact handles (`[REDACTED_PHONE]`, `[REDACTED_PAYMENT_ID]`).
  5. `CONTEXT ONLY` label with zero automatic criminality score.

### Step 5: Show Existing Project Feature & Close (3:00 - 3:45)
- Navigate to **2. 🔍 Alert Detail** or **3. 🕸️ Entity Graph**.
- Show the RFC-8785 tamper-evident SHA-256 seal verification.
- Point out the provenance banner clearly labelling legacy demo records as synthetic demo data.
- Emphasize compliance with Section 63 BSA and strict local data privacy.

---

## 6. Fallback Procedures

1. **Missing Archive File:**
   - If `data/participant_input/PS02_demo_data.zip` is moved or missing, the UI gracefully displays an alert instructing the operator to place the archive in `data/participant_input/`.
   - The operator can seamlessly demonstrate the existing application features (Alert Detail, Entity Graph, Coordinated Campaigns) which operate independently on `data/demo.db`.
2. **Missing Local Tesseract OCR:**
   - OCR falls back safely to heuristic text extraction without raising unhandled exceptions.
3. **Port Conflicts:**
   - If port 8501 is busy, start with `--server.port 8502`.
