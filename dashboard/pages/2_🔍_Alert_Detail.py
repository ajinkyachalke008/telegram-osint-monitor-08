"""Page 2: Forensic Alert Detail & Cryptographic Hash Chain Verifier."""
import json
import hashlib
import streamlit as st

from core.db import Database
from addons.evidence import canonical_json_dumps, verify_evidence_record
from addons.financial_detector import FinancialAdDetector

st.set_page_config(page_title="Alert Detail & Hash Ledger | TGSherlock", page_icon="🔍", layout="wide")

st.title("🔍 Forensic Alert Detail & Evidence Seal Verifier")
st.caption("RFC-8785 canonical evidence inspection, cryptographic hash verification, and deep financial signals.")

db = Database()
fin_detector = FinancialAdDetector()

# Select Alert
with db.get_connection() as conn:
    rows = conn.execute(
        """
        SELECT a.alert_id, a.post_uid, a.category, a.risk_level, a.threat_score, a.status,
               p.channel_id, p.platform, p.message_id, p.timestamp_utc, p.raw_text, p.ingestion_source,
               e.evidence_id, e.canonical_json, e.current_hash, e.prev_hash, e.block_height, e.generated_at_utc
        FROM alerts a
        JOIN posts p ON a.post_uid = p.post_uid
        LEFT JOIN evidence e ON a.post_uid = e.post_uid
        ORDER BY a.created_at DESC LIMIT 100
        """
    ).fetchall()
    alerts = [dict(r) for r in rows]

if not alerts:
    st.warning("No alerts available in database. Run ingestion or synthetic replay first.")
    st.stop()

alert_options = {f"{a['alert_id']} | [{a['risk_level']}] {a['category']} ({a['channel_id']})": a for a in alerts}
selected_key = st.selectbox("Select Alert Record to Inspect", list(alert_options.keys()))
alert = alert_options[selected_key]

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📄 Raw Post & Metadata")
    st.markdown(f"**Post UID:** `{alert['post_uid']}`")
    st.markdown(f"**Channel / Source:** `{alert['channel_id']}` ({alert['platform']})")
    st.markdown(f"**Timestamp (UTC):** `{alert['timestamp_utc']}`")
    st.markdown(f"**Provenance:** `{alert['ingestion_source']}`")
    st.markdown(f"**Risk Level:** `{alert['risk_level']}` | **Threat Score:** `{alert['threat_score']:.1f}/10`")
    
    st.markdown("#### Message Text")
    st.text_area("Content", alert["raw_text"], height=130, disabled=True)

    # Financial Signal Extraction
    fin_res = fin_detector.detect(alert["raw_text"])
    st.markdown("#### 💼 Financial Ad Analysis (R3)")
    if fin_res.is_financial_ad:
        if fin_res.mule_recruitment_pattern:
            st.error("🚨 **MULE RECRUITMENT PATTERN DETECTED** (High Confidence)")
        else:
            st.warning(f"Financial Trade Signal Detected: Intent '{fin_res.intent}'")

        st.markdown(f"• **Intent:** `{fin_res.intent}`")
        st.markdown(f"• **Instruments:** `{', '.join(fin_res.instruments) if fin_res.instruments else 'None'}`")
        st.markdown(f"• **Signals:** `{list(fin_res.signals.keys())}`")
        
        if fin_res.evidence_spans:
            with st.expander("📍 Evidentiary Text Spans & Character Offsets"):
                for sp in fin_res.evidence_spans:
                    st.code(f"[{sp.signal_type}] offset {sp.start}:{sp.end} -> \"{sp.text}\"")
    else:
        st.info("No illicit financial recruitment signals detected in this post.")

with col_right:
    st.subheader("🔒 Cryptographic Evidence Ledger (RFC-8785)")
    if not alert.get("current_hash"):
        st.warning("No evidence block sealed for this post.")
    else:
        st.markdown(f"**Evidence Block Height:** `#{alert['block_height']}`")
        st.markdown(f"**Generated UTC:** `{alert['generated_at_utc']}`")
        st.markdown(f"**Previous Hash:** `{alert['prev_hash']}`")
        st.markdown(f"**Current Hash:** `{alert['current_hash']}`")

        # Live Verification Action
        if st.button("🛡️ Verify Cryptographic Seal Live"):
            c_json = alert.get("canonical_json", "")
            payload_str = f"{c_json}:{alert['prev_hash']}"
            computed_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            if computed_hash == alert["current_hash"]:
                st.success(f"✅ **EVIDENCE VERIFIED:** SHA-256 seal matches exactly. Block #{alert['block_height']} is tamper-evident and chained to parent.")
            else:
                st.error(f"❌ **HASH MISMATCH:** Computed `{computed_hash}` does not match stored `{alert['current_hash']}`. Possible tampering detected!")

        st.markdown("#### Canonical RFC-8785 Deterministic Payload")
        try:
            parsed_canonical = json.loads(alert.get("canonical_json") or "{}")
            st.json(parsed_canonical)
        except Exception:
            st.code(alert.get("canonical_json") or "{}")
