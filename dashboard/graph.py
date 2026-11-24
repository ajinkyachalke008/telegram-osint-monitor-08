"""Link Analysis and Entity Knowledge Graph Module.

Constructs multi-relational NetworkX graphs linking:
- Identifiers (UPI, Phone, Username, Crypto Wallet, IFSC, Location)
- Public Channels
- Flagged Posts

Calculates centrality (degree, betweenness), persists edges to SQLite WAL DB,
identifies cross-channel syndicates (actors operating in 2+ channels),
generates detailed Seller Profiles, and renders interactive Plotly visualizations.
"""
from typing import List, Dict, Any, Tuple, Optional
import json
import networkx as nx
import plotly.graph_objects as go

from core.db import Database

# Color palette for node types
NODE_COLORS = {
    "Channel": "#00ADB5",           # Teal
    "UPI": "#FFD369",               # Gold / Yellow
    "Phone": "#FF5722",             # Deep Orange
    "Crypto (ETH/EVM)": "#9C27B0",  # Purple
    "Crypto (BTC)": "#F7931A",      # Bitcoin Orange
    "Crypto (TRX/TRC20)": "#E91E63",# Deep Pink / Tron
    "Username": "#2196F3",          # Blue
    "IFSC": "#4CAF50",              # Green
    "Location": "#8BC34A",          # Light Green
    "Post": "#607D8B",              # Blue Grey
    "Cross-Channel": "#E50914",     # Red alert
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
            G.add_node(channel, node_type="Channel", label=channel, size=22, color=NODE_COLORS["Channel"])

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

            color = NODE_COLORS.get(etype, "#FFC107")

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
            G.nodes[node_id]["size"] = 24  # Larger node size
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
            G.nodes[u]["size"] = 22
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
                G.nodes[node_id]["color"] = NODE_COLORS["Cross-Channel"] if is_cross else NODE_COLORS.get(r["type"], "#FFC107")
                G.nodes[node_id]["size"] = 24 if is_cross else 14
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


def plot_entity_graph(G: nx.Graph, title: str = "Cross-Channel Link Analysis Graph") -> go.Figure:
    """Generate interactive Plotly Graph of the entity network."""
    if len(G.nodes) == 0:
        fig = go.Figure()
        fig.update_layout(title="No entity nodes to display.")
        return fig

    # Layout using Spring layout
    pos = nx.spring_layout(G, k=0.45, iterations=50, seed=42)

    # Edge traces
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color="rgba(150, 150, 150, 0.45)"),
        hoverinfo="none",
        mode="lines"
    )

    # Node traces
    node_x, node_y, node_colors, node_sizes, node_text, node_hover = [], [], [], [], [], []

    for node, data in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_colors.append(data.get("color", "#999"))
        node_sizes.append(data.get("size", 12))

        ntype = data.get("node_type", "Node")
        lbl = data.get("label", node)
        
        # Display text on node for cross-channel or channels
        if data.get("cross_channel") or ntype == "Channel":
            node_text.append(f"<b>{lbl}</b>")
        else:
            node_text.append("")

        # Detailed hover tooltip
        if data.get("cross_channel"):
            chans = "<br> • ".join(data.get("channels", []))
            hover = (
                f"🚨 <b>CROSS-CHANNEL ACTOR</b><br>"
                f"<b>Identifier:</b> {lbl}<br>"
                f"<b>Type:</b> {ntype}<br>"
                f"<b>Channel Count:</b> {data.get('channel_count')}<br>"
                f"<b>Betweenness Centrality:</b> {data.get('betweenness_centrality', 0.0):.4f}<br>"
                f"<b>Appears In:</b><br> • {chans}"
            )
        elif ntype == "Channel":
            hover = f"📢 <b>Telegram Channel</b><br><b>Name:</b> {lbl}<br><b>Degree:</b> {G.degree(node)}"
        elif ntype == "Post":
            hover = (
                f"📝 <b>Post</b><br>"
                f"<b>Channel:</b> {data.get('channel')}<br>"
                f"<b>Category:</b> {data.get('category')}<br>"
                f"<b>Risk:</b> {data.get('risk')}<br>"
                f"<b>Preview:</b> {data.get('text', '')}"
            )
        else:
            hover = f"🔍 <b>Identifier:</b> {lbl}<br><b>Type:</b> {ntype}<br><b>Channel:</b> {', '.join(data.get('channels', []))}"

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
            line=dict(width=2, color="#FFFFFF"),
            opacity=0.92,
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(text=title, font=dict(size=18, color="#FFFFFF")),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=10, r=10, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="#11151C",
            paper_bgcolor="#11151C",
            font=dict(color="#ECEFF1"),
        )
    )
    return fig
