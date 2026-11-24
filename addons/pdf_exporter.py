"""Forensic PDF Evidence Export Module for Law Enforcement OSINT.

Generates official evidence packages prepared to support a Section 63 BSA 2023 certificate:
- Case / Alert Reference ID and timestamp
- Cryptographic hash-chain evidence seal (RFC-8785 Canonical JSON + SHA-256)
- Chain-Head SHA-256 anchor
- Intercepted message details and forensic text verbatim
- Extracted actionable identifiers (UPI, Phone, Crypto, IFSC, Location)
- Legal disclaimer: Prepared to support a Section 63 BSA 2023 certificate (must be signed
  by the responsible person and an expert). Not legal advice.
"""
import io
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)


def generate_evidence_pdf(
    alert: Dict[str, Any],
    evidence: Optional[Dict[str, Any]] = None,
    identifiers: Optional[List[Dict[str, Any]]] = None,
    chain_head_hash: Optional[str] = None,
) -> bytes:
    """
    Generate an in-memory PDF evidence report.
    Returns bytes of the compiled PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F2027"),
    )
    sub_header_style = ParagraphStyle(
        "SubHeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1A365D"),
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
    )
    code_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.0,
        leading=10,
        textColor=colors.HexColor("#1A202C"),
    )
    legal_style = ParagraphStyle(
        "LegalNotice",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#4A5568"),
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("🛡️ telegram-osint-monitor-08 Threat Intelligence", header_style))
    elements.append(Paragraph("FORENSIC EVIDENCE PACKAGE // SECTION 63 BSA 2023 SUPPORTING DOSSIER", sub_header_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#00ADB5"), spaceAfter=14))

    # Alert Metadata Table
    alert_id = alert.get("alert_id", "ALT-UNKNOWN")
    risk_level = alert.get("risk_level", "High")
    category = alert.get("category", "General").upper()
    platform = alert.get("platform", "Telegram")
    channel = alert.get("channel_id", "Unknown")
    msg_id = alert.get("message_id", "N/A")
    ts_utc = alert.get("timestamp_utc", datetime.now(timezone.utc).isoformat())
    score = alert.get("threat_score", 0.0)

    risk_bg = colors.HexColor("#E53E3E") if risk_level == "High" else colors.HexColor("#DD6B20") if risk_level == "Medium" else colors.HexColor("#38A169")

    meta_data = [
        [
            Paragraph("<b>Case / Alert ID:</b>", body_style),
            Paragraph(f"<code>{alert_id}</code>", code_style),
            Paragraph("<b>Risk Tier:</b>", body_style),
            Paragraph(f"<font color='{risk_bg.hexval()}'><b>{risk_level.upper()}</b></font>", body_style),
        ],
        [
            Paragraph("<b>Threat Category:</b>", body_style),
            Paragraph(f"<b>{category}</b>", body_style),
            Paragraph("<b>Threat Score:</b>", body_style),
            Paragraph(f"{score:.2f} / 10.0", body_style),
        ],
        [
            Paragraph("<b>Target Channel:</b>", body_style),
            Paragraph(f"<code>{channel}</code> ({platform})", body_style),
            Paragraph("<b>Message ID:</b>", body_style),
            Paragraph(f"#{msg_id}", body_style),
        ],
        [
            Paragraph("<b>Intercept Timestamp:</b>", body_style),
            Paragraph(f"{ts_utc}", body_style),
            Paragraph("<b>Provenance:</b>", body_style),
            Paragraph(f"<b>{alert.get('ingestion_source', 'IMPORTED')}</b>", body_style),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[110, 160, 90, 170])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 14))

    # Cryptographic Chain of Custody Seal
    elements.append(Paragraph("🔒 Cryptographic Evidence Seal & Chain of Custody", section_style))
    elements.append(Spacer(1, 6))

    cur_hash = "N/A"
    prev_hash = "N/A"
    canon_json = "{}"
    block_h = 1
    sealed_at = ts_utc

    if evidence:
        cur_hash = evidence.get("current_hash", "N/A")
        prev_hash = evidence.get("prev_hash", "N/A")
        canon_json = evidence.get("canonical_json", "{}")
        block_h = evidence.get("block_height", 1)
        sealed_at = evidence.get("generated_at_utc", ts_utc)

        # Re-compute to verify
        payload = f"{canon_json}:{prev_hash}"
        recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        is_verified = (recomputed == cur_hash)

        ev_rows = [
            [Paragraph("<b>Block Height:</b>", body_style), Paragraph(f"#{block_h}", body_style)],
            [Paragraph("<b>Sealed Timestamp:</b>", body_style), Paragraph(f"{sealed_at}", body_style)],
            [Paragraph("<b>Integrity Status:</b>", body_style), Paragraph(f"<b>{'VALID &amp; INTACT (100% Cryptographic Match) ✅' if is_verified else 'CORRUPTED / TAMPERED ❌'}</b>", body_style)],
            [Paragraph("<b>Current SHA-256:</b>", body_style), Paragraph(f"<code>{cur_hash}</code>", code_style)],
            [Paragraph("<b>Previous SHA-256:</b>", body_style), Paragraph(f"<code>{prev_hash}</code>", code_style)],
        ]
        if chain_head_hash:
            ev_rows.append([Paragraph("<b>Chain-Head SHA-256:</b>", body_style), Paragraph(f"<code>{chain_head_hash}</code>", code_style)])
        ev_rows.append([Paragraph("<b>RFC-8785 JSON:</b>", body_style), Paragraph(f"<code>{canon_json}</code>", code_style)])
    else:
        ev_rows = [
            [Paragraph("<b>Status:</b>", body_style), Paragraph("No cryptographic ledger block recorded for this alert.", body_style)]
        ]
        if chain_head_hash:
            ev_rows.append([Paragraph("<b>Chain-Head SHA-256:</b>", body_style), Paragraph(f"<code>{chain_head_hash}</code>", code_style)])

    ev_table = Table(ev_rows, colWidths=[120, 410])
    ev_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(ev_table)
    elements.append(Spacer(1, 14))

    # Raw Intercepted Text
    elements.append(Paragraph("📝 Intercepted Post Content (Forensic Verbatim)", section_style))
    elements.append(Spacer(1, 6))
    raw_text = alert.get("raw_text", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text_table = Table([[Paragraph(f"\"{raw_text}\"", code_style)]], colWidths=[530])
    text_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#A0AEC0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(text_table)
    elements.append(Spacer(1, 14))

    # Extracted Actionable Identifiers
    elements.append(Paragraph("🔍 Extracted Actionable Identifiers", section_style))
    elements.append(Spacer(1, 6))

    if identifiers:
        id_table_data = [[
            Paragraph("<b>Identifier Type</b>", body_style),
            Paragraph("<b>Normalized Value</b>", body_style),
            Paragraph("<b>Channel Count</b>", body_style),
            Paragraph("<b>Cross-Channel Syndicate</b>", body_style),
        ]]
        for i in identifiers:
            is_cross = bool(i.get("cross_channel"))
            val = str(i.get("normalized_value", i.get("raw_value", ""))).replace("&", "&amp;").replace("<", "&lt;")
            id_table_data.append([
                Paragraph(f"<b>{i.get('type', 'N/A')}</b>", body_style),
                Paragraph(f"<code>{val}</code>", code_style),
                Paragraph(str(i.get("channel_count", 1)), body_style),
                Paragraph("<font color='#E53E3E'><b>YES 🚨</b></font>" if is_cross else "No", body_style),
            ])
        id_table = Table(id_table_data, colWidths=[120, 200, 90, 120])
        id_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(id_table)
    else:
        elements.append(Paragraph("<i>No actionable payment or contact identifiers extracted.</i>", body_style))

    elements.append(Spacer(1, 20))

    # Judicial & Statutory Compliance Notice
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E0"), spaceAfter=8))
    elements.append(Paragraph(
        "<b>STATUTORY NOTICE &amp; LEGAL CERTIFICATION:</b><br/>"
        "• <b>Section 63 BSA 2023 Notice:</b> Section 63 requires a certificate (signed by the responsible person and an expert) with a hash value; anchoring the chain head outside the DB is recommended practice, not a statutory requirement; consult legal counsel.<br/>"
        "• <b>Chain of Custody:</b> Evidence hashes were cryptographically computed using RFC-8785 deterministic JSON formatting linked sequentially to the tamper-evident hash ledger.<br/>"
        "• <b>Public Broadcast Feeds Only:</b> Monitoring is restricted strictly to public broadcast feeds. The system never infiltrates private groups, posts messages, reacts, sends DMs, or enumerates member lists.<br/>"
        "• <b>Leads, Not Courtroom Proof:</b> Algorithmic detections constitute investigative intelligence leads for certified human analysts, not automated convictions.",
        legal_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
