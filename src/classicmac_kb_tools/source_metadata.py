"""Persist optional rich source metadata alongside the canonical source table.

The base `sources` table intentionally keeps stable provenance fields. This module
stores version/vendor/retrieval/applicability/multipart metadata without making
those fields mandatory for every historical source record.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import yaml


_METADATA_KEYS = (
    "vendor",
    "revision",
    "retrieval",
    "applicability",
    "domains",
    "parts",
    "restrictions",
    "collected_at",
)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def index_source_metadata(database: Path, root: Path) -> int:
    """Replace the derived rich-metadata table from source YAML records."""

    if not database.exists():
        raise ValueError(f"database does not exist: {database}")

    rows: list[tuple[str, str]] = []
    sources_root = root / "sources"
    if sources_root.exists():
        for path in sorted(sources_root.rglob("*.yaml")):
            with path.open("r", encoding="utf-8") as handle:
                doc = yaml.safe_load(handle)
            if not isinstance(doc, dict) or doc.get("schema_version") != 1:
                continue
            for item in doc.get("sources", []):
                if not isinstance(item, dict) or "id" not in item:
                    continue
                metadata = {key: item[key] for key in _METADATA_KEYS if key in item}
                rows.append((item["id"], _json(metadata)))

    db = sqlite3.connect(database)
    try:
        db.executescript(
            """
            DROP TABLE IF EXISTS source_metadata;
            CREATE TABLE source_metadata (
                source_id TEXT PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE,
                metadata_json TEXT NOT NULL
            );
            """
        )
        for source_id, metadata_json in rows:
            db.execute(
                "INSERT INTO source_metadata (source_id, metadata_json) VALUES (?, ?)",
                (source_id, metadata_json),
            )
        db.commit()
    finally:
        db.close()

    return len(rows)
