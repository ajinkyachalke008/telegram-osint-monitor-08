# Judges Q&A Brief: TGSherlock OSINT Threat Intelligence System

### Problem Statement
**Telegram & Social Media Illegal Trade Monitor (Drugs, Arms, Bank Accounts & ATM Cards for Sale)**

---

## 1. Regulatory, Privacy & Telegram API Compliance

### Q1: How do you access Telegram data without violating API Terms of Service or getting banned?
> **Answer:**
> 1. **Public Broadcast Scope:** Our system strictly monitors **publicly viewable Telegram broadcast channels** using read-only API calls or standard HTTP preview mechanisms.
> 2. **Zero Infiltration:** We never join private groups, never message or direct message (DM) administrators, never post messages or reactions, and never enumerate channel member lists.
> 3. **Rate Limit Defenses:** The poller respects Telegram's `FloodWait` exceptions with exponential backoff and randomized inter-request jitter (2–5 seconds).
> 4. **No Model Training on Telegram Content:** Telegram API terms strictly prohibit training or fine-tuning models on collected messages. In full compliance, **our machine learning model was trained 100% on synthetic and handcrafted datasets (`data/train_synthetic.jsonl`)**. Telegram posts are consumed solely as read-only runtime inference inputs.

---

## 2. Machine Learning & Detection Methodology

### Q2: How do you prevent false positives on legitimate banking warnings or licensed pharmacies?
> **Answer:**
> We implement a multi-layered **Hard-Negative Suppression Engine**:
> 1. **Lexical & Semantic Disclaimers:** Official bank notices containing phrases like *"never share OTP"*, *"beware of fraudsters"*, or *"report to 1930"* activate suppression filters that damp threat confidence by 85%.
> 2. **Intent Verification:** Legitimate pharmacies (e.g., Apollo, MedPlus) requiring *"doctor prescription"* or sports clubs advertising *"10m air rifle shooting trials"* lack the commercial solicitations, mule commission offers, and anonymized delivery guarantees that trigger our illegal classifier.
> 3. **Empirical Verification:** In our held-out test suite of 602 synthetic records, **hard negative bank advisories and pharmacy notices achieved 0% false alarm rate**, remaining classified as `Clean` or `benign`.

### Q3: What is the benefit of your Hybrid Classifier over a pure keyword list or pure LLM?
> **Answer:**
> - **Pure Keywords Fail** against evasion tactics like leetspeak (`c0ke`), homoglyphs (`а` vs `a`), spaced characters (`a t m`), or Devanagari numerals (`९००००`). Our Normalizer defeats these evasion tactics before matching.
> - **Pure LLMs / APIs** are slow, expensive, rate-limited, and vulnerable to hallucinations or cloud data leaks.
> - **Our Hybrid Architecture:** Combines deterministic slang/coded lexicons (`addons/lexicon.yaml`) with a local scikit-learn TF-IDF n-gram Logistic Regression classifier. It runs completely offline in <5 milliseconds per post, provides exact numerical confidence, and outputs plain-language explainability traces (`why_flagged`).

---

## 3. Financial Instrument & Mule Recruitment Detection (R3)

### Q3: How do you differentiate between an innocent mention of a bank account and an illicit money mule solicitation?
> **Answer:**
> Our dedicated `FinancialAdDetector` looks for the **triad of mule recruitment**:
> 1. **Action Intent:** Solicitations to *"rent"*, *"sell"*, *"recruit"*, or *"provide idle account"*.
> 2. **Financial Instrument:** Current account, corporate net-banking kit, pre-activated ATM card, or KYC-less SIM.
> 3. **Criminal Incentive:** Mentions of *"daily commission"*, *"10% commission"*, *"heavy daily limit"*, or *"clean KYC/zero dispute"*.
> When all three co-occur, the post is automatically flagged as **High Risk Mule Recruitment Pattern**.

---

## 4. Chain of Custody & Court Admissibility (R6)

### Q4: How is evidence preserved so that it is admissible in legal proceedings?
> **Answer:**
> 1. **RFC-8785 Canonical JSON:** Dictionary keys, Unicode characters, and floats are deterministically serialized so the exact hash can be re-derived independently by any forensics lab worldwide.
> 2. **Cryptographic Hash Chain:** Each post's canonical hash is chained to the preceding block's hash:
>    $$\text{Block Hash} = \text{SHA256}(\text{Canonical JSON} \parallel \text{Previous Hash})$$
> 3. **Block Height Indexing:** Tampering with any historical post immediately invalidates all subsequent block hashes, providing undeniable mathematical proof of evidence integrity.
> 4. **CLI Verifier:** Sworn examiners can execute `python addons/verify_evidence.py` to independently audit the SQLite ledger in seconds.

---

## 5. Link Analysis & Cross-Channel Syndicates (R5)

### Q5: How do you identify whether isolated channels are operated by the same criminal syndicate?
> **Answer:**
> 1. **Cross-Channel Entity Graph:** When an extracted identifier (UPI ID like `mule.syndicate@ybl`, phone number, TRON wallet, or Telegram handle) appears in $\ge 2$ distinct public channels, the node is flagged in red with elevated priority.
> 2. **Betweenness Centrality:** Graph analytics reveal bridge nodes that connect seemingly separate channel networks.
> 3. **Coordinated Campaign Detection:** Our MinHash Jaccard algorithm groups templated ad copies across channels, exposing copy-paste broadcast spam networks.

---

## 6. Deployment & Provenance

### Q6: Can this system run in an air-gapped law enforcement intranet?
> **Answer:**
> **Yes, 100%.**
> - The entire stack runs on standard Python 3.11+ with SQLite WAL mode.
> - No external cloud API keys, proprietary models, or external vector databases are required.
> - The UI clearly labels all data provenance: `LIVE` (real Telegram), `IMPORTED` (investigator CSV/JSON dumps), or `SIMULATED` (replay benchmarks).
