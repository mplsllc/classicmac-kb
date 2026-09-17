# Knowledge Promotion Policy

## Purpose

ClassicMacKB distinguishes searchable evidence from reviewed canonical knowledge. Promotion is the process by which a claim becomes safe enough for automatic target-programming retrieval.

## Eligible source classes

Candidate claims may originate from:

- project/hardware evidence;
- workflow documentation;
- CodeWarrior diagnostics or behavior;
- vendor documentation or SDK headers;
- historical books;
- differential compiler tests;
- source-code archaeology.

Origin alone does not determine truth.

## Promotion requirements

A canonical record must state:

- the claim;
- exact applicability/scope;
- epistemic state;
- validation level;
- supporting evidence;
- conflicting evidence if known;
- source revisions/versions;
- rationale for generalizing beyond a single observation, if applicable.

## Scope rule

Prefer a narrow true claim to a broad plausible claim.

For example, evidence from one tested CodeWarrior 8.3 installation should normally produce `CodeWarrior 8.3 in the tested environment` rather than `CodeWarrior 8.x` unless broader evidence exists.

## Conflicts

Conflicting evidence is preserved. Do not erase an earlier or later contradiction merely to keep one clean rule.

A record may remain `unknown`, `context_dependent`, or scoped to a particular SDK/toolchain combination.

## Vendor documentation

Vendor documentation establishes documented behavior for the documented version. It becomes stronger for another target version only when exact-version headers, release notes, API discovery, or controlled tests support that applicability.

## Negative knowledge

Failures and false assumptions are first-class promotion candidates when reproducible. Examples include success return codes without state changes, false-green host checks, stale artifacts, header collisions, missing runtime APIs, and timeout ambiguity.

These records often provide more practical value to agents than generic success examples.

## Review

Promotion is an explicit repository change. Automated ingestion may propose records but must not silently change canonical knowledge.

## Validation levels

Use explicit levels such as:

- `documented`
- `static_verified`
- `retro68_verified`
- `codewarrior_verified`
- `hardware_verified`

These are not synonyms and should not be collapsed into a single confidence score.