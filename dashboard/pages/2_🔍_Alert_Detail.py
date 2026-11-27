"""Page 2: Forensic Alert Detail & Cryptographic Hash Chain Verifier."""
import sys
import json
import hashlib
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st

from core.db import Database
from addons.evidence import canonical_json, verify_evidence_record
from addons.financial_detector import FinancialAdDetector
from addons.pdf_exporter import generate_evidence_pdf
from addons.ocr_extractor import OCRExtractor
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme

st.set_page_config(page_title="Alert Detail & Hash Ledger | telegram-osint-monitor-08", page_icon="🔍", layout="wide")

# Inject Master Theme
inject_theme()

# Standard Provenance Banner
render_provenance_banner(page_title="Alert Detail", active_stream="VERIFIED-SYNTHETIC")

st.title("🔍 Forensic Alert Detail & Evidence Seal Verifier")
st.caption("RFC-8785 canonical evidence inspection, cryptographic hash verification, and Section 63 BSA evidence package export.")

db = Database()
fin_detector = FinancialAdDetector()
ocr_extractor = OCRExtractor()
ocr_status = ocr_extractor.get_detection_status()

# Query latest Chain Head Hash
with db.get_connection() as conn:
    head_row = conn.execute("SELECT current_hash, block_height FROM evidence ORDER BY block_height DESC LIMIT 1").fetchone()
    chain_head_hash = head_row["current_hash"] if head_row else "GENESIS"
    chain_head_block = head_row["block_height"] if head_row else 0

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

# Alert Selector Card
st.markdown("""
<div style="background-color:#0D1424; border:1px solid #1E2B45; border-radius:8px; padding:14px 18px; margin-bottom:16px;">
    <span style="font-size:11.5px; font-weight:700; color:#00E5FF; text-transform:uppercase; letter-spacing:0.06em;">TARGET INVESTIGATION RECORD</span>
</div>
""", unsafe_allow_html=True)

alert_options = {f"{a['alert_id']} | [{a['risk_level']}] {a['category']} ({a['channel_id']})": a for a in alerts}
selected_key = st.selectbox("Select Alert Record to Inspect", list(alert_options.keys()), label_visibility="collapsed")
alert = alert_options[selected_key]

st.divider()

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📄 Raw Post & Metadata")
    
    # Metadata Card
    st.markdown(f"""
    <div class="intel-card" style="padding:14px 18px; margin-bottom:14px;">
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:12.5px;">
            <div><span style="color:#64748B;">Post UID:</span><br><code style="color:#E2E8F0;">{alert['post_uid']}</code></div>
            <div><span style="color:#64748B;">Channel / Source:</span><br><b style="color:#00ADB5;">{alert['channel_id']}</b> ({alert['platform']})</div>
            <div><span style="color:#64748B;">Timestamp (UTC):</span><br><span style="font-family:'JetBrains Mono',monospace; color:#94A3B8;">{alert['timestamp_utc']}</span></div>
            <div><span style="color:#64748B;">Data Provenance:</span><br><span class="badge-pill badge-source">{alert['ingestion_source']}</span></div>
            <div><span style="color:#64748B;">Risk Level:</span><br><b style="color:{'#FF3366' if alert.get('risk_level')=='High' else '#FFAA00'};">[{str(alert.get('risk_level') or 'LOW').upper()}]</b></div>
            <div><span style="color:#64748B;">Threat Score:</span><br><b style="color:#F8FAFC;">{float(alert.get('threat_score') or 0.0):.1f} / 10.0</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Message Content")
    st.text_area("Content", alert["raw_text"], height=130, disabled=True, label_visibility="collapsed")

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

    # OCR Subsystem Status
    st.markdown("#### 🖼️ Image OCR Capability Status")
    if not ocr_status["tesseract_binary_detected"]:
        st.info(f"ℹ️ **OCR Engine:** `{ocr_status['engine']}` (System Tesseract binary not installed on host. Multilingual extraction disabled).")
    else:
        st.success(f"✅ **OCR Engine Active:** Tesseract `{ocr_status['tesseract_binary_path']}` (languages: {ocr_status['supported_languages']})")

with col_right:
    st.subheader("🔒 Cryptographic Evidence Ledger (RFC-8785)")
    if not alert.get("current_hash"):
        st.warning("No evidence block sealed for this post.")
    else:
        # Fixed literal code tag defect and long hash wrapping
        st.markdown(f"""
        <div class="intel-card" style="padding:14px 18px; margin-bottom:14px;">
            <div style="font-size:12px; color:#94A3B8; margin-bottom:4px;">
                <b>EVIDENCE BLOCK HEIGHT:</b> <span style="color:#00E5FF; font-weight:700;">#{alert['block_height']}</span> &bull; 
                <b>GENERATED (UTC):</b> <span style="font-family:'JetBrains Mono',monospace;">{alert['generated_at_utc']}</span>
            </div>
            <div style="margin-top:8px;">
                <span style="color:#64748B; font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">Previous Hash:</span>
                <div class="hash-container">{alert['prev_hash']}</div>
            </div>
            <div style="margin-top:4px;">
                <span style="color:#64748B; font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">Current Sealed Hash:</span>
                <div class="hash-container" style="color:#34D399; border-color:rgba(16,185,129,0.3);">{alert['current_hash']}</div>
            </div>
            <div style="margin-top:4px;">
                <span style="color:#64748B; font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">Ledger Chain-Head Hash:</span>
                <div class="hash-container" style="color:#00E5FF;">{chain_head_hash}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Live Verification Action
        if st.button("🛡️ Verify Cryptographic Seal Live", use_container_width=True, type="primary"):
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

        st.divider()
        st.subheader("📄 Section 63 BSA Evidence Package")
        idents = db.get_post_identifiers(alert["post_uid"])
        pdf_bytes = generate_evidence_pdf(
            alert=alert,
            evidence={
                "current_hash": alert.get("current_hash"),
                "prev_hash": alert.get("prev_hash"),
                "canonical_json": alert.get("canonical_json"),
                "block_height": alert.get("block_height"),
                "generated_at_utc": alert.get("generated_at_utc"),
            },
            identifiers=idents,
            chain_head_hash=chain_head_hash,
        )
        st.download_button(
            label="📥 Export Section 63 BSA Evidence Package (PDF)",
            data=pdf_bytes,
            file_name=f"evidence_package_{alert['alert_id']}.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Evidence package to support a Section 63 BSA certificate (signed by the person in charge and an expert). Not legal advice."
        )
        st.caption("⚖️ *Evidence package to support a Section 63 BSA certificate (signed by the person in charge and an expert). Not legal advice.*")
