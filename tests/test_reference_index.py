import sqlite3
from pathlib import Path

from classicmac_kb_tools.build_index import build
from classicmac_kb_tools.reference_index import ReferenceRoot, index_references


SOURCE_SCHEMA = r'''{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["id","kind","title","locator","redistribution","trust"]
}'''

KNOWLEDGE_SCHEMA = r'''{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "type":"object",
  "required":["id","title","scope","state","validation_level","statement","applicability","evidence","tags"]
}'''


def _minimal_kb(root: Path) -> None:
    (root / "schema").mkdir(parents=True)
    (root / "schema" / "source-record.schema.json").write_text(SOURCE_SCHEMA, encoding="utf-8")
    (root / "schema" / "knowledge-record.schema.json").write_text(KNOWLEDGE_SCHEMA, encoding="utf-8")
    (root / "sources").mkdir()
    (root / "knowledge").mkdir()
    (root / "sources" / "test.yaml").write_text(
        """schema_version: 1
sources:
  - id: test.source
    kind: repository_file
    title: Test
    locator: {repository: example/repo, path: README.md}
    redistribution: public
    trust: controlled_observation
""",
        encoding="utf-8",
    )
    (root / "knowledge" / "test.yaml").write_text(
        """schema_version: 1
records:
  - id: test.fact
    title: Test
    scope: global
    state: verified
    validation_level: static_verified
    statement: Test statement.
    applicability: {}
    evidence:
      - {source_id: test.source, role: origin}
    tags: [test]
""",
        encoding="utf-8",
    )


def test_reference_index_is_separate_and_searchable(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    _minimal_kb(root)
    database = root / "classicmac.sqlite"
    build(root, database, [])

    references = tmp_path / "references"
    references.mkdir()
    (references / "manual.txt").write_text(
        "CodeWarrior SDK API Reference\nCWGetProjectFileCount returns the number of files in the active target.\n",
        encoding="utf-8",
    )
    (references / "section.html").write_text(
        "<html><head><title>Access Paths</title></head><body>"
        "<h1>CWGetAccessPathInfo</h1><p>Returns information about an access path.</p>"
        "<script>ignore_me()</script></body></html>",
        encoding="utf-8",
    )

    count = index_references(
        database,
        [ReferenceRoot("metrowerks-private", references, "vendor_documentation")],
    )
    assert count == 2

    db = sqlite3.connect(database)
    try:
        row = db.execute(
            "SELECT corpus, source_layer, path, title FROM reference_fts "
            "WHERE reference_fts MATCH 'CWGetProjectFileCount'"
        ).fetchone()
        assert row == (
            "metrowerks-private",
            "vendor_documentation",
            "manual.txt",
            "manual",
        )

        html_row = db.execute(
            "SELECT title, content FROM reference_fts WHERE reference_fts MATCH 'CWGetAccessPathInfo'"
        ).fetchone()
        assert html_row is not None
        assert html_row[0] == "Access Paths"
        assert "ignore_me" not in html_row[1]

        assert db.execute("SELECT count(*) FROM knowledge").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM reference_documents").fetchone()[0] == 2
    finally:
        db.close()


def test_single_reference_file_can_be_a_separate_historical_book_corpus(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    _minimal_kb(root)
    database = root / "classicmac.sqlite"
    build(root, database, [])

    book = tmp_path / "sydow.txt"
    book.write_text("CodeWarrior project and resource discussion", encoding="utf-8")
    count = index_references(
        database,
        [ReferenceRoot("sydow", book, "historical_book")],
    )
    assert count == 1

    db = sqlite3.connect(database)
    try:
        row = db.execute(
            "SELECT source_layer, path FROM reference_documents WHERE corpus='sydow'"
        ).fetchone()
        assert row == ("historical_book", "sydow.txt")
    finally:
        db.close()


def test_reference_input_must_exist(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    _minimal_kb(root)
    database = root / "classicmac.sqlite"
    build(root, database, [])

    missing = tmp_path / "missing"
    try:
        index_references(database, [ReferenceRoot("missing", missing)])
    except ValueError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("expected missing reference input to fail")
