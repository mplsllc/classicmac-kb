"""Build reference-index roots from registered private source metadata."""

from __future__ import annotations

from pathlib import Path

import yaml

from .reference_index import ReferenceRoot, index_references


_REFERENCE_KINDS = {
    "primary_documentation": "primary_vendor_documentation",
    "historical_book": "historical_book",
    "vendor_header": "vendor_header_or_sdk",
    "vendor_release_note": "primary_vendor_documentation",
    "vendor_sample_code": "vendor_sample_code",
}


def _load_registered_sources(kb_root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for path in sorted((kb_root / "sources").rglob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        if not isinstance(doc, dict) or doc.get("schema_version") != 1:
            continue
        for source in doc.get("sources", []):
            if isinstance(source, dict):
                result.append(source)
    return result


def _part_path(part: object) -> str | None:
    if isinstance(part, str):
        return part
    if isinstance(part, dict) and isinstance(part.get("path"), str):
        return part["path"]
    return None


def registered_reference_roots(
    kb_root: Path,
    *,
    repository_name: str,
    repository_root: Path,
) -> list[ReferenceRoot]:
    """Resolve registered source parts against a private repository checkout.

    Only metadata is read from the public KB. The referenced private files remain
    outside the public repository and are read only by the caller's local build.
    """

    roots: list[ReferenceRoot] = []
    for source in _load_registered_sources(kb_root):
        kind = source.get("kind")
        if kind not in _REFERENCE_KINDS:
            continue
        locator = source.get("locator")
        if not isinstance(locator, dict) or locator.get("repository") != repository_name:
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str):
            continue
        parts = source.get("parts", [])
        if not isinstance(parts, list):
            continue
        for index, part in enumerate(parts, start=1):
            relative = _part_path(part)
            if relative is None:
                continue
            roots.append(
                ReferenceRoot(
                    name=f"{source_id}:part-{index}",
                    path=(repository_root / relative).resolve(),
                    source_layer=_REFERENCE_KINDS[kind],
                    source_id=source_id,
                    vendor=source.get("vendor") if isinstance(source.get("vendor"), str) else None,
                    revision=source.get("revision") if isinstance(source.get("revision"), str) else None,
                    retrieval=source.get("retrieval") if isinstance(source.get("retrieval"), str) else None,
                    applicability=(
                        source.get("applicability")
                        if isinstance(source.get("applicability"), dict)
                        else {}
                    ),
                    restrictions=(
                        source.get("restrictions")
                        if isinstance(source.get("restrictions"), dict)
                        else {}
                    ),
                )
            )
    return roots


def index_registered_references(
    database: Path,
    kb_root: Path,
    *,
    repository_name: str,
    repository_root: Path,
) -> int:
    roots = registered_reference_roots(
        kb_root,
        repository_name=repository_name,
        repository_root=repository_root,
    )
    return index_references(database, roots)
