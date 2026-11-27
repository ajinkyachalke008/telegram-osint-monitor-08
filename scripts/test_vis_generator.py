"""Test render_vis_network_html."""
import json
import html
from pathlib import Path
import networkx as nx

def generate_vis_html(G: nx.Graph, height: int = 700, title: str = "Cross-Channel Link Analysis") -> str:
    js_path = Path("dashboard/static/vis-network.min.js")
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
        val = data.get("value", lbl)
        is_cross = bool(data.get("cross_channel"))
        chans = data.get("channels", [])
        ch_count = data.get("channel_count", len(chans))

        if is_cross:
            cross_actor_count += 1
        if ntype == "Channel":
            channel_count += 1

        # Shape, color and sizing
        if ntype == "Channel":
            shape = "box"
            size = 24
            border_color = "#00ADB5"
            bg_color = "rgba(0, 173, 181, 0.22)"
            font_size = 12
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
        else:
            shape = "dot"
            size = 15
            border_color = data.get("color", "#FFD369")
            bg_color = data.get("color", "#FFD369")
            font_size = 11

        short_lbl = lbl if len(lbl) <= 22 else f"{lbl[:20]}.."

        chans_formatted = ", ".join(chans[:4]) + (f" (+{len(chans)-4} more)" if len(chans) > 4 else "")
        title_tooltip = (
            f"<b>{html.escape(str(lbl))}</b><br/>"
            f"Type: {ntype}<br/>"
            f"Channels: {html.escape(chans_formatted) if chans else 'N/A'}"
        )
        if is_cross:
            title_tooltip += f"<br/><b style='color:#FF3366;'>🚨 ACTIVE IN {ch_count} CHANNELS</b>"

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
            "font": {"color": "#F8FAFC", "size": font_size, "face": "Inter, sans-serif"},
            "shadow": {"enabled": True, "color": "rgba(0,0,0,0.5)", "size": 6},
        })

    vis_edges = []
    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "linked_to")
        w = data.get("weight", 1.0)
        u_cross = G.nodes[u].get("cross_channel", False)
        v_cross = G.nodes[v].get("cross_channel", False)
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
        background: rgba(14, 20, 36, 0.88);
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
        background: rgba(11, 19, 34, 0.92);
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
    <div style="display:flex; align-items:center; gap:6px;">
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
    <span id="inspectText">👆 <b>Interactive Network:</b> Touch or drag any node to rearrange. Click a node to isolate syndicate connections.</span>
    <span style="color:#64748B; font-size:11px;">Movable Nodes &bull; Air-Gap Safe</span>
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

// Node selection & neighborhood isolation
network.on('click', function(params) {{
    if (params.nodes.length > 0) {{
        var selectedId = params.nodes[0];
        var clickedNode = nodes.get(selectedId);
        var connectedNodes = network.getConnectedNodes(selectedId);
        var connectedEdges = network.getConnectedEdges(selectedId);

        // Update inspector text
        var ntype = clickedNode.node_type || 'Entity';
        var chans = clickedNode.channels || [];
        var crossTag = clickedNode.is_cross ? "<span style='color:#FF3366; font-weight:700;'>[🚨 CROSS-CHANNEL SYNDICATE]</span> " : "";
        var inspectHtml = crossTag + "<b>[" + ntype + "]</b> <code style='color:#00E5FF;'>" + clickedNode.raw_label + "</code> &bull; Degree: <b>" + connectedNodes.length + "</b>";
        if (chans.length > 0) {{
            inspectHtml += " &bull; Active in: <b>" + chans.join(", ") + "</b>";
        }}
        document.getElementById('inspectText').innerHTML = inspectHtml;

        // Highlight neighborhood
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
        // Reset full opacity
        var resetNodes = rawNodes.map(function(n) {{ return {{ id: n.id, opacity: 1.0, font: {{ color: '#F8FAFC' }} }}; }});
        nodes.update(resetNodes);
        var resetEdges = rawEdges.map(function(e) {{ return {{ id: e.id, color: e.color, width: e.width }}; }});
        edges.update(resetEdges);
        document.getElementById('inspectText').innerHTML = '👆 <b>Interactive Network:</b> Touch or drag any node to rearrange. Click a node to isolate syndicate connections.';
    }}
}});
</script>
</body>
</html>"""
    return html_code

if __name__ == "__main__":
    G = nx.Graph()
    G.add_node("ch1", node_type="Channel", label="Channel A", color="#00ADB5")
    G.add_node("id1", node_type="UPI", label="mule@ybl", cross_channel=True, color="#FF3366")
    G.add_edge("ch1", "id1", weight=2)
    h = generate_vis_html(G)
    print("Generated HTML size:", len(h), "bytes")
    assert "<!DOCTYPE html>" in h
    assert "vis.Network" in h
    print("Vis-Network HTML generation passed!")
