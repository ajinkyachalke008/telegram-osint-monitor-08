"""Multi-Platform Ingestion Module for External Dumps, Forum Scrapes & CSV/JSON Data.

Standardizes input records (columns: platform, source, post_id, timestamp, text, image_path)
and processes each through the detection pipeline:
1. Identifier Extraction (extractors.py)
2. Risk Scoring & Classification (scorer.py)
3. Cryptographic Chain-of-Custody Hashing (evidence.py)
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from datetime import datetime, timezone

from .extractors import extract_all_entities
from .scorer import RuleScorer
from .evidence import build_evidence_record, normalize_utc_timestamp

# Standard column mapping to handle variations in external dumps
COLUMN_MAPPINGS = {
    "platform": ["platform", "app", "network", "service"],
    "source": ["source", "channel", "channel_title", "chat_title", "group", "forum"],
    "post_id": ["post_id", "msg_id", "message_id", "id", "item_id"],
    "timestamp": ["timestamp", "date", "created_at", "time", "captured_at"],
    "text": ["text", "message", "content", "body", "caption"],
    "image_path": ["image_path", "media_path", "media", "image", "attachment"],
}


class DataImporter:
    def __init__(self, scorer: Optional[RuleScorer] = None):
        self.scorer = scorer or RuleScorer()

    def _normalize_row(self, raw_row: Dict[str, Any], default_platform: str = "Unknown") -> Dict[str, Any]:
        """Map raw dictionary keys to canonical fields."""
        norm = {
            "platform": default_platform,
            "source": "Unknown Channel",
            "post_id": 0,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "text": "",
            "image_path": None,
        }

        # Case-insensitive lookup
        lower_keys = {str(k).strip().lower(): k for k in raw_row.keys()}

        for canonical_col, aliases in COLUMN_MAPPINGS.items():
            for alias in aliases:
                if alias in lower_keys:
                    val = raw_row[lower_keys[alias]]
                    if val is not None:
                        norm[canonical_col] = val
                    break

        # Formatting corrections
        norm["platform"] = str(norm["platform"]).strip()
        norm["source"] = str(norm["source"]).strip()
        norm["text"] = str(norm["text"]) if norm["text"] is not None else ""
        norm["timestamp"] = normalize_utc_timestamp(norm["timestamp"])
        
        return norm

    def process_record(self, raw_record: Dict[str, Any], default_platform: str = "External") -> Dict[str, Any]:
        """Ingest a single record through the extraction, scoring, and evidence pipeline."""
        norm = self._normalize_row(raw_record, default_platform=default_platform)
        
        # 1. Extract Identifiers
        extracted = extract_all_entities(norm["text"])
        
        # 2. Risk Scoring & Explainability
        score_res = self.scorer.score(norm["text"], identifiers=extracted)
        score_dict = score_res.to_dict()
        
        # 3. Cryptographic Chain of Custody
        evidence = build_evidence_record(
            channel=norm["source"],
            message_id=norm["post_id"],
            timestamp=norm["timestamp"],
            text=norm["text"],
            matched_terms=score_res.matched_terms,
            extracted_identifiers=extracted,
            media_path=norm.get("image_path"),
            category=score_res.primary_category,
            risk_level=score_res.risk_level,
        )

        return {
            "platform": norm["platform"],
            "source": norm["source"],
            "post_id": norm["post_id"],
            "timestamp": norm["timestamp"],
            "text": norm["text"],
            "image_path": norm.get("image_path"),
            "extracted": extracted,
            "risk_level": score_res.risk_level,
            "total_score": score_res.total_score,
            "primary_category": score_res.primary_category,
            "is_actionable": score_res.is_actionable,
            "matched_terms": score_res.matched_terms,
            "evidence": evidence,
        }

    def import_from_json(self, file_path: Union[str, Path], default_platform: str = "JSON_Dump") -> List[Dict[str, Any]]:
        """Load external posts from a JSON file (array of objects or single dict)."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"JSON import file not found: {p}")
            
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, dict):
            # Check if wrapped in key like 'posts' or 'messages'
            for wrap_key in ("posts", "messages", "items", "data"):
                if wrap_key in data and isinstance(data[wrap_key], list):
                    data = data[wrap_key]
                    break
            else:
                data = [data]
                
        results = [self.process_record(r, default_platform=default_platform) for r in data]
        return results

    def import_from_csv(self, file_path: Union[str, Path], default_platform: str = "CSV_Dump") -> List[Dict[str, Any]]:
        """Load external posts from a CSV file."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"CSV import file not found: {p}")
            
        results = []
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(self.process_record(row, default_platform=default_platform))
        return results

    def import_file(self, file_path: Union[str, Path], default_platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Auto-detect format (CSV or JSON) and process."""
        p = Path(file_path)
        suffix = p.suffix.lower()
        plat = default_platform or f"{p.stem}_import"
        if suffix == ".json":
            return self.import_from_json(p, default_platform=plat)
        elif suffix in (".csv", ".tsv"):
            return self.import_from_csv(p, default_platform=plat)
        else:
            raise ValueError(f"Unsupported file format '{suffix}'. Supported: .json, .csv")
