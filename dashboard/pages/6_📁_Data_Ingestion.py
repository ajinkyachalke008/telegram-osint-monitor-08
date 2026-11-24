"""Page 6: Multi-Platform Data Ingestion & Live Pipeline Execution."""
import io
import json
import streamlit as st
import pandas as pd

from core.db import Database
from ingestion.adapters import CSVJSONImporter
from ingestion.worker import PipelineWorker

st.set_page_config(page_title="Data Ingestion | TGSherlock", page_icon="📁", layout="wide")

st.title("📁 Multi-Platform Threat Data Ingestion (R1)")
st.caption("Upload CSV or JSON dumps from Twitter, WhatsApp, darknet forums, or Telegram for pipeline ingestion.")

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
        st.markdown(f"**Total Records in File:** {len(df)}")

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
            run_dry = st.button("🔍 Dry Run Validation")
        with b_col2:
            run_ingest = st.button("🚀 Ingest into Unified Database & Pipeline")

        if run_dry:
            st.info("Performing dry-run validation...")
            valid_count = 0
            for _, row in df.iterrows():
                if str(row.get(col_text, "")).strip():
                    valid_count += 1
            st.success(f"Dry run complete: {valid_count} of {len(df)} records are valid for pipeline processing.")

        if run_ingest:
            with st.spinner("Processing posts through Normalization -> ML Classifier -> Financial Detector -> Evidence Hash Chain..."):
                ingested = 0
                for _, row in df.iterrows():
                    text = str(row.get(col_text, "")).strip()
                    if not text:
                        continue
                    worker.process_raw_post(
                        platform=str(row.get(col_plat, "imported")),
                        channel_id=str(row.get(col_src, "uploaded_source")),
                        message_id=str(row.get(col_id, f"imp_{ingested+1}")),
                        timestamp_utc=str(row.get(col_time, "")),
                        raw_text=text,
                        ingestion_source="IMPORTED"
                    )
                    ingested += 1
                db.log_audit("csv_json_ingest", {"filename": uploaded_file.name, "records": ingested})
                st.success(f"Successfully ingested and processed {ingested} threat records into SQLite ledger!")
                st.balloons()

    except Exception as e:
        st.error(f"Error reading uploaded file: {e}")
