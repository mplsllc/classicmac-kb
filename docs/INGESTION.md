# Knowledge and History Ingestion

ClassicMac's database has three deliberately different layers:

1. **canonical knowledge** — reviewed records in `knowledge/` with explicit applicability and evidence;
2. **raw project history** — every commit from configured Git repositories, indexed as evidence candidates;
3. **raw repository documents** — explicitly opted-in current Markdown/text documentation, indexed for navigation and prior-work discovery.

Raw commits and raw documents are never automatically compatibility facts.

## Build the database

From a checkout of this repository:

```sh
uv sync
uv run classicmac-kb-build \
  --git-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --git-repo mplsllc/workflow=/srv/classicmac/sources/workflow \
  --document-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --document-repo mplsllc/workflow=/srv/classicmac/sources/workflow
```

The default derived output is:

```text
build/classicmac.sqlite
```

The file is disposable. Delete it and run the builder again to recreate it from canonical records, Git histories and explicitly selected documentation repositories.

Additional projects can be included without changing the database schema:

```sh
uv run classicmac-kb-build \
  --git-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --git-repo myorg/my-codewarrior-project=/srv/classicmac/sources/my-project \
  --document-repo myorg/my-codewarrior-project=/srv/classicmac/sources/my-project
```

The repository name supplied before `=` is the stable namespace stored with each indexed commit/document.

`--git-repo` and `--document-repo` are separate intentionally. A repository can contribute commit evidence without exposing its current documentation to the document search surface. Production deployment must opt repositories into the appropriate tenant/public database explicitly.

## What the builder validates

Before emitting the SQLite database the builder checks:

- source records against `schema/source-record.schema.json`;
- canonical knowledge against `schema/knowledge-record.schema.json`;
- duplicate source IDs;
- duplicate knowledge IDs;
- evidence references to nonexistent sources;
- `related` / `supersedes` references to nonexistent knowledge records.

A validation failure aborts the build. The service must never quietly serve a partially valid corpus.

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

`git_fts` contains commit subject/body plus changed paths. It exists so agents can efficiently ask questions such as:

- Have we encountered this CodeWarrior diagnostic before?
- When did this subsystem last change?
- Was there an earlier fix/revert involving this symbol or file?
- What experiments previously tried to solve this class of problem?

`document_fts` contains the current tracked `.md`, `.txt`, `.rst`, and `.adoc` files from repositories explicitly passed with `--document-repo`. Files larger than 1 MB and binary/NUL-containing files are skipped. It is useful for questions such as:

- Which workflow document explains project mutation safety?
- Where is this CodeWarrior command documented in our current catalog?
- Which MacSurf design document describes this subsystem?

ClassicMacMCP labels results from both derived layers as noncanonical evidence. `classicmac_search_knowledge` remains the compatibility-filtered trusted surface for target-programming guidance.

## Promotion from history/documents into knowledge

A useful commit or documentation passage is not copied wholesale into the trusted corpus. Instead:

1. identify the narrow statement actually supported by the evidence;
2. choose the narrowest correct scope (experiment, project, machine, toolchain, platform, etc.);
3. record applicability explicitly;
4. cite the source through a source record;
5. distinguish observation, hypothesis, verification, incompatibility and engineering decision;
6. preserve contradictory or superseding evidence;
7. broaden scope only after additional evidence supports the generalization.

Example:

A MacSurf commit showing that a particular CW8/Tiger `Add Files` AppleEvent returned `noErr` without changing the project supports a machine/toolchain observation. It does **not** prove that Add Files is broken on every CodeWarrior version.

The broader workflow lesson — automation success codes require independently verified postconditions — may be promoted separately because the evidence demonstrates that failure mode and the rule does not assert universal CodeWarrior behavior.

## Updating project histories/documents

The builder reads local Git repositories. Commit history is read with `git log --all`; documentation is read from tracked files at the checkout's current `HEAD`. Before a production rebuild, update mirrors/checkouts using the deployment process in `classicmac-infra` and then rerun the builder.

The database build itself does not contact GitHub, run an LLM, rewrite canonical knowledge, or mutate source repositories.

## LLM-assisted candidate extraction

An LLM may help identify candidate facts in new commits/documents, but generated candidates must enter a review queue rather than being written directly as verified records. The promotion process must preserve the source and retain uncertainty.

This prevents a plausible summary from becoming institutional truth merely because it was generated automatically.
