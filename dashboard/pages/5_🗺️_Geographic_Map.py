"""Page 5: Geographic Distribution & Hotspot Mapping.

Spatial intelligence visualization mapping regional cybercrime syndicates,
Rajasthan trade hubs, cross-border mule corridors, and threat density across India.
Integrates live operational telemetry with the official PS02 participant dataset.
"""
import sys
import zipfile
import csv
import io
from pathlib import Path
from typing import Dict, Any, List

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.db import Database
from addons.extractors import extract_locations, INDIAN_GAZETTEER
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme

st.set_page_config(page_title="Geographic Map | telegram-osint-monitor-08", page_icon="🗺️", layout="wide")

# Inject Master Cyber Theme
inject_theme()

# Standard Provenance Banner
render_provenance_banner(page_title="Geographic Map", active_stream="VERIFIED-SYNTHETIC")

st.title("🗺️ Geographic Distribution & Hotspot Mapping")
st.caption("Spatial intelligence visualization mapping regional cybercrime syndicates, Rajasthan illicit trade corridors, and geographic threat density across India.")

db = Database()

# Known Interstate Cybercrime Corridors (Mewat - Alwar - Bharatpur Triangle & Trade Hubs)
CORRIDOR_SEGMENTS = [
    (("Mewat (Nuh)", 28.1000, 77.0500), ("Alwar", 27.5530, 76.6346)),
    (("Alwar", 27.5530, 76.6346), ("Bharatpur", 27.2152, 77.5030)),
    (("Bharatpur", 27.2152, 77.5030), ("Mewat (Nuh)", 28.1000, 77.0500)),
    (("Alwar", 27.5530, 76.6346), ("Jaipur", 26.9124, 75.7873)),
    (("Mewat (Nuh)", 28.1000, 77.0500), ("Delhi", 28.7041, 77.1025)),
    (("Jaipur", 26.9124, 75.7873), ("Kota", 25.2138, 75.8648)),
    (("Jaipur", 26.9124, 75.7873), ("Ajmer", 26.4499, 74.6399)),
    (("Ajmer", 26.4499, 74.6399), ("Jodhpur", 26.2389, 73.0243)),
]

# Color map for hub classifications
HUB_COLOR_MAP = {
    "Cybercrime Hotspot": "#FF3366",       # Crimson Red Alert
    "Capital / Trade Hub": "#00E5FF",      # Cyber Cyan
    "Commercial Hub": "#FFD369",           # Vibrant Gold
    "Metropolis": "#3B82F6",               # Electric Blue
    "Regional Center": "#10B981",          # Emerald Green
    "State Node": "#8BC34A",               # Light Green
}


@st.cache_data(ttl=300, show_spinner=False)
def load_participant_social_locations() -> List[Dict[str, Any]]:
    """Loads social media post locations from PS02 demo dataset archive."""
    zip_path = Path("data/participant_input/PS02_demo_data-20261127T071007Z-1-001.zip")
    if not zip_path.exists():
        return []
    try:
        records = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            social_files = [n for n in zf.namelist() if n.endswith(".csv") and "social" in n]
            for sf in social_files:
                content = zf.read(sf).decode("utf-8-sig", errors="ignore")
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    loc = row.get("location_tag", "").strip()
                    if loc:
                        records.append({
                            "location_raw": loc,
                            "platform": row.get("platform", "Social Media"),
                            "text": row.get("text", ""),
                            "hashtags": row.get("hashtags", ""),
                        })
        return records
    except Exception:
        return []


# Load operational database posts
with db.get_connection() as conn:
    op_posts = conn.execute(
        "SELECT post_uid, raw_text, channel_id, category, risk_level FROM posts"
    ).fetchall()

# Load participant records from ZIP archive
participant_records = load_participant_social_locations()

# ----------------- SIDEBAR / CONTROLS -----------------
with st.sidebar:
    st.markdown("""
    <div style="padding-bottom:8px; border-bottom:1px solid #1E2B45; margin-bottom:12px;">
        <span style="font-weight:700; color:#00E5FF; font-size:12px; text-transform:uppercase; letter-spacing:0.06em;">⚙️ SPATIAL FILTERS</span>
    </div>
    """, unsafe_allow_html=True)

    stream_option = st.selectbox(
        "Intelligence Stream",
        [
            "Unified Forensic Intelligence (Live Telemetry + Official PS02 Dataset)",
            "Official PS02 Participant Dataset Only (350 Posts)",
            "Live Monitored Broadcast Channels Only (Operational DB)",
        ],
        index=0,
        help="Select which telemetry sources are mapped on the spatial canvas."
    )

    region_focus = st.selectbox(
        "Geographic Focus & Projection",
        [
            "Rajasthan & North-Western Corridor (High-Resolution Zoom)",
            "All India Strategic View",
            "Mewat-NCR Cybercrime Triangle Focus",
        ],
        index=0,
        help="Select the camera bounding box and regional centering."
    )

    show_corridors = st.toggle(
        "Overlay Interstate Syndicates & Corridors",
        value=True,
        help="Renders tactical links between Mewat, Alwar, Bharatpur, Jaipur, Kota, and Delhi NCR."
    )

# ----------------- DATA AGGREGATION ENGINE -----------------
geo_hubs: Dict[str, Dict[str, Any]] = {}


def add_location_hit(city_key: str, category: str, source_type: str):
    clean_k = city_key.strip().lower()
    if clean_k in ("nuh", "mewat"):
        clean_k = "mewat"
    
    if clean_k in INDIAN_GAZETTEER:
        info = INDIAN_GAZETTEER[clean_k]
        city_display = "Mewat (Nuh)" if clean_k == "mewat" else clean_k.title()
        
        # Categorize hub type
        raw_type = info.get("type", "City")
        if "hotspot" in raw_type.lower() or clean_k in ("mewat", "jamtara", "alwar", "bharatpur"):
            hub_type = "Cybercrime Hotspot"
        elif "capital" in raw_type.lower() or clean_k in ("jaipur", "delhi"):
            hub_type = "Capital / Trade Hub"
        elif clean_k in ("kota", "ajmer", "jodhpur", "pune", "indore", "surat"):
            hub_type = "Commercial Hub"
        elif "metropolis" in raw_type.lower():
            hub_type = "Metropolis"
        elif "state" in raw_type.lower():
            hub_type = "State Node"
        else:
            hub_type = "Regional Center"

        if city_display not in geo_hubs:
            geo_hubs[city_display] = {
                "City": city_display,
                "State": info["state"],
                "Latitude": info["lat"],
                "Longitude": info["lon"],
                "Classification": hub_type,
                "Mentions": 0,
                "Operational_Hits": 0,
                "Participant_Hits": 0,
                "Categories": set(),
                "Sources": set(),
            }
        
        geo_hubs[city_display]["Mentions"] += 1
        if source_type == "operational":
            geo_hubs[city_display]["Operational_Hits"] += 1
        else:
            geo_hubs[city_display]["Participant_Hits"] += 1
            
        if category:
            geo_hubs[city_display]["Categories"].add(category)
        geo_hubs[city_display]["Sources"].add(source_type.capitalize())


# 1. Process Operational DB posts
include_op = "Live Monitored" in stream_option or "Unified" in stream_option
if include_op:
    for r in op_posts:
        full_text = f"{r['raw_text'] or ''} {r['channel_id'] or ''}"
        locs = extract_locations(full_text)
        cat = r["category"] or "General Illicit"
        for loc in locs:
            if loc.get("lat") and loc.get("lon"):
                add_location_hit(loc["name"], cat, "operational")

# 2. Process Participant Dataset records
include_pt = "Official PS02" in stream_option or "Unified" in stream_option
if include_pt and participant_records:
    for pr in participant_records:
        raw_loc = pr["location_raw"].split(",")[0].strip()
        add_location_hit(raw_loc, "Social Media Infiltration", "participant")

# Build DataFrame
if not geo_hubs:
    st.info("No geographic locations detected in the selected intelligence stream.")
    st.stop()

plot_rows = []
for k, v in geo_hubs.items():
    cats_str = ", ".join(sorted(list(v["Categories"]))) if v["Categories"] else "General Illicit Activity"
    srcs_str = ", ".join(sorted(list(v["Sources"])))
    plot_rows.append({
        "City": v["City"],
        "State": v["State"],
        "Latitude": v["Latitude"],
        "Longitude": v["Longitude"],
        "Classification": v["Classification"],
        "Mentions": v["Mentions"],
        "Operational Hits": v["Operational_Hits"],
        "Participant Hits": v["Participant_Hits"],
        "Categories": cats_str,
        "Sources": srcs_str,
    })

df_geo = pd.DataFrame(plot_rows).sort_values("Mentions", ascending=False)

# ----------------- TOP KPI METRIC STRIP -----------------
top_hub = df_geo.iloc[0]["City"] if not df_geo.empty else "N/A"
top_mentions = df_geo.iloc[0]["Mentions"] if not df_geo.empty else 0
total_mentions = df_geo["Mentions"].sum()
hotspot_count = sum(1 for r in plot_rows if r["Classification"] == "Cybercrime Hotspot")

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Identified Regional Hubs", f"{len(df_geo)} Locations", delta="All Active")
with k2:
    st.metric("Total Geographic Mentions", f"{total_mentions:,}", delta=f"{len(df_geo)} Hubs Monitored")
with k3:
    st.metric("Primary Focal Hotspot", top_hub, delta=f"{top_mentions} Mentions Detected", delta_color="inverse")
with k4:
    st.metric("High-Risk Cyber Hotspots", f"{hotspot_count} Hotspots", delta="Mewat Triangle Active", delta_color="inverse")

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ----------------- PLOTLY SCATTE_GEO CANVASES -----------------
# Setup Map Projection Centering & Scale based on user selection
if region_focus == "Rajasthan & North-Western Corridor (High-Resolution Zoom)":
    center_lat, center_lon, proj_scale = 26.5, 75.5, 7.8
elif region_focus == "Mewat-NCR Cybercrime Triangle Focus":
    center_lat, center_lon, proj_scale = 27.8, 76.8, 11.2
else:
    center_lat, center_lon, proj_scale = 23.5, 78.5, 5.2

fig = px.scatter_geo(
    df_geo,
    lat="Latitude",
    lon="Longitude",
    size="Mentions",
    color="Classification",
    color_discrete_map=HUB_COLOR_MAP,
    hover_name="City",
    hover_data={
        "State": True,
        "Classification": True,
        "Mentions": True,
        "Categories": True,
        "Sources": True,
        "Latitude": False,
        "Longitude": False,
    },
    size_max=36,
    scope="asia",
    template="plotly_dark",
    title="Detected Illicit Trade & Cybercrime Activity across Indian Regional Hubs"
)

# Overlay Interstate Syndicate Corridors (Mewat - Alwar - Bharatpur Network)
if show_corridors:
    corridor_lats: List[Any] = []
    corridor_lons: List[Any] = []
    for (name1, lat1, lon1), (name2, lat2, lon2) in CORRIDOR_SEGMENTS:
        corridor_lats.extend([lat1, lat2, None])
        corridor_lons.extend([lon1, lon2, None])

    corridor_trace = go.Scattergeo(
        lat=corridor_lats,
        lon=corridor_lons,
        mode="lines",
        line=dict(width=2.4, color="rgba(255, 51, 102, 0.70)", dash="solid"),
        name="Mewat-Alwar-Bharatpur Cyber Corridor",
        hoverinfo="none",
        showlegend=True,
    )
    fig.add_trace(corridor_trace)

# Polished Dark Tactical Geospatial Layout
fig.update_geos(
    center=dict(lat=center_lat, lon=center_lon),
    projection_scale=proj_scale,
    visible=True,
    showland=True, landcolor="#0F172A",
    showocean=True, oceancolor="#080C14",
    showlakes=True, lakecolor="#080C14",
    showrivers=False,
    showcountries=True, countrycolor="#334155",
    showsubunits=True, subunitcolor="#1E293B",
    resolution=50,
)

fig.update_traces(
    marker=dict(
        line=dict(width=1.8, color="#FFFFFF"),
        opacity=0.92,
    ),
    selector=dict(mode="markers")
)

fig.update_layout(
    margin=dict(l=10, r=10, t=45, b=10),
    height=620,
    paper_bgcolor="#0A0F1D",
    plot_bgcolor="#0A0F1D",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(color="#E2E8F0", size=11),
        bgcolor="rgba(10, 15, 29, 0.8)",
        bordercolor="#1E2B45",
        borderwidth=1,
    ),
    font=dict(family="Inter, -apple-system, sans-serif", color="#ECEFF1"),
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": True,
        "displaylogo": False,
        "modeBarButtonsToAdd": ["drawline", "drawcircle", "eraseshape"]
    }
)

st.divider()

# ----------------- TACTICAL INTELLIGENCE PANELS -----------------
tab1, tab2, tab3 = st.tabs([
    "📍 Regional Hotspots Dossier",
    "🏛️ State-Level Threat Distribution",
    "⚡ Interstate Cybercrime Corridors",
])

with tab1:
    st.subheader("Regional Hotspots & Activity Breakdown")
    st.caption("Comprehensive registry of detected geographic nodes with activity volume and associated crime classifications.")
    st.dataframe(
        df_geo[["City", "State", "Classification", "Mentions", "Operational Hits", "Participant Hits", "Categories", "Sources"]],
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    st.subheader("Detected Activity by Indian State / Territory")
    st.caption("Distribution of illicit mentions aggregated by regional jurisdiction.")
    state_series = df_geo.groupby("State")["Mentions"].sum().reset_index().sort_values("Mentions", ascending=True)

    fig_bar = px.bar(
        state_series,
        x="Mentions",
        y="State",
        orientation="h",
        color="Mentions",
        color_continuous_scale=["#00E5FF", "#FF3366"],
        template="plotly_dark",
        title="Detected Threat Mentions by State / Union Territory"
    )
    fig_bar.update_layout(
        paper_bgcolor="#0A0F1D",
        plot_bgcolor="#0A0F1D",
        margin=dict(l=20, r=20, t=40, b=20),
        height=340,
        font=dict(family="Inter, -apple-system, sans-serif", color="#E2E8F0"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.subheader("⚡ Interstate Cybercrime Corridor Intelligence Brief")
    st.caption("Tactical breakdown of the primary operational corridors detected in Telegram broadcasts and social engineering campaigns.")

    ccol1, ccol2 = st.columns([1, 1])
    with ccol1:
        st.markdown("""
        <div style="background-color:#0D1424; border:1px solid #1E2B45; border-radius:8px; padding:16px 20px; margin-bottom:12px;">
            <div style="color:#FF3366; font-weight:700; font-size:14px; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:8px;">
                🚨 1. Mewat - Alwar - Bharatpur Triangle (Origin Hub)
            </div>
            <p style="font-size:13px; color:#94A3B8; margin-bottom:8px;">
                <b>Primary Operations:</b> Pre-activated SIM farming (+91 bulk OTP bypass), forged PVC Aadhaar/PAN identity cards, and WhatsApp/Telegram extortion rings.
            </p>
            <p style="font-size:12.5px; color:#64748B; margin-bottom:0;">
                • <b>Mewat (Nuh):</b> Central syndicate coordinating encrypted broadcast channels.<br/>
                • <b>Alwar & Bharatpur:</b> Localized biometric cloning and bank mule account recruitment.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with ccol2:
        st.markdown("""
        <div style="background-color:#0D1424; border:1px solid #1E2B45; border-radius:8px; padding:16px 20px; margin-bottom:12px;">
            <div style="color:#00E5FF; font-weight:700; font-size:14px; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:8px;">
                💼 2. Jaipur - Kota - Delhi Corridor (Financial Transit & Cashout)
            </div>
            <p style="font-size:13px; color:#94A3B8; margin-bottom:8px;">
                <b>Primary Operations:</b> High-limit current account rentals, ATM card wholesale kits, and P2P crypto-fiat cashout settlement.
            </p>
            <p style="font-size:12.5px; color:#64748B; margin-bottom:0;">
                • <b>Jaipur & Kota:</b> Transit hubs where students and shell entities are recruited for mule bank accounts.<br/>
                • <b>Delhi NCR & Mumbai:</b> Terminal cash-out points utilizing crypto wallets (USDT/TRC20) and rapid ATM withdrawals.
            </p>
        </div>
        """, unsafe_allow_html=True)
