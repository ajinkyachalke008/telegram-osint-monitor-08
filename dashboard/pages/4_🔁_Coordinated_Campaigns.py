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

st.set_page_config(page_title="Coordinated Campaigns | TGSherlock", page_icon="🔁", layout="wide")

st.title("🔁 Coordinated Marketing Campaigns & Repeated Ads")
st.caption("MinHash Jaccard text similarity to uncover copy-pasted marketing templates and coordinated syndicates.")

db = Database()

# Sidebar threshold
threshold = st.sidebar.slider("MinHash Jaccard Similarity Threshold", 0.40, 0.95, 0.65, 0.05)

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

st.markdown(f"**Found {len(clusters)} coordinated ad clusters across monitored channels.**")

if not clusters:
    st.info("No repeated ad clusters detected above the selected threshold.")
else:
    for idx, cl in enumerate(clusters, 1):
        channels = cl.get("channels", [])
        post_count = cl.get("post_count", len(cl.get("posts", [])))
        sample_text = cl.get("sample_text", "")

        is_cross = len(channels) >= 2
        header_badge = "🚨 CROSS-CHANNEL CAMPAIGN" if is_cross else "LOCAL CHANNEL SPAM"

        with st.expander(f"Campaign #{idx:02d}: {header_badge} ({post_count} posts across {len(channels)} channels)"):
            st.markdown(f"**Channels Involved:** `{', '.join(channels)}`")
            st.markdown(f"**Total Ad Instances:** `{post_count}`")
            st.markdown("#### Representative Ad Copy Template")
            st.code(sample_text)

            st.markdown("#### Matched Posts Instances")
            matched_posts = cl.get("posts", [])
            for mp in matched_posts[:5]:
                st.caption(f"• **{mp.get('source')}** (Msg #{mp.get('post_id')} | {mp.get('timestamp')}): {mp.get('text')[:100]}...")
