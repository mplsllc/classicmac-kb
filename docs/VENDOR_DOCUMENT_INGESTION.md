# Vendor Document Ingestion

## Goal

Index private historical vendor documentation for follow-up research without redistributing full manuals or allowing unverified cross-version guidance into canonical target-programming context.

## Preferred representations

For a manual available in several forms:

1. HTML section/page tree — preferred semantic structure;
2. TXT — broad full-text fallback;
3. original PDF/media — archival/page verification.

The ingester should preserve manual identity, chapter/section titles, API symbol headings, anchor/path, revision/version, and physical source path.

## Chunking

Prefer semantic units over arbitrary token windows:

- API routine entry;
- data-structure entry;
- chapter section;
- subsection;
- table/option description with surrounding heading context.

Large units may be subdivided while retaining the complete heading path.

## Multipart sources

Ordered parts belong to one source identity. `SDKAPIRM.txt` and `SDKAPIRM2.txt`, for example, are indexed as one CodeWarrior IDE 5.1 SDK API Reference.

## Search result contract

Each result must include:

- logical source ID/title;
- vendor/author;
- source class;
- manual/revision version;
- heading path;
- physical file/path/part;
- applicability status;
- `canonical_knowledge: false`;
- redistribution/display policy.

## Applicability

The indexer does not infer that later documentation applies to an earlier product. A CodeWarrior IDE 5.1 SDK API routine is `documented_for_5_1`; CW8 applicability remains `unknown` until verified against exact-version headers/API discovery or controlled behavior.

## Code examples

Extracted example code is searchable as reference evidence but excluded from automatic implementation context unless compatibility policy explicitly permits it.

## Promotion

Search results can support a candidate canonical record, but promotion requires an explicit reviewed KB change with scoped applicability and provenance.