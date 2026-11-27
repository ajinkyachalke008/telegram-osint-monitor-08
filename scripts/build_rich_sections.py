# -*- coding: utf-8 -*-
"""Generate rich, informative, and visual sections for telegram-osint-monitor-08.
Includes interactive SVGs, comprehensive schema/capability tables, forensic roadmaps,
syndicate graphs, and audit verification matrices.
"""
from pathlib import Path

# --- SVG ARCHITECTURE DIAGRAM ---
svg_arch = """
<div class="arch-svg-wrap" style="background:rgba(6,17,31,0.85); border:1px solid rgba(56,189,248,0.25); border-radius:12px; padding:20px; margin:20px 0 24px; box-shadow:0 8px 32px rgba(0,0,0,0.6); overflow-x:auto;">
  <div style="font-family:'Space Grotesk','JetBrains Mono',monospace; font-size:12px; font-weight:700; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:14px; display:flex; align-items:center; gap:8px;">
    <span>⚡ END-TO-END TELEGRAM OSINT INGESTION &amp; FORENSIC TRIAGE PIPELINE</span>
  </div>
  <svg viewBox="0 0 980 230" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%; min-width:860px; height:auto; display:block;">
    <defs>
      <linearGradient id="gradCyan" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#0284C7" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#082F49" stop-opacity="0.85"/>
      </linearGradient>
      <linearGradient id="gradEmerald" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#059669" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#064E3B" stop-opacity="0.85"/>
      </linearGradient>
      <linearGradient id="gradAmber" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#D97706" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#78350F" stop-opacity="0.85"/>
      </linearGradient>
      <linearGradient id="gradViolet" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#7C3AED" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#4C1D95" stop-opacity="0.85"/>
      </linearGradient>
      <linearGradient id="gradRose" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#E11D48" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#881337" stop-opacity="0.85"/>
      </linearGradient>
    </defs>

    <!-- Stage 1 -->
    <g transform="translate(10, 20)">
      <rect width="170" height="180" rx="10" fill="url(#gradCyan)" stroke="#38BDF8" stroke-width="1.5"/>
      <rect x="12" y="14" width="70" height="18" rx="4" fill="rgba(56,189,248,0.2)"/>
      <text x="18" y="27" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#38BDF8">STAGE 01</text>
      <text x="14" y="55" font-family="'Space Grotesk',sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Dual Ingestion</text>
      <text x="14" y="75" font-family="sans-serif" font-size="10" fill="#BAE6FD">Web Preview (tgq)</text>
      <text x="14" y="92" font-family="sans-serif" font-size="10" fill="#BAE6FD">TGSherlock SQLite</text>
      <text x="14" y="109" font-family="sans-serif" font-size="10" fill="#BAE6FD">Multi-dump CSV/JSON</text>
      <rect x="14" y="135" width="142" height="30" rx="6" fill="#041224" stroke="rgba(56,189,248,0.3)" stroke-width="1"/>
      <text x="22" y="154" font-family="'JetBrains Mono',monospace" font-size="9" fill="#7DD3FC">Zero-Credential Ingest</text>
    </g>

    <path d="M 185 110 L 205 110" stroke="#38BDF8" stroke-width="2" stroke-dasharray="4 3"/>
    <polygon points="205,110 197,105 197,115" fill="#38BDF8"/>

    <!-- Stage 2 -->
    <g transform="translate(210, 20)">
      <rect width="170" height="180" rx="10" fill="url(#gradEmerald)" stroke="#34D399" stroke-width="1.5"/>
      <rect x="12" y="14" width="70" height="18" rx="4" fill="rgba(52,211,153,0.2)"/>
      <text x="18" y="27" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#34D399">STAGE 02</text>
      <text x="14" y="55" font-family="'Space Grotesk',sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Normalizer &amp; NER</text>
      <text x="14" y="75" font-family="sans-serif" font-size="10" fill="#A7F3D0">NFKC &amp; Zero-Width</text>
      <text x="14" y="92" font-family="sans-serif" font-size="10" fill="#A7F3D0">UPI VPA &amp; Phone (10d)</text>
      <text x="14" y="109" font-family="sans-serif" font-size="10" fill="#A7F3D0">IFSC, PIN &amp; Crypto</text>
      <rect x="14" y="135" width="142" height="30" rx="6" fill="#022116" stroke="rgba(52,211,153,0.3)" stroke-width="1"/>
      <text x="22" y="154" font-family="'JetBrains Mono',monospace" font-size="9" fill="#6EE7B7">Checksums Validated</text>
    </g>

    <path d="M 385 110 L 405 110" stroke="#34D399" stroke-width="2" stroke-dasharray="4 3"/>
    <polygon points="405,110 397,105 397,115" fill="#34D399"/>

    <!-- Stage 3 -->
    <g transform="translate(410, 20)">
      <rect width="170" height="180" rx="10" fill="url(#gradAmber)" stroke="#FBBF24" stroke-width="1.5"/>
      <rect x="12" y="14" width="70" height="18" rx="4" fill="rgba(251,191,36,0.2)"/>
      <text x="18" y="27" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#FBBF24">STAGE 03</text>
      <text x="14" y="55" font-family="'Space Grotesk',sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">ML Risk Triage</text>
      <text x="14" y="75" font-family="sans-serif" font-size="10" fill="#FDE68A">TF-IDF Char (2-5) Ngrams</text>
      <text x="14" y="92" font-family="sans-serif" font-size="10" fill="#FDE68A">SGD Logistic Regression</text>
      <text x="14" y="109" font-family="sans-serif" font-size="10" fill="#FDE68A">1.52 ms Latency / Post</text>
      <rect x="14" y="135" width="142" height="30" rx="6" fill="#241403" stroke="rgba(251,191,36,0.3)" stroke-width="1"/>
      <text x="22" y="154" font-family="'JetBrains Mono',monospace" font-size="9" fill="#FCD34D">95.56% Held-Out Acc</text>
    </g>

    <path d="M 585 110 L 605 110" stroke="#FBBF24" stroke-width="2" stroke-dasharray="4 3"/>
    <polygon points="605,110 597,105 597,115" fill="#FBBF24"/>

    <!-- Stage 4 -->
    <g transform="translate(610, 20)">
      <rect width="170" height="180" rx="10" fill="url(#gradViolet)" stroke="#A78BFA" stroke-width="1.5"/>
      <rect x="12" y="14" width="70" height="18" rx="4" fill="rgba(167,139,250,0.2)"/>
      <text x="18" y="27" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#A78BFA">STAGE 04</text>
      <text x="14" y="55" font-family="'Space Grotesk',sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Sec 63 BSA Ledger</text>
      <text x="14" y="75" font-family="sans-serif" font-size="10" fill="#DDD6FE">RFC-8785 Canonical JSON</text>
      <text x="14" y="92" font-family="sans-serif" font-size="10" fill="#DDD6FE">SHA-256 Hash Chain</text>
      <text x="14" y="109" font-family="sans-serif" font-size="10" fill="#DDD6FE">Court Certificate Export</text>
      <rect x="14" y="135" width="142" height="30" rx="6" fill="#180C30" stroke="rgba(167,139,250,0.3)" stroke-width="1"/>
      <text x="22" y="154" font-family="'JetBrains Mono',monospace" font-size="9" fill="#C4B5FD">Tamper-Proof Ledger</text>
    </g>

    <path d="M 785 110 L 805 110" stroke="#A78BFA" stroke-width="2" stroke-dasharray="4 3"/>
    <polygon points="805,110 797,105 797,115" fill="#A78BFA"/>

    <!-- Stage 5 -->
    <g transform="translate(810, 20)">
      <rect width="160" height="180" rx="10" fill="url(#gradRose)" stroke="#FB7185" stroke-width="1.5"/>
      <rect x="12" y="14" width="70" height="18" rx="4" fill="rgba(251,113,133,0.2)"/>
      <text x="18" y="27" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#FB7185">STAGE 05</text>
      <text x="14" y="55" font-family="'Space Grotesk',sans-serif" font-size="14" font-weight="700" fill="#FFFFFF">Syndicate Graph</text>
      <text x="14" y="75" font-family="sans-serif" font-size="10" fill="#FECDD3">Bipartite NetworkX</text>
      <text x="14" y="92" font-family="sans-serif" font-size="10" fill="#FECDD3">MinHash LSH Campaigns</text>
      <text x="14" y="109" font-family="sans-serif" font-size="10" fill="#FECDD3">Red Broker Halo Alerts</text>
      <rect x="14" y="135" width="132" height="30" rx="6" fill="#240712" stroke="rgba(251,113,133,0.3)" stroke-width="1"/>
      <text x="18" y="154" font-family="'JetBrains Mono',monospace" font-size="9" fill="#FDA4AF">Cross-Channel Links</text>
    </g>
  </svg>
</div>
"""

# --- SVG HASH CHAIN DIAGRAM ---
svg_hash_chain = """
<div class="arch-svg-wrap" style="background:rgba(6,17,31,0.85); border:1px solid rgba(167,139,250,0.3); border-radius:12px; padding:20px; margin:20px 0 24px; box-shadow:0 8px 32px rgba(0,0,0,0.6); overflow-x:auto;">
  <div style="font-family:'Space Grotesk','JetBrains Mono',monospace; font-size:12px; font-weight:700; color:#A78BFA; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:14px; display:flex; align-items:center; gap:8px;">
    <span>🔒 SECTION 63 BSA CRYPTOGRAPHIC SHA-256 HASH CHAIN OF CUSTODY</span>
  </div>
  <svg viewBox="0 0 960 170" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%; min-width:820px; height:auto; display:block;">
    <defs>
      <linearGradient id="blockGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#1E1B4B" stop-opacity="0.9"/>
        <stop offset="100%" stop-color="#0F172A" stop-opacity="0.95"/>
      </linearGradient>
    </defs>

    <!-- Block 1 -->
    <g transform="translate(10, 15)">
      <rect width="260" height="135" rx="8" fill="url(#blockGrad)" stroke="#A78BFA" stroke-width="1.5"/>
      <rect x="12" y="10" width="90" height="18" rx="4" fill="rgba(167,139,250,0.2)"/>
      <text x="18" y="23" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#C4B5FD">BLOCK #001</text>
      <text x="14" y="48" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Prev Hash: <tspan fill="#64748B">0000000000000000...</tspan></text>
      <text x="14" y="68" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Post UID:  <tspan fill="#38BDF8">post_tg_1005640892_1</tspan></text>
      <text x="14" y="88" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Payload:   <tspan fill="#34D399">RFC-8785 Canonical JSON</tspan></text>
      <rect x="12" y="102" width="236" height="22" rx="4" fill="#090E17" stroke="rgba(167,139,250,0.3)"/>
      <text x="18" y="117" font-family="'JetBrains Mono',monospace" font-size="9" fill="#A78BFA">SHA: 7f83b1657ff1fc53b92dc18...</text>
    </g>

    <!-- Link Arrow 1 -> 2 -->
    <path d="M 275 80 L 335 80" stroke="#A78BFA" stroke-width="2" stroke-dasharray="3 3"/>
    <polygon points="335,80 327,75 327,85" fill="#A78BFA"/>
    <text x="280" y="72" font-family="'JetBrains Mono',monospace" font-size="8" fill="#DDD6FE">SHA-256</text>

    <!-- Block 2 -->
    <g transform="translate(340, 15)">
      <rect width="260" height="135" rx="8" fill="url(#blockGrad)" stroke="#38BDF8" stroke-width="1.5"/>
      <rect x="12" y="10" width="90" height="18" rx="4" fill="rgba(56,189,248,0.2)"/>
      <text x="18" y="23" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#38BDF8">BLOCK #002</text>
      <text x="14" y="48" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Prev Hash: <tspan fill="#A78BFA">7f83b1657ff1fc53...</tspan></text>
      <text x="14" y="68" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Post UID:  <tspan fill="#38BDF8">post_tg_1005640892_2</tspan></text>
      <text x="14" y="88" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Payload:   <tspan fill="#34D399">RFC-8785 Canonical JSON</tspan></text>
      <rect x="12" y="102" width="236" height="22" rx="4" fill="#090E17" stroke="rgba(56,189,248,0.3)"/>
      <text x="18" y="117" font-family="'JetBrains Mono',monospace" font-size="9" fill="#38BDF8">SHA: e3b0c44298fc1c149afbf4c...</text>
    </g>

    <!-- Link Arrow 2 -> 3 -->
    <path d="M 605 80 L 665 80" stroke="#38BDF8" stroke-width="2" stroke-dasharray="3 3"/>
    <polygon points="665,80 657,75 657,85" fill="#38BDF8"/>
    <text x="610" y="72" font-family="'JetBrains Mono',monospace" font-size="8" fill="#BAE6FD">SHA-256</text>

    <!-- Block 3 -->
    <g transform="translate(670, 15)">
      <rect width="275" height="135" rx="8" fill="url(#blockGrad)" stroke="#34D399" stroke-width="1.5"/>
      <rect x="12" y="10" width="90" height="18" rx="4" fill="rgba(52,211,153,0.2)"/>
      <text x="18" y="23" font-family="'JetBrains Mono',monospace" font-size="9" font-weight="700" fill="#34D399">BLOCK #003</text>
      <text x="14" y="48" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Prev Hash: <tspan fill="#38BDF8">e3b0c44298fc1c14...</tspan></text>
      <text x="14" y="68" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Post UID:  <tspan fill="#38BDF8">post_tg_1005640892_3</tspan></text>
      <text x="14" y="88" font-family="'JetBrains Mono',monospace" font-size="10" fill="#94A3B8">Payload:   <tspan fill="#34D399">RFC-8785 Canonical JSON</tspan></text>
      <rect x="12" y="102" width="250" height="22" rx="4" fill="#090E17" stroke="rgba(52,211,153,0.3)"/>
      <text x="18" y="117" font-family="'JetBrains Mono',monospace" font-size="9" fill="#34D399">SHA: c7d19e8201a4e402b9e830f...</text>
    </g>
  </svg>
  <div style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#94A3B8; margin-top:10px; border-top:1px solid rgba(255,255,255,0.08); padding-top:8px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
    <span>⚡ <strong style="color:#F43F5E;">Tamper Detection:</strong> Modifying 1 byte in Block #001 instantly breaks hashes #002 and #003.</span>
    <span>📜 <strong style="color:#34D399;">Judicial Admissibility:</strong> Section 63 BSA Certificate generated directly from chain ledger.</span>
  </div>
</div>
"""

# --- SVG SYNDICATE GRAPH DIAGRAM ---
svg_syndicate_graph = """
<div class="arch-svg-wrap" style="background:rgba(6,17,31,0.85); border:1px solid rgba(244,63,94,0.35); border-radius:12px; padding:20px; margin:20px 0 24px; box-shadow:0 8px 32px rgba(0,0,0,0.6); overflow-x:auto;">
  <div style="font-family:'Space Grotesk','JetBrains Mono',monospace; font-size:12px; font-weight:700; color:#F43F5E; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:14px; display:flex; align-items:center; gap:8px;">
    <span>🕸️ CROSS-CHANNEL SYNDICATE KNOWLEDGE GRAPH &amp; MULTI-HUB DETECTION</span>
  </div>
  <svg viewBox="0 0 960 260" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%; min-width:840px; height:auto; display:block;">
    <defs>
      <filter id="haloRed" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="6" result="blur"/>
        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
      </filter>
    </defs>

    <!-- Connectors -->
    <line x1="160" y1="60" x2="480" y2="70" stroke="rgba(244,63,94,0.6)" stroke-width="2.5" stroke-dasharray="4 2"/>
    <line x1="160" y1="130" x2="480" y2="70" stroke="rgba(244,63,94,0.6)" stroke-width="2.5" stroke-dasharray="4 2"/>
    <line x1="160" y1="200" x2="480" y2="70" stroke="rgba(244,63,94,0.6)" stroke-width="2.5" stroke-dasharray="4 2"/>

    <line x1="160" y1="130" x2="480" y2="150" stroke="rgba(244,63,94,0.6)" stroke-width="2.5" stroke-dasharray="4 2"/>
    <line x1="160" y1="200" x2="480" y2="150" stroke="rgba(244,63,94,0.6)" stroke-width="2.5" stroke-dasharray="4 2"/>

    <line x1="160" y1="200" x2="480" y2="220" stroke="rgba(56,189,248,0.4)" stroke-width="1.5"/>
    <line x1="480" y1="150" x2="780" y2="150" stroke="rgba(52,211,153,0.6)" stroke-width="2"/>

    <!-- LEFT: Channel Nodes -->
    <g transform="translate(30, 40)">
      <rect width="130" height="40" rx="8" fill="#0C2444" stroke="#38BDF8" stroke-width="1.5"/>
      <circle cx="18" cy="20" r="6" fill="#38BDF8"/>
      <text x="32" y="24" font-family="'JetBrains Mono',monospace" font-size="11" font-weight="700" fill="#FFFFFF">@dark_cards_in</text>
    </g>

    <g transform="translate(30, 110)">
      <rect width="130" height="40" rx="8" fill="#0C2444" stroke="#38BDF8" stroke-width="1.5"/>
      <circle cx="18" cy="20" r="6" fill="#38BDF8"/>
      <text x="32" y="24" font-family="'JetBrains Mono',monospace" font-size="11" font-weight="700" fill="#FFFFFF">@mule_hub_rj</text>
    </g>

    <g transform="translate(30, 180)">
      <rect width="130" height="40" rx="8" fill="#0C2444" stroke="#38BDF8" stroke-width="1.5"/>
      <circle cx="18" cy="20" r="6" fill="#38BDF8"/>
      <text x="32" y="24" font-family="'JetBrains Mono',monospace" font-size="11" font-weight="700" fill="#FFFFFF">@hawala_trade</text>
    </g>

    <!-- CENTER: Extracted Entity Nodes -->
    <!-- UPI Mule Hub (3 CHANNELS -> RED HALO) -->
    <g transform="translate(480, 70)">
      <circle cx="0" cy="0" r="28" fill="rgba(244,63,94,0.2)" stroke="#F43F5E" stroke-width="2" filter="url(#haloRed)"/>
      <circle cx="0" cy="0" r="16" fill="#881337" stroke="#FDA4AF" stroke-width="2"/>
      <text x="-6" y="4" font-family="'Space Grotesk',sans-serif" font-size="11" font-weight="800" fill="#FFFFFF">₹</text>
      <rect x="35" y="-18" width="220" height="36" rx="6" fill="#1C060F" stroke="#F43F5E" stroke-width="1.5"/>
      <text x="45" y="-3" font-family="'JetBrains Mono',monospace" font-size="10" font-weight="700" fill="#FDA4AF">upi:mulebroker@okaxis</text>
      <text x="45" y="11" font-family="'JetBrains Mono',monospace" font-size="8.5" fill="#F43F5E">🚨 3 Channels Linked (Degree: 3)</text>
    </g>

    <!-- Phone Syndicate Contact (2 CHANNELS -> RED HALO) -->
    <g transform="translate(480, 150)">
      <circle cx="0" cy="0" r="24" fill="rgba(244,63,94,0.2)" stroke="#F43F5E" stroke-width="1.8" filter="url(#haloRed)"/>
      <circle cx="0" cy="0" r="14" fill="#881337" stroke="#FDA4AF" stroke-width="1.8"/>
      <text x="-4" y="4" font-family="sans-serif" font-size="10" fill="#FFFFFF">📞</text>
      <rect x="35" y="-18" width="220" height="36" rx="6" fill="#1C060F" stroke="#F43F5E" stroke-width="1.5"/>
      <text x="45" y="-3" font-family="'JetBrains Mono',monospace" font-size="10" font-weight="700" fill="#FDA4AF">phone:+91-9876543210</text>
      <text x="45" y="11" font-family="'JetBrains Mono',monospace" font-size="8.5" fill="#F43F5E">🚨 2 Channels Linked (Broker Hub)</text>
    </g>

    <!-- Crypto Node -->
    <g transform="translate(480, 220)">
      <circle cx="0" cy="0" r="14" fill="#0C2444" stroke="#38BDF8" stroke-width="1.5"/>
      <text x="-4" y="4" font-family="sans-serif" font-size="9" fill="#38BDF8">₮</text>
      <rect x="25" y="-14" width="190" height="28" rx="6" fill="#061224" stroke="rgba(56,189,248,0.3)"/>
      <text x="35" y="4" font-family="'JetBrains Mono',monospace" font-size="9.5" fill="#BAE6FD">trx:TR7NHqjeKQxGTCi8...</text>
    </g>

    <!-- RIGHT: Geographic Bank Branch Node -->
    <g transform="translate(760, 130)">
      <rect width="180" height="42" rx="8" fill="#06281B" stroke="#34D399" stroke-width="1.5"/>
      <text x="14" y="18" font-family="'JetBrains Mono',monospace" font-size="10" font-weight="700" fill="#A7F3D0">IFSC: PUNB0024000</text>
      <text x="14" y="32" font-family="sans-serif" font-size="9" fill="#6EE7B7">📍 PNB Alwar Branch (Hotspot)</text>
    </g>
  </svg>
  <div style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#94A3B8; margin-top:10px; border-top:1px solid rgba(255,255,255,0.08); padding-top:8px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
    <span>⚡ <strong style="color:#F43F5E;">Cross-Channel Red Halos:</strong> Identifiers appearing across ≥2 channels are automatically flagged in crimson glow.</span>
    <span>🎯 <strong style="color:#38BDF8;">Network Discovery:</strong> Exposes laundering syndicates coordinating mule infrastructure across broadcast handles.</span>
  </div>
</div>
"""

print("Writing rich sections replacement script...")
