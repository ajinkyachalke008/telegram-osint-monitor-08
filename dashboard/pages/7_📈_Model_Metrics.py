"""Page 7: Machine Learning Model Metrics & Evaluation."""
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Model Metrics | TGSherlock", page_icon="📈", layout="wide")

from dashboard.provenance_banner import render_provenance_banner
render_provenance_banner(page_title="Model Metrics", active_stream="VERIFIED-SYNTHETIC")

st.title("📈 Machine Learning Performance & Validation Benchmarks (R2)")
st.caption("Held-out evaluation metrics, hard-negative suppression results, and training compliance declaration.")

METRICS_FILE = Path(__file__).resolve().parent.parent.parent / "docs" / "METRICS.md"

if METRICS_FILE.exists():
    content = METRICS_FILE.read_text(encoding="utf-8")
    st.markdown(content)
else:
    st.warning("docs/METRICS.md not found. Run `python eval/evaluate_model.py` to generate evaluation metrics.")
