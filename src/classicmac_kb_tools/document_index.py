"""Index explicitly opted-in repository documentation as raw evidence.

This layer is intentionally separate from canonical knowledge. It makes current
project/workflow documentation discoverable without granting every sentence in
those documents toolchain-wide authority.
"""

from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path


_DOC_SUFFIXES = {".md", ".txt", ".rst", ".adoc"}
_MAX_DOCUMENT_BYTES = 1_000_000


@dataclass(frozen=True)
class DocumentRepo:
    name: str
    path: Path


def _git(repo: DocumentRepo, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo.path), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout


def _tracked_text_documents(repo: DocumentRepo) -> list[tuple[str, str]]:
    """Return `(blob_sha, path)` for documentation-like files at HEAD."""

    raw = _git(repo, "ls-files", "-s", "-z")
    result: list[tuple[str, str]] = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        try:
            meta, path_raw = entry.split(b"\t", 1)
            _mode, blob_sha, _stage = meta.decode("ascii").split(" ", 2)
            path = path_raw.decode("utf-8", errors="replace")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f"could not parse git ls-files entry in {repo.name}") from exc
        candidate = Path(path)
        if candidate.suffix.lower() in _DOC_SUFFIXES:
            result.append((blob_sha, path))
    return result


def _title(path: str, text: str) -> str:
    for line in text.splitlines()[:80]:
        stripped = line.strip()
        if stripped.startswith("#"):
            value = stripped.lstrip("#").strip()
            if value:
                return value[:300]
    return Path(path).name


def _read_document(repo: DocumentRepo, path: str) -> str | None:
    candidate = repo.path / path
    try:
        data = candidate.read_bytes()
    except OSError:
        return None
    if len(data) > _MAX_DOCUMENT_BYTES or b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def _ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        DROP TABLE IF EXISTS document_fts;
        DROP TABLE IF EXISTS documents;

        CREATE TABLE documents (
            repository TEXT NOT NULL,
            path TEXT NOT NULL,
            blob_sha TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            PRIMARY KEY (repository, path)
        );

        CREATE VIRTUAL TABLE document_fts USING fts5(
            repository UNINDEXED,
            path,
            title,
            content,
            tokenize='unicode61'
        );

        CREATE INDEX document_path ON documents(repository, path);
        """
    )


def index_documents(database: Path, repos: list[DocumentRepo]) -> int:
    """Replace the raw-document index in an existing ClassicMac SQLite DB."""

    if not database.exists():
        raise ValueError(f"database does not exist: {database}")
    db = sqlite3.connect(database)
    count = 0
    try:
        _ensure_schema(db)
        for repo in repos:
            if not (repo.path / ".git").exists():
                raise ValueError(f"{repo.name}: not a Git checkout: {repo.path}")
            for blob_sha, path in _tracked_text_documents(repo):
                text = _read_document(repo, path)
                if text is None:
                    continue
                title = _title(path, text)
                db.execute(
                    "INSERT INTO documents(repository, path, blob_sha, title, content) VALUES (?, ?, ?, ?, ?)",
                    (repo.name, path, blob_sha, title, text),
                )
                db.execute(
                    "INSERT INTO document_fts(repository, path, title, content) VALUES (?, ?, ?, ?)",
                    (repo.name, path, title, text),
                )
                count += 1
        db.commit()
    finally:
        db.close()
    return count
