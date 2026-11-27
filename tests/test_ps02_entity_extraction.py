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


def test_safe_child_rejects_windows_drive_paths(tmp_path):
    with pytest.raises(PS02DatasetError):
        safe_child(tmp_path, r"C:\\Windows\\system.ini")
