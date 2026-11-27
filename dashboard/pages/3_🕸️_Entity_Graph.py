"""Page 3: Entity Knowledge Graph, Centrality, and Seller Profiling."""
import sys
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd
import json

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

st.title("🕸️ Cross-Source Entity Links & Identifier Analysis")
st.caption("Multi-relational graph of source records and extracted identifiers. Shared values are correlation leads, not proof of common ownership or identity.")

db = Database()

with db.get_connection() as conn:
    source_rows = conn.execute("SELECT ingestion_source, COUNT(*) AS total FROM posts GROUP BY ingestion_source").fetchall()
source_counts = {row["ingestion_source"]: row["total"] for row in source_rows}
source_options = ["All sources"] + sorted(source_counts)
default_source = "HACKATHON_SAMPLE" if "HACKATHON_SAMPLE" in source_counts else "All sources"
source_filter = st.selectbox(
    "Dataset / provenance filter",
    source_options,
    index=source_options.index(default_source),
    help="Keeps unrelated live, imported and replay data separate from the PS02 sample.",
)

# Load posts and identifiers to construct graph
with db.get_connection() as conn:
    posts_rows = conn.execute(
        """
        SELECT p.post_uid, p.channel_id as source, p.message_id as post_id, p.raw_text as text,
               p.category as primary_category, p.risk_level
        FROM posts p
        WHERE (? = 'All sources' OR p.ingestion_source = ?)
        ORDER BY p.timestamp_utc DESC LIMIT 5000
        """,
        (source_filter, source_filter),
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
    st.metric("Shared Identifiers", len(cross_actors), delta="Seen in 2+ sources")
with kcol4:
    st.metric("Candidate Connected Clusters", len(syndicates))

st.divider()

# Graph Visualization
st.subheader("🌐 Interactive Entity Knowledge Graph")
st.caption("Drag, zoom and hover on nodes. Red nodes represent identifiers observed in 2+ source names; they are not confirmed people or shared operators.")
fig = plot_entity_graph(G, title="OSINT Cross-Channel Entity Network")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Tabs for Dossiers & Syndicates
tab1, tab2, tab3, tab4 = st.tabs(["🚨 Shared Identifiers", "👥 Candidate Clusters", "👤 Identifier Profiles", "↪️ Forwarded-From Evidence"])

with tab1:
    st.subheader("Identifiers Seen Across Multiple Sources")
    if cross_actors:
        df_cross = pd.DataFrame(cross_actors)
        st.dataframe(df_cross, use_container_width=True)
    else:
        st.info("No cross-channel actors identified in the current sample.")

with tab2:
    st.subheader("Candidate Connected Components")
    if syndicates:
        for syn in syndicates:
            with st.expander(f"Syndicate {syn['syndicate_id']} | Risk: {syn['risk_tier']} | {syn['channel_count']} Channels | {syn['total_nodes']} Nodes"):
                st.markdown(f"**Channels Involved:** `{', '.join(syn['channels'])}`")
                st.markdown(f"**Total Identifiers:** `{syn['identifier_count']}` (Cross-Channel Actors: `{syn['cross_channel_actors']}`)")
                st.markdown(f"**Posts Linked:** `{syn['post_count']}`")
    else:
        st.info("No clustered syndicates found.")

with tab3:
    st.subheader("Identifier Context Profile")
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


with tab4:
    st.subheader('Forwarded-From Source Mentions')
    st.caption('Telegram Desktop export metadata records a forwarded_from source label. These are unverified source mentions, not authenticated forwarding chains or proof that two operators are the same.')
    with db.get_connection() as conn:
        forward_rows = conn.execute("SELECT channel_id, message_id, timestamp_utc, source_metadata_json FROM posts WHERE (? = 'All sources' OR ingestion_source = ?) ORDER BY timestamp_utc DESC", (source_filter, source_filter)).fetchall()
    forward_records = []
    for row in forward_rows:
        try:
            metadata = json.loads(row['source_metadata_json'] or '{}')
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        forwarded_from = metadata.get('forwarded_from')
        if forwarded_from:
            forward_records.append({
                'Receiving source': row['channel_id'],
                'Message ID': row['message_id'],
                'Timestamp (UTC)': row['timestamp_utc'],
                'Reported forwarded-from': str(forwarded_from),
            })
    if forward_records:
        st.metric('Forwarded messages with source labels', len(forward_records))
        st.dataframe(pd.DataFrame(forward_records), use_container_width=True, hide_index=True)
    else:
        st.info('No forwarded-from metadata is available in the current hackathon sample.')
