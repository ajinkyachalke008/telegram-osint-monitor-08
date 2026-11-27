from addons.extractors import extract_all_entities


def test_context_labelled_bank_account_is_extracted_for_cross_source_linking():
    first = extract_all_entities("Ready stock: HDFC current a/c 50200087431926 (IFSC HDFC0004821) + kit.")
    second = extract_all_entities("Ready stock: HDFC current a/c 50200087431926 + net banking.")

    assert first["bank_accounts"] == ["50200087431926"]
    assert second["bank_accounts"] == ["50200087431926"]
    assert any(
        item["type"] == "BankAccount" and item["value"] == "50200087431926"
        for item in first["all_flat"]
    )


def test_bank_account_extraction_requires_account_context():
    assert extract_all_entities("Reference number 50200087431926")["bank_accounts"] == []
    # A ten-digit mobile-shaped value is not reclassified as a bank account.
    assert extract_all_entities("A/C 9876543210")["bank_accounts"] == []


def test_bank_account_candidate_links_telegram_and_social_sources_in_graph():
    from dashboard.graph import build_entity_graph

    text = "Ready stock: HDFC current a/c 50200087431926 + kit."
    posts = [
        {"source": "Telegram:channel_s5", "post_id": "1", "text": text,
         "extracted": extract_all_entities(text)},
        {"source": "Facebook:corp_ac_supply", "post_id": "2", "text": text,
         "extracted": extract_all_entities(text)},
    ]
    graph = build_entity_graph(posts)
    node = graph.nodes["id_50200087431926"]
    assert node["node_type"] == "BankAccount"
    assert node["cross_channel"] is True
    assert set(node["channels"]) == {"Telegram:channel_s5", "Facebook:corp_ac_supply"}




def test_telegram_desktop_sender_accounts_are_linked_across_group_sources(tmp_path):
    from core.db import Database
    from core.models import ChannelRecord
    from ingestion.worker import IngestionWorker

    db = Database(tmp_path / "ps02-sender-accounts.db")
    channel_a = "Telegram:group_08"
    channel_b = "Telegram:group_09"
    db.upsert_channel(ChannelRecord(channel_id=channel_a, title="Synthetic Group 08"))
    db.upsert_channel(ChannelRecord(channel_id=channel_b, title="Synthetic Group 09"))
    worker = IngestionWorker(db=db)
    metadata = {"schema": "telegram_desktop_export", "sender_id": "user987654321", "sender_name": "Sample Member", "provenance": "HACKATHON_SAMPLE"}

    assert worker.process_raw_post("Telegram [PS02:test]", channel_a, "1", "2026-10-01T10:00:00Z", "Sample post one", "HACKATHON_SAMPLE", source_metadata=metadata)
    assert worker.process_raw_post("Telegram [PS02:test]", channel_b, "2", "2026-10-01T11:00:00Z", "Sample post two", "HACKATHON_SAMPLE", source_metadata=metadata)

    linked = [item for item in db.list_cross_channel_identifiers() if item.get("type") == "TelegramAccount"]
    assert len(linked) == 1
    assert linked[0]["normalized_value"] == "user987654321"
    assert channel_a in linked[0]["linked_channels"]
    assert channel_b in linked[0]["linked_channels"]
