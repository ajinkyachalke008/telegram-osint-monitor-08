"""Unit tests for Phase 2 Link Analysis & Dashboard Modules:
- Graph construction and cross-channel identifier detection
- MinHash text ad campaign clustering
- Synthetic dataset loading
"""
import pytest
from pathlib import Path

from dashboard.graph import build_entity_graph, get_cross_channel_identifiers
from dashboard.similarity import find_text_ad_clusters
from dashboard.db_reader import load_synthetic_demo_posts


def test_synthetic_data_loading():
    posts = load_synthetic_demo_posts()
    assert len(posts) >= 5
    # Confirm primary fields exist
    first = posts[0]
    assert "source" in first
    assert "text" in first
    assert "extracted" in first
    assert "risk_level" in first
    assert "evidence" in first


def test_cross_channel_entity_graph():
    posts = load_synthetic_demo_posts()
    G = build_entity_graph(posts)
    assert len(G.nodes) > 0
    assert len(G.edges) > 0

    cross_actors = get_cross_channel_identifiers(G)
    assert len(cross_actors) > 0

    # Specifically check demo.seller@ybl is detected as a cross-channel syndicate
    values = [ca["value"] for ca in cross_actors]
    assert "demo.seller@ybl" in values

    seller_actor = next(ca for ca in cross_actors if ca["value"] == "demo.seller@ybl")
    # Must appear in 3 or more channels as designed
    assert seller_actor["channel_count"] >= 3


def test_minhash_ad_campaign_clustering():
    posts = load_synthetic_demo_posts()
    clusters = find_text_ad_clusters(posts, threshold=0.60)
    assert len(clusters) > 0

    # Verify that the repeated mule recruitment ads were clustered together
    first_cluster = clusters[0]
    assert first_cluster["ad_count"] >= 2
    assert first_cluster["cross_channel"] is True
    assert len(first_cluster["channels"]) >= 2
    assert "demo.seller@ybl" in first_cluster["shared_upis"]
