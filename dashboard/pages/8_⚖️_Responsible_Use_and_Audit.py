"""Page 8: Responsible Use, Legal Compliance & System Audit Log."""
import json
import streamlit as st
import pandas as pd

from core.db import Database

st.set_page_config(page_title="Responsible Use & Audit | TGSherlock", page_icon="⚖️", layout="wide")

st.title("⚖️ Responsible Use, Legal Guidelines & Tamper-Evident Audit Log")
st.caption("Operational constraints, human-in-the-loop validation, and permanent system audit trail.")

db = Database()

st.markdown("""
### 🏛️ Operational Constraints & Law Enforcement Protocols
1. **Public Channel Broadcast Scope:**
   - The monitoring engine strictly operates on publicly accessible Telegram broadcast channels.
   - The system **never** joins private groups, requests invite access, posts messages, reacts, sends DMs, or enumerates member lists.
2. **Human-in-the-Loop Requirement ("Leads, Not Proof"):**
   - Algorithmic outputs, risk tiers, and entity links represent **leads for sworn investigator verification**.
   - No automatic coercive or legal action is taken without human analyst review and corroboration.
3. **Training Data Governance & API Terms Compliance:**
   - Under Telegram API terms of service, posts collected from Telegram are **never used to train or fine-tune machine learning models**.
   - All ML training was conducted strictly on synthetic/handcrafted examples (`data/train_synthetic.jsonl`).
4. **Data Retention & Chain of Custody:**
   - Every flagged post is deterministically serialized under RFC-8785 and anchored to an immutable cryptographic SHA-256 hash chain with block height indexing.
""")

st.divider()

st.subheader("📜 System Audit Log")
st.caption("Immutable append-only record of all analyst actions, status updates, and ingestion operations.")

with db.get_connection() as conn:
    rows = conn.execute("SELECT id, action, details_json, timestamp FROM audit_log ORDER BY id DESC LIMIT 100").fetchall()

if rows:
    records = []
    for r in rows:
        records.append({
            "Log ID": r["id"],
            "Timestamp (UTC)": r["timestamp"],
            "Action Type": r["action"],
            "Details": r["details_json"]
        })
    df_audit = pd.DataFrame(records)
    st.dataframe(df_audit, use_container_width=True)
else:
    st.info("No audit log records recorded yet.")
