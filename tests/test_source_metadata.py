import json
import sqlite3

from classicmac_kb_tools.source_metadata import index_source_metadata


def test_source_metadata_is_persisted(tmp_path):
    root = tmp_path / "kb"
    sources = root / "sources"
    sources.mkdir(parents=True)
    (sources / "vendor.yaml").write_text(
        """schema_version: 1
sources:
  - id: vendor.sdk
    kind: primary_documentation
    title: Vendor SDK
    locator:
      repository: private/repo
    redistribution: metadata_only
    trust: primary_source
    vendor: Vendor
    revision: '2003-08-25'
    retrieval: followup
    applicability:
      target: unverified
    domains: [ide, plugin_api]
    parts:
      - order: 1
        path: SDK1.txt
      - order: 2
        path: SDK2.txt
    restrictions:
      c89_default_context: exclude
""",
        encoding="utf-8",
    )

    database = tmp_path / "classicmac.sqlite"
    db = sqlite3.connect(database)
    try:
        db.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE sources (id TEXT PRIMARY KEY);
            INSERT INTO sources (id) VALUES ('vendor.sdk');
            """
        )
        db.commit()
    finally:
        db.close()

    assert index_source_metadata(database, root) == 1

    db = sqlite3.connect(database)
    try:
        raw = db.execute(
            "SELECT metadata_json FROM source_metadata WHERE source_id='vendor.sdk'"
        ).fetchone()[0]
    finally:
        db.close()

    metadata = json.loads(raw)
    assert metadata["vendor"] == "Vendor"
    assert metadata["revision"] == "2003-08-25"
    assert metadata["applicability"]["target"] == "unverified"
    assert metadata["parts"][1]["path"] == "SDK2.txt"
    assert metadata["restrictions"]["c89_default_context"] == "exclude"
