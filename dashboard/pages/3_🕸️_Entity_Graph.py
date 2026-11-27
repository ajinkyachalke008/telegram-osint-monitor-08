"""Page 3: Entity Knowledge Graph, Centrality, and Seller Profiling."""
import sys
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd

from core.db import Database
from dashboard.graph import (
    build_entity_graph,
    calculate_centrality,
    plot_entity_graph,
    get_cross_channel_identifiers,
    get_connected_syndicates,
    generate_seller_profile,
)

st.set_page_config(page_title="Entity Graph | telegram-osint-monitor-08", page_icon="🕸️", layout="wide")

from dashboard.provenance_banner import render_provenance_banner
render_provenance_banner(page_title="Entity Graph", active_stream="VERIFIED-SYNTHETIC")

st.title("🕸️ Cross-Channel Entity Knowledge Graph & Profiling")
st.caption("Multi-relational NetworkX graph linking Telegram channels, payment identifiers, and seller profiles.")

db = Database()

# Load posts and identifiers to construct graph
with db.get_connection() as conn:
    posts_rows = conn.execute(
        """
        SELECT p.post_uid, p.channel_id as source, p.message_id as post_id, p.raw_text as text,
               p.category as primary_category, p.risk_level
        FROM posts p
        ORDER BY p.timestamp_utc DESC LIMIT 5000
        """
    ).fetchall()

posts_data = []
for pr in posts_rows:
    p_dict = dict(pr)
    # fetch identifiers
    idents = db.get_post_identifiers(p_dict["post_uid"])
    p_dict["extracted"] = {
        "all_flat": [{"type": i["type"], "value": i["normalized_value"]} for i in idents]
    }
    posts_data.append(p_dict)

if not posts_data:
    st.warning("No posts available in database to build graph.")
    st.stop()

# Build and analyze graph
G = build_entity_graph(posts_data)
metrics = calculate_centrality(G)
cross_actors = get_cross_channel_identifiers(G)
syndicates = get_connected_syndicates(G)

# Top KPI Summary
kcol1, kcol2, kcol3, kcol4 = st.columns(4)
with kcol1:
    st.metric("Total Graph Nodes", len(G.nodes))
with kcol2:
    st.metric("Total Inter-Entity Edges", len(G.edges))
with kcol3:
    st.metric("Cross-Channel Actors", len(cross_actors), delta="CRITICAL: >= 2 Channels")
with kcol4:
    st.metric("Connected Syndicates", len(syndicates))

st.divider()

# Graph Visualization
st.subheader("🌐 Interactive Entity Knowledge Graph")
st.caption("Drag, zoom, and hover on nodes. Red nodes represent actors identified across 2 or more channels.")
fig = plot_entity_graph(G, title="OSINT Cross-Channel Entity Network")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Tabs for Dossiers & Syndicates
tab1, tab2, tab3 = st.tabs(["🚨 Cross-Channel Actors", "👥 Connected Syndicates", "👤 Seller Dossier Lookup"])

with tab1:
    st.subheader("Identified Cross-Channel Actors")
    if cross_actors:
        df_cross = pd.DataFrame(cross_actors)
        st.dataframe(df_cross, use_container_width=True)
    else:
        st.info("No cross-channel actors identified in the current sample.")

with tab2:
    st.subheader("Connected Campaign Syndicates")
    if syndicates:
        for syn in syndicates:
            with st.expander(f"Syndicate {syn['syndicate_id']} | Risk: {syn['risk_tier']} | {syn['channel_count']} Channels | {syn['total_nodes']} Nodes"):
                st.markdown(f"**Channels Involved:** `{', '.join(syn['channels'])}`")
                st.markdown(f"**Total Identifiers:** `{syn['identifier_count']}` (Cross-Channel Actors: `{syn['cross_channel_actors']}`)")
                st.markdown(f"**Posts Linked:** `{syn['post_count']}`")
    else:
        st.info("No clustered syndicates found.")

with tab3:
    st.subheader("Deep Seller Profile Dossier")
    # All identifiers list for search
    all_ident_values = [d.get("value") for n, d in G.nodes(data=True) if d.get("node_type") not in ("Channel", "Post") and d.get("value")]
    if all_ident_values:
        selected_target = st.selectbox("Select Identifier to Generate Dossier", sorted(list(set(all_ident_values))))
        if selected_target:
            profile = generate_seller_profile(selected_target, db)
            if profile.get("found"):
                pcol1, pcol2 = st.columns([1, 1])
                with pcol1:
                    st.markdown(f"### Profile: `{profile['identifier']}`")
                    st.markdown(f"• **Type:** `{profile['type']}`")
                    st.markdown(f"• **Cross-Channel:** `{'YES 🚨' if profile['cross_channel'] else 'No'}`")
                    st.markdown(f"• **Channels Used ({profile['channel_count']}):** `{', '.join(profile['channels'])}`")
                    st.markdown(f"• **First Seen:** `{profile['first_seen']}` | **Last Seen:** `{profile['last_seen']}`")
                    st.markdown(f"• **Total Linked Posts:** `{profile['total_posts']}`")
                with pcol2:
                    st.markdown("### Co-Occurring Identifiers")
                    if profile.get("co_occurring_identifiers"):
                        for co in profile["co_occurring_identifiers"]:
                            st.markdown(f"- `{co['type']}`: **{co['normalized_value']}** (channel count: {co.get('channel_count', 1)})")
                    else:
                        st.info("No co-occurring identifiers found.")
            else:
                st.warning(profile.get("summary", "Not found."))
