# Historical Reference Corpus

The ClassicMac knowledge system may use privately held vendor documentation and historical books as a **follow-up reference layer**. These materials improve recall and historical accuracy without becoming first-layer canonical truth.

## Retrieval priority

The intended order is:

1. canonical reviewed ClassicMac knowledge;
2. project/CodeWarrior/hardware evidence;
3. applicable primary vendor documentation;
4. historical books and secondary references;
5. general external/model knowledge.

The reference corpus therefore answers questions such as:

- what did Metrowerks document for this API?
- what runtime/library behavior did MSL intend?
- what project/access-path semantics were documented?
- what period-correct implementation patterns should we investigate?

It does not answer, by itself:

- did CW8.3 accept this construct?
- does this exact CarbonLib/import library export the symbol?
- did this AppleEvent actually mutate the project on the tested machine?
- does this behavior hold on the target hardware?

## Private source repository

Current private corpus location:

`mplsllc/macsurf-private/books/`

The public KB stores source metadata in `sources/private-vendor-docs.yaml`; it does not redistribute the full documents.

## Text and HTML representations

Where both are available:

- **HTML** is the preferred structural representation because it preserves manual/chapter/section/API boundaries, anchors, indexes, and cross-references.
- **TXT** is useful for broad full-text search, normalization, and fallback parsing.
- **PDF/original media**, when retained privately, remains the archival representation for pagination, figures, tables, and visual verification.

Do not create duplicate logical sources merely because multiple representations exist. Representations should be grouped under one manual identity where practical.

## Current high-value Metrowerks corpus

High-priority documents include:

- C Compilers Reference 3.0;
- MSL C Reference;
- Targeting Mac OS;
- IDE 5.0 User Guide;
- Extending CodeWarrior IDE;
- IDE 5.1 SDK API Reference;
- Assembler Reference;
- Porting Guide;
- PowerPlant Carbon Porting Guide;
- Profiler User Guide;
- ZoneRanger User Guide.

PowerPlant manuals are useful for period application conventions but should normally be excluded from non-PowerPlant project coding context unless explicitly relevant.

Windows, Java VM, C++, COM, or other cross-target documentation should be tagged for explicit-only retrieval when the current project is Classic Mac C/C89.

## Split manuals

The IDE 5.1 SDK API Reference is currently split into:

- `books/text/SDKAPIRM.txt`
- `books/text/SDKAPIRM2.txt`

Treat these as two physical parts of a single logical source. Part 1 contains the manual front matter, functional indexes, and common Plugin API reference; Part 2 continues the manual around SDK-372 and includes the VCS Plugin API material.

## Ingestion unit

Do not chunk vendor HTML blindly by token count when structural boundaries exist.

Preferred logical unit:

```text
manual
  -> chapter
    -> section
      -> symbol/API/concept
```

Each indexed unit should preserve:

- logical manual ID;
- title/vendor/revision;
- physical representation/path;
- chapter/section/API symbol where known;
- source class;
- target/product applicability;
- redistribution policy;
- canonical=false.

## Search result contract

Historical/vendor search results must identify themselves explicitly, for example:

```yaml
canonical: false
source_layer: vendor_documentation
source_id: metrowerks.ide-5.1-sdk-api-reference.part1
manual: CodeWarrior IDE 5.1 SDK API Reference
section: CWGetAccessPathInfo
applicability:
  documented_for: ide-5.1-sdk
  cw8_3: unknown
```

This prevents an LLM from converting retrieval relevance into compatibility authority.

## Promotion rule

A vendor/book-derived statement becomes canonical only after review establishes an appropriately scoped claim. Exact toolchain/runtime claims should normally require installed-header/toolchain evidence or controlled reproduction.

Example:

```text
IDE 5.1 manual documents CWGetProjectFileCount
              |
              v
candidate: Plugin API can enumerate active target files
              |
       inspect CW8 headers
              |
       compile/link fixture
              |
      test on installed IDE
              |
              v
CW8-scoped canonical knowledge
```

## Copyright and redistribution

The system is intended to index lawfully held private reference material for the owner's use, not republish manuals. Public outputs should consist of original summaries, source metadata, compatibility facts, and appropriately limited citations/references.

A public MCP endpoint must not provide a generic "dump manual section" capability that effectively reconstructs copyrighted works.
