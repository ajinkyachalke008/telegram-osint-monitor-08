"""Page 8: Responsible Use, Legal Compliance & System Audit Log."""
import sys
import json
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd

from core.db import Database
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme

st.set_page_config(page_title="Responsible Use & Audit | telegram-osint-monitor-08", page_icon="⚖️", layout="wide")

# Inject Master Theme
inject_theme()

render_provenance_banner(page_title="Responsible Use & Audit", active_stream="VERIFIED-SYNTHETIC")

st.title("⚖️ Responsible Use, Legal Guidelines & Tamper-Evident Audit Log")
st.caption("Operational constraints, human-in-the-loop validation, and permanent system audit trail.")

db = Database()

# Operational Constraints Grid
st.markdown("""
<div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:20px;">
    <div class="intel-card" style="padding:14px 18px; margin-bottom:0;">
        <b style="color:#00E5FF; font-size:13px;">1. Public Channel Broadcast Scope</b>
        <div style="color:#94A3B8; font-size:12px; margin-top:4px;">
            The monitoring engine strictly operates on publicly accessible open web previews. The system <b>never</b> joins private groups, posts messages, reacts, or enumerates member lists.
        </div>
    </div>
    <div class="intel-card" style="padding:14px 18px; margin-bottom:0;">
        <b style="color:#00E5FF; font-size:13px;">2. Human-in-the-Loop Protocol</b>
        <div style="color:#94A3B8; font-size:12px; margin-top:4px;">
            Algorithmic outputs, risk tiers, and entity links represent <b>investigative leads</b>. No automatic coercive or legal action is taken without sworn analyst verification.
        </div>
    </div>
    <div class="intel-card" style="padding:14px 18px; margin-bottom:0;">
        <b style="color:#00E5FF; font-size:13px;">3. Zero Telegram Data ML Retraining</b>
        <div style="color:#94A3B8; font-size:12px; margin-top:4px;">
            Under Telegram API terms, posts collected from Telegram are <b>never used to train or fine-tune machine learning models</b>. ML training is strictly conducted on synthetic data.
        </div>
    </div>
    <div class="intel-card" style="padding:14px 18px; margin-bottom:0;">
        <b style="color:#00E5FF; font-size:13px;">4. Section 63 BSA Chain of Custody</b>
        <div style="color:#94A3B8; font-size:12px; margin-top:4px;">
            Every flagged post is deterministically serialized under RFC-8785 and anchored to an immutable cryptographic SHA-256 hash chain with block height indexing.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Lexicon Feedback Loop
st.subheader("🎯 Lexicon Feedback Loop (Analyst Weight Calibration)")
st.caption("Calibrate slang sensitivity without retraining: Analyst flags adjust rule weights ONLY. ZERO ML model retraining on collected Telegram data.")

from addons.scorer import RuleScorer
scorer = RuleScorer()

fcol1, fcol2 = st.columns([1, 1], gap="large")

with fcol1:
    st.markdown("#### Adjust Term Weight")
    cat_options = list(scorer.lexicon.get("categories", {}).keys())
    sel_cat = st.selectbox("Threat Category", cat_options)
    
    # Pre-populate terms from category
    cat_terms = []
    cat_data = scorer.lexicon.get("categories", {}).get(sel_cat, {})
    for sec in ["slang_en", "slang_hinglish", "slang_marathi", "coded_words", "emojis"]:
        cat_terms.extend(cat_data.get(sec, []))
    
    sel_term = st.selectbox("Select Existing Term or Type New", sorted(list(set(cat_terms))))
    custom_term_input = st.text_input("Or Custom Slang Term", value=sel_term)
    final_term = custom_term_input.strip() if custom_term_input else sel_term
    
    new_weight = st.slider("New Term Weight", min_value=0.0, max_value=15.0, value=3.5, step=0.5,
                           help="0.0 suppresses false positives; higher weights elevate threat triage priority.")
    analyst_id = st.text_input("Analyst Badge / ID", value="analyst_osint_01")
    reason = st.text_input("Operational Justification", value="Street intelligence confirmed terminology shift")

    if st.button("💾 Apply Weight Adjustment (No ML Retraining)", type="primary"):
        res = scorer.adjust_term_weight(
            category=sel_cat,
            term=final_term,
            new_weight=new_weight,
            analyst_id=analyst_id,
            reason=reason
        )
        st.success(f"✅ Adjusted weight for '{final_term}' ({sel_cat}) to {new_weight}. Lexicon reloaded immediately.")
        st.rerun()

with fcol2:
    st.markdown("#### Active Feedback Overrides")
    active_overrides = scorer.feedback_weights
    if active_overrides:
        df_fb = pd.DataFrame([
            {
                "Key": k,
                "Category": v.get("category"),
                "Term": v.get("term"),
                "Weight": v.get("weight"),
                "Analyst": v.get("updated_by"),
                "Updated At": v.get("updated_at"),
                "Reason": v.get("reason"),
            }
            for k, v in active_overrides.items()
        ])
        st.dataframe(df_fb, use_container_width=True, hide_index=True)
        if st.button("🔄 Reset Overrides to Lexicon Defaults"):
            scorer.reset_feedback_weights()
            st.toast("Feedback overrides reset to lexicon defaults.", icon="🔄")
            st.rerun()
    else:
        st.info("No manual feedback overrides currently active. Operating on baseline rule weights.")
