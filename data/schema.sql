-- ============================================================================
-- Unified SQLite Schema for OSINT Threat Intelligence System
-- Tables: channels, posts, identifiers, post_identifiers, evidence, alerts,
--         entities_edges, feedback, audit_log
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Channels Table
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL DEFAULT 'Telegram',
    username TEXT DEFAULT '',
    title TEXT DEFAULT '',
    subscribers INTEGER DEFAULT 0,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    risk_level TEXT DEFAULT 'Clean',
    threat_score REAL DEFAULT 0.0,
    is_monitored INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_channels_username ON channels(username);
CREATE INDEX IF NOT EXISTS ix_channels_risk ON channels(risk_level);

-- 2. Posts Table (Idempotent unique constraint on platform, channel_id, message_id)
CREATE TABLE IF NOT EXISTS posts (
    post_uid TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    media_path TEXT,
    media_hash TEXT,
    source_metadata_json TEXT NOT NULL DEFAULT '{}',
    category TEXT DEFAULT 'Clean',
    risk_level TEXT DEFAULT 'Clean',
    threat_score REAL DEFAULT 0.0,
    ingestion_source TEXT NOT NULL, -- LIVE / IMPORTED / SIMULATED / VERIFIED-SYNTHETIC / HACKATHON_SAMPLE
    created_at TEXT NOT NULL,
    UNIQUE(platform, channel_id, message_id)
);
CREATE INDEX IF NOT EXISTS ix_posts_channel ON posts(channel_id);
CREATE INDEX IF NOT EXISTS ix_posts_time ON posts(timestamp_utc);
CREATE INDEX IF NOT EXISTS ix_posts_risk ON posts(risk_level);
CREATE INDEX IF NOT EXISTS ix_posts_category ON posts(category);

-- 3. Identifiers Table
CREATE TABLE IF NOT EXISTS identifiers (
    identifier_id TEXT PRIMARY KEY, -- e.g. "upi:demo.seller@ybl"
    type TEXT NOT NULL,             -- "UPI", "Phone", "BankAccount", "Crypto", "Username", "IFSC", "Location"
    raw_value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    channel_count INTEGER DEFAULT 1,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    cross_channel INTEGER DEFAULT 0, -- 1 if channel_count >= 2
    UNIQUE(type, normalized_value)
);
CREATE INDEX IF NOT EXISTS ix_identifiers_norm ON identifiers(normalized_value);
CREATE INDEX IF NOT EXISTS ix_identifiers_cross ON identifiers(cross_channel);

-- 4. Post-Identifier Junction Table
CREATE TABLE IF NOT EXISTS post_identifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_uid TEXT NOT NULL,
    identifier_id TEXT NOT NULL,
    extraction_source TEXT NOT NULL DEFAULT 'text', -- 'text' or 'image_ocr'
    FOREIGN KEY(post_uid) REFERENCES posts(post_uid) ON DELETE CASCADE,
    FOREIGN KEY(identifier_id) REFERENCES identifiers(identifier_id) ON DELETE CASCADE,
    UNIQUE(post_uid, identifier_id)
);
CREATE INDEX IF NOT EXISTS ix_post_ident_post ON post_identifiers(post_uid);
CREATE INDEX IF NOT EXISTS ix_post_ident_ident ON post_identifiers(identifier_id);

-- 5. Evidence Ledger Table (Cryptographic Hash Chain)
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    post_uid TEXT NOT NULL,
    canonical_json TEXT NOT NULL,
    current_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    block_height INTEGER NOT NULL,
    generated_at_utc TEXT NOT NULL,
    FOREIGN KEY(post_uid) REFERENCES posts(post_uid) ON DELETE CASCADE,
    UNIQUE(post_uid)
);
CREATE INDEX IF NOT EXISTS ix_evidence_height ON evidence(block_height);
CREATE INDEX IF NOT EXISTS ix_evidence_hash ON evidence(current_hash);

-- 6. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    post_uid TEXT NOT NULL,
    category TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    threat_score REAL NOT NULL,
    matched_terms_json TEXT DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'new', -- 'new', 'reviewing', 'confirmed', 'false_positive'
    analyst_notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(post_uid) REFERENCES posts(post_uid) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS ix_alerts_created ON alerts(created_at);

-- 7. Entity Graph Edges Table
CREATE TABLE IF NOT EXISTS entities_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    UNIQUE(source_id, target_id, relation)
);
CREATE INDEX IF NOT EXISTS ix_edges_source ON entities_edges(source_id);
CREATE INDEX IF NOT EXISTS ix_edges_target ON entities_edges(target_id);

-- 8. Analyst Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT NOT NULL,
    verdict TEXT NOT NULL, -- 'confirmed', 'false_positive', 'ignored'
    notes TEXT DEFAULT '',
    submitted_at TEXT NOT NULL,
    FOREIGN KEY(alert_id) REFERENCES alerts(alert_id) ON DELETE CASCADE
);

-- 9. Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details_json TEXT DEFAULT '{}',
    timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audit_time ON audit_log(timestamp);
