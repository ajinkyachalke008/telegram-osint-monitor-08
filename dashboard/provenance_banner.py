"""Reusable Data Provenance & Operational Boundary Banner for all Dashboard Pages.

Derives provenance labels dynamically from records actually present in data/osint_monitor.db.
Refined for elite command-centre visual hierarchy, readability, and responsiveness.
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
                badges_html.append(
                    f'<span style="background-color:rgba(126, 87, 194, 0.16); color:#D1C4E9; border:1px solid rgba(126, 87, 194, 0.4); padding:3px 9px; border-radius:4px; font-weight:700; font-size:11px; letter-spacing:0.04em;">VERIFIED-SYNTHETIC ({count} posts)</span>'
                )
            elif source == "IMPORTED":
                badges_html.append(
                    f'<span style="background-color:rgba(30, 136, 229, 0.16); color:#BBDEFB; border:1px solid rgba(30, 136, 229, 0.4); padding:3px 9px; border-radius:4px; font-weight:700; font-size:11px; letter-spacing:0.04em;">IMPORTED ({count} posts)</span>'
                )
            elif source == "LIVE":
                badges_html.append(
                    f'<span style="background-color:rgba(0, 137, 123, 0.16); color:#B2DFDB; border:1px solid rgba(0, 137, 123, 0.4); padding:3px 9px; border-radius:4px; font-weight:700; font-size:11px; letter-spacing:0.04em;">LIVE ({count} posts)</span>'
                )
            else:
                badges_html.append(
                    f'<span style="background-color:rgba(74, 85, 104, 0.2); color:#E2E8F0; border:1px solid rgba(74, 85, 104, 0.4); padding:3px 9px; border-radius:4px; font-weight:600; font-size:11px;">{source} ({count} posts)</span>'
                )
    else:
        badges_html.append(
            '<span style="background-color:rgba(74, 85, 104, 0.2); color:#94A3B8; border:1px solid rgba(74, 85, 104, 0.4); padding:3px 9px; border-radius:4px; font-size:11px;">Awaiting Data / Replay Stream</span>'
        )

    active_badges_str = " &nbsp; ".join(badges_html)

    # Check if any synthetic data is present in the database (Row Provenance Derivation)
    synthetic_count = sum(
        count for src, count in prov_counts.items()
        if src and any(k in str(src).upper() for k in ("SYNTHETIC", "SIMULAT", "DEMO", "MOCK"))
    )

    if synthetic_count > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, rgba(229, 9, 20, 0.14) 0%, rgba(229, 9, 20, 0.05) 100%); border: 1.5px dashed #FF3366; color: #FECDD3; padding: 10px 16px; border-radius: 6px; margin-bottom: 14px; text-align: center; font-weight: 700; font-size: 13px; letter-spacing: 0.06em; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.1);">
            ⚠️ SIMULATED DATA — NOT REAL CRIMINAL EVIDENCE (DERIVED FROM DATABASE PROVENANCE: {synthetic_count} SYNTHETIC RECORDS PRESENT IN {db.db_path.name}) ⚠️
        </div>
        """, unsafe_allow_html=True)

    # Air-gap unverified status for Telegram Web Preview Poller
    unverified_badge = '<span style="background-color:rgba(84, 110, 122, 0.2); color:#CFD8DC; border:1px solid rgba(84, 110, 122, 0.35); padding:3px 8px; border-radius:4px; font-size:11px;">AIR-GAP UNVERIFIED: Telegram Web Preview Poller &amp; OSINT Ingestion</span>'

    st.markdown(f"""
    <div style="background-color: #0C1322; border-left: 4px solid #00ADB5; border-top: 1px solid #16233B; border-right: 1px solid #16233B; border-bottom: 1px solid #16233B; padding: 12px 18px; border-radius: 6px; margin-bottom: 18px; font-size: 13px; color: #E2E8F0; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
                <b style="color:#00E5FF; letter-spacing:0.04em;">📡 DATA PROVENANCE NOTICE:</b>
                <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#94A3B8; margin-left:4px;">[{db.db_path.name}]</span>
            </div>
            <div>
                {unverified_badge}
            </div>
        </div>
        <div style="margin-top:8px; display:flex; align-items:center; flex-wrap:wrap; gap:8px;">
            <b style="color:#94A3B8; font-size:11.5px; text-transform:uppercase; letter-spacing:0.04em;">Active Feeds:</b>
            {active_badges_str}
        </div>
        <div style="margin-top:6px; color:#64748B; font-size:11.5px;">
            Public broadcast feeds only &bull; Zero automated channel joining &bull; Evidence package to support a Section 63 BSA certificate. Not legal advice.
        </div>
    </div>
    """, unsafe_allow_html=True)
