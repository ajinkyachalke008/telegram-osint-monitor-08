"""Page 5: Geographic Distribution & Hotspot Mapping."""
import sys
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd
import plotly.express as px

from core.db import Database
from addons.extractors import extract_locations
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme, apply_plotly_theme

st.set_page_config(page_title="Geographic Map | telegram-osint-monitor-08", page_icon="🗺️", layout="wide")

# Inject Master Theme
inject_theme()

# Standard Provenance Banner
render_provenance_banner(page_title="Geographic Map", active_stream="VERIFIED-SYNTHETIC")

st.title("🗺️ Geographic Distribution & Hotspot Mapping")
st.caption("Spatial visualization of extracted Indian locations, regional cybercrime hubs (Mewat, Jamtara), and geographic threat density.")

db = Database()

# Known Indian Hotspot coordinates
KNOWN_LOCATIONS = {
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai"},
    "delhi": {"lat": 28.7041, "lon": 77.1025, "name": "Delhi"},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "name": "Bengaluru"},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "name": "Hyderabad"},
    "pune": {"lat": 18.5204, "lon": 73.8567, "name": "Pune"},
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "name": "Jaipur"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "name": "Kolkata"},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "name": "Ahmedabad"},
    "mewat": {"lat": 28.1000, "lon": 76.9900, "name": "Mewat (Nuh)"},
    "jamtara": {"lat": 23.9600, "lon": 86.8000, "name": "Jamtara"},
    "lucknow": {"lat": 26.8467, "lon": 80.9462, "name": "Lucknow"},
    "indore": {"lat": 22.7196, "lon": 75.8577, "name": "Indore"},
    "surat": {"lat": 21.1702, "lon": 72.8311, "name": "Surat"},
    "chandigarh": {"lat": 30.7333, "lon": 76.7794, "name": "Chandigarh"}
}

# Fetch locations from posts
with db.get_connection() as conn:
    rows = conn.execute("SELECT raw_text, category, risk_level FROM posts").fetchall()

geo_counts = {}
all_categories = set()
for r in rows:
    text = r["raw_text"] or ""
    locs = extract_locations(text)
    for loc in locs:
        lname = loc["name"].lower()
        if lname in KNOWN_LOCATIONS:
            if lname not in geo_counts:
                geo_counts[lname] = {
                    "city": KNOWN_LOCATIONS[lname]["name"],
                    "lat": KNOWN_LOCATIONS[lname]["lat"],
                    "lon": KNOWN_LOCATIONS[lname]["lon"],
                    "count": 0,
                    "categories": set()
                }
            geo_counts[lname]["count"] += 1
            geo_counts[lname]["categories"].add(r["category"])
            all_categories.add(r["category"])

if not geo_counts:
    st.info("No geographic locations detected in current post database.")
else:
    plot_data = []
    for k, v in geo_counts.items():
        plot_data.append({
            "City": v["city"],
            "Latitude": v["lat"],
            "Longitude": v["lon"],
            "Mentions": v["count"],
            "Categories": ", ".join(v["categories"])
        })
    df_geo = pd.DataFrame(plot_data).sort_values("Mentions", ascending=False)

    # Top KPI Metrics Strip
    top_city = df_geo.iloc[0]["City"] if not df_geo.empty else "N/A"
    top_mentions = df_geo.iloc[0]["Mentions"] if not df_geo.empty else 0
    total_mentions = df_geo["Mentions"].sum()

    gk1, gk2, gk3, gk4 = st.columns(4)
    with gk1:
        st.metric("Total Regional Hubs", f"{len(df_geo)}")
    with gk2:
        st.metric("Geographic Mentions", f"{total_mentions:,}")
    with gk3:
        st.metric("Top Hotspot", f"{top_city}", delta=f"{top_mentions} mentions", delta_color="inverse")
    with gk4:
        st.metric("Categories Spanned", f"{len(all_categories)}")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    fig = px.scatter_geo(
        df_geo,
        lat="Latitude",
        lon="Longitude",
        size="Mentions",
        hover_name="City",
        hover_data={"Mentions": True, "Categories": True, "Latitude": False, "Longitude": False},
        color="Mentions",
        color_continuous_scale=["#1E3A5F", "#00ADB5", "#FF3366"],
        scope="asia",
        template="plotly_dark",
        title="Detected Illicit Trade Activity across Indian Geographic Hubs"
    )
    fig.update_geos(
        center=dict(lat=21.5937, lon=78.9629),
        projection_scale=4.6,
        visible=True,
        showland=True, landcolor="#0F172A",
        showocean=True, oceancolor="#080C14",
        showcountries=True, countrycolor="#334155",
        showsubunits=True, subunitcolor="#1E293B"
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=540,
        paper_bgcolor="#0A0F1D",
        plot_bgcolor="#0A0F1D"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Regional Hotspots & Crime Categories Breakdown")
    st.dataframe(df_geo[["City", "Mentions", "Categories"]], use_container_width=True, hide_index=True)
