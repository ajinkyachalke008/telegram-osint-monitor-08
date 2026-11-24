# System Limitations, Operational Boundaries & Legal Disclosures

This document details the intentional design limitations, data boundaries, and technical caveats of the telegram-osint-monitor-08 Threat Intelligence Platform.

---

## 1. Synthetic Metrics & Benchmark Scope
- **Synthetic Training Data:** In strict compliance with the Telegram API Terms of Service, **ZERO machine learning models were trained, fine-tuned, or calibrated on collected Telegram data**. Training was conducted strictly on synthetic JSONL datasets (`data/train_synthetic.jsonl`).
- **Benchmark Generalization:** The performance metrics presented in `docs/METRICS.md` (95.56% accuracy for TF-IDF + Logistic Regression, 94.89% for Multilingual MiniLM-L12) were computed on a held-out novel template split (`data/test_heldout_novel_templates.jsonl`). While designed to test out-of-distribution regional phrasing, spelling variants, and leetspeak, they remain synthetic benchmarks.
- **Human-Written Ground Truth:** The file `data/test_human_written.jsonl` contains 40 placeholder rows awaiting ground-truth manual population. Model generalization on wild human-written posts cannot be definitively proven until this test set is filled and evaluated.
- **Model Choice Grounding:** Model A (TF-IDF) is designated as the active pipeline default due to higher accuracy (95.56% vs 94.89%) and 19.5x lower inference latency (1.67 ms vs 32.67 ms). Embeddings will only be made default if empirical evaluation on populated human-written records proves superior generalization.

---

## 2. Unproven Live Operational Components
- **Public Web Previews (`t.me/s/*`):** The zero-authentication scraper relies on Telegram's public web preview endpoint. In live continuous production, this endpoint is subject to Telegram rate-limiting, IP-based Cloudflare challenges, and network-level blocking.
- **External Client Daemons:** The upstream daemon database (`~/.local/share/tgsherlock/accounts/*/tgsherlock.db` or external Telegram client) is an upstream client intake feed. In air-gapped or fresh test environments where no Telegram account is signed in, this feed produces zero posts, and the system relies on replay and imported streams.
- **No Direct Message (DM) Attribution:** The system captures public broadcast posts only. Discussions that transition into private 1-on-1 chats ("DM for price", "Ping secret chat") cannot be monitored or verified by this system.

---

## 3. Public Broadcast Channels Only (Zero Channel Joining)
- **Strict Infiltration Ban:** The system never executes channel join requests, never accepts private invite links (`t.me/+*`), and never infiltrates closed or private groups.
- **Zero Interactive Behavior:** The engine never posts messages, reacts with emojis, sends direct messages, or enumerates channel subscriber lists.
- **Public Domain Boundaries:** Monitoring is restricted strictly to content published openly to the public domain without access credentials.

---

## 4. Investigative Leads, Not Courtroom Proof
- **No Autonomous Convictions:** All algorithmic outputs—including threat classifications, risk scores, MinHash campaign clusters, and entity graphs—constitute **investigative intelligence leads** for human review, not automated judicial proof.
- **Sworn Analyst Prerequisite:** Under Indian legal standards, algorithmic flags must be reviewed, corroborated, and affirmed by a certified cybercell investigator before initiating coercive measures, account freezes, or formal FIR filings.
- **Potential for False Identifiers:** Fraudsters frequently post public complaints containing the UPI handles or phone numbers of victims or competitors to trigger harassment or retaliatory freezes. Automated extraction alone does not prove the account holder is the perpetrator.

---

## 5. Evidence Hash Chain & Section 63 BSA 2023 Statutory Requirements
- **Local Ledger Tamper-Evidence:** The internal SQLite hash chain (`evidence` table) computes RFC-8785 canonical JSON and SHA-256 digests chained sequentially (`prev_hash`). This guarantees internal chronological consistency and detects post-hoc database tampering.
- **Section 63 BSA 2023 Certification:** Section 63 requires a certificate (signed by the responsible person and an expert) with a hash value; anchoring the chain head outside the DB is recommended practice, not a statutory requirement; consult legal counsel.

---

## 6. Optical Character Recognition (OCR) Engine Honesty
- **Binary Dependency:** Multilingual OCR (`eng+hin+mar`) requires an external installation of the Google Tesseract OCR binary (`tesseract.exe` on Windows or `tesseract-ocr` on Linux) along with trained data packs (`hin.traineddata`, `mar.traineddata`).
- **Strict Honesty Policy:** When the underlying Tesseract system binary is not detected on the host machine, the OCR subsystem reports `OCR DISABLED`. The platform intentionally contains zero hardcoded shortcuts or mocked extraction routines for demo images.

---

## 7. Multilingual Embeddings Dependency & First-Run Model Download
- **Core Pipeline Independence:** The primary production pipeline, dashboard, and full test suite run entirely on standard dependencies (`requirements.txt`) using the ultra-fast TF-IDF model (1.67 ms / post) without requiring PyTorch, CUDA, or large binary packages.
- **Optional Neural Extension:** Multilingual dense embeddings (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) are packaged separately in `requirements-embeddings.txt`.
- **First-Run HuggingFace Download:** When embeddings are installed and initialized for the first time, `sentence-transformers` automatically downloads the model weights (~470 MB) from the HuggingFace Hub (`huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) and caches them in `~/.cache/huggingface/hub/`. Subsequent runs use the local cached weights.
