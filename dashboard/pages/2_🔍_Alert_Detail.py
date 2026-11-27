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

st.set_page_config(page_title="Alert Detail & Hash Ledger | telegram-osint-monitor-08", page_icon="🔍", layout="wide")

# Standard Provenance Banner
render_provenance_banner(page_title="Alert Detail", active_stream="VERIFIED-SYNTHETIC")

st.title("🔍 Forensic Alert Detail & Evidence Seal Verifier")
st.caption("RFC-8785 canonical evidence inspection, cryptographic hash verification, and Section 63 BSA 2023 evidence package export.")

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
               p.media_path, p.media_hash, p.source_metadata_json,
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
    source_metadata = json.loads(alert.get('source_metadata_json') or '{}')
    if source_metadata:
        st.write('Original sender:', source_metadata.get('sender_name') or source_metadata.get('author') or 'Not supplied')
        if source_metadata.get('sender_id'):
            st.write('Export sender account ID:', source_metadata['sender_id'])
        if source_metadata.get('forwarded_from'):
            st.write('Forwarded from:', source_metadata['forwarded_from'])
        if source_metadata.get('edited_at'):
            st.write('Edited at (source timezone):', source_metadata['edited_at'])
        with st.expander('Source metadata, OCR and attachment integrity'):
            st.json({key: value for key, value in source_metadata.items() if key != 'text_entities'})
            if source_metadata.get('text_entities'):
                st.caption('Preserved Telegram text entity segments:', len(source_metadata['text_entities']))
            st.write('Stored media SHA-256:', alert.get('media_hash') or 'No media')
            if source_metadata.get('ocr_text'):
                st.text_area('OCR analysis text', source_metadata['ocr_text'], height=140, disabled=True)
            media_path = alert.get('media_path')
            if media_path and Path(media_path).is_file():
                st.image(media_path, caption='Original imported attachment', use_container_width=True)
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
        st.markdown(f"**Evidence Block Height:** `#{alert['block_height']}`")
        st.markdown(f"**Generated UTC:** `{alert['generated_at_utc']}`")
        st.markdown(f"**Previous Hash:** `{alert['prev_hash']}`")
        st.markdown(f"**Current Hash:** `{alert['current_hash']}`")
        st.markdown(f"**Ledger Chain-Head:** `<code>{chain_head_hash}</code>` (Block #{chain_head_block})")

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

        st.divider()
        st.subheader("📄 Section 63 BSA 2023 Evidence Package")
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
            label="📥 Export Section 63 BSA 2023 Evidence Package (PDF)",
            data=pdf_bytes,
            file_name=f"evidence_package_{alert['alert_id']}.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Evidence package prepared to support a Section 63 BSA 2023 certificate (must be signed by the responsible person and an expert). Not legal advice."
        )
        st.caption("⚖️ *Evidence package prepared to support a Section 63 BSA 2023 certificate (must be signed by the responsible person and an expert). Not legal advice.*")
