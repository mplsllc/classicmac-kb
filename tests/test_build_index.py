import sqlite3
import subprocess
from pathlib import Path

import pytest

from classicmac_kb_tools.build_index import GitRepo, build
from classicmac_kb_tools.document_index import DocumentRepo, index_documents


def _write_schema(root: Path) -> None:
    (root / "schema").mkdir(parents=True)
    # Use compact test schemas; production schemas are exercised by the repository build.
    (root / "schema" / "source-record.schema.json").write_text(
        r'''{
          "$schema":"https://json-schema.org/draft/2020-12/schema",
          "type":"object",
          "required":["schema_version","id","kind","title","locator","redistribution","trust"]
        }''',
        encoding="utf-8",
    )
    (root / "schema" / "knowledge-record.schema.json").write_text(
        r'''{
          "$schema":"https://json-schema.org/draft/2020-12/schema",
          "type":"object",
          "required":["schema_version","id","title","scope","state","validation_level","statement","applicability","evidence","tags"]
        }''',
        encoding="utf-8",
    )


def _write_minimal_corpus(root: Path, source_id: str = "test.source") -> None:
    _write_schema(root)
    (root / "sources").mkdir()
    (root / "sources" / "test.yaml").write_text(
        f"""schema_version: 1
sources:
  - id: {source_id}
    kind: repository_file
    title: Test source
    locator: {{repository: example/repo, path: README.md}}
    redistribution: public
    trust: controlled_observation
""",
        encoding="utf-8",
    )
    (root / "knowledge").mkdir()
    (root / "knowledge" / "test.yaml").write_text(
        f"""schema_version: 1
records:
  - id: test.fact
    title: Test fact
    scope: global
    state: verified
    validation_level: static_verified
    statement: CodeWarrior fact for search.
    applicability: {{}}
    evidence:
      - {{source_id: {source_id}, role: origin}}
    tags: [codewarrior]
""",
        encoding="utf-8",
    )


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def _make_repo(path: Path) -> None:
    path.mkdir()
    _git(path, "init")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    (path / "file.c").write_text("int one;\n", encoding="utf-8")
    (path / "README.md").write_text(
        "# CodeWarrior Workflow\n\nUse text diagnostics before screenshots.\n",
        encoding="utf-8",
    )
    _git(path, "add", ".")
    _git(path, "commit", "-m", "first CodeWarrior commit")
    (path / "file.c").write_text("int two;\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-m", "second C89 fix", "-m", "declaration ordering")


def test_build_creates_canonical_and_full_git_history_indexes(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    _write_minimal_corpus(root)
    repo = tmp_path / "project"
    _make_repo(repo)
    output = root / "build" / "classicmac.sqlite"

    build(root, output, [GitRepo("example/project", repo)])

    db = sqlite3.connect(output)
    try:
        assert db.execute("SELECT count(*) FROM knowledge").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM sources").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM git_commits").fetchone()[0] == 2
        hit = db.execute(
            "SELECT sha, subject FROM git_fts WHERE git_fts MATCH 'CodeWarrior'"
        ).fetchone()
        assert hit is not None
        assert "CodeWarrior" in hit[1]
    finally:
        db.close()


def test_document_index_is_opt_in_and_searchable(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    _write_minimal_corpus(root)
    repo = tmp_path / "project"
    _make_repo(repo)
    output = root / "build.sqlite"
    build(root, output, [])

    count = index_documents(output, [DocumentRepo("example/project", repo)])
    assert count == 1

    db = sqlite3.connect(output)
    try:
        row = db.execute(
            "SELECT repository, path, title FROM document_fts WHERE document_fts MATCH 'screenshots'"
        ).fetchone()
        assert row == ("example/project", "README.md", "CodeWarrior Workflow")
        assert db.execute("SELECT count(*) FROM documents").fetchone()[0] == 1
    finally:
        db.close()


def test_build_rejects_unknown_evidence_source(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    _write_minimal_corpus(root, source_id="real.source")
    path = root / "knowledge" / "test.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("real.source", "missing.source"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown source"):
        build(root, root / "build.sqlite", [])


def test_build_rejects_duplicate_knowledge_ids(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    _write_minimal_corpus(root)
    duplicate = root / "knowledge" / "duplicate.yaml"
    duplicate.write_text(
        (root / "knowledge" / "test.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate knowledge id"):
        build(root, root / "build.sqlite", [])
