# PS02 Offline Dataset Preflight

A lightweight structural QA tool for the participant-facing PS02 demo dataset.
Run it locally before demo ingestion.

```bash
python scripts/ps02_preflight.py --dataset /path/to/PS02_demo_data
python scripts/ps02_preflight.py --dataset /path/to/PS02_demo_data.zip --output preflight.json
```

The report contains aggregate counts only. This utility does not classify text,
extract contact/payment identifiers, profile people, or create cross-platform
links. The dataset is read offline; ZIP members are not extracted.

This is a preflight/QA tool, not a production ingestion pipeline or evidence
verification system. Participant data should remain local; do not commit exports
or source dataset files to the repository.
