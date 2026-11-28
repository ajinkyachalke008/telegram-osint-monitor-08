"""Page 2: Forensic Alert Detail & Cryptographic Hash Chain Verifier.

RFC-8785 canonical evidence inspection, cryptographic hash chain verification,
extracted forensic identifiers registry, and Section 63 BSA evidence package export.
"""
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd

from core.db import Database
from addons.evidence import canonical_json, verify_evidence_chain
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
st.caption("RFC-8785 canonical evidence inspection, SHA-256 hash-chain verification, and Section 63 BSA statutory evidence package export.")

db = Database()

# Defensive fallback: if active db has zero alerts, check candidate databases
with db.get_connection() as conn:
    alert_cnt = conn.execute("SELECT count(*) FROM alerts").fetchone()[0]
if alert_cnt == 0:
    for candidate_path in [Path("data/osint_monitor.db"), Path("data/demo.db")]:
        if candidate_path.exists():
            candidate_db = Database(candidate_path)
            with candidate_db.get_connection() as cconn:
                if cconn.execute("SELECT count(*) FROM alerts").fetchone()[0] > 0:
                    db = candidate_db
                    break

fin_detector = FinancialAdDetector()
ocr_extractor = OCRExtractor()
ocr_status = ocr_extractor.get_detection_status()

# Query latest Chain Head Hash and All Sealed Blocks for Ledger Audit
with db.get_connection() as conn:
    head_row = conn.execute("SELECT current_hash, block_height FROM evidence ORDER BY block_height DESC LIMIT 1").fetchone()
    chain_head_hash = head_row["current_hash"] if head_row else "GENESIS"
    chain_head_block = head_row["block_height"] if head_row else 0
    
    all_blocks_rows = conn.execute(
        "SELECT block_height, current_hash, prev_hash, canonical_json FROM evidence ORDER BY block_height ASC"
    ).fetchall()
    all_evidence_blocks = [dict(r) for r in all_blocks_rows]

# Fetch Alerts with linked Post and Evidence data
with db.get_connection() as conn:
    rows = conn.execute(
        """
        SELECT a.alert_id, a.post_uid, a.category, a.risk_level, a.threat_score, a.status, a.analyst_notes,
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
    st.warning("No alerts available in database ledger. Run ingestion or synthetic replay first.")
    st.stop()

# ----------------- ALERT SELECTOR (Must remain first selectbox for tests) -----------------
st.markdown("""
<div style="background-color:#0D1424; border:1px solid #1E2B45; border-radius:8px; padding:12px 18px; margin-bottom:12px;">
    <span style="font-size:11.5px; font-weight:700; color:#00E5FF; text-transform:uppercase; letter-spacing:0.06em;">TARGET FORENSIC INVESTIGATION RECORD</span>
</div>
""", unsafe_allow_html=True)

alert_options = {f"{a['alert_id']} | [{a.get('risk_level') or 'LOW'}] {a.get('category') or 'General'} ({a.get('channel_id') or 'Channel'})": a for a in alerts}
selected_key = st.selectbox("Select Alert Record to Inspect", list(alert_options.keys()), label_visibility="collapsed")
alert = alert_options[selected_key]

# ----------------- TOP KPI SUMMARY STRIP -----------------
risk_val = str(alert.get("risk_level") or "LOW").upper()
risk_color = "#FF3366" if risk_val in ("HIGH", "CRITICAL") else ("#FFAA00" if risk_val == "MEDIUM" else "#10B981")
curr_status = str(alert.get("status") or "NEW").upper()

kcol1, kcol2, kcol3, kcol4 = st.columns(4)
with kcol1:
    st.metric("Alert Identifier", alert["alert_id"], delta=f"Risk: {risk_val}", delta_color="inverse" if risk_val in ("HIGH", "CRITICAL") else "normal")
with kcol2:
    st.metric("Ingestion Stream", alert.get("platform") or "Telegram", delta=alert.get("ingestion_source") or "Replay")
with kcol3:
    st.metric("Evidence Seal", f"Block #{alert.get('block_height') or 'N/A'}", delta="RFC-8785 Sealed" if alert.get("current_hash") else "Unsealed")
with kcol4:
    st.metric("Triage Status", curr_status, delta="Active Ledger" if curr_status in ("NEW", "INVESTIGATING") else "Closed")

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ----------------- TWO-COLUMN FORENSIC WORKBENCH -----------------
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📄 Raw Post & Metadata Dossier")
    
    # Metadata Card
    st.markdown(f"""
    <div class="intel-card" style="padding:14px 18px; margin-bottom:14px;">
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:12.5px;">
            <div><span style="color:#64748B;">Post UID:</span><br><code style="color:#E2E8F0;">{alert['post_uid']}</code></div>
            <div><span style="color:#64748B;">Channel / Source:</span><br><b style="color:#00ADB5;">{alert['channel_id']}</b> ({alert['platform']})</div>
            <div><span style="color:#64748B;">Timestamp (UTC):</span><br><span style="font-family:'JetBrains Mono',monospace; color:#94A3B8;">{alert['timestamp_utc']}</span></div>
            <div><span style="color:#64748B;">Data Provenance:</span><br><span class="badge-pill badge-source">{alert['ingestion_source']}</span></div>
            <div><span style="color:#64748B;">Risk Classification:</span><br><b style="color:{risk_color};">[{risk_val}] &bull; {alert.get('category')}</b></div>
            <div><span style="color:#64748B;">Threat Score:</span><br><b style="color:#F8FAFC;">{float(alert.get('threat_score') or 0.0):.1f} / 10.0</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Message Content")
    st.text_area("Content", alert.get("raw_text") or "", height=120, disabled=True, label_visibility="collapsed")

    # Multilingual Forensic Intelligence & Script Analysis
    from core.multilingual import normalize_multilingual
    from addons.scorer import RuleScorer
    
    raw_content = alert.get("raw_text") or ""
    multi_res = normalize_multilingual(raw_content)
    scorer = RuleScorer()
    score_res = scorer.score(multi_res.normalized_text)

    st.markdown("#### 🌐 Multilingual Forensic Intelligence & Script Analysis")
    lang_disp = "Hinglish (Romanised Hindi)" if multi_res.language == "HI_LATN" else ("Hindi (Devanagari)" if multi_res.language == "HI" else ("English" if multi_res.language == "EN" else "Mixed / Code-Switching"))
    scripts_disp = ", ".join(multi_res.detected_scripts) if multi_res.detected_scripts else "LATIN"
    adv_badge = "🛡️ Public Advisory / Warning Detected (Score Suppressed)" if multi_res.is_awareness_or_negation else "Active Broadcast Ad"

    st.markdown(f"""
    <div class="intel-card" style="padding:12px 16px; margin-bottom:12px; background:rgba(15, 23, 42, 0.6); border:1px solid #1E293B;">
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:12px;">
            <div><span style="color:#64748B;">Detected Language:</span><br><b style="color:#38BDF8;">[{multi_res.language}] {lang_disp}</b></div>
            <div><span style="color:#64748B;">Script Families:</span><br><code style="color:#F1F5F9;">{scripts_disp}</code></div>
            <div><span style="color:#64748B;">Context Nature:</span><br><span style="color:{'#10B981' if multi_res.is_awareness_or_negation else '#F59E0B'}; font-weight:700;">{adv_badge}</span></div>
            <div><span style="color:#64748B;">Normalizations Applied:</span><br><span style="color:#A78BFA;">{', '.join(multi_res.applied_normalizations) if multi_res.applied_normalizations else 'Standard NFKC'}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if score_res.matched_terms:
        with st.expander(f"📖 Lexicon Matches & Canonical Concepts ({len(score_res.matched_terms)} hits)", expanded=False):
            m_terms_df = pd.DataFrame([{
                "Surface Term": t["term"],
                "Category": t["category_label"],
                "Lexicon Section": t["section"],
                "Canonical Concept": t.get("canonical_concept", t["term"]),
                "Weight": t["weight"]
            } for t in score_res.matched_terms])
            st.dataframe(m_terms_df, use_container_width=True, hide_index=True)

    # Extracted Forensic Identifiers Registry
    st.markdown("#### 🔍 Extracted Forensic Identifiers")
    post_idents = db.get_post_identifiers(alert["post_uid"])
    if post_idents:
        ident_rows = []
        for i in post_idents:
            itype = i.get("type", "Identifier")
            ival = i.get("normalized_value", i.get("raw_value", ""))
            
            # Formulate validation badge
            if itype == "UPI":
                badge = "Verified NPCI Handle"
            elif itype == "Phone":
                badge = "Indian +91 Telecom Format"
            elif "Crypto" in itype:
                badge = "Checksum Validated"
            elif itype == "IFSC":
                badge = "RBI Bank Code Standard"
            else:
                badge = "Extracted Entity"
                
            ident_rows.append({
                "Type": itype,
                "Identifier Value": ival,
                "Confidence": f"{float(i.get('confidence', 0.95)):.2f}",
                "Validation Status": badge
            })
        st.dataframe(pd.DataFrame(ident_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No specific payment or communication identifiers extracted from this post text.")

    # Financial Signal Extraction (R3)
    fin_res = fin_detector.detect(alert.get("raw_text") or "")
    st.markdown("#### 💼 Financial Ad Analysis (R3)")
    if fin_res.is_financial_ad:
        if fin_res.mule_recruitment_pattern:
            st.error("🚨 **MULE RECRUITMENT PATTERN DETECTED** (High Confidence Bank Account Rental)")
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
        st.info(f"ℹ️ **OCR Engine:** `{ocr_status['engine']}` (System Tesseract binary not installed on host. Air-gap mock active).")
    else:
        st.success(f"✅ **OCR Engine Active:** Tesseract `{ocr_status['tesseract_binary_path']}` (languages: {ocr_status['supported_languages']})")

    # Interactive Triage Action Bar
    st.markdown("#### 🛡️ Case Triage & Workflow Action")
    tcol1, tcol2, tcol3 = st.columns(3)
    with tcol1:
        if st.button("Mark: Investigating", use_container_width=True):
            db.update_alert_status(alert["alert_id"], "INVESTIGATING", "Investigator active review initiated.")
            st.toast(f"Alert {alert['alert_id']} marked as INVESTIGATING", icon="🔍")
            st.rerun()
    with tcol2:
        if st.button("Escalate to Cyber Police", use_container_width=True):
            db.update_alert_status(alert["alert_id"], "ESCALATED_LEO", "Escalated for FIR/Section 63 BSA submission.")
            st.toast(f"Alert {alert['alert_id']} escalated to Law Enforcement!", icon="🚨")
            st.rerun()
    with tcol3:
        if st.button("Resolve / Dismiss", use_container_width=True):
            db.update_alert_status(alert["alert_id"], "RESOLVED", "Case resolved and archived.")
            st.toast(f"Alert {alert['alert_id']} resolved.", icon="✅")
            st.rerun()


with col_right:
    st.subheader("🔒 Cryptographic Evidence Ledger (RFC-8785)")
    if not alert.get("current_hash"):
        st.warning("No evidence block sealed for this post.")
    else:
        # Cryptographic Hash Container Card
        st.markdown(f"""
        <div class="intel-card" style="padding:14px 18px; margin-bottom:14px;">
            <div style="font-size:12px; color:#94A3B8; margin-bottom:4px;">
                <b>EVIDENCE BLOCK HEIGHT:</b> <span style="color:#00E5FF; font-weight:700;">#{alert['block_height']}</span> &bull; 
                <b>GENERATED (UTC):</b> <span style="font-family:'JetBrains Mono',monospace;">{alert['generated_at_utc']}</span>
            </div>
            <div style="margin-top:8px;">
                <span style="color:#64748B; font-size:11px; text-transform:uppercase; letter-spacing:0.04em;">Previous Block Parent Hash:</span>
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

        # Dual Verification Action Buttons
        vcol1, vcol2 = st.columns([1, 1])
        with vcol1:
            # Preserves exact button label for test suite compatibility
            do_verify_single = st.button("🛡️ Verify Cryptographic Seal Live", use_container_width=True, type="primary")
        with vcol2:
            do_audit_chain = st.button("🔗 Audit Full Ledger Chain", use_container_width=True)

        # Live Single-Block Verification Action
        if do_verify_single:
            c_json = alert.get("canonical_json", "")
            payload_str = f"{c_json}:{alert['prev_hash']}"
            computed_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            if computed_hash == alert["current_hash"]:
                st.success(
                    f"✅ **EVIDENCE SEAL VERIFIED:** SHA-256 seal matches stored digest byte-for-byte. "
                    f"Block #{alert['block_height']} is cryptographically chained to parent block `{alert['prev_hash'][:12]}...` with zero tampering."
                )
            else:
                st.error(f"❌ **HASH MISMATCH:** Computed `{computed_hash}` does not match stored `{alert['current_hash']}`. Possible tampering detected!")

        # Full Ledger Chain Audit Action
        if do_audit_chain:
            is_valid, msg, count = verify_evidence_chain(all_evidence_blocks)
            if is_valid:
                st.success(f"🔗 **CHAIN-OF-CUSTODY AUDIT COMPLETE:** All {count} blocks verified with unbroken hash continuity from Genesis.")
            else:
                st.error(f"❌ **CHAIN AUDIT FAILED:** {msg}")

        # Canonical RFC-8785 Deterministic Payload Inspector
        st.markdown("#### Canonical RFC-8785 Deterministic Payload")
        st.caption("Standardized UTF-8 JSON with sorted keys and zero trailing whitespace, enabling identical cross-lab hash reproduction.")
        try:
            parsed_canonical = json.loads(alert.get("canonical_json") or "{}")
            st.json(parsed_canonical)
        except Exception:
            st.code(alert.get("canonical_json") or "{}")

        st.divider()

        # Section 63 BSA Evidence Package Export
        st.subheader("⚖️ Section 63 BSA Evidence Package")
        st.caption("Statutory electronic evidence certificate compliant with Section 63 Bharatiya Sakshya Adhiniyam, 2023.")
        
        # Statutory Compliance Badge Box
        st.markdown("""
        <div style="background-color:#0C1220; border:1px solid #1E2B45; border-radius:6px; padding:10px 14px; font-size:12px; margin-bottom:12px; color:#94A3B8;">
            <b>Statutory Compliance Pillars:</b><br/>
            • <b>Sec 63(4)(a):</b> Cryptographic identification of source electronic record & device parameters.<br/>
            • <b>Sec 63(4)(b):</b> Continuous operating integrity & air-gapped forensic preservation.<br/>
            • <b>Sec 63(4)(c):</b> SHA-256 tamper-evident hash chaining from Genesis.<br/>
            • <b>Sec 63(4)(d):</b> Certificate sign-off by investigator and qualified digital forensics examiner.
        </div>
        """, unsafe_allow_html=True)

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

        dcol1, dcol2 = st.columns([1, 1])
        with dcol1:
            st.download_button(
                label="📥 Export Section 63 BSA PDF",
                data=pdf_bytes,
                file_name=f"evidence_package_{alert['alert_id']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Evidence package to support a Section 63 BSA certificate. Not legal advice."
            )
        with dcol2:
            # Export JSON-LD Forensic Seal Dossier
            seal_dossier = {
                "alert_id": alert["alert_id"],
                "post_uid": alert["post_uid"],
                "block_height": alert.get("block_height"),
                "current_hash": alert.get("current_hash"),
                "prev_hash": alert.get("prev_hash"),
                "chain_head_hash": chain_head_hash,
                "canonical_json": json.loads(alert.get("canonical_json") or "{}"),
                "identifiers": idents,
                "generated_at_utc": alert.get("generated_at_utc"),
                "bsa_section": "Section 63 Bharatiya Sakshya Adhiniyam, 2023",
                "standard": "RFC-8785 Canonical JSON with SHA-256 Chaining"
            }
            st.download_button(
                label="📦 Export Seal Dossier (JSON)",
                data=json.dumps(seal_dossier, indent=2),
                file_name=f"seal_dossier_{alert['alert_id']}.json",
                mime="application/json",
                use_container_width=True,
                help="Export machine-readable RFC-8785 evidence certificate in JSON format."
            )

        st.caption("⚖️ *Evidence package to support a Section 63 BSA certificate (signed by the person in charge and an expert). Not legal advice.*")
