"""Unit tests for Workstream F: Graph Persistence, Centrality, and Seller Profiling."""
import pytest
from pathlib import Path
import networkx as nx

from core.db import Database
from core.models import PostRecord, IdentifierRecord, now_utc_iso
from dashboard.graph import (
    build_entity_graph,
    calculate_centrality,
    persist_graph_to_db,
    load_graph_from_db,
    get_connected_syndicates,
    generate_seller_profile,
    get_cross_channel_identifiers,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_graph.db"
    return Database(db_path=db_file)


def test_graph_centrality_and_cross_channel_detection():
    sample_posts = [
        {
            "source": "Channel_Alpha",
            "post_id": 101,
            "risk_level": "High",
            "primary_category": "bank_account",
            "text": "Mule account with atm kit. DM @mule_king",
            "extracted": {
                "all_flat": [
                    {"type": "UPI", "value": "shared.mule@ybl"},
                    {"type": "Username", "value": "@mule_king"}
                ]
            }
        },
        {
            "source": "Channel_Beta",
            "post_id": 202,
            "risk_level": "High",
            "primary_category": "bank_account",
            "text": "Fresh bank accounts available. Contact @mule_king",
            "extracted": {
                "all_flat": [
                    {"type": "UPI", "value": "shared.mule@ybl"},
                    {"type": "Username", "value": "@mule_king"},
                    {"type": "Phone", "value": "90000 11111"}
                ]
            }
        }
    ]

    G = build_entity_graph(sample_posts)
    metrics = calculate_centrality(G)

    assert "id_shared.mule@ybl" in G.nodes
    assert G.nodes["id_shared.mule@ybl"]["cross_channel"] is True
    assert G.nodes["id_shared.mule@ybl"]["channel_count"] == 2

    # Verify centrality computed
    assert metrics["id_shared.mule@ybl"]["degree"] > 0

    cross_actors = get_cross_channel_identifiers(G)
    cross_vals = [a["value"] for a in cross_actors]
    assert "shared.mule@ybl" in cross_vals
    assert "@mule_king" in cross_vals


def test_graph_persistence_to_db(temp_db):
    sample_posts = [
        {
            "source": "Channel_Gamma",
            "post_id": 303,
            "risk_level": "High",
            "primary_category": "drugs",
            "text": "Fresh charas delivery. Ping @dealer_gamma",
            "extracted": {
                "all_flat": [
                    {"type": "Phone", "value": "90000 22222"}
                ]
            }
        }
    ]
    G = build_entity_graph(sample_posts)
    edge_count = persist_graph_to_db(G, temp_db)
    assert edge_count >= 2

    db_edges = temp_db.get_all_edges()
    assert len(db_edges) == edge_count

    # Load back
    loaded_G = load_graph_from_db(temp_db)
    assert len(loaded_G.nodes) > 0


def test_seller_profile_generation(temp_db):
    now = now_utc_iso()
    # Ingest two posts across two channels with the same UPI identifier
    post1 = PostRecord(
        post_uid="chan1_101",
        platform="telegram",
        channel_id="chan1",
        message_id=101,
        timestamp_utc=now,
        raw_text="Fresh ATM kit available. UPI demo.mule@ybl",
        normalized_text="fresh atm kit available. upi demo.mule@ybl",
        category="bank_account",
        risk_level="High",
        threat_score=8.5,
        ingestion_source="SIMULATED",
        created_at=now
    )
    post2 = PostRecord(
        post_uid="chan2_202",
        platform="telegram",
        channel_id="chan2",
        message_id=202,
        timestamp_utc=now,
        raw_text="Sell bank account. Contact UPI demo.mule@ybl or 90000 33333",
        normalized_text="sell bank account. contact upi demo.mule@ybl or 90000 33333",
        category="bank_account",
        risk_level="High",
        threat_score=9.0,
        ingestion_source="SIMULATED",
        created_at=now
    )
    temp_db.insert_post(post1)
    temp_db.insert_post(post2)

    ident1 = IdentifierRecord(
        identifier_id="upi:demo.mule@ybl",
        type="UPI",
        raw_value="demo.mule@ybl",
        normalized_value="demo.mule@ybl",
        channel_count=1,
        first_seen=now,
        last_seen=now,
        cross_channel=False
    )
    ident2 = IdentifierRecord(
        identifier_id="phone:9000033333",
        type="Phone",
        raw_value="90000 33333",
        normalized_value="9000033333",
        channel_count=1,
        first_seen=now,
        last_seen=now,
        cross_channel=False
    )
    temp_db.upsert_identifier(ident1, "chan1")
    temp_db.link_post_identifier(post1.post_uid, ident1.identifier_id)
    temp_db.upsert_identifier(ident1, "chan2")
    temp_db.link_post_identifier(post2.post_uid, ident1.identifier_id)
    temp_db.upsert_identifier(ident2, "chan2")
    temp_db.link_post_identifier(post2.post_uid, ident2.identifier_id)

    profile = generate_seller_profile("demo.mule@ybl", temp_db)
    assert profile["found"] is True
    assert profile["channel_count"] == 2
    assert "chan1" in profile["channels"]
    assert "chan2" in profile["channels"]
    assert profile["total_posts"] == 2
    co_occurring = [c["normalized_value"] for c in profile["co_occurring_identifiers"]]
    assert "9000033333" in co_occurring
