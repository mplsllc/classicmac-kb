# Knowledge and History Ingestion

ClassicMac's database has two deliberately different layers:

1. **canonical knowledge** — reviewed records in `knowledge/` with explicit applicability and evidence;
2. **raw project history** — every commit from configured Git repositories, indexed as evidence candidates.

A raw commit is never automatically a compatibility fact.

## Build the database

From a checkout of this repository:

```sh
uv sync
uv run classicmac-kb-build \
  --git-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --git-repo mplsllc/workflow=/srv/classicmac/sources/workflow
```

The default derived output is:

```text
build/classicmac.sqlite
```

The file is disposable. Delete it and run the builder again to recreate it from canonical records plus Git histories.

Additional projects can be included without changing the database schema:

```sh
uv run classicmac-kb-build \
  --git-repo mplsllc/macsurf=/srv/classicmac/sources/macsurf \
  --git-repo mplsllc/workflow=/srv/classicmac/sources/workflow \
  --git-repo myorg/my-codewarrior-project=/srv/classicmac/sources/my-project
```

The repository name supplied before `=` is the stable namespace stored with each indexed commit.

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

`git_fts` contains commit subject/body plus changed paths. It exists so agents can efficiently ask questions such as:

- Have we encountered this CodeWarrior diagnostic before?
- When did this subsystem last change?
- Was there an earlier fix/revert involving this symbol or file?
- What experiments previously tried to solve this class of problem?

Results from this layer are labelled `raw_git_history` and `canonical_knowledge: false` by ClassicMacMCP.

## Promotion from history into knowledge

A useful commit is not copied wholesale into the trusted corpus. Instead:

1. identify the narrow statement actually supported by the commit/evidence;
2. choose the narrowest correct scope (experiment, project, machine, toolchain, platform, etc.);
3. record applicability explicitly;
4. cite the Git commit through a source record;
5. distinguish observation, hypothesis, verification, incompatibility and engineering decision;
6. preserve contradictory or superseding evidence;
7. broaden scope only after additional evidence supports the generalization.

Example:

A MacSurf commit showing that a particular CW8/Tiger `Add Files` AppleEvent returned `noErr` without changing the project supports a machine/toolchain observation. It does **not** prove that Add Files is broken on every CodeWarrior version.

The broader workflow lesson — automation success codes require independently verified postconditions — may be promoted separately because the evidence demonstrates that failure mode and the rule does not assert universal CodeWarrior behavior.

## Updating project histories

The builder reads local Git repositories with `git log --all`. Before a production rebuild, update mirrors/checkouts using the deployment process in `classicmac-infra` and then rerun the builder.

The database build itself does not contact GitHub, run an LLM, rewrite canonical knowledge, or mutate source repositories.

## LLM-assisted candidate extraction

An LLM may help identify candidate facts in new commits, but generated candidates must enter a review queue rather than being written directly as verified records. The promotion process must preserve the source commit and retain uncertainty.

This prevents a plausible summary from becoming institutional truth merely because it was generated automatically.
