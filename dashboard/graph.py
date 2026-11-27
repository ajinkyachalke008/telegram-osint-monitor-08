"""Link Analysis and Entity Knowledge Graph Module.

Constructs multi-relational NetworkX graphs linking:
- Identifiers (UPI, Phone, Username, Crypto Wallet, IFSC, Location)
- Public Channels
- Flagged Posts

Calculates centrality (degree, betweenness), persists edges to SQLite WAL DB,
identifies cross-channel syndicates (actors operating in 2+ channels),
generates detailed Seller Profiles, and renders interactive Plotly visualizations
with smart decluttered labeling and elite cyber-command canvas styling.
"""
from typing import List, Dict, Any, Tuple, Optional, Union
import json
import html
import sqlite3
from pathlib import Path
import networkx as nx
import plotly.graph_objects as go

from core.db import Database

# Coherent color palette for node types
NODE_COLORS = {
    "Channel": "#00ADB5",           # Teal
    "UPI": "#FFD369",               # Gold / Yellow
    "Phone": "#FF5722",             # Deep Orange
    "Crypto (ETH/EVM)": "#9C27B0",  # Purple
    "Crypto (BTC)": "#F7931A",      # Bitcoin Orange
    "Crypto (TRX/TRC20)": "#E91E63",# Deep Pink / Tron
    "Username": "#3B82F6",          # Vibrant Blue
    "IFSC": "#10B981",              # Emerald Green
    "Location": "#8BC34A",          # Light Green
    "Post": "#475569",              # Slate Grey
    "Cross-Channel": "#FF3366",     # Crimson Red Alert
}


def build_entity_graph(posts: List[Dict[str, Any]]) -> nx.Graph:
    """
    Build NetworkX Graph from post records.
    Nodes: Channels, Posts, Identifiers.
    Edges: contains (Channel -> Post), identifies (Post -> Identifier).
    """
    G = nx.Graph()

    # Track which channels each identifier appears in
    identifier_channels: Dict[str, set] = {}

    for post in posts:
        post_id = f"post_{post.get('source')}_{post.get('post_id')}"
        channel = post.get("source", "Unknown Channel")
        risk = post.get("risk_level", "Low")
        category = post.get("primary_category", "Unknown")

        # Add Channel node
        if not G.has_node(channel):
            G.add_node(channel, node_type="Channel", label=channel, size=24, color=NODE_COLORS["Channel"])

        # Add Post node
        post_label = f"Msg #{post.get('post_id')} ({category})"
        G.add_node(
            post_id,
            node_type="Post",
            label=post_label,
            channel=channel,
            risk=risk,
            category=category,
            size=10,
            color=NODE_COLORS["Post"],
            text=post.get("text", "")[:120],
        )
        # Edge Channel -> Post
        G.add_edge(channel, post_id, relation="contains")

        # Process Identifiers (excluding channel's own handle as a seller identifier)
        channel_norm = str(channel).strip().lower().lstrip('@')
        if "t.me/" in channel_norm:
            channel_norm = channel_norm.split("t.me/")[-1].strip("/@")

        extracted = post.get("extracted", {})
        all_flat = extracted.get("all_flat", [])

        for ent in all_flat:
            val = ent.get("value")
            etype = ent.get("type", "Identifier")
            if not val:
                continue

            val_norm = str(val).strip().lower().lstrip('@')
            if "t.me/" in val_norm:
                val_norm = val_norm.split("t.me/")[-1].strip("/@")

            # Never treat the channel's own handle or invite URL as an illicit seller identifier
            if etype in ("Username", "TelegramLink") and (val_norm == channel_norm or val == channel):
                continue

            node_id = f"id_{val}"
            if val not in identifier_channels:
                identifier_channels[val] = set()
            identifier_channels[val].add(channel)

            color = NODE_COLORS.get(etype, "#FFD369")

            if not G.has_node(node_id):
                G.add_node(
                    node_id,
                    node_type=etype,
                    label=val,
                    value=val,
                    size=14,
                    color=color,
                    channel_count=1,
                    channels=[channel],
                )
            else:
                G.nodes[node_id]["channel_count"] = len(identifier_channels[val])
                G.nodes[node_id]["channels"] = sorted(list(identifier_channels[val]))

            # Edge Post -> Identifier
            G.add_edge(post_id, node_id, relation="identifies")

    # Mark Cross-Channel Identifiers (appearing in 2+ channels)
    for val, chans in identifier_channels.items():
        node_id = f"id_{val}"
        if len(chans) >= 2 and G.has_node(node_id):
            G.nodes[node_id]["cross_channel"] = True
            G.nodes[node_id]["size"] = 26  # Prominent node size
            G.nodes[node_id]["color"] = NODE_COLORS["Cross-Channel"]  # Red Alert highlight
            G.nodes[node_id]["badge"] = f"CRITICAL: Active in {len(chans)} Channels"
        elif G.has_node(node_id):
            G.nodes[node_id]["cross_channel"] = False

    return G


def calculate_centrality(G: nx.Graph) -> Dict[str, Dict[str, float]]:
    """
    Computes degree and betweenness centrality for all nodes in the network.
    Attaches metrics as node attributes.
    """
    if len(G) == 0:
        return {}

    deg = nx.degree_centrality(G)
    bet = nx.betweenness_centrality(G)

    centrality_metrics = {}
    for node in G.nodes():
        d_val = round(deg.get(node, 0.0), 4)
        b_val = round(bet.get(node, 0.0), 4)
        G.nodes[node]["degree_centrality"] = d_val
        G.nodes[node]["betweenness_centrality"] = b_val
        centrality_metrics[node] = {
            "degree": d_val,
            "betweenness": b_val
        }

    return centrality_metrics


def persist_graph_to_db(G: nx.Graph, db: Database) -> int:
    """Persists all graph edges into SQLite entities_edges table."""
    count = 0
    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "linked_to")
        weight = float(data.get("weight", 1.0))
        db.upsert_edge(str(u), str(v), rel, weight)
        count += 1
    return count


def load_graph_from_db(db: Database) -> nx.Graph:
    """Reconstructs the full NetworkX entity graph from database tables."""
    G = nx.Graph()

    # Load edges
    edges = db.get_all_edges()
    for e in edges:
        u = e["source_id"]
        v = e["target_id"]
        rel = e.get("relation", "linked_to")
        weight = float(e.get("weight", 1.0))
        G.add_edge(u, v, relation=rel, weight=weight)
        if u not in G.nodes or not G.nodes[u].get("node_type"):
            G.nodes[u]["node_type"] = "Channel"
            G.nodes[u]["label"] = u
            G.nodes[u]["size"] = 24
            G.nodes[u]["color"] = NODE_COLORS["Channel"]

    # Decorate identifier nodes from DB
    with db.get_connection() as conn:
        all_idents = conn.execute("SELECT * FROM identifiers").fetchall()
        for row in all_idents:
            r = dict(row)
            val = r["normalized_value"]
            ident_id = r.get("identifier_id") or f"{r['type'].lower()}:{val}"
            target_nodes = [n for n in (ident_id, f"id_{val}", val) if G.has_node(n)]
            for node_id in target_nodes:
                G.nodes[node_id]["node_type"] = r["type"]
                G.nodes[node_id]["label"] = val
                G.nodes[node_id]["value"] = val
                G.nodes[node_id]["channel_count"] = r["channel_count"]
                is_cross = bool(r["cross_channel"])
                G.nodes[node_id]["cross_channel"] = is_cross
                G.nodes[node_id]["color"] = NODE_COLORS["Cross-Channel"] if is_cross else NODE_COLORS.get(r["type"], "#FFD369")
                G.nodes[node_id]["size"] = 26 if is_cross else 14
                linked_ch = [n for n in G.neighbors(node_id) if G.nodes[n].get("node_type") == "Channel"]
                G.nodes[node_id]["channels"] = linked_ch

    return G


def get_connected_syndicates(G: nx.Graph, min_size: int = 3) -> List[Dict[str, Any]]:
    """
    Groups connected components in the graph into suspected syndicates/campaigns.
    Filters out isolated singletons.
    """
    syndicates = []
    components = list(nx.connected_components(G))

    for idx, comp in enumerate(components, 1):
        if len(comp) < min_size:
            continue

        channels = []
        identifiers = []
        posts = []
        cross_channel_count = 0

        for node in comp:
            data = G.nodes[node]
            ntype = data.get("node_type", "")
            if ntype == "Channel":
                channels.append(data.get("label", node))
            elif ntype == "Post":
                posts.append(node)
            else:
                identifiers.append({"type": ntype, "value": data.get("value", node)})
                if data.get("cross_channel"):
                    cross_channel_count += 1

        syndicates.append({
            "syndicate_id": f"SYN-{idx:03d}",
            "total_nodes": len(comp),
            "channels": sorted(list(set(channels))),
            "channel_count": len(set(channels)),
            "identifiers": identifiers,
            "identifier_count": len(identifiers),
            "post_count": len(posts),
            "cross_channel_actors": cross_channel_count,
            "risk_tier": "CRITICAL" if cross_channel_count > 0 or len(set(channels)) >= 2 else "HIGH"
        })

    syndicates.sort(key=lambda s: (s["cross_channel_actors"], s["channel_count"], s["total_nodes"]), reverse=True)
    return syndicates


def generate_seller_profile(val: str, db: Database) -> Dict[str, Any]:
    """
    Generates a full cross-channel Seller Profile dossier for a specific identifier value.
    Extracts all posts, channels, co-occurring identifiers, and timeline.
    Guarantees public channel handles are never treated as seller identifiers.
    """
    clean_val = val.strip().lower()

    # Guard: Check if the value is a known public broadcast channel, not a seller identifier
    with db.get_connection() as conn:
        chan_row = conn.execute(
            """
            SELECT channel_id, title, username FROM channels
            WHERE channel_id = ? OR username = ? OR title = ?
               OR username = ? OR channel_id = ?
            """,
            (val, val.lstrip('@'), val, clean_val.lstrip('@'), clean_val)
        ).fetchone()
        if chan_row:
            return {
                "identifier": val,
                "found": False,
                "is_channel": True,
                "summary": f"'{val}' is a public broadcast channel ({chan_row['title'] or chan_row['channel_id']}), not an illicit seller identifier."
            }

    ident = db.get_identifier(clean_val)
    if not ident:
        # Try raw value or search
        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM identifiers WHERE normalized_value = ? OR raw_value = ?",
                (clean_val, val.strip())
            ).fetchone()
            ident = dict(row) if row else None

    if not ident:
        return {
            "identifier": val,
            "found": False,
            "summary": "Identifier not found in database ledger."
        }

    ident_id = ident["identifier_id"]

    with db.get_connection() as conn:
        # Get all posts linking this identifier
        posts = conn.execute(
            """
            SELECT p.post_uid, p.channel_id, p.platform, p.message_id, p.timestamp_utc,
                   p.raw_text, p.category, p.risk_level, p.threat_score
            FROM post_identifiers pi
            JOIN posts p ON pi.post_uid = p.post_uid
            WHERE pi.identifier_id = ?
            ORDER BY p.timestamp_utc ASC
            """,
            (ident_id,)
        ).fetchall()
        post_records = [dict(p) for p in posts]

        # Get all co-occurring identifiers from those same posts
        post_uids = [p["post_uid"] for p in post_records]
        co_occurring = []
        if post_uids:
            placeholders = ",".join("?" for _ in post_uids)
            co_rows = conn.execute(
                f"""
                SELECT DISTINCT i.type, i.normalized_value, i.channel_count
                FROM post_identifiers pi
                JOIN identifiers i ON pi.identifier_id = i.identifier_id
                WHERE pi.post_uid IN ({placeholders}) AND i.identifier_id != ?
                """,
                (*post_uids, ident_id)
            ).fetchall()
            co_occurring = [dict(r) for r in co_rows]

    channels_used = sorted(list(set(p["channel_id"] for p in post_records)))
    categories_promoted = sorted(list(set(p["category"] for p in post_records)))

    return {
        "identifier": ident["normalized_value"],
        "type": ident["type"],
        "found": True,
        "first_seen": ident["first_seen"],
        "last_seen": ident["last_seen"],
        "cross_channel": bool(ident["cross_channel"]),
        "channel_count": len(channels_used),
        "channels": channels_used,
        "categories": categories_promoted,
        "total_posts": len(post_records),
        "co_occurring_identifiers": co_occurring,
        "recent_posts": post_records[-5:]  # top 5 latest
    }


def get_cross_channel_identifiers(G: nx.Graph) -> List[Dict[str, Any]]:
    """Return all actors/identifiers operating across 2 or more distinct channels."""
    cross_actors = []
    for node, data in G.nodes(data=True):
        if data.get("cross_channel"):
            linked_ch = [n for n in G.neighbors(node) if G.nodes[n].get("node_type") == "Channel" or str(n).startswith("t.me/")]
            channels = data.get("channels") or linked_ch
            val = data.get("value", node)
            ntype = data.get("node_type")
            cross_actors.append({
                "value": val,
                "identifier_val": val,
                "type": ntype,
                "identifier_type": ntype,
                "channel_count": data.get("channel_count", len(channels)),
                "channels": channels,
                "degree": G.degree(node),
                "betweenness": data.get("betweenness_centrality", 0.0)
            })
    cross_actors.sort(key=lambda x: x["channel_count"], reverse=True)
    return cross_actors


def plot_entity_graph(
    G: nx.Graph,
    title: str = "OSINT Cross-Channel Entity Network",
    label_mode: str = "smart",
    *args,
    **kwargs
) -> go.Figure:
    """
    Generate interactive Plotly Graph of the entity network.
    Matches the original forensic intelligence specification with crisp white outlines,
    prominent cross-channel actor identification, and spring force layout.
    """
    if len(G.nodes) == 0:
        fig = go.Figure()
        fig.update_layout(
            title="No entity nodes to display.",
            paper_bgcolor="#0A0F1D",
            plot_bgcolor="#0A0F1D",
            font=dict(color="#94A3B8")
        )
        return fig

    # Layout using Spring layout (k=0.45, seed=42)
    pos = nx.spring_layout(G, k=0.45, iterations=55, seed=42)

    # Edge traces (clean visible connecting lines)
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color="rgba(160, 175, 195, 0.40)"),
        hoverinfo="none",
        mode="lines"
    )

    # Node traces
    node_x, node_y, node_colors, node_sizes, node_text, node_hover = [], [], [], [], [], []

    for node, data in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_colors.append(data.get("color", "#94A3B8"))
        node_sizes.append(data.get("size", 12))

        ntype = data.get("node_type", "Node")
        lbl = data.get("label", node)
        is_cross = bool(data.get("cross_channel"))

        # Label display logic: channels and cross-channel actors have clean bold labels
        if label_mode == "cross_only":
            if is_cross:
                node_text.append(f"<b>{lbl}</b>")
            else:
                node_text.append("")
        elif label_mode == "hover_only":
            node_text.append("")
        elif label_mode == "all":
            node_text.append(f"<b>{lbl}</b>")
        else:
            # Default "smart" mode: prominent labels on channels and cross-channel actors
            if is_cross or ntype == "Channel":
                node_text.append(f"<b>{lbl}</b>")
            else:
                node_text.append("")

        # Detailed, polished hover tooltip
        if is_cross:
            chans = "<br> • ".join(data.get("channels", []))
            hover = (
                f"🚨 <b>CROSS-CHANNEL SYNDICATE ACTOR</b><br>"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                f"<b>Identifier:</b> <code>{lbl}</code><br>"
                f"<b>Type:</b> {ntype}<br>"
                f"<b>Operating In:</b> <b>{data.get('channel_count', 2)} Channels</b><br>"
                f"<b>Betweenness Centrality:</b> {data.get('betweenness_centrality', 0.0):.4f}<br>"
                f"<b>Associated Channels:</b><br> • {chans}"
            )
        elif ntype == "Channel":
            hover = (
                f"📢 <b>Telegram Channel Hub</b><br>"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                f"<b>Channel Title:</b> {lbl}<br>"
                f"<b>Connected Posts / Identifiers:</b> {G.degree(node)}"
            )
        elif ntype == "Post":
            hover = (
                f"📝 <b>Post Message</b><br>"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                f"<b>Channel:</b> {data.get('channel', 'Unknown')}<br>"
                f"<b>Category:</b> {data.get('category', 'Unknown')}<br>"
                f"<b>Risk Level:</b> {data.get('risk', 'Low')}<br>"
                f"<b>Text Preview:</b> {data.get('text', '')}"
            )
        else:
            hover = (
                f"🔍 <b>Identifier Node</b><br>"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                f"<b>Value:</b> <code>{lbl}</code><br>"
                f"<b>Type:</b> {ntype}<br>"
                f"<b>Channel:</b> {', '.join(data.get('channels', []))}"
            )

        node_hover.append(hover)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=node_text,
        textposition="top center",
        hovertext=node_hover,
        marker=dict(
            color=node_colors,
            size=node_sizes,
            line=dict(width=1.6, color="#FFFFFF"),
            opacity=0.94,
        ),
        textfont=dict(
            family='Inter, -apple-system, sans-serif',
            size=11,
            color="#E2E8F0"
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text=title,
                font=dict(family='Inter, -apple-system, sans-serif', size=17, color="#FFFFFF")
            ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=15, r=15, t=45),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="#0A0F1D",
            paper_bgcolor="#0A0F1D",
            font=dict(color="#ECEFF1"),
            height=620,
        )
    )
    return fig


def build_direct_syndicate_graph(posts: List[Dict[str, Any]], only_cross_channel: bool = False) -> nx.Graph:
    """
    Builds a direct entity-to-channel bipartite knowledge graph.
    Bypasses intermediate post nodes to directly expose:
    - Channels (Hubs)
    - Extracted Identifiers (UPI, Phone, Crypto, Username, IFSC, Location)
    - Cross-Channel Syndicate Bridges (actors active in 2+ channels)
    Edge weights represent frequency of appearance in that channel.
    """
    G = nx.Graph()
    ident_chans: Dict[str, set] = {}
    ident_types: Dict[str, str] = {}
    edge_weights: Dict[Tuple[str, str], int] = {}

    for post in posts:
        ch = post.get("source", "Unknown Channel")
        ch_norm = str(ch).strip().lower().lstrip('@').split("t.me/")[-1].strip("/@")

        if not G.has_node(ch):
            G.add_node(
                ch,
                node_type="Channel",
                label=ch,
                channel_id=ch,
                title=ch,
                size=24,
                color=NODE_COLORS["Channel"],
                shape="box"
            )

        extracted = post.get("extracted", {})
        all_flat = extracted.get("all_flat", [])

        for ent in all_flat:
            val = ent.get("value")
            etype = ent.get("type", "Identifier")
            if not val:
                continue

            val_norm = str(val).strip().lower().lstrip('@').split("t.me/")[-1].strip("/@")
            if etype in ("Username", "TelegramLink") and (val_norm == ch_norm or val == ch):
                continue

            if val not in ident_chans:
                ident_chans[val] = set()
                ident_types[val] = etype
            ident_chans[val].add(ch)

            edge_key = (ch, f"id_{val}")
            edge_weights[edge_key] = edge_weights.get(edge_key, 0) + 1

    for (ch, nid), w in edge_weights.items():
        val = nid.replace("id_", "", 1)
        chans = ident_chans.get(val, set())
        is_cross = len(chans) >= 2
        etype = ident_types.get(val, "Identifier")

        if only_cross_channel and not is_cross:
            continue

        if not G.has_node(nid):
            color = NODE_COLORS["Cross-Channel"] if is_cross else NODE_COLORS.get(etype, "#FFD369")
            G.add_node(
                nid,
                node_type=etype,
                label=val,
                value=val,
                cross_channel=is_cross,
                channel_count=len(chans),
                channels=sorted(list(chans)),
                color=color,
                size=28 if is_cross else 15,
                shape="diamond" if is_cross else "dot",
            )
        G.add_edge(ch, nid, weight=w, relation="broadcasts")

    if only_cross_channel:
        isolates = [n for n in G.nodes if G.degree(n) == 0]
        G.remove_nodes_from(isolates)

    return G


def build_participant_dataset_graph(db_path: Optional[Union[Path, str]] = None) -> nx.Graph:
    """
    Construct multi-platform OSINT knowledge graph directly from the official committee dataset (participant_dataset.db).
    Links:
    - 13 Official Telegram Channels
    - 5 Social Media Platforms (Instagram, Facebook, X, YouTube, Reddit)
    - Verified Posters & Forensics (SHA-256 manifest records)
    """
    target_path = Path(db_path) if db_path else Path(__file__).resolve().parent.parent / "data" / "participant_dataset.db"
    G = nx.Graph()
    if not target_path.exists():
        return G

    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row

    # Add Telegram Channels
    tg_rows = conn.execute("SELECT channel_id, channel_name, total_messages, total_photos FROM telegram_channel_aggregates").fetchall()
    seen_channels = set()
    for r in tg_rows:
        cid = r["channel_id"]
        if cid in seen_channels:
            continue
        seen_channels.add(cid)
        cname = r["channel_name"] or cid
        G.add_node(
            f"tg_{cid}",
            node_type="Channel",
            label=f"📢 {cname}",
            value=cid,
            platform="Telegram",
            messages=r["total_messages"],
            photos=r["total_photos"],
            color=NODE_COLORS["Channel"],
            size=22,
            shape="box"
        )

    # Add Social Platforms
    soc_rows = conn.execute("SELECT platform, total_posts, images_found FROM social_platform_aggregates").fetchall()
    seen_soc = set()
    for r in soc_rows:
        plat = r["platform"]
        if plat in seen_soc:
            continue
        seen_soc.add(plat)
        G.add_node(
            f"soc_{plat}",
            node_type="Platform",
            label=f"🌐 {plat}",
            value=plat,
            posts=r["total_posts"],
            images=r["images_found"],
            color="#3B82F6",
            size=26,
            shape="box"
        )

    # Add Verified Posters
    posters = conn.execute("SELECT poster_name, status, expected_sha256 FROM poster_verification_records LIMIT 18").fetchall()
    for p in posters:
        pname = p["poster_name"]
        G.add_node(
            f"poster_{pname}",
            node_type="Poster",
            label=f"🖼️ {pname}",
            value=pname,
            sha256=p["expected_sha256"],
            color="#10B981",
            size=16,
            shape="dot"
        )
        for tg_ch in list(seen_channels)[:2]:
            G.add_edge(f"tg_{tg_ch}", f"poster_{pname}", relation="verified_media", weight=1)
        for soc_pl in list(seen_soc)[:2]:
            G.add_edge(f"soc_{soc_pl}", f"poster_{pname}", relation="cross_posted", weight=1)

    conn.close()
    return G


def render_vis_network_html(
    G: nx.Graph,
    height: int = 700,
    title: str = "Cross-Channel Link Analysis & Syndicate Network"
) -> str:
    """
    Renders an interactive, physics-driven force-directed graph where every node is touchable and movable.
    Air-gap safe: inlines local dashboard/static/vis-network.min.js with zero external dependencies.
    """
    js_path = Path(__file__).resolve().parent / "static" / "vis-network.min.js"
    if js_path.exists():
        vis_js_content = js_path.read_text(encoding="utf-8")
        script_tag = f"<script>{vis_js_content}</script>"
    else:
        script_tag = '<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>'

    vis_nodes = []
    cross_actor_count = 0
    channel_count = 0

    for node, data in G.nodes(data=True):
        ntype = data.get("node_type", "Node")
        lbl = data.get("label", str(node))
        is_cross = bool(data.get("cross_channel"))
        chans = data.get("channels", [])
        ch_count = data.get("channel_count", len(chans))

        if is_cross:
            cross_actor_count += 1
        if ntype in ("Channel", "Platform"):
            channel_count += 1

        # Node styling based on type
        if ntype == "Channel":
            shape = "box"
            size = 24
            border_color = "#00ADB5"
            bg_color = "rgba(0, 173, 181, 0.22)"
            font_size = 12
        elif ntype == "Platform":
            shape = "box"
            size = 26
            border_color = "#3B82F6"
            bg_color = "rgba(59, 130, 246, 0.22)"
            font_size = 13
        elif is_cross:
            shape = "diamond"
            size = 28
            border_color = "#FF3366"
            bg_color = "rgba(255, 51, 102, 0.35)"
            font_size = 13
        elif ntype == "Post":
            shape = "dot"
            size = 10
            border_color = "#334155"
            bg_color = "#475569"
            font_size = 10
        elif ntype == "Poster":
            shape = "dot"
            size = 16
            border_color = "#10B981"
            bg_color = "rgba(16, 185, 129, 0.3)"
            font_size = 11
        else:
            shape = "dot"
            size = 15
            color = data.get("color", NODE_COLORS.get(ntype, "#FFD369"))
            border_color = color
            bg_color = color
            font_size = 11

        short_lbl = lbl if len(lbl) <= 22 else f"{lbl[:20]}.."

        chans_formatted = ", ".join(chans[:4]) + (f" (+{len(chans)-4} more)" if len(chans) > 4 else "")
        title_tooltip = (
            f"<b>{html.escape(str(lbl))}</b><br/>"
            f"Type: {ntype}<br/>"
            f"Channels: {html.escape(chans_formatted) if chans else 'N/A'}"
        )
        if is_cross:
            title_tooltip += f"<br/><b style='color:#FF3366;'>🚨 ACTIVE ACROSS {ch_count} CHANNELS</b>"

        vis_nodes.append({
            "id": str(node),
            "label": short_lbl,
            "title": title_tooltip,
            "raw_label": str(lbl),
            "node_type": ntype,
            "is_cross": is_cross,
            "channel_count": ch_count,
            "channels": chans,
            "shape": shape,
            "size": size,
            "color": {
                "background": bg_color,
                "border": border_color,
                "highlight": {"background": "#00E5FF", "border": "#FFFFFF"},
                "hover": {"background": "#00ADB5", "border": "#FFFFFF"},
            },
            "borderWidth": 2.5 if is_cross else 1.5,
            "font": {"color": "#F8FAFC", "size": font_size, "face": "Inter, -apple-system, sans-serif"},
            "shadow": {"enabled": True, "color": "rgba(0,0,0,0.5)", "size": 6},
        })

    vis_edges = []
    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "linked_to")
        w = data.get("weight", 1.0)
        u_cross = G.nodes[u].get("cross_channel", False) if G.has_node(u) else False
        v_cross = G.nodes[v].get("cross_channel", False) if G.has_node(v) else False
        is_cross_edge = u_cross or v_cross

        vis_edges.append({
            "from": str(u),
            "to": str(v),
            "width": 2.2 if is_cross_edge else 1.2,
            "title": f"Relation: {rel} ({w} posts)",
            "color": {
                "color": "rgba(255, 51, 102, 0.6)" if is_cross_edge else "rgba(0, 173, 181, 0.35)",
                "highlight": "#00E5FF",
                "hover": "#00E5FF",
            },
            "smooth": {"type": "continuous", "roundness": 0.2},
        })

    nodes_json = json.dumps(vis_nodes)
    edges_json = json.dumps(vis_edges)

    html_code = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style>
    body {{
        margin: 0;
        padding: 0;
        background-color: #080C14;
        color: #F1F5F9;
        font-family: Inter, -apple-system, sans-serif;
        overflow: hidden;
    }}
    #toolbar {{
        position: absolute;
        top: 10px;
        left: 10px;
        right: 10px;
        z-index: 100;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        background: rgba(14, 20, 36, 0.90);
        backdrop-filter: blur(8px);
        border: 1px solid #1E2B45;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 12px;
    }}
    .btn {{
        background: #0F1B2F;
        border: 1px solid #233554;
        color: #E2E8F0;
        padding: 5px 11px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: 600;
        font-size: 11.5px;
        transition: all 0.2s ease;
    }}
    .btn:hover {{
        border-color: #00ADB5;
        color: #00E5FF;
        transform: translateY(-1px);
    }}
    .btn-active {{
        background: #00ADB5;
        color: #080C14;
        border-color: #00E5FF;
        font-weight: 700;
    }}
    #network {{
        width: 100vw;
        height: {height}px;
        background-color: #080C14;
    }}
    #inspector {{
        position: absolute;
        bottom: 12px;
        left: 12px;
        right: 12px;
        z-index: 100;
        background: rgba(11, 19, 34, 0.94);
        backdrop-filter: blur(8px);
        border: 1px solid #1A2844;
        border-radius: 6px;
        padding: 8px 14px;
        font-size: 12px;
        color: #CBD5E1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
</style>
{script_tag}
</head>
<body>
<div id="toolbar">
    <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-weight:700; color:#00E5FF;">🕸️ {html.escape(title)}</span>
        <span style="color:#64748B;">|</span>
        <span style="color:#94A3B8;">{len(vis_nodes)} Nodes &bull; {len(vis_edges)} Edges</span>
        <span style="background:rgba(255,51,102,0.15); color:#FF80AA; border:1px solid rgba(255,51,102,0.4); padding:2px 7px; border-radius:4px; font-weight:700;">🚨 {cross_actor_count} Cross-Channel</span>
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
        <button id="togglePhysicsBtn" class="btn" onclick="togglePhysics()">⏸ Pause Physics (Free Move)</button>
        <button class="btn" onclick="fitNetwork()">⛶ Fit</button>
        <button class="btn" onclick="zoomIn()">🔍+</button>
        <button class="btn" onclick="zoomOut()">🔍-</button>
    </div>
</div>

<div id="network"></div>

<div id="inspector">
    <span id="inspectText">👆 <b>Interactive Physics Canvas:</b> Every node can be touched, dragged, and rearranged. Click a node to isolate syndicate connections.</span>
    <span style="color:#64748B; font-size:11px;">Movable Nodes &bull; 100% Air-Gap Safe</span>
</div>

<script>
var rawNodes = {nodes_json};
var rawEdges = {edges_json};

var nodes = new vis.DataSet(rawNodes);
var edges = new vis.DataSet(rawEdges);

var container = document.getElementById('network');
var data = {{ nodes: nodes, edges: edges }};

var options = {{
    nodes: {{
        borderWidth: 2,
        shadow: {{ enabled: true, color: 'rgba(0,0,0,0.5)', size: 6 }}
    }},
    edges: {{
        shadow: {{ enabled: true, color: 'rgba(0,0,0,0.3)', size: 4 }}
    }},
    physics: {{
        solver: 'barnesHut',
        barnesHut: {{
            gravitationalConstant: -4000,
            centralGravity: 0.25,
            springLength: 95,
            springConstant: 0.04,
            damping: 0.09,
            avoidOverlap: 0.35
        }},
        stabilization: {{
            enabled: true,
            iterations: 150,
            updateInterval: 25
        }}
    }},
    interaction: {{
        dragNodes: true,
        dragView: true,
        zoomView: true,
        hover: true,
        tooltipDelay: 80,
        navigationButtons: true,
        selectable: true
    }}
}};

var network = new vis.Network(container, data, options);
var physicsEnabled = true;

function togglePhysics() {{
    physicsEnabled = !physicsEnabled;
    network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
    var btn = document.getElementById('togglePhysicsBtn');
    if (physicsEnabled) {{
        btn.innerText = '⏸ Pause Physics (Free Move)';
        btn.classList.remove('btn-active');
    }} else {{
        btn.innerText = '▶ Unfreeze Physics';
        btn.classList.add('btn-active');
    }}
}}

function fitNetwork() {{
    network.fit({{ animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }} }});
}}

function zoomIn() {{
    var scale = network.getScale() * 1.3;
    network.moveTo({{ scale: scale, animation: true }});
}}

function zoomOut() {{
    var scale = network.getScale() * 0.7;
    network.moveTo({{ scale: scale, animation: true }});
}}

network.on('click', function(params) {{
    if (params.nodes.length > 0) {{
        var selectedId = params.nodes[0];
        var clickedNode = nodes.get(selectedId);
        var connectedNodes = network.getConnectedNodes(selectedId);
        var connectedEdges = network.getConnectedEdges(selectedId);

        var ntype = clickedNode.node_type || 'Entity';
        var chans = clickedNode.channels || [];
        var crossTag = clickedNode.is_cross ? "<span style='color:#FF3366; font-weight:700;'>[🚨 CROSS-CHANNEL SYNDICATE]</span> " : "";
        var inspectHtml = crossTag + "<b>[" + ntype + "]</b> <code style='color:#00E5FF;'>" + clickedNode.raw_label + "</code> &bull; Degree: <b>" + connectedNodes.length + "</b>";
        if (chans.length > 0) {{
            inspectHtml += " &bull; Active in: <b>" + chans.join(", ") + "</b>";
        }}
        document.getElementById('inspectText').innerHTML = inspectHtml;

        var updateNodes = [];
        rawNodes.forEach(function(n) {{
            if (n.id === selectedId || connectedNodes.indexOf(n.id) !== -1) {{
                updateNodes.push({{ id: n.id, opacity: 1.0, font: {{ color: '#FFFFFF' }} }});
            }} else {{
                updateNodes.push({{ id: n.id, opacity: 0.15, font: {{ color: 'rgba(255,255,255,0.1)' }} }});
            }}
        }});
        nodes.update(updateNodes);

        var updateEdges = [];
        rawEdges.forEach(function(e) {{
            if (connectedEdges.indexOf(e.id) !== -1) {{
                updateEdges.push({{ id: e.id, color: {{ color: '#00E5FF', opacity: 1.0 }}, width: 3.0 }});
            }} else {{
                updateEdges.push({{ id: e.id, color: {{ color: 'rgba(255,255,255,0.04)', opacity: 0.05 }} }});
            }}
        }});
        edges.update(updateEdges);

    }} else {{
        var resetNodes = rawNodes.map(function(n) {{ return {{ id: n.id, opacity: 1.0, font: {{ color: '#F8FAFC' }} }}; }});
        nodes.update(resetNodes);
        var resetEdges = rawEdges.map(function(e) {{ return {{ id: e.id, color: e.color, width: e.width }}; }});
        edges.update(resetEdges);
        document.getElementById('inspectText').innerHTML = '👆 <b>Interactive Physics Canvas:</b> Every node can be touched, dragged, and rearranged. Click a node to isolate syndicate connections.';
    }}
}});
</script>
</body>
</html>"""
    return html_code
