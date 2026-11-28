"""Page 1: Live Threat Alerts & Analyst Triage Workflow."""
import sys
import json
import html
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd

from core.db import Database
from core.models import now_utc_iso
from core.multilingual import detect_language_and_script
from dashboard.provenance_banner import render_provenance_banner
from dashboard.demo_sidebar import render_demo_maintenance_sidebar
from dashboard.theme import inject_theme

st.set_page_config(page_title="Live Alerts | telegram-osint-monitor-08", page_icon="🚨", layout="wide")

# Inject Master Theme
inject_theme()

# Standard Provenance Banner
render_provenance_banner(page_title="Live Alerts", active_stream="VERIFIED-SYNTHETIC")

st.title("🚨 Live Threat Alerts & Triage Workflow")
st.caption("Actionable illegal trade detections across public broadcast channels with 5-second streaming auto-refresh.")

db = Database()

# Sidebar Filters
st.sidebar.markdown("""
<div style="padding-bottom:8px; border-bottom:1px solid #1E2B45; margin-bottom:12px;">
    <span style="font-weight:700; color:#00E5FF; font-size:12px; text-transform:uppercase; letter-spacing:0.06em;">🔍 ALERT FILTERS</span>
</div>
""", unsafe_allow_html=True)

risk_filter = st.sidebar.multiselect(
    "Risk Level", ["High", "Medium", "Low"], default=["High", "Medium"]
)
status_filter = st.sidebar.selectbox(
    "Workflow Status", ["All", "new", "reviewing", "confirmed", "false_positive"], index=0
)
category_filter = st.sidebar.selectbox(
    "Threat Category",
    ["All", "drugs", "arms", "bank_account", "atm_card", "sim_card", "fake_documents", "net_banking_kit"],
    index=0
)
auto_refresh = st.sidebar.checkbox("⚡ Auto-refresh feed (every 5s)", value=True)

# Gated Reset Demo State & Scripted Post Injection: ONLY visible when DEMO_MODE=1
render_demo_maintenance_sidebar(db)


@st.fragment(run_every=5 if auto_refresh else None)
def render_live_feed(r_filter, s_filter, c_filter):
    with db.get_connection() as conn:
        query = """
        SELECT a.*, p.channel_id, p.platform, p.message_id, p.timestamp_utc, p.raw_text, p.normalized_text, p.ingestion_source,
               e.evidence_id, e.current_hash, e.block_height
        FROM alerts a
        JOIN posts p ON a.post_uid = p.post_uid
        LEFT JOIN evidence e ON a.post_uid = e.post_uid
        WHERE 1=1
        """
        params = []
        if r_filter:
            placeholders = ",".join("?" for _ in r_filter)
            query += f" AND a.risk_level IN ({placeholders})"
            params.extend(r_filter)
        if s_filter != "All":
            query += " AND a.status = ?"
            params.append(s_filter)
        if c_filter != "All":
            query += " AND a.category = ?"
            params.append(c_filter)

        query += " ORDER BY a.created_at DESC LIMIT 100"
        rows = conn.execute(query, tuple(params)).fetchall()
        alerts = [dict(r) for r in rows]

    current_count = len(alerts)
    last_count = st.session_state.get("last_seen_alert_count", None)
    if last_count is not None and current_count > last_count:
        new_diff = current_count - last_count
        if new_diff == 1:
            st.toast("🚨 New threat alert received! (+1 new)", icon="⚠️")
        else:
            st.toast(f"🚨 New threat alerts received! (+{new_diff} new)", icon="⚠️")
    st.session_state["last_seen_alert_count"] = current_count

    # Group identical ad text across channels into one alert card
    grouped_cards = []
    seen_groups = {}
    for a in alerts:
        n_text = (a.get("normalized_text") or a.get("raw_text") or "").strip().lower()
        cat = a.get("category", "")
        group_key = (n_text, cat)
        if group_key not in seen_groups:
            entry = {
                "primary": a,
                "channels": [a["channel_id"]],
                "all_alerts": [a]
            }
            seen_groups[group_key] = entry
            grouped_cards.append(entry)
        else:
            entry = seen_groups[group_key]
            if a["channel_id"] not in entry["channels"]:
                entry["channels"].append(a["channel_id"])
            entry["all_alerts"].append(a)

    # Top KPI Metrics Strip
    high_count = sum(1 for a in alerts if a["risk_level"] == "High")
    med_count = sum(1 for a in alerts if a["risk_level"] == "Medium")
    new_status_count = sum(1 for a in alerts if a["status"] == "new")

    mk1, mk2, mk3, mk4 = st.columns(4)
    with mk1:
        st.metric("Total Filtered Alerts", f"{len(alerts)}")
    with mk2:
        st.metric("Critical High Risk", f"{high_count}", delta="Priority Triage", delta_color="inverse")
    with mk3:
        st.metric("Medium Risk Alerts", f"{med_count}")
    with mk4:
        st.metric("Unreviewed (New)", f"{new_status_count}", delta=f"{len(grouped_cards)} Deduplicated")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    col_meta1, col_meta2 = st.columns([3, 1])
    with col_meta1:
        st.markdown(f"<span style='color:#94A3B8; font-size:13px;'>Showing <b>{len(alerts)}</b> raw detections grouped into <b>{len(grouped_cards)}</b> cross-channel campaigns.</span>", unsafe_allow_html=True)
    with col_meta2:
        if alerts:
            df_export = pd.DataFrame([{
                "alert_id": a["alert_id"],
                "channel": a["channel_id"],
                "platform": a["platform"],
                "category": a["category"],
                "risk_level": a["risk_level"],
                "status": a["status"],
                "timestamp": a["timestamp_utc"],
                "text": a["raw_text"],
                "evidence_hash": a.get("current_hash")
            } for a in alerts])
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Export Alerts (CSV)", csv_data, "threat_alerts.csv", "text/csv", use_container_width=True)

    st.divider()

    if not grouped_cards:
        st.info("No alerts found for the selected criteria.")
        return

    for card in grouped_cards:
        alert = card["primary"]
        card_class = "threat-card-high" if alert["risk_level"] == "High" else "threat-card-med" if alert["risk_level"] == "Medium" else "threat-card-low"
        risk_color = "#FF3366" if alert["risk_level"] == "High" else "#FFAA00" if alert["risk_level"] == "Medium" else "#00ADB5"
        post_uid = alert["post_uid"]
        other_channels = [ch for ch in card["channels"] if ch != alert["channel_id"]]

        # Fetch identifiers linked to this post
        idents = db.get_post_identifiers(post_uid)
        
        # Detect language and script for forensic badge
        raw_msg = alert.get('raw_text') or ''
        lang_tag, _ = detect_language_and_script(raw_msg)
        lang_code = lang_tag.value
        lang_display = "HI-LATN" if lang_code == "HI_LATN" else lang_code
        lang_color = "#38BDF8" if lang_code == "EN" else ("#F59E0B" if lang_code == "HI" else ("#10B981" if lang_code == "HI_LATN" else "#A855F7"))
        lang_badge = f'<span style="background-color:rgba(255,255,255,0.06); color:{lang_color}; border:1px solid {lang_color}; padding:2px 7px; border-radius:4px; font-weight:700; font-size:11px; margin-right:6px;">[{lang_display}]</span>'

        with st.container():
            cross_badge = ""
            if other_channels:
                cross_badge = f'<span style="background-color:rgba(255, 51, 102, 0.16); color:#FF80AA; border:1px solid rgba(255, 51, 102, 0.4); padding:2px 7px; border-radius:4px; font-weight:700; font-size:11px; margin-left:6px;">🔁 CROSS-CHANNEL (+{len(other_channels)} channels)</span>'

            # Identifiers HTML
            ident_htmls = []
            for i in idents:
                itype = i["type"]
                ival = i["normalized_value"]
                badge_class = "badge-upi" if "UPI" in itype else "badge-phone" if "Phone" in itype else "badge-crypto" if "Crypto" in itype else "badge-user"
                ident_htmls.append(f'<span class="badge-pill {badge_class}">{itype}: {html.escape(ival)}</span>')
            
            ident_block = f"<div style='margin-top:10px;'>{' '.join(ident_htmls)}</div>" if ident_htmls else ""

            # Evidence block link
            ev_html = ""
            if alert.get("current_hash"):
                ev_html = f"""
                <div style="margin-top:8px; font-size:11.5px; color:#64748B; font-family:'JetBrains Mono',monospace;">
                    🔒 Block #{alert.get('block_height')} &bull; SHA-256: <span style="color:#38BDF8;">{alert.get('current_hash')[:16]}...{alert.get('current_hash')[-8:]}</span>
                </div>
                """

            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                    <div>
                        <span style="font-weight:700; color:#F8FAFC; font-size:13.5px;">📢 {html.escape(str(alert['channel_id']))}</span>
                        <span style="color:#64748B; font-size:12px; margin: 0 4px;">&bull;</span>
                        <span style="color:#94A3B8; font-size:12px;">{html.escape(str(alert['platform']))}</span>
                        <span style="color:#64748B; font-size:12px; margin: 0 4px;">&bull;</span>
                        <span style="color:#64748B; font-size:12px; font-family:'JetBrains Mono',monospace;">{alert['timestamp_utc']}</span>
                        {cross_badge}
                    </div>
                    <div>
                        {lang_badge}
                        <span class="badge-pill badge-source">{alert['ingestion_source']}</span>
                        <span style="background-color:rgba({255 if alert['risk_level']=='High' else 255 if alert['risk_level']=='Medium' else 0}, {51 if alert['risk_level']=='High' else 170 if alert['risk_level']=='Medium' else 173}, {102 if alert['risk_level']=='High' else 0 if alert['risk_level']=='Medium' else 181}, 0.16); color:{risk_color}; border:1px solid {risk_color}; padding:2px 8px; border-radius:4px; font-weight:700; font-size:11px; letter-spacing:0.04em;">
                            [{alert['risk_level'].upper()}]
                        </span>
                    </div>
                </div>
                <div style="margin-top:10px; font-size:14px; color:#E2E8F0; line-height:1.45; background-color:rgba(0,0,0,0.22); padding:10px 12px; border-radius:6px; border:1px solid rgba(255,255,255,0.04);">
                    {html.escape(alert.get('raw_text') or '')}
                </div>
                {ident_block}
                {ev_html}
            </div>
            """, unsafe_allow_html=True)

            # Triage action toolbar
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
            with btn_col1:
                status_opts = ["new", "reviewing", "confirmed", "false_positive"]
                curr_st = alert.get("status", "new")
                st_idx = status_opts.index(curr_st) if curr_st in status_opts else 0
                new_st = st.selectbox(
                    "Status",
                    status_opts,
                    index=st_idx,
                    key=f"status_{alert['alert_id']}",
                    label_visibility="collapsed"
                )
                if new_st != alert.get("status"):
                    db.update_alert_status(alert["alert_id"], new_st, notes="Updated via Live Alerts UI")
                    st.toast(f"Updated alert {alert['alert_id']} to '{new_st}'", icon="✅")
                    st.rerun()

            with btn_col2:
                notes_val = alert.get("analyst_notes") or alert.get("notes") or ""
                notes_input = st.text_input(
                    "Triage Notes",
                    value=notes_val,
                    key=f"notes_{alert['alert_id']}",
                    placeholder="Add triage notes...",
                    label_visibility="collapsed"
                )
                if notes_input != notes_val and st.button("Save", key=f"btn_save_{alert['alert_id']}"):
                    db.update_alert_status(alert["alert_id"], alert.get("status", "new"), notes=notes_input)
                    st.toast(f"Notes saved for alert {alert['alert_id']}", icon="💾")
                    st.rerun()


render_live_feed(risk_filter, status_filter, category_filter)
