"""Link Analysis and Entity Knowledge Graph Module.

Constructs multi-relational NetworkX graphs linking:
- Identifiers (UPI, Phone, Username, Crypto Wallet, IFSC)
- Public Channels
- Flagged Posts

Calculates centrality, identifies cross-channel syndicates (actors operating in 2+ channels),
and generates interactive Plotly visualizations.
"""
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx
import plotly.graph_objects as go


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
    Build NetworkX Graph from standard post records.
    Nodes: Channels, Posts, Identifiers.
    Edges: contains (Channel -> Post), mentions (Post -> Identifier).
    """
    G = nx.Graph()

    # Track which channels each identifier appears in
    identifier_channels = {}

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

        # Process Identifiers
        extracted = post.get("extracted", {})
        all_flat = extracted.get("all_flat", [])

        for ent in all_flat:
            val = ent.get("value")
            etype = ent.get("type", "Identifier")
            if not val:
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


def get_cross_channel_identifiers(G: nx.Graph) -> List[Dict[str, Any]]:
    """Return all actors/identifiers operating across 2 or more distinct channels."""
    cross_actors = []
    for node, data in G.nodes(data=True):
        if data.get("cross_channel"):
            cross_actors.append({
                "value": data.get("value", node),
                "type": data.get("node_type"),
                "channel_count": data.get("channel_count", 0),
                "channels": data.get("channels", []),
                "degree": G.degree(node),
            })
    cross_actors.sort(key=lambda x: x["channel_count"], reverse=True)
    return cross_actors


def plot_entity_graph(G: nx.Graph, title: str = "Cross-Channel Link Analysis Graph") -> go.Figure:
    """
    Generate interactive Plotly Graph of the entity network.
    Highlights cross-channel actors and relationships.
    """
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
