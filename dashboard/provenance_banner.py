"""Reusable Data Provenance & Operational Boundary Banner for all Dashboard Pages.

Derives provenance labels dynamically from records actually present in data/osint_monitor.db.
"""
import streamlit as st
from core.db import Database


def render_provenance_banner(page_title: str = "", active_stream: str = None):
    """Render standardized provenance banner deriving labels dynamically from database records."""
    db = Database()
    prov_counts = {}
    try:
        with db.get_connection() as conn:
            rows = conn.execute(
                "SELECT ingestion_source, COUNT(*) as cnt FROM posts GROUP BY ingestion_source"
            ).fetchall()
            prov_counts = {r["ingestion_source"]: r["cnt"] for r in rows}
    except Exception:
        pass

    # Build badge HTML dynamically from actual database records
    badges_html = []
    if prov_counts:
        for source, count in sorted(prov_counts.items()):
            if source == "VERIFIED-SYNTHETIC":
                badges_html.append(f'<span style="background-color:#7E57C2; color:#EDE7F6; padding:2px 7px; border-radius:4px; font-weight:bold; font-size:11px;">VERIFIED-SYNTHETIC ({count} posts)</span>')
            elif source == "IMPORTED":
                badges_html.append(f'<span style="background-color:#1E88E5; color:#E3F2FD; padding:2px 7px; border-radius:4px; font-weight:bold; font-size:11px;">IMPORTED ({count} posts)</span>')
            elif source == "LIVE":
                badges_html.append(f'<span style="background-color:#00897B; color:#E0F2F1; padding:2px 7px; border-radius:4px; font-weight:bold; font-size:11px;">LIVE ({count} posts)</span>')
            else:
                badges_html.append(f'<span style="background-color:#4A5568; color:#ECEFF1; padding:2px 7px; border-radius:4px; font-weight:bold; font-size:11px;">{source} ({count} posts)</span>')
    else:
        badges_html.append('<span style="background-color:#4A5568; color:#ECEFF1; padding:2px 7px; border-radius:4px; font-size:11px;">Awaiting Data / Replay Stream</span>')

    active_badges_str = " &nbsp; ".join(badges_html)

    # Air-gap unverified status for Telegram Web Preview Poller and telegram-osint-monitor-08 Ingestion
    unverified_badge = '<span style="background-color:#546E7A; color:#ECEFF1; padding:2px 7px; border-radius:4px; font-size:11px;">UNVERIFIED: Telegram Web Preview Poller &amp; telegram-osint-monitor-08 Ingestion (air-gap unverified)</span>'

    st.markdown(f"""
    <div style="background-color: #162032; border-left: 5px solid #00ADB5; padding: 10px 14px; border-radius: 6px; margin-bottom: 15px; font-size: 13px; color: #ECEFF1;">
        <b>📡 DATA PROVENANCE NOTICE (DERIVED FROM SQLITE DB):</b><br/>
        <b>Active Database Feeds:</b> {active_badges_str}
        &nbsp;|&nbsp; 
        {unverified_badge}
        <br/>
        <span style="color:#A0AEC0; font-size:12px;">Public broadcast feeds only • Zero channel joining • Leads, not courtroom proof • Consult legal counsel for Section 63 BSA certificate.</span>
    </div>
    """, unsafe_allow_html=True)
