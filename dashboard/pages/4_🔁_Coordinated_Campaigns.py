"""Page 4: Coordinated Campaigns & Repeated-Ad Detection."""
import sys
from pathlib import Path

for p in [Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent]:
    if (p / "core").exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd

from core.db import Database
from dashboard.similarity import find_text_ad_clusters
from dashboard.provenance_banner import render_provenance_banner
from dashboard.theme import inject_theme

st.set_page_config(page_title="Coordinated Campaigns | telegram-osint-monitor-08", page_icon="🔁", layout="wide")

# Inject Master Theme
inject_theme()

# Standard Provenance Banner
render_provenance_banner(page_title="Coordinated Campaigns", active_stream="VERIFIED-SYNTHETIC")

st.title("🔁 Coordinated Marketing Campaigns & Repeated Ads")
st.caption("MinHash Jaccard text similarity to uncover copy-pasted marketing templates and coordinated syndicates across monitored channels.")

db = Database()

# Sidebar threshold
st.sidebar.markdown("""
<div style="padding-bottom:8px; border-bottom:1px solid #1E2B45; margin-bottom:12px;">
    <span style="font-weight:700; color:#00E5FF; font-size:12px; text-transform:uppercase; letter-spacing:0.06em;">⚙️ SIMILARITY CONTROLS</span>
</div>
""", unsafe_allow_html=True)

threshold = st.sidebar.slider("MinHash Jaccard Similarity Threshold", 0.40, 0.95, 0.65, 0.05,
                              help="Controls how strictly duplicate ad text is grouped into coordinated campaign clusters.")

# Load posts
with db.get_connection() as conn:
    rows = conn.execute(
        """
        SELECT p.post_uid, p.channel_id as source, p.message_id as post_id, p.raw_text as text,
               p.category as primary_category, p.risk_level, p.timestamp_utc as timestamp
        FROM posts p
        ORDER BY p.timestamp_utc DESC LIMIT 250
        """
    ).fetchall()
    posts = [dict(r) for r in rows]

if not posts:
    st.warning("No posts available in database.")
    st.stop()

# Find clusters
clusters = find_text_ad_clusters(posts, threshold=threshold)
cross_clusters = [cl for cl in clusters if len(cl.get("channels", [])) >= 2]

# Top KPI Overview Strip
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Monitored Posts Analyzed", f"{len(posts)}")
with k2:
    st.metric("Coordinated Ad Clusters", f"{len(clusters)}")
with k3:
    st.metric("Cross-Channel Campaigns", f"{len(cross_clusters)}", delta="Active in ≥2 Channels", delta_color="inverse")
with k4:
    st.metric("Jaccard Threshold", f"{threshold*100:.0f}%", delta="MinHash LSH Matching")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

if not clusters:
    st.info("No repeated ad clusters detected above the selected threshold.")
else:
    for idx, cl in enumerate(clusters, 1):
        channels = cl.get("channels", [])
        post_count = cl.get("post_count", len(cl.get("posts", [])))
        sample_text = cl.get("sample_text", "")

        is_cross = len(channels) >= 2
        header_color = "#FF3366" if is_cross else "#00ADB5"
        header_badge = "🚨 CROSS-CHANNEL SYNDICATE CAMPAIGN" if is_cross else "LOCAL CHANNEL SPAM"

        ch_badges = " ".join([f'<span class="badge-pill badge-user">{ch}</span>' for ch in channels])

        with st.expander(f"Campaign #{idx:02d}: {header_badge} ({post_count} posts across {len(channels)} channels)"):
            st.markdown(f"""
            <div style="background-color:rgba(0,0,0,0.2); padding:12px 16px; border-radius:6px; border:1px solid #1E2B45; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <b style="color:{header_color}; font-size:13px;">{header_badge}</b> &bull; 
                        <span style="color:#94A3B8; font-size:12px;">{post_count} instances recorded</span>
                    </div>
                    <div>
                        {ch_badges}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Representative Ad Copy Template")
            st.code(sample_text)

            st.markdown("#### Matched Post Instances")
            matched_posts = cl.get("posts", [])
            for mp in matched_posts[:6]:
                mp_text = (mp.get("text") or "")[:120]
                st.caption(f"• **{mp.get('source')}** (Msg #{mp.get('post_id')} | {mp.get('timestamp')}): {mp_text}...")
