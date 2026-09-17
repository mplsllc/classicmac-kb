# Source Hierarchy

## Purpose

ClassicMacKB deliberately separates knowledge by evidence class. Searchability does not imply authority.

## Retrieval order

For target-programming and compatibility questions, prefer:

1. reviewed canonical ClassicMac knowledge;
2. exact project/toolchain/hardware evidence;
3. applicable primary vendor documentation;
4. historical books and contemporary secondary references;
5. general external/model knowledge.

A lower layer may suggest or explain a possibility but must not silently override a higher layer.

## Canonical knowledge

Canonical records are reviewed, scoped claims stored in Git. They include applicability metadata, provenance, epistemic state, and validation level.

Only canonical records are injected automatically as trusted programming guidance.

## Project and hardware evidence

Raw Git history, build logs, diagnostics, experiment reports, hardware captures, and workflow documents are evidence. They are searchable but are not automatically generalized into platform facts.

A project observation may be promoted only after its scope is understood.

## Primary vendor documentation

Metrowerks and Apple documentation are high-value follow-up sources. Examples include:

- CodeWarrior C Compiler Reference;
- MSL C Reference;
- Targeting Mac OS;
- CodeWarrior IDE User Guide;
- Extending CodeWarrior IDE;
- CodeWarrior IDE SDK API Reference;
- Universal Interfaces / SDK headers;
- Apple runtime, CarbonLib, Open Transport, Apple Event/OSA, and Inside Macintosh material.

Vendor documentation establishes documented/intended behavior for the documented version. It does not automatically prove behavior in a different CodeWarrior/SDK release.

## Private vendor-document corpus

User-owned manuals may remain in private repositories or server-local storage. The hosted/public KB should store metadata and derived reviewed facts, not redistribute copyrighted manuals unless rights clearly permit it.

Private indexing may expose bounded search results to an authorized user while preserving source identity and noncanonical status.

Example result metadata:

```yaml
canonical_knowledge: false
evidence_class: primary_vendor_documentation
vendor: Metrowerks
manual: CodeWarrior IDE SDK API Reference
manual_version: "5.1"
revision: "2003-08-25"
applicability:
  codewarrior_8_3: unverified
```

## Split/manual multipart sources

A manual split into multiple repository files is one logical source. For example, `SDKAPIRM.txt` and `SDKAPIRM2.txt` are two parts of the same CodeWarrior IDE 5.1 SDK API Reference and should share one source identity with ordered parts.

The indexer should preserve part order and original location.

## Historical books

Third-party period books are useful for explanation, terminology, examples, and corroboration but rank below applicable primary vendor documentation.

Book examples are not automatically valid C89/CW8 implementation examples. Code snippets are treated as secondary evidence until compatibility is established.

## Applicability filtering

Retrieval must consider at least:

- target OS/version;
- CPU/architecture;
- language standard;
- compiler/toolchain and exact version when known;
- runtime library;
- SDK/interface version;
- API family;
- project-specific policy.

If applicability is unknown, return `compatibility unknown` rather than silently substituting modern behavior.

## Promotion

Promotion flow:

```text
raw evidence / vendor docs / historical source
                |
                v
       candidate claim
                |
        reproduce/corroborate
                |
          human review
                |
                v
       canonical KB record
```

The resulting canonical record retains all supporting and conflicting provenance.