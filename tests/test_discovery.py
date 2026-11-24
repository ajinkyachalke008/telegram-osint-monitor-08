"""Unit tests for Phase 3 Channel Discovery & Snowball Module:
- Keyword loading
- Forward origin extraction for snowballing
- Channel threat score aggregation
- Watchlist CSV generation
"""
from pathlib import Path
import pytest

from discovery.finder import (
    load_keywords,
    extract_forward_origins,
    score_channel_posts,
    save_watchlist_csv,
)
from addons.scorer import RuleScorer


def test_load_keywords():
    keywords = load_keywords()
    assert len(keywords) >= 5
    assert any("mule" in k.lower() or "khata" in k.lower() for k in keywords)


def test_extract_forward_origins():
    sample_posts = [
        {
            "id": 1,
            "text": "Check this update https://t.me/central_mule_channel/40",
            "fwd_from": {"channel": "underground_deals", "id": 12}
        },
        {
            "id": 2,
            "text": "Join our backup channel t.me/p2p_backup_hub now",
            "fwd_from": "direct_vendor_channel"
        }
    ]
    origins = extract_forward_origins(sample_posts)
    assert "underground_deals" in origins
    assert "direct_vendor_channel" in origins
    assert "central_mule_channel" in origins
    assert "p2p_backup_hub" in origins


def test_score_channel_posts():
    scorer = RuleScorer()
    sample_posts = [
        {
            "id": 10,
            "text": "Current account rent khata available demo.seller@ybl +91 90000 00000"
        },
        {
            "id": 11,
            "text": "Regular news and updates about morning events"
        }
    ]
    metrics = score_channel_posts(sample_posts, scorer)
    assert metrics["total_posts"] == 2
    assert metrics["threat_score"] > 0
    assert metrics["actionable_posts"] == 1
    assert "demo.seller@ybl" in metrics["upis"]
    assert "+919000000000" in metrics["phones"]


def test_save_watchlist_csv(tmp_path):
    output_file = tmp_path / "watchlist_test.csv"
    ranked_channels = [
        {
            "channel": "test_mule_channel",
            "threat_score": 14.5,
            "high_risk_posts": 3,
            "actionable_posts": 5,
            "total_posts": 10,
            "categories": ["bank_account", "sim_card"],
            "upis": ["demo.seller@ybl"],
            "phones": ["+919000000000"],
            "sample_text": "Sample illicit post",
        }
    ]
    save_watchlist_csv(ranked_channels, output_path=output_file)
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8-sig")
    assert "test_mule_channel" in content
    assert "14.5" in content
    assert "demo.seller@ybl" in content
