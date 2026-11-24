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

st.set_page_config(page_title="Channel Discovery | telegram-osint-monitor-08", page_icon="🔭", layout="wide")

from dashboard.provenance_banner import render_provenance_banner
render_provenance_banner(page_title="Channel Discovery", active_stream="UNVERIFIED")

st.title("🔭 Public Channel Discovery & Snowball Watchlist")
st.caption("Automated public Telegram broadcast discovery, forward origin snowballing (d ≤ 2), and threat-ranked surveillance watchlist.")

# Mandatory Compliance Banner
st.markdown("""
<div style="background-color: #1B263B; border-left: 6px solid #00ADB5; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 13px;">
    <b>⚖️ OPERATIONAL CONSTRAINTS & ENGAGEMENT POLICY:</b><br>
    • <b>Public Broadcast Channels Only:</b> Reads open web previews (<code>t.me/s/</code>). The engine <b>NEVER joins any channel</b>, group, or forum automatically.<br>
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
    st.metric("High-Risk Posts Identified", f"{high_p:,}")
with mcol3:
    act_p = int(df_watchlist["actionable_posts"].sum()) if (df_watchlist is not None and "actionable_posts" in df_watchlist) else 0
    st.metric("Actionable Illicit Ads", f"{act_p:,}")
with mcol4:
    max_score = float(df_watchlist["threat_score"].max()) if (df_watchlist is not None and "threat_score" in df_watchlist and not df_watchlist.empty) else 0.0
    st.metric("Max Channel Threat Score", f"{max_score:.1f}")

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
                color_continuous_scale="Reds",
                title="Top 10 Threat-Ranked Channels",
                labels={"channel": "Channel", "threat_score": "Composite Threat Score"},
            )
            fig_wl.update_layout(template="plotly_dark", height=320, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_wl, use_container_width=True)

        st.dataframe(df_watchlist, use_container_width=True)

        # Download button
        with open(WATCHLIST_FILE, "r", encoding="utf-8-sig") as f:
            csv_content = f.read()
        st.download_button(
            label="📥 Export Watchlist (CSV)",
            data=csv_content,
            file_name="watchlist.csv",
            mime="text/csv",
        )
    else:
        st.info("No channels currently recorded in `watchlist.csv`. Run the discovery engine or add seed channels.")

with tab2:
    st.subheader("Automated Public Channel Discovery (finder.py)")
    st.caption("Conducts snowball discovery via public web previews: keywords -> search leads -> forward origin expansion (d ≤ 2).")

    kcol1, kcol2 = st.columns([1, 1])
    with kcol1:
        loaded_kw = load_keywords()
        kw_text = st.text_area("Search Query Keywords (one per line)", value="\n".join(loaded_kw[:8]), height=150)
        seed_ch_input = st.text_area(
            "Seed Public Channels (one per line)",
            value="t.me/delhi_classifieds_demo\nt.me/mumbai_trade_network\nt.me/mule_accounts_market",
            height=100
        )
    with kcol2:
        max_d = st.slider("Snowball Forward Origin Max Depth", min_value=1, max_value=2, value=2,
                          help="Depth 1: inspects seed channels; Depth 2: inspects channels forwarded by seeds.")
        max_c = st.slider("Max Channels to Sweep", min_value=3, max_value=25, value=10)
        delay = st.slider("Politeness Delay Between Requests (sec)", min_value=0.5, max_value=5.0, value=1.0)

    if st.button("🚀 Execute Discovery Run (discovery/finder.py)", type="primary"):
        seeds = [s.strip() for s in seed_ch_input.splitlines() if s.strip()]
        with st.spinner("Executing discovery and snowball expansion over public broadcast feeds..."):
            ranked = discover_and_snowball(
                seed_channels=seeds,
                max_depth=max_d,
                max_channels=max_c,
                delay_seconds=delay
            )
            save_watchlist_csv(ranked)

            # Persist to database channels table
            for c in ranked:
                ch_id = c["channel"]
                threat_score = c.get("threat_score", 0.0)
                risk_tier = "High" if threat_score >= 10.0 else "Medium" if threat_score >= 3.0 else "Low"
                db.upsert_channel(
                    ChannelRecord(
                        channel_id=ch_id,
                        platform="Telegram",
                        username=ch_id.replace("t.me/", "").lstrip("@"),
                        title=ch_id,
                        risk_level=risk_tier,
                        threat_score=threat_score,
                        is_monitored=True
                    )
                )

        st.success(f"✅ Discovery pass complete! Discovered and ranked {len(ranked)} public channels into `watchlist.csv` and database.")
        st.rerun()

with tab3:
    st.subheader("Manual Channel Intake")
    st.caption("Add an independently discovered public Telegram channel to the active watchlist.")
    
    with st.form("manual_channel_form"):
        new_ch_handle = st.text_input("Public Channel Handle or URL (e.g. t.me/jaipur_classifieds_sim)")
        new_ch_threat = st.selectbox("Suspected Threat Domain", ["bank_account", "drugs", "arms", "fake_documents", "atm_card", "sim_card", "crypto"])
        new_ch_notes = st.text_input("Investigator Referral Notes", value="Referred from field investigation")
        submitted = st.form_submit_button("➕ Add Channel to Watchlist")

        if submitted and new_ch_handle:
            clean_ch = new_ch_handle.strip()
            db.upsert_channel(
                ChannelRecord(
                    channel_id=clean_ch,
                    platform="Telegram",
                    username=clean_ch.replace("t.me/", "").lstrip("@"),
                    title=clean_ch,
                    risk_level="High",
                    threat_score=5.0,
                    is_monitored=True
                )
            )

            # Append to watchlist.csv
            new_row = {
                "channel": clean_ch,
                "threat_score": 5.0,
                "high_risk_posts": 1,
                "actionable_posts": 1,
                "total_posts": 1,
                "categories": new_ch_threat,
                "unique_upis": "",
                "unique_phones": "",
                "sample_snippet": new_ch_notes,
            }
            if df_watchlist is not None and not df_watchlist.empty:
                df_updated = pd.concat([df_watchlist, pd.DataFrame([new_row])], ignore_index=True)
            else:
                df_updated = pd.DataFrame([new_row])
            df_updated.to_csv(WATCHLIST_FILE, index=False, encoding="utf-8-sig")

            st.success(f"Channel '{clean_ch}' added to active watchlist and database!")
            st.rerun()
