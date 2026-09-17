"""Build the complete derived ClassicMac SQLite database."""

from __future__ import annotations

import argparse
from pathlib import Path

from .build_index import GitRepo, build
from .document_index import DocumentRepo, index_documents
from .reference_index import ReferenceRoot, index_references


def _parse_named_path(value: str, *, label: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{label} must be NAME=/path/to/location")
    name, raw_path = value.split("=", 1)
    if not name or not raw_path:
        raise argparse.ArgumentTypeError(f"{label} must be NAME=/path/to/location")
    return name, Path(raw_path).expanduser().resolve()


def _parse_git_repo(value: str) -> GitRepo:
    name, path = _parse_named_path(value, label="repository")
    return GitRepo(name=name, path=path)


def _parse_document_repo(value: str) -> DocumentRepo:
    name, path = _parse_named_path(value, label="repository")
    return DocumentRepo(name=name, path=path)


def _parse_reference_root(value: str) -> ReferenceRoot:
    name, path = _parse_named_path(value, label="reference root")
    return ReferenceRoot(name=name, path=path)


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
        type=_parse_git_repo,
        default=[],
        metavar="NAME=/PATH",
        help="index the full Git history of a local checkout; repeatable",
    )
    parser.add_argument(
        "--document-repo",
        action="append",
        type=_parse_document_repo,
        default=[],
        metavar="NAME=/PATH",
        help=(
            "opt in a repository's tracked Markdown/text documentation to the raw "
            "document evidence index; repeatable"
        ),
    )
    parser.add_argument(
        "--reference-root",
        action="append",
        type=_parse_reference_root,
        default=[],
        metavar="NAME=/PATH",
        help=(
            "index a private historical/vendor reference directory into the separate "
            "noncanonical follow-up reference index; repeatable"
        ),
    )
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    output = args.output.expanduser()
    if not output.is_absolute():
        output = root / output
    output = output.resolve()

    build(root, output, args.git_repo)
    document_count = index_documents(output, args.document_repo)
    reference_count = index_references(output, args.reference_root)
    print(f"indexed {document_count} current repository documents")
    print(f"indexed {reference_count} historical/vendor reference documents")


if __name__ == "__main__":
    main()
