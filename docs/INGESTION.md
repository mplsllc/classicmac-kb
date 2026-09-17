# Knowledge and History Ingestion

ClassicMac's database has four deliberately different layers:

1. **canonical knowledge** — reviewed records in `knowledge/` with explicit applicability and evidence;
2. **raw project history** — every commit from configured Git repositories, indexed as evidence candidates;
3. **raw repository documents** — explicitly opted-in current Markdown/text documentation, indexed for navigation and prior-work discovery;
4. **historical/vendor references** — optional private manuals/books/reference trees, indexed in a separate follow-up-only search layer.

Raw commits, raw documents, and historical references are never automatically compatibility facts.

## Build the database

From a checkout of this repository:

```sh
uv sync
uv run classicmac-kb-build \
  --git-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --git-repo mplsllc/workflow=/srv/classicmac/sources/workflow \
  --document-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --document-repo mplsllc/workflow=/srv/classicmac/sources/workflow \
  --reference-root metrowerks-text=/srv/classicmac/private/macsurf-private/books/text \
  --reference-root metrowerks-html=/srv/classicmac/private/macsurf-private/books/HTML
```

The `--reference-root` arguments are optional. Public builds should omit private corpora unless the deployment has an explicit legal/operational reason to include an allowed reference set.

The default derived output is:

```text
build/classicmac.sqlite
```

The file is disposable. Delete it and run the builder again to recreate it from canonical records and the configured evidence/reference inputs.

Additional projects can be included without changing the database schema:

```sh
uv run classicmac-kb-build \
  --git-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --git-repo myorg/my-codewarrior-project=/srv/classicmac/sources/my-project \
  --document-repo myorg/my-codewarrior-project=/srv/classicmac/sources/my-project
```

The name supplied before `=` is the stable namespace stored with each indexed item.

`--git-repo`, `--document-repo`, and `--reference-root` are separate intentionally. A source can contribute one evidence class without being exposed through every retrieval surface.

## What the builder validates

Before emitting the SQLite database the canonical builder checks:

- source records against `schema/source-record.schema.json`;
- canonical knowledge against `schema/knowledge-record.schema.json`;
- duplicate source IDs;
- duplicate knowledge IDs;
- evidence references to nonexistent sources;
- `related` / `supersedes` references to nonexistent knowledge records.

A validation failure aborts the build. The service must never quietly serve a partially valid canonical corpus.

Reference/document/history indexing is derived. A configured input path that cannot be read is an error rather than a silent empty corpus.

## SQLite contents

Canonical tables:

- `sources`
- `knowledge`
- `evidence`
- `knowledge_fts`

Raw-history tables:

- `git_commits`
- `git_commit_files`
- `git_fts`

Raw-document tables:

- `documents`
- `document_fts`

Optional historical/vendor reference tables:

- `reference_documents`
- `reference_fts`

`git_fts` contains commit subject/body plus changed paths. It exists so agents can efficiently ask questions such as:

- Have we encountered this CodeWarrior diagnostic before?
- When did this subsystem last change?
- Was there an earlier fix/revert involving this symbol or file?
- What experiments previously tried to solve this class of problem?

`document_fts` contains the current tracked `.md`, `.txt`, `.rst`, and `.adoc` files from repositories explicitly passed with `--document-repo`. Files larger than 1 MB and binary/NUL-containing files are skipped.

`reference_fts` indexes `.txt`, `.md`, `.rst`, `.adoc`, `.html`, and `.htm` files below explicitly configured private reference roots. Reference files larger than 2 MB or containing NUL bytes are skipped. HTML indexing removes script/style content and preserves page-level files as independent retrieval units, which works well with section-oriented vendor HTML exports.

ClassicMacMCP labels results from all three noncanonical retrieval layers explicitly. `classicmac_search_knowledge` remains the compatibility-filtered trusted surface for target-programming guidance. `classicmac_search_references` is follow-up-only.

## Historical/vendor reference policy

Current private source metadata is recorded in `sources/private-vendor-docs.yaml`; full copyrighted content remains in private storage.

The Metrowerks IDE 5.1 SDK API Reference currently exists as two physical text files (`SDKAPIRM.txt` and `SDKAPIRM2.txt`) but represents one logical manual. Retrieval/build tooling may index both files, while source metadata preserves that relationship.

Historical/vendor references should answer questions such as:

- What did Metrowerks document for this API?
- What did the MSL reference say about a library facility?
- Which Plugin API calls appear to expose project/access-path/IDE information?
- What period-correct implementation approach should be tested next?

They must not, without additional evidence, answer:

- Is this symbol present in CW8.3?
- Does this exact CodeWarrior build implement the same API revision?
- Does the API work in the current project/request context?
- Does the behavior reproduce on target hardware?

## Promotion from evidence/reference material into knowledge

A useful commit, document, or manual passage is not copied wholesale into the trusted corpus. Instead:

1. identify the narrow statement actually supported by the source;
2. choose the narrowest correct scope;
3. record applicability explicitly;
4. cite the source through a source record;
5. distinguish documented behavior, observation, hypothesis, verification, incompatibility and engineering decision;
6. preserve contradictory or superseding evidence;
7. verify exact-toolchain/runtime claims where appropriate;
8. broaden scope only after additional evidence supports the generalization.

Example:

A MacSurf commit showing that a particular CW8/Tiger `Add Files` AppleEvent returned `noErr` without changing the project supports a machine/toolchain observation. It does **not** prove that Add Files is broken on every CodeWarrior version.

Likewise, the IDE 5.1 SDK API Reference documenting `CWAddProjectEntry` proves documented availability in that SDK family. It does not prove ABI/runtime compatibility with the installed CW Pro 8.x environment until the actual headers/toolchain/runtime are checked.

## Updating source inputs

The builder reads local repositories/directories. Commit history is read with `git log --all`; repository documentation is read from tracked files at the checkout's current `HEAD`; private references are read from the configured filesystem roots.

Before a production rebuild, update mirrors/checkouts using the deployment process in `classicmac-infra` and then rerun the builder.

The database build itself does not contact GitHub, run an LLM, rewrite canonical knowledge, or mutate source/reference repositories.

## LLM-assisted candidate extraction

An LLM may help identify candidate facts in new commits, project documents, or historical references, but generated candidates must enter a review queue rather than being written directly as verified records. The promotion process must preserve the source and retain uncertainty.

This prevents a plausible summary from becoming institutional truth merely because it was generated automatically.
