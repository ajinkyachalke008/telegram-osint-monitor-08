"""Page 6: Multi-Platform Data Ingestion & Live Pipeline Execution."""
import sys
import io
import json
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd

from core.db import Database
from ingestion.adapters import CSVJSONImporter
from ingestion.worker import PipelineWorker
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme

st.set_page_config(page_title="Data Ingestion | telegram-osint-monitor-08", page_icon="📁", layout="wide")

# Inject Master Theme
inject_theme()

render_provenance_banner(page_title="Data Ingestion", active_stream="IMPORTED")

st.title("📁 Multi-Platform Threat Data Ingestion (R1)")
st.caption("Upload CSV or JSON dumps from Twitter, WhatsApp, darknet forums, or Telegram for pipeline ingestion.")

# Visual Pipeline Stages
st.markdown("""
<div style="background-color: #0C1220; border: 1px solid #1A263D; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 12.5px;">
        <span style="color:#00E5FF; font-weight:700;">1. Select Data Dump</span> &bull; 
        <span style="color:#94A3B8;">2. Schema Preview</span> &bull; 
        <span style="color:#94A3B8;">3. Column Mapping</span> &bull; 
        <span style="color:#94A3B8;">4. Dry-Run Validation</span> &bull; 
        <span style="color:#94A3B8;">5. Ingest &amp; Seal Evidence</span>
    </div>
</div>
""", unsafe_allow_html=True)

db = Database()
worker = PipelineWorker(db=db)
importer = CSVJSONImporter(db=db, worker=worker)

uploaded_file = st.file_uploader("Upload CSV or JSON Threat Intelligence Dump", type=["csv", "json"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            data = json.load(uploaded_file)
            df = pd.DataFrame(data if isinstance(data, list) else [data])

        st.subheader("📋 Upload Preview")
        st.dataframe(df.head(10), use_container_width=True)
        st.markdown(f"**Total Records in File:** `{len(df):,}`")

        # Column mapping configuration
        st.subheader("🗺️ Column Mapping")
        cols = list(df.columns)
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            col_plat = st.selectbox("Platform Column", cols, index=cols.index("platform") if "platform" in cols else 0)
            col_src = st.selectbox("Source / Channel Column", cols, index=cols.index("source") if "source" in cols else min(1, len(cols)-1))
        with m_col2:
            col_id = st.selectbox("Post ID Column", cols, index=cols.index("post_id") if "post_id" in cols else min(2, len(cols)-1))
            col_time = st.selectbox("Timestamp Column", cols, index=cols.index("timestamp") if "timestamp" in cols else min(3, len(cols)-1))
        with m_col3:
            col_text = st.selectbox("Text / Message Column", cols, index=cols.index("text") if "text" in cols else min(4, len(cols)-1))

        # Dry Run & Ingest Actions
        b_col1, b_col2 = st.columns([1, 4])
        with b_col1:
            run_dry = st.button("🔍 Dry Run Validation", use_container_width=True)
        with b_col2:
            run_ingest = st.button("🚀 Process & Ingest to Evidence Ledger", type="primary", use_container_width=True)

        mapping = {
            "platform": col_plat,
            "source": col_src,
            "post_id": col_id,
            "timestamp": col_time,
            "text": col_text
        }

        if run_dry:
            with st.spinner("Validating dump records without writing to database..."):
                res = importer.import_dataframe(df, mapping=mapping, dry_run=True)
                st.info(f"**Dry Run Validation Complete:** {res.get('processed', 0)} records validated ({res.get('valid', 0)} compliant, {res.get('skipped', 0)} skipped).")

        if run_ingest:
            with st.spinner("Executing pipeline worker ingestion and RFC-8785 evidence sealing..."):
                res = importer.import_dataframe(df, mapping=mapping, dry_run=False)
                st.success(f"🎉 **Ingestion Succeeded:** {res.get('processed', 0)} posts parsed, classified, and sealed into evidence ledger.")

    except Exception as e:
        st.error(f"Failed to parse uploaded file: {e}")
