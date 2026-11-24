"""OSINT Law Enforcement Dashboard - Executive Overview & Status."""
import json
import html
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.db import Database
from core.models import now_utc_iso
from dashboard.db_reader import load_dashboard_data

# Page configuration
st.set_page_config(
    page_title="TGSherlock OSINT Threat Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom dark law-enforcement styling
st.markdown("""
<style>
    .main { background-color: #0E131F; color: #ECEFF1; }
    .stMetric { background-color: #1A2238; border-radius: 8px; padding: 14px; border: 1px solid #283747; }
    .legal-banner {
        background-color: #1B263B; border-left: 6px solid #00ADB5;
        padding: 14px 18px; border-radius: 6px; margin-bottom: 20px;
        font-size: 13.5px; line-height: 1.5;
    }
    .badge-live { background-color: #00897B; color: #E0F2F1; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-imported { background-color: #1E88E5; color: #E3F2FD; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-sim { background-color: #FB8C00; color: #FFF3E0; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# Mandatory Legal & OSINT Disclaimer
st.markdown("""
<div class="legal-banner">
    <b>⚖️ LAW ENFORCEMENT OSINT MONITORING NOTICE & OPERATIONAL CONSTRAINTS:</b><br>
    • <b>Public Channels Only:</b> Monitoring is restricted to public broadcast channels. The system never joins private groups, posts, reacts, DMs, or enumerates channel members.<br>
    • <b>Leads, Not Proof:</b> All algorithmic classifications and link clusters represent intelligence leads for certified human review, not courtroom proof.<br>
    • <b>Strict Training Compliance:</b> ZERO models were trained or fine-tuned on Telegram data. ML classification is trained exclusively on synthetic/handcrafted benchmarks.
</div>
""", unsafe_allow_html=True)

st.title("🛡️ TGSherlock OSINT Threat Monitor")
st.caption("Telegram & Multi-Platform Illegal Trade Intelligence Engine | Real-Time Detection & Link Analysis")

# Database connection
db = Database()

# Load summary metrics
with db.get_connection() as conn:
    total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    high_threats = conn.execute("SELECT COUNT(*) FROM posts WHERE risk_level = 'High'").fetchone()[0]
    med_threats = conn.execute("SELECT COUNT(*) FROM posts WHERE risk_level = 'Medium'").fetchone()[0]
    total_identifiers = conn.execute("SELECT COUNT(*) FROM identifiers").fetchone()[0]
    cross_actors = conn.execute("SELECT COUNT(*) FROM identifiers WHERE cross_channel = 1").fetchone()[0]
    evidence_blocks = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    
    # Ingestion provenance counts
    prov_rows = conn.execute("SELECT ingestion_source, COUNT(*) as cnt FROM posts GROUP BY ingestion_source").fetchall()
    prov_counts = {r["ingestion_source"]: r["cnt"] for r in prov_rows}

# Top Metric Banner
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Ingested Posts", f"{total_posts:,}")
with col2:
    st.metric("Actionable Threats (High)", f"{high_threats:,}", delta=f"{high_threats+med_threats} Total Flagged")
with col3:
    st.metric("Extracted Identifiers", f"{total_identifiers:,}")
with col4:
    st.metric("Cross-Channel Syndicates", f"{cross_actors:,}", delta="Active in 2+ Chans")
with col5:
    st.metric("Sealed Evidence Blocks", f"{evidence_blocks:,}", delta="Tamper-Evident Chain")

st.divider()

# Ingestion Source & Provenance
st.subheader("📡 Live Ingestion Streams & Data Provenance")
pcol1, pcol2, pcol3 = st.columns(3)
with pcol1:
    live_c = prov_counts.get("LIVE", 0)
    st.markdown(f'<span class="badge-live">LIVE TELEGRAM</span> &nbsp; <b>{live_c}</b> posts ingested from local TGSherlock daemon.', unsafe_allow_html=True)
with pcol2:
    imp_c = prov_counts.get("IMPORTED", 0)
    st.markdown(f'<span class="badge-imported">IMPORTED DUMPS</span> &nbsp; <b>{imp_c}</b> posts ingested via multi-platform CSV/JSON.', unsafe_allow_html=True)
with pcol3:
    sim_c = prov_counts.get("SIMULATED", 0)
    st.markdown(f'<span class="badge-sim">SIMULATED REPLAY</span> &nbsp; <b>{sim_c}</b> benchmark posts replayed for demonstration.', unsafe_allow_html=True)

st.write("")

# Charts Row
row1_col1, row1_col2 = st.columns([1, 1])

with row1_col1:
    st.markdown("### 📊 Threat Categories Distribution")
    with db.get_connection() as conn:
        cat_rows = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM posts WHERE category != 'benign' AND category != 'unclassified' GROUP BY category ORDER BY cnt DESC"
        ).fetchall()
    if cat_rows:
        df_cat = pd.DataFrame([dict(r) for r in cat_rows])
        fig_cat = px.bar(
            df_cat, x="cnt", y="category", orientation="h",
            labels={"cnt": "Flagged Posts", "category": "Trade Category"},
            color="cnt", color_continuous_scale="Reds",
            template="plotly_dark"
        )
        fig_cat.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("No categorized illegal posts in database yet.")

with row1_col2:
    st.markdown("### 🔍 Extracted Identifiers by Type")
    with db.get_connection() as conn:
        ident_rows = conn.execute(
            "SELECT type, COUNT(*) as cnt FROM identifiers GROUP BY type ORDER BY cnt DESC"
        ).fetchall()
    if ident_rows:
        df_ident = pd.DataFrame([dict(r) for r in ident_rows])
        fig_ident = px.pie(
            df_ident, names="type", values="cnt", hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Bold,
            template="plotly_dark"
        )
        fig_ident.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(fig_ident, use_container_width=True)
    else:
        st.info("No identifiers extracted yet.")

st.divider()

# System Architecture Flow
st.subheader("⚙️ Real-Time Intelligence Pipeline Flow")
st.markdown("""
```text
[Public Telegram / CSV Dump / Replay Stream]
                   │
                   ▼
       1. Text Normalization (NFKC, Homoglyphs, Leetspeak, Spaced Words, Devanagari)
                   │
                   ▼
       2. Hybrid Classification (Slang Lexicon + Scikit-Learn TF-IDF + Hard-Negative Calibrator)
                   │
                   ▼
       3. Financial-Ad Detector (Mule Recruitment Intent, Instruments, Commission, Text Offsets)
                   │
                   ▼
       4. Identifier Extraction (UPI, Phones, Base58Check Wallets, Usernames, IFSC, Gazetteer)
                   │
                   ▼
       5. Evidence Ledger (RFC-8785 Canonical JSON + SHA-256 Hash Chaining)
                   │
                   ▼
       6. Link Analysis (Entities Graph, Centrality, Cross-Channel Syndicates, MinHash Ads)
                   │
                   ▼
       7. Multipage Law Enforcement Dashboard (Triage, Verification, Dossiers, Export)
```
""")

st.info("💡 **Navigation:** Use the left sidebar to navigate across the full suite: **Live Alerts**, **Alert Detail & Hash Verification**, **Entity Graph**, **Coordinated Campaigns**, **Geographic Map**, **Data Ingestion**, **Model Metrics**, and **Responsible Use & Audit**.")
