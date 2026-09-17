"""Build a disposable SQLite search database from the canonical KB.

The SQLite file is derived data. Canonical truth remains the YAML/Markdown
content committed to this repository.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml
from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class GitRepo:
    name: str
    path: Path


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level YAML value must be a mapping")
    return value


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def _iter_grouped(root: Path, dirname: str, key: str) -> Iterable[tuple[Path, dict]]:
    base = root / dirname
    if not base.exists():
        return
    for path in sorted(base.rglob("*.yaml")):
        doc = _load_yaml(path)
        if doc.get("schema_version") != 1:
            raise ValueError(
                f"{path}: unsupported or missing grouped schema_version; expected 1"
            )
        unexpected = set(doc) - {"schema_version", key}
        if unexpected:
            raise ValueError(
                f"{path}: unexpected top-level keys: {', '.join(sorted(unexpected))}"
            )
        items = doc.get(key, [])
        if not isinstance(items, list):
            raise ValueError(f"{path}: {key} must be a list")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: every {key} item must be a mapping")
            yield path, item


def _validate_record(validator: Draft202012Validator, item: dict, path: Path) -> None:
    errors = sorted(validator.iter_errors(item), key=lambda e: list(e.path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in err.path) or '<root>'}: {err.message}"
            for err in errors
        )
        raise ValueError(f"{path}: {rendered}")


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _create_schema(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        PRAGMA foreign_keys = ON;

        DROP TABLE IF EXISTS knowledge_fts;
        DROP TABLE IF EXISTS git_fts;
        DROP TABLE IF EXISTS evidence;
        DROP TABLE IF EXISTS knowledge;
        DROP TABLE IF EXISTS sources;
        DROP TABLE IF EXISTS git_commit_files;
        DROP TABLE IF EXISTS git_commits;

        CREATE TABLE sources (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            repository TEXT,
            sha TEXT,
            path TEXT,
            url TEXT,
            local_source_id TEXT,
            redistribution TEXT NOT NULL,
            trust TEXT NOT NULL,
            notes TEXT,
            source_file TEXT NOT NULL
        );

        CREATE TABLE knowledge (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            scope TEXT NOT NULL,
            state TEXT NOT NULL,
            validation_level TEXT NOT NULL,
            statement TEXT NOT NULL,
            applicability_json TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            related_json TEXT NOT NULL,
            supersedes_json TEXT NOT NULL,
            last_reviewed TEXT,
            source_file TEXT NOT NULL
        );

        CREATE TABLE evidence (
            record_id TEXT NOT NULL REFERENCES knowledge(id) ON DELETE CASCADE,
            source_id TEXT NOT NULL REFERENCES sources(id),
            role TEXT NOT NULL,
            note TEXT,
            PRIMARY KEY (record_id, source_id, role)
        );

        CREATE VIRTUAL TABLE knowledge_fts USING fts5(
            id UNINDEXED,
            title,
            statement,
            tags,
            tokenize='unicode61'
        );

        CREATE TABLE git_commits (
            repository TEXT NOT NULL,
            sha TEXT NOT NULL,
            author_date TEXT,
            commit_date TEXT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            PRIMARY KEY (repository, sha)
        );

        CREATE TABLE git_commit_files (
            repository TEXT NOT NULL,
            sha TEXT NOT NULL,
            path TEXT NOT NULL,
            PRIMARY KEY (repository, sha, path),
            FOREIGN KEY (repository, sha) REFERENCES git_commits(repository, sha)
                ON DELETE CASCADE
        );

        CREATE VIRTUAL TABLE git_fts USING fts5(
            repository UNINDEXED,
            sha UNINDEXED,
            subject,
            body,
            files,
            tokenize='unicode61'
        );

        CREATE INDEX evidence_by_source ON evidence(source_id);
        CREATE INDEX git_file_path ON git_commit_files(path);
        """
    )


def _insert_canonical(root: Path, db: sqlite3.Connection) -> tuple[int, int]:
    source_schema = _load_json(root / "schema" / "source-record.schema.json")
    record_schema = _load_json(root / "schema" / "knowledge-record.schema.json")
    source_validator = Draft202012Validator(source_schema)
    record_validator = Draft202012Validator(record_schema)

    source_ids: set[str] = set()
    source_count = 0
    for path, item in _iter_grouped(root, "sources", "sources"):
        _validate_record(source_validator, item, path)
        source_id = item["id"]
        if source_id in source_ids:
            raise ValueError(f"duplicate source id: {source_id}")
        source_ids.add(source_id)
        locator = item.get("locator", {})
        db.execute(
            """INSERT INTO sources
               (id, kind, title, repository, sha, path, url, local_source_id,
                redistribution, trust, notes, source_file)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                item["kind"],
                item["title"],
                locator.get("repository"),
                locator.get("sha"),
                locator.get("path"),
                locator.get("url"),
                locator.get("local_source_id"),
                item["redistribution"],
                item["trust"],
                item.get("notes"),
                str(path.relative_to(root)),
            ),
        )
        source_count += 1

    record_ids: set[str] = set()
    pending_evidence: list[tuple[str, dict, Path]] = []
    record_count = 0
    for path, item in _iter_grouped(root, "knowledge", "records"):
        _validate_record(record_validator, item, path)
        record_id = item["id"]
        if record_id in record_ids:
            raise ValueError(f"duplicate knowledge id: {record_id}")
        record_ids.add(record_id)
        tags = item.get("tags", [])
        db.execute(
            """INSERT INTO knowledge
               (id, title, scope, state, validation_level, statement,
                applicability_json, tags_json, related_json, supersedes_json,
                last_reviewed, source_file)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record_id,
                item["title"],
                item["scope"],
                item["state"],
                item["validation_level"],
                item["statement"],
                _json(item.get("applicability", {})),
                _json(tags),
                _json(item.get("related", [])),
                _json(item.get("supersedes", [])),
                item.get("last_reviewed"),
                str(path.relative_to(root)),
            ),
        )
        db.execute(
            "INSERT INTO knowledge_fts (id, title, statement, tags) VALUES (?, ?, ?, ?)",
            (record_id, item["title"], item["statement"], " ".join(tags)),
        )
        for evidence in item["evidence"]:
            pending_evidence.append((record_id, evidence, path))
        record_count += 1

    for record_id, evidence, path in pending_evidence:
        if evidence["source_id"] not in source_ids:
            raise ValueError(
                f"{path}: record {record_id} references unknown source "
                f"{evidence['source_id']}"
            )
        db.execute(
            "INSERT INTO evidence (record_id, source_id, role, note) VALUES (?, ?, ?, ?)",
            (record_id, evidence["source_id"], evidence["role"], evidence.get("note")),
        )

    # Related/supersedes identifiers are checked only after all records exist.
    rows = db.execute("SELECT id, related_json, supersedes_json FROM knowledge").fetchall()
    for record_id, related_json, supersedes_json in rows:
        for ref in json.loads(related_json) + json.loads(supersedes_json):
            if ref not in record_ids:
                raise ValueError(f"record {record_id} references unknown record {ref}")

    return source_count, record_count


def _git(repo: GitRepo, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo.path), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.decode("utf-8", errors="replace")


def _read_git_commits(repo: GitRepo) -> list[tuple[str, str, str, str, str]]:
    # ASCII record/unit separators avoid ambiguity with ordinary multiline messages.
    raw = _git(
        repo,
        "log",
        "--all",
        "--date=iso-strict",
        "--pretty=format:%H%x1f%aI%x1f%cI%x1f%s%x1f%B%x1e",
    )
    commits: list[tuple[str, str, str, str, str]] = []
    for record in raw.split("\x1e"):
        record = record.strip("\r\n")
        if not record:
            continue
        fields = record.split("\x1f", 4)
        if len(fields) != 5:
            raise ValueError(f"could not parse git record in {repo.name}: {record[:120]!r}")
        sha, author_date, commit_date, subject, body = fields
        commits.append((sha, author_date, commit_date, subject, body))
    return commits


def _read_git_files(repo: GitRepo) -> dict[str, list[str]]:
    raw = _git(repo, "log", "--all", "--name-only", "--pretty=format:%x1e%H")
    result: dict[str, list[str]] = {}
    for record in raw.split("\x1e"):
        lines = [line.strip() for line in record.splitlines() if line.strip()]
        if not lines:
            continue
        sha = lines[0]
        # Merge duplicate paths while preserving order.
        result[sha] = list(dict.fromkeys(lines[1:]))
    return result


def _insert_git_history(db: sqlite3.Connection, repos: list[GitRepo]) -> int:
    count = 0
    for repo in repos:
        if not (repo.path / ".git").exists():
            raise ValueError(f"{repo.name}: not a Git checkout: {repo.path}")
        files_by_sha = _read_git_files(repo)
        for sha, author_date, commit_date, subject, body in _read_git_commits(repo):
            db.execute(
                """INSERT OR REPLACE INTO git_commits
                   (repository, sha, author_date, commit_date, subject, body)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (repo.name, sha, author_date, commit_date, subject, body),
            )
            paths = files_by_sha.get(sha, [])
            for path in paths:
                db.execute(
                    "INSERT OR IGNORE INTO git_commit_files (repository, sha, path) VALUES (?, ?, ?)",
                    (repo.name, sha, path),
                )
            db.execute(
                "INSERT INTO git_fts (repository, sha, subject, body, files) VALUES (?, ?, ?, ?, ?)",
                (repo.name, sha, subject, body, "\n".join(paths)),
            )
            count += 1
    return count


def _parse_repo(value: str) -> GitRepo:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--git-repo must be NAME=/path/to/checkout")
    name, raw_path = value.split("=", 1)
    if not name or not raw_path:
        raise argparse.ArgumentTypeError("--git-repo must be NAME=/path/to/checkout")
    return GitRepo(name=name, path=Path(raw_path).expanduser().resolve())


def build(root: Path, output: Path, repos: list[GitRepo]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    db = sqlite3.connect(output)
    try:
        _create_schema(db)
        source_count, record_count = _insert_canonical(root, db)
        commit_count = _insert_git_history(db, repos)
        db.commit()
        print(
            f"built {output}: {record_count} knowledge records, "
            f"{source_count} sources, {commit_count} indexed git commits"
        )
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="classicmac-kb repository root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/classicmac.sqlite"),
        help="derived SQLite output path",
    )
    parser.add_argument(
        "--git-repo",
        action="append",
        type=_parse_repo,
        default=[],
        metavar="NAME=/PATH",
        help="index the full history of a local Git checkout; repeatable",
    )
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    output = args.output.expanduser()
    if not output.is_absolute():
        output = root / output
    build(root, output.resolve(), args.git_repo)


if __name__ == "__main__":
    main()
