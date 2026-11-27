"""Core data models and type definitions for OSINT Threat Intelligence System."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


def now_utc_iso() -> str:
    """Return current UTC time in strict ISO-8601 with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ChannelRecord:
    channel_id: str
    platform: str = "Telegram"
    username: str = ""
    title: str = ""
    subscribers: int = 0
    first_seen: str = field(default_factory=now_utc_iso)
    last_seen: str = field(default_factory=now_utc_iso)
    risk_level: str = "Clean"
    threat_score: float = 0.0
    is_monitored: bool = False


@dataclass
class PostRecord:
    platform: str
    channel_id: str
    message_id: str
    timestamp_utc: str
    raw_text: str
    normalized_text: str = ""
    media_path: Optional[str] = None
    media_hash: Optional[str] = None
    category: str = "Clean"
    risk_level: str = "Clean"
    threat_score: float = 0.0
    ingestion_source: str = "LIVE"  # 'LIVE', 'IMPORTED', 'SIMULATED'
    created_at: str = field(default_factory=now_utc_iso)
    post_uid: str = ""
    source_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.post_uid:
            self.post_uid = f"{self.platform.lower()}_{self.channel_id}_{self.message_id}"


@dataclass
class IdentifierRecord:
    identifier_id: str
    type: str  # UPI, Phone, BankAccount, Crypto, Username, IFSC, Location
    raw_value: str
    normalized_value: str
    channel_count: int = 1
    first_seen: str = field(default_factory=now_utc_iso)
    last_seen: str = field(default_factory=now_utc_iso)
    cross_channel: bool = False


@dataclass
class EvidenceBlock:
    evidence_id: str
    post_uid: str
    canonical_json: str
    current_hash: str
    prev_hash: str
    block_height: int
    generated_at_utc: str = field(default_factory=now_utc_iso)


@dataclass
class AlertRecord:
    alert_id: str
    post_uid: str
    category: str
    risk_level: str
    threat_score: float
    matched_terms: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "new"  # 'new', 'reviewing', 'confirmed', 'false_positive'
    analyst_notes: str = ""
    created_at: str = field(default_factory=now_utc_iso)
