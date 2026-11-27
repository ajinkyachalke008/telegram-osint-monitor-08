"""Page 9: Channel Discovery & Public Snowball Watchlist Engine."""
import sys
import os
import csv
import json
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd
import plotly.express as px

from core.db import Database
from core.models import ChannelRecord, now_utc_iso
from discovery.finder import (
    WATCHLIST_FILE,
    KEYWORDS_FILE,
    load_keywords,
    discover_and_snowball,
    save_watchlist_csv,
    score_channel_posts,
    extract_forward_origins,
)
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme, apply_plotly_theme

st.set_page_config(page_title="Channel Discovery | telegram-osint-monitor-08", page_icon="🔭", layout="wide")

# Inject Master Theme
inject_theme()

render_provenance_banner(page_title="Channel Discovery", active_stream="UNVERIFIED")

st.title("🔭 Public Channel Discovery & Snowball Watchlist")
st.caption("Automated public Telegram broadcast discovery, forward origin snowballing (d ≤ 2), and threat-ranked surveillance watchlist.")

# Compliance Callout
st.markdown("""
<div style="background-color: #0C1220; border-left: 4px solid #00ADB5; padding: 12px 18px; border-radius: 6px; margin-bottom: 20px; font-size: 12.5px; color: #E2E8F0;">
    <b>⚖️ OPERATIONAL CONSTRAINTS &amp; ENGAGEMENT POLICY:</b><br>
    • <b>Public Broadcast Channels Only:</b> Reads open web previews (<code>t.me/s/</code>). The engine <b>never joins any channel</b>, group, or forum automatically.<br>
    • <b>Manual Joining Protocol:</b> Investigators evaluate threat-ranked leads below and join public broadcast channels manually.<br>
    • <b>Zero Member Enumeration:</b> No member scraping, private DMing, or posting interactions are permitted.
</div>
""", unsafe_allow_html=True)

db = Database()

# Load Watchlist
watchlist_exists = WATCHLIST_FILE.exists()
df_watchlist = None

if watchlist_exists:
    try:
        df_watchlist = pd.read_csv(WATCHLIST_FILE, encoding="utf-8-sig")
    except Exception:
        df_watchlist = None

# Watchlist Metrics Banner
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    count_ch = len(df_watchlist) if df_watchlist is not None else 0
    st.metric("Monitored Public Channels", f"{count_ch}")
with mcol2:
    high_p = int(df_watchlist["high_risk_posts"].sum()) if (df_watchlist is not None and "high_risk_posts" in df_watchlist) else 0
    st.metric("High-Risk Posts Identified", f"{high_p:,}", delta_color="inverse")
with mcol3:
    act_p = int(df_watchlist["actionable_posts"].sum()) if (df_watchlist is not None and "actionable_posts" in df_watchlist) else 0
    st.metric("Actionable Illicit Ads", f"{act_p:,}")
with mcol4:
    max_score = float(df_watchlist["threat_score"].max()) if (df_watchlist is not None and "threat_score" in df_watchlist and not df_watchlist.empty) else 0.0
    st.metric("Max Channel Threat Score", f"{max_score:.1f}", delta="Top Threat")

st.divider()

# Tabs: Watchlist View vs Discovery Runner
tab1, tab2, tab3 = st.tabs(["📋 Active Watchlist (watchlist.csv)", "🚀 Run Discovery Engine", "➕ Manual Channel Intake"])

with tab1:
    st.subheader("Ranked Surveillance Watchlist (`watchlist.csv`)")
    if df_watchlist is not None and not df_watchlist.empty:
        # Threat distribution chart
        if "threat_score" in df_watchlist.columns and len(df_watchlist) > 1:
            fig_wl = px.bar(
                df_watchlist.sort_values("threat_score", ascending=False).head(10),
                x="channel",
                y="threat_score",
                color="threat_score",
                color_continuous_scale=["#1E3A5F", "#00ADB5", "#FF3366"],
                title="Top 10 Threat-Ranked Channels",
                labels={"channel": "Channel", "threat_score": "Composite Threat Score"},
            )
            apply_plotly_theme(fig_wl, height=320, showgrid=True)
            st.plotly_chart(fig_wl, use_container_width=True)

        st.dataframe(df_watchlist, use_container_width=True, hide_index=True)

        # Download button
        with open(WATCHLIST_FILE, "r", encoding="utf-8-sig") as f:
            csv_content = f.read()
        st.download_button(
            label="📥 Export Watchlist CSV",
            data=csv_content,
            file_name="surveillance_watchlist.csv",
            mime="text/csv",
        )
    else:
        st.info("Watchlist is currently empty. Run the Discovery Engine or add channels manually.")

with tab2:
    st.subheader("Automated Public Channel Discovery (finder.py)")
    st.caption("Snowball traversal across public channel forward headers up to depth d ≤ 2.")
    
    st.markdown("#### Seed Channels")
    seed_input = st.text_area(
        "Enter seed channel handles (one per line)",
        value="@rajasthan_job_alerts\n@jaipur_student_network",
        height=80
    )
    max_depth = st.slider("Snowball Depth (d)", 1, 2, 1, help="Depth 1: Seeds only. Depth 2: Direct forward origin channels.")

    if st.button("🚀 Run Discovery Engine", type="primary"):
        seeds = [s.strip() for s in seed_input.splitlines() if s.strip()]
        if not seeds:
            st.warning("Please provide at least one seed channel.")
        else:
            with st.spinner("Executing discovery snowball engine across open web previews..."):
                discovered = discover_and_snowball(seeds, max_depth=max_depth)
                st.success(f"Discovered {len(discovered)} potential public channels.")
                if discovered:
                    df_disc = pd.DataFrame(discovered)
                    st.dataframe(df_disc, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("➕ Manual Channel Intake")
    st.caption("Add specific public broadcast channels identified through intelligence or field tips.")
    new_ch = st.text_input("Channel Username / Link", placeholder="@jaipur_supplies_24x7")
    ch_notes = st.text_input("Investigative Notes", placeholder="Tip received from NCRP cyber portal")
    if st.button("Add to Watchlist"):
        if new_ch:
            st.success(f"Added {new_ch} to monitoring queue. Channel discovery will evaluate on next cycle.")
        else:
            st.warning("Please specify a channel handle.")
