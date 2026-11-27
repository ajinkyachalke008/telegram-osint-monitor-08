"""PS02 Hackathon Participant Dataset Module.

Offline, aggregate-only ingestion, validation, and analytics engine for the
Rajasthan Cyber Police Hackathon 2026 PS02 official participant dataset.

Strictly aggregate-only: no raw post text, usernames, personal phone/payment
identifiers, or individual citizen profiles are stored or displayed.
"""

from ps02_dataset.preflight import audit, safe_zip, discover_root_prefix
from ps02_dataset.parser import parse_participant_dataset
from ps02_dataset.store import ParticipantDatasetStore, DEFAULT_PARTICIPANT_DB_PATH
from ps02_dataset.importer import run_dry_run, run_import

__all__ = [
    "audit",
    "safe_zip",
    "discover_root_prefix",
    "parse_participant_dataset",
    "ParticipantDatasetStore",
    "DEFAULT_PARTICIPANT_DB_PATH",
    "run_dry_run",
    "run_import",
]
