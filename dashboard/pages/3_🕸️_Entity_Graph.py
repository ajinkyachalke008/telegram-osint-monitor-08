"""Page 3: Entity Knowledge Graph, Centrality, and Seller Profiling."""
import sys
import html
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import networkx as nx

from core.db import Database
from dashboard.graph import (
    build_entity_graph,
    build_direct_syndicate_graph,
    build_participant_dataset_graph,
    render_vis_network_html,
    calculate_centrality,
    plot_entity_graph,
    get_cross_channel_identifiers,
    get_connected_syndicates,
    generate_seller_profile,
    NODE_COLORS,
)
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme

st.set_page_config(page_title="Entity Graph | telegram-osint-monitor-08", page_icon="🕸️", layout="wide")

# Inject Master Theme
inject_theme()

# Standard Provenance Banner
render_provenance_banner(page_title="Entity Graph", active_stream="VERIFIED-SYNTHETIC")

st.title("🕸️ Cross-Channel Entity Knowledge Graph & Profiling")
st.caption("Interactive, physics-driven force-directed network linking broadcast channels, financial payment identifiers, and cross-channel mule syndicates. Every node is touchable, draggable, and movable.")

db = Database()

# Sidebar: Graph Topology & Canvas Engine Configuration
with st.sidebar:
    st.markdown("""
    <div style="padding-bottom:8px; border-bottom:1px solid #1E2B45; margin-bottom:12px;">
        <span style="font-weight:700; color:#00E5FF; font-size:12px; text-transform:uppercase; letter-spacing:0.06em;">⚙️ GRAPH CONFIGURATION</span>
    </div>
    """, unsafe_allow_html=True)

    graph_model = st.selectbox(
        "Dataset Topology Model",
        [
            "Direct Syndicate Network (Entities & Channels)",
            "Cross-Channel Syndicates Only (Targeted Triage)",
            "Full Forensic Tripartite (Channels + Posts + Entities)",
            "Official PS02 Participant Dataset Topology",
        ],
        index=0,
        help="Select how the knowledge graph is constructed from database records."
    )

    canvas_engine = st.radio(
        "Visualization Canvas Engine",
        [
            "🎮 Touchable & Movable Physics (Vis-Network)",
            "📊 Plotly Static Topology Canvas",
        ],
        index=0,
        help="Touchable & Movable physics engine allows clicking, dragging, and rearranging every node."
    )

# Load posts and identifiers to construct graph
with db.get_connection() as conn:
    posts_rows = conn.execute(
        """
        SELECT p.post_uid, p.channel_id as source, p.message_id as post_id, p.raw_text as text,
               p.category as primary_category, p.risk_level
        FROM posts p
        ORDER BY p.timestamp_utc DESC LIMIT 250
        """
    ).fetchall()

posts_data = []
for pr in posts_rows:
    p_dict = dict(pr)
    idents = db.get_post_identifiers(p_dict["post_uid"])
    p_dict["extracted"] = {
        "all_flat": [{"type": i["type"], "value": i["normalized_value"]} for i in idents]
    }
    posts_data.append(p_dict)

if not posts_data:
    st.warning("No posts available in database to build graph.")
    st.stop()

# Build selected graph model
if graph_model == "Direct Syndicate Network (Entities & Channels)":
    G = build_direct_syndicate_graph(posts_data, only_cross_channel=False)
    graph_title = "Direct Syndicate Topology (Entities & Monitored Channels)"
elif graph_model == "Cross-Channel Syndicates Only (Targeted Triage)":
    G = build_direct_syndicate_graph(posts_data, only_cross_channel=True)
    graph_title = "Cross-Channel Illicit Syndicate Actors & Compromised Channels"
elif graph_model == "Official PS02 Participant Dataset Topology":
    G = build_participant_dataset_graph()
    graph_title = "Official PS02 Participant Dataset Multi-Platform Topology"
else:
    G = build_entity_graph(posts_data)
    graph_title = "Full Forensic Tripartite Graph (Channels, Posts, Entities)"

# Fallback if selected model is empty
if len(G.nodes) == 0:
    G = build_direct_syndicate_graph(posts_data, only_cross_channel=False)
    graph_title = "Direct Syndicate Topology (Fallback)"

# Graph metrics calculation
metrics = calculate_centrality(G)
cross_actors = get_cross_channel_identifiers(G)
syndicates = get_connected_syndicates(G)

# Top KPI Summary Cards
kcol1, kcol2, kcol3, kcol4 = st.columns(4)
with kcol1:
    st.metric("Total Graph Nodes", len(G.nodes), delta="Physics Active")
with kcol2:
    st.metric("Total Inter-Entity Edges", len(G.edges))
with kcol3:
    st.metric("Cross-Channel Actors", len(cross_actors), delta="CRITICAL: ≥ 2 Channels", delta_color="inverse")
with kcol4:
    st.metric("Connected Syndicates", len(syndicates))

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Controls & Interactive Visual Legend
ctrl_col1, ctrl_col2 = st.columns([1, 1])
with ctrl_col1:
    if canvas_engine == "📊 Plotly Static Topology Canvas":
        label_choice = st.radio(
            "Canvas Label Display Mode",
            ["Smart (Syndicates & Key Channels)", "Cross-Channel Actors Only", "Hover Tooltips Only"],
            horizontal=True,
            index=0,
            help="Declutters canvas by showing prominent labels only for key nodes."
        )
        mode_map = {
            "Smart (Syndicates & Key Channels)": "smart",
            "Cross-Channel Actors Only": "cross_only",
            "Hover Tooltips Only": "hover_only",
        }
        active_mode = mode_map[label_choice]
    else:
        st.markdown("""
        <div style="background-color: #0C1220; border: 1px solid #1A263D; border-radius: 6px; padding: 10px 14px; font-size: 12px; color: #94A3B8;">
            🎮 <b>Touchable Canvas Active:</b> Touch or click any node to drag it across the canvas. Click empty space to unselect.
        </div>
        """, unsafe_allow_html=True)
        active_mode = "smart"

with ctrl_col2:
    st.markdown("""
    <div style="background-color: #0C1220; border: 1px solid #1A263D; border-radius: 6px; padding: 10px 14px; font-size: 11.5px;">
        <b style="color: #94A3B8; text-transform: uppercase; letter-spacing: 0.04em;">Node Legend:</b><br/>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px;">
            <span><span style="color:#FF3366;">◆</span> <b>Cross-Channel (≥2 Chans)</b></span>
            <span><span style="color:#00ADB5;">■</span> Channel Hub</span>
            <span><span style="color:#FFD369;">●</span> UPI ID</span>
            <span><span style="color:#FF5722;">●</span> Phone</span>
            <span><span style="color:#9C27B0;">●</span> Crypto</span>
            <span><span style="color:#3B82F6;">●</span> Username</span>
            <span><span style="color:#10B981;">●</span> IFSC</span>
            <span><span style="color:#475569;">●</span> Post</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# Render Graph Visualization based on chosen canvas engine
if "Touchable & Movable" in canvas_engine:
    vis_html = render_vis_network_html(G, height=660, title=graph_title)
    components.html(vis_html, height=690)
else:
    try:
        fig = plot_entity_graph(G, title=graph_title, label_mode=active_mode)
    except TypeError:
        fig = plot_entity_graph(G, title=graph_title)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Tabs for Dossiers & Syndicates
tab1, tab2, tab3 = st.tabs(["🚨 Cross-Channel Actors", "👥 Connected Syndicates", "👤 Deep Seller Dossier Lookup"])

with tab1:
    st.subheader("Identified Cross-Channel Actors")
    st.caption("Illicit payment accounts, phones, and handles observed operating across multiple broadcast channels.")
    if cross_actors:
        df_cross = pd.DataFrame(cross_actors)
        df_cross = df_cross.rename(columns={
            "value": "Identifier Value",
            "type": "Entity Type",
            "channel_count": "Active Channels Count",
            "channels": "Channel List",
            "degree": "Node Degree",
            "betweenness": "Betweenness Centrality"
        })
        st.dataframe(df_cross[["Identifier Value", "Entity Type", "Active Channels Count", "Channel List", "Node Degree", "Betweenness Centrality"]], use_container_width=True, hide_index=True)
    else:
        st.info("No cross-channel actors identified in the current graph view.")

with tab2:
    st.subheader("Connected Campaign Syndicates")
    st.caption("Multi-node clusters sharing overlapping infrastructure and mule accounts.")
    if syndicates:
        for syn in syndicates:
            with st.expander(f"Syndicate {syn['syndicate_id']} | Risk: {syn['risk_tier']} | {syn['channel_count']} Channels | {syn['total_nodes']} Total Nodes"):
                st.markdown(f"**Channels Involved:** `{', '.join(syn['channels'])}`")
                st.markdown(f"**Cross-Channel Mule Actors:** `{syn['cross_channel_actors']}`")
                st.markdown(f"**Total Identifier Nodes:** `{syn['identifier_count']}`")
                st.markdown(f"**Associated Posts:** `{syn['post_count']}`")
    else:
        st.info("No multi-node connected syndicates detected.")

with tab3:
    st.subheader("👤 Deep Seller Dossier Lookup")
    st.caption("Generate complete cross-channel forensic dossier for an identifier.")
    default_id = cross_actors[0]["value"] if cross_actors else "mule.syndicate@ybl"
    search_val = st.text_input("Enter Identifier (UPI, Phone, Username)", value=default_id)
    if search_val:
        profile = generate_seller_profile(search_val, db)
        if profile.get("found"):
            st.markdown(f"""
            <div class="intel-card" style="padding:16px 20px;">
                <h4 style="color:#00E5FF; margin:0 0 10px 0;">Dossier: {profile['identifier']} ({profile['type']})</h4>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:13px;">
                    <div><b>First Observed:</b> <code style="color:#94A3B8;">{profile['first_seen']}</code></div>
                    <div><b>Last Observed:</b> <code style="color:#94A3B8;">{profile['last_seen']}</code></div>
                    <div><b>Channels Active ({profile.get('channel_count', 0)}):</b> <code>{', '.join(str(c) for c in profile.get('channels', []))}</code></div>
                    <div><b>Total Linked Posts:</b> <b>{profile['total_posts']}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if profile.get("co_occurring_identifiers"):
                st.markdown("#### Co-Occurring Identifiers in Same Post")
                df_co = pd.DataFrame(profile["co_occurring_identifiers"])
                st.dataframe(df_co, use_container_width=True, hide_index=True)
        else:
            st.info(profile.get("summary", "Identifier not found."))
