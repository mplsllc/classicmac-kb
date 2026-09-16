# ClassicMac Knowledge Base

This repository is the canonical public knowledge corpus for ClassicMacMCP.

Its purpose is not to collect every piece of retro-computing information. It exists to give humans and AI agents a small, trustworthy, compatibility-aware body of knowledge for developing Classic Macintosh software.

## Core rule

**Unknown is better than contaminated.**

A fact is not automatically applicable because it is old, written in C, or found in a historical source tree. Records carry explicit applicability, provenance, verification state, and evidence.

Generic modern C/C++ examples, unrelated retro-platform code, and unverified internet material are not admitted as target-programming knowledge.

## Knowledge scopes

Records can apply at one or more levels:

- `global` — broadly applicable Classic Mac development knowledge;
- `platform` — a specific Mac OS family/version;
- `architecture` — e.g. PowerPC or 68K;
- `toolchain` — e.g. CodeWarrior Pro 8.3;
- `sdk` — a particular headers/interfaces generation;
- `machine` — a verified machine/OS/toolchain environment;
- `project` — knowledge that has not been generalized beyond one project;
- `experiment` — a single observation or controlled test.

Project and experiment observations are never silently promoted into global facts.

## Epistemic states

Canonical records use states such as:

- `documented` — supported by an identified primary source;
- `observed` — directly measured but not necessarily generalized;
- `verified` — reproduced sufficiently for the stated applicability;
- `decision` — an explicit engineering policy, not a claim about nature;
- `hypothesis` — plausible and under test;
- `disproved` — tested and rejected for its stated scope;
- `superseded` — replaced by better knowledge;
- `unknown` — intentionally unresolved;
- `incompatible` — established not to work for the stated target.

## Validation levels

Evidence may establish different levels without conflating them:

- `static_verified`
- `retro68_verified`
- `codewarrior_verified`
- `hardware_verified`

A Retro68 success does not establish CodeWarrior compatibility. A CodeWarrior compile does not establish runtime behavior.

## Sources

Preferred sources are:

1. verified project/hardware evidence with preserved provenance;
2. installed toolchain dictionaries, headers, and behavior;
3. Apple/Metrowerks primary documentation where redistribution is permitted;
4. carefully reviewed historical source/examples whose applicability is explicit.

Copyrighted manuals, SDKs, and headers with unclear redistribution rights are referenced by metadata and local-source identifiers rather than mirrored indiscriminately.

## Repository layout

- `schema/` — versioned machine-readable record schemas.
- `knowledge/` — canonical human-readable records with structured front matter.
- `evidence/` — public evidence manifests; large/private/raw evidence may remain elsewhere.
- `sources/` — source catalog and licensing/redistribution notes.
- `contrib/` — contribution and verification procedures.

The searchable database used by ClassicMacMCP is generated from this repository. The database is an index, not the source of truth.
