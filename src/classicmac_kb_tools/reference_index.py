"""Index optional private historical/vendor references as noncanonical follow-up data.

The reference index is deliberately separate from canonical knowledge and from raw
project documentation. A server may build it from lawfully held private manuals
without committing or redistributing their contents.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Mapping


_TEXT_SUFFIXES = {".txt", ".md", ".rst", ".adoc"}
_HTML_SUFFIXES = {".html", ".htm"}
_SUPPORTED_SUFFIXES = _TEXT_SUFFIXES | _HTML_SUFFIXES
_MAX_REFERENCE_BYTES = 2_000_000
_WHITESPACE = re.compile(r"[ \t\r\f\v]+")


@dataclass(frozen=True)
class ReferenceRoot:
    name: str
    path: Path
    source_layer: str = "historical_reference"
    source_id: str | None = None
    vendor: str | None = None
    revision: str | None = None
    retrieval: str | None = None
    applicability: Mapping[str, object] = field(default_factory=dict)
    restrictions: Mapping[str, object] = field(default_factory=dict)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.title_parts: list[str] = []
        self.heading_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._in_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = True
        if tag in {"h1", "h2", "h3"}:
            self._in_heading = True
        if tag in {"p", "div", "li", "br", "tr", "dt", "dd", "pre"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = False
        if tag in {"h1", "h2", "h3"}:
            self._in_heading = False
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = data.strip()
        if not value:
            return
        if self._in_title:
            self.title_parts.append(value)
        if self._in_heading:
            self.heading_parts.append(value)
        self.text_parts.append(value)
        self.text_parts.append(" ")


def _normalize_text(text: str) -> str:
    lines: list[str] = []
    for raw in text.replace("\u00a0", " ").splitlines():
        line = _WHITESPACE.sub(" ", raw).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _read_reference(path: Path) -> tuple[str, str] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > _MAX_REFERENCE_BYTES or b"\0" in data:
        return None

    text = data.decode("utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix in _HTML_SUFFIXES:
        parser = _HTMLTextExtractor()
        try:
            parser.feed(text)
        except Exception:
            return None
        title = " ".join(parser.title_parts).strip()
        if not title and parser.heading_parts:
            title = " ".join(parser.heading_parts[:4]).strip()
        content = _normalize_text(html.unescape("".join(parser.text_parts)))
        return (title or path.stem, content)

    if suffix in _TEXT_SUFFIXES:
        content = _normalize_text(text)
        title = path.stem
        for line in content.splitlines()[:100]:
            if line.startswith("#"):
                candidate = line.lstrip("#").strip()
                if candidate:
                    title = candidate
                    break
        return (title, content)
    return None


def _ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        DROP TABLE IF EXISTS reference_fts;
        DROP TABLE IF EXISTS reference_documents;

        CREATE TABLE reference_documents (
            corpus TEXT NOT NULL,
            source_layer TEXT NOT NULL,
            source_id TEXT,
            vendor TEXT,
            revision TEXT,
            retrieval TEXT,
            applicability_json TEXT NOT NULL,
            restrictions_json TEXT NOT NULL,
            path TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            PRIMARY KEY (corpus, path)
        );

        CREATE VIRTUAL TABLE reference_fts USING fts5(
            corpus UNINDEXED,
            source_layer UNINDEXED,
            source_id UNINDEXED,
            vendor UNINDEXED,
            revision UNINDEXED,
            retrieval UNINDEXED,
            applicability_json UNINDEXED,
            restrictions_json UNINDEXED,
            path,
            title,
            content,
            tokenize='unicode61'
        );

        CREATE INDEX reference_path ON reference_documents(corpus, path);
        CREATE INDEX reference_source_id ON reference_documents(source_id);
        """
    )


def _input_files(root: ReferenceRoot) -> list[tuple[Path, str]]:
    path = root.path
    if path.is_file():
        if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
            raise ValueError(f"{root.name}: unsupported reference file type: {path}")
        return [(path, path.name)]
    if not path.is_dir():
        raise ValueError(f"{root.name}: reference input does not exist: {path}")

    result: list[tuple[Path, str]] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.is_file() and candidate.suffix.lower() in _SUPPORTED_SUFFIXES:
            result.append((candidate, candidate.relative_to(path).as_posix()))
    return result


def index_references(database: Path, roots: list[ReferenceRoot]) -> int:
    """Replace the optional historical/vendor reference index."""

    if not database.exists():
        raise ValueError(f"database does not exist: {database}")
    db = sqlite3.connect(database)
    count = 0
    try:
        _ensure_schema(db)
        for root in roots:
            applicability_json = json.dumps(
                dict(root.applicability), sort_keys=True, separators=(",", ":")
            )
            restrictions_json = json.dumps(
                dict(root.restrictions), sort_keys=True, separators=(",", ":")
            )
            for path, relative in _input_files(root):
                loaded = _read_reference(path)
                if loaded is None:
                    continue
                title, content = loaded
                if not content:
                    continue
                values = (
                    root.name,
                    root.source_layer,
                    root.source_id,
                    root.vendor,
                    root.revision,
                    root.retrieval,
                    applicability_json,
                    restrictions_json,
                    relative,
                    title,
                    content,
                )
                db.execute(
                    """INSERT INTO reference_documents
                       (corpus, source_layer, source_id, vendor, revision, retrieval,
                        applicability_json, restrictions_json, path, title, content)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    values,
                )
                db.execute(
                    """INSERT INTO reference_fts
                       (corpus, source_layer, source_id, vendor, revision, retrieval,
                        applicability_json, restrictions_json, path, title, content)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    values,
                )
                count += 1
        db.commit()
    finally:
        db.close()
    return count
