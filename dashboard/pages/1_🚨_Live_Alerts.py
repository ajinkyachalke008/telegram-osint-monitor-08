"""Page 1: Live Threat Alerts & Analyst Triage Workflow."""
import json
import html
import streamlit as st
import pandas as pd

from core.db import Database
from core.models import now_utc_iso

st.set_page_config(page_title="Live Alerts | TGSherlock", page_icon="🚨", layout="wide")

st.markdown("""
<style>
    .threat-card-high {
        background-color: #231215; border-left: 5px solid #FF3366;
        padding: 16px; border-radius: 8px; margin-bottom: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .threat-card-med {
        background-color: #242013; border-left: 5px solid #FFAA00;
        padding: 16px; border-radius: 8px; margin-bottom: 14px;
    }
    .threat-card-low {
        background-color: #14221A; border-left: 5px solid #00CC88;
        padding: 16px; border-radius: 8px; margin-bottom: 14px;
    }
    .badge-pill {
        display: inline-block; padding: 2px 7px; border-radius: 10px;
        font-size: 11px; font-weight: bold; margin-right: 5px; margin-bottom: 3px;
    }
    .badge-upi { background-color: #3E2723; color: #FFE082; border: 1px solid #FFE082; }
    .badge-phone { background-color: #372023; color: #FF8A80; border: 1px solid #FF8A80; }
    .badge-crypto { background-color: #261738; color: #EA80FC; border: 1px solid #EA80FC; }
    .badge-user { background-color: #102A43; color: #82B1FF; border: 1px solid #82B1FF; }
    .badge-source { background-color: #1C2833; color: #B0BEC5; border: 1px solid #455A64; }
</style>
""", unsafe_allow_html=True)

st.title("🚨 Live Threat Alerts & Triage Workflow")
st.caption("Actionable illegal trade detections across public channels with analyst confirmation workflow.")

db = Database()

# Sidebar Filters
st.sidebar.header("🔍 Alert Filters")
risk_filter = st.sidebar.multiselect(
    "Risk Level", ["High", "Medium", "Low"], default=["High", "Medium"]
)
status_filter = st.sidebar.selectbox(
    "Workflow Status", ["All", "new", "reviewing", "confirmed", "false_positive"], index=0
)
category_filter = st.sidebar.selectbox(
    "Category",
    ["All", "drugs", "arms", "bank_account", "atm_card", "sim_card", "fake_documents", "net_banking_kit"],
    index=0
)

# Fetch alerts
with db.get_connection() as conn:
    query = """
    SELECT a.*, p.channel_id, p.platform, p.message_id, p.timestamp_utc, p.raw_text, p.ingestion_source,
           e.evidence_id, e.current_hash, e.block_height
    FROM alerts a
    JOIN posts p ON a.post_uid = p.post_uid
    LEFT JOIN evidence e ON a.post_uid = e.post_uid
    WHERE 1=1
    """
    params = []
    if risk_filter:
        placeholders = ",".join("?" for _ in risk_filter)
        query += f" AND a.risk_level IN ({placeholders})"
        params.extend(risk_filter)
    if status_filter != "All":
        query += " AND a.status = ?"
        params.append(status_filter)
    if category_filter != "All":
        query += " AND a.category = ?"
        params.append(category_filter)

    query += " ORDER BY a.created_at DESC LIMIT 100"
    rows = conn.execute(query, tuple(params)).fetchall()
    alerts = [dict(r) for r in rows]

st.markdown(f"**Found {len(alerts)} alerts matching active filters.**")

# Export bar
col_exp1, col_exp2 = st.columns([1, 4])
with col_exp1:
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
        st.download_button("📥 Export Alerts (CSV)", csv_data, "threat_alerts.csv", "text/csv")

st.divider()

if not alerts:
    st.info("No alerts found for the selected criteria.")
else:
    for alert in alerts:
        card_class = "threat-card-high" if alert["risk_level"] == "High" else "threat-card-med" if alert["risk_level"] == "Medium" else "threat-card-low"
        post_uid = alert["post_uid"]

        # Fetch identifiers linked to this post
        idents = db.get_post_identifiers(post_uid)

        with st.container():
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span><b>📢 Channel:</b> {html.escape(str(alert['channel_id']))} &nbsp;|&nbsp; <b>Platform:</b> {html.escape(str(alert['platform']))} &nbsp;|&nbsp; <b>Time:</b> {alert['timestamp_utc']}</span>
                    <span>
                        <span class="badge-pill badge-source">{alert['ingestion_source']}</span>
                        <span style="font-weight:bold; color:{'#FF3366' if alert['risk_level'] == 'High' else '#FFAA00'};">[{alert['risk_level'].upper()}]</span>
                    </span>
                </div>
                <div style="margin-top:8px; font-size:15px;">
                    {html.escape(alert['raw_text'])}
                </div>
                <div style="margin-top:8px;">
                    <b>Category:</b> {alert['category']} &nbsp;|&nbsp; <b>Threat Score:</b> {alert['threat_score']:.1f}/10 &nbsp;|&nbsp; <b>Status:</b> <code>{alert['status']}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Identifiers row
            if idents:
                pills_html = "<div><b>Extracted Identifiers:</b> "
                for i in idents:
                    itype = i["type"]
                    val = i["normalized_value"]
                    bclass = "badge-upi" if itype == "UPI" else "badge-phone" if itype == "Phone" else "badge-crypto" if "Crypto" in itype else "badge-user"
                    cross_note = " 🚨(2+ Chans)" if i.get("cross_channel") else ""
                    pills_html += f'<span class="badge-pill {bclass}">{itype}: {html.escape(val)}{cross_note}</span> '
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)

            # Evidence block summary
            if alert.get("current_hash"):
                st.caption(f"🔒 **Evidence Block #{alert.get('block_height')}:** `{alert['current_hash']}`")

            # Analyst Workflow Action
            with st.expander(f"⚙️ Triage & Analyst Action for Alert {alert['alert_id']}"):
                act_col1, act_col2, act_col3 = st.columns([1, 2, 1])
                with act_col1:
                    new_status = st.selectbox(
                        "Update Status",
                        ["new", "reviewing", "confirmed", "false_positive"],
                        index=["new", "reviewing", "confirmed", "false_positive"].index(alert["status"]),
                        key=f"status_{alert['alert_id']}"
                    )
                with act_col2:
                    analyst_notes = st.text_input(
                        "Analyst Notes",
                        value=alert.get("analyst_notes") or "",
                        key=f"notes_{alert['alert_id']}"
                    )
                with act_col3:
                    st.write("")
                    st.write("")
                    if st.button("Save Verdict", key=f"btn_{alert['alert_id']}"):
                        db.update_alert_status(alert["alert_id"], new_status, analyst_notes)
                        db.log_audit("alert_status_change", {
                            "alert_id": alert["alert_id"],
                            "old_status": alert["status"],
                            "new_status": new_status,
                            "notes": analyst_notes
                        })
                        st.success(f"Status updated to '{new_status}'")
                        st.rerun()

            st.write("")
