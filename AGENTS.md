# Agent Instructions

Do not commit `_scratch/`, `tmp/`, `.fp/`, secrets, dependencies, build outputs, or local caches.

## Where things live

- `tmp/` — logs, build output, agent working files. Gitignored. Delete freely.
- `_scratch/` — brainstorms, drafts, grill transcripts. Gitignored. Thinking, not conclusions.
- `design/specs/` — what we're building. Point-in-time.
- `design/adr/` — why we chose it. Immutable.
- `ARCHITECTURE.md` — the map. Must be true right now.
- `docs/` — the toolchain's, not ours. Never design docs. (pkgdown *output* in R; *source* in mkdocs/sphinx/docusaurus.)

Triage, in order:

1. Losing it costs nothing → `_scratch/`
2. For people who *use* this → README / vignettes / `docs/`
3. Else → `design/`

## Specs

- Draft in `_scratch/`. Move to `design/specs/` when it stops being "what if".
- Frontmatter `status: draft|accepted|shipped|abandoned`. Prose below.
- On ship: distill into `ARCHITECTURE.md` + an ADR, then freeze. Never update a shipped spec.
- Spec and code disagree → code and ADR win.

## ADRs

- One decision per file: `design/adr/NNNN-slug.md`, from `0000-template.md`.
- Frontmatter `status: proposed|accepted|superseded|deprecated`; `superseded-by:` required when superseded.
- Never edit an accepted ADR. Write a new one; mark the old superseded.
- Link from `ARCHITECTURE.md` where the structure it governs is described.

## ARCHITECTURE.md

- Coarse: directories, responsibilities, seams, invariants. No line numbers, no signatures.
- Name every top-level source dir — `check-design` fails on a missing one.
- Update on structure change, not code change.

## Checks

- `python3 scripts/check-design.py` — pre-push. ADR immutability, ARCHITECTURE coverage, frontmatter.
- `sh scripts/clean-tmp.sh` — empties `tmp/`.
- Warns: `_scratch/` untouched 3+ days. Graduate or delete.

## Git hygiene

This project uses the [pre-commit](https://pre-commit.com) framework. Its config (`.pre-commit-config.yaml`) is cloned with the repo; each clone enables the hooks once:

```bash
pre-commit install && pre-commit install --hook-type pre-push
```

`pre-commit` is a Python tool. For non-Python templates, install it with `uv tool install pre-commit` or `pipx install pre-commit`.

### Per-commit checks

On every commit, lightweight hooks run: end-of-file fixer, trailing-whitespace trimming, merge-conflict detection, YAML/TOML validation, mixed-line-ending and case-conflict guards, and `check-added-large-files` — a portable 5 MB size guard that blocks accidentally committing heavy blobs (a big blob bloats `.git` history even after deletion).

### Pre-push verify gate

On `git push`, the `verify` hook runs the project's verify command — the same chain CI runs. GitLab Free does offer protected branches, so wire those up too, but they only gate what reaches the default branch; this local hook blocks a push whose tree would turn CI red before it ever leaves your machine.

**On a feature branch this hook is the only gate that runs anywhere, and that is deliberate.** `.gitlab-ci.yml` carries a top-level `workflow:` block admitting only a tag, a push to `main`, or a hand-started (`web`) pipeline — so a branch push creates no pipeline and a merge request creates none either, one pipeline per merge instead of three (SEOR-bmgkzhvy). Do not read a branch's clean pipeline list as a passing result: there is no result. To get a server-side answer on a branch before merging it, start one by hand at **Build > Pipelines > Run pipeline** and pick the ref; the full gate runs there. `pages` is the single exception, pinned to `main`, because it publishes rather than reports.

### Slice flow (standing authorization)

Work a task as a self-contained slice and carry the whole flow through without pausing to confirm each step: branch → commit → push → open MR → merge → delete branch (local+remote). Do this once the slice is complete and the local verify gate passes. `.claude/settings.json` pre-allows the `git`/`glab` commands this needs, so there are no per-step permission prompts.

Branch names use `feature/`, `fix/`, `chore/` prefixes. Still stop and confirm first for force-push, history rewrites (rebase / `reset --hard` / amending pushed commits), and merges into a shared or protected branch — those stay confirm-first (and `.claude/settings.json` keeps them on the `ask` list).

### Issue tracking is decoupled from git

If this project uses fp for issue tracking, keep it **decoupled from git** — issue-status changes must have no git side effects. Do not add an fp extension that turns status transitions (`in-progress`, `done`, …) into branch/merge/push operations; track issues with fp and drive git with the slice flow above. (A sibling project wired `done` to a local fast-forward merge into `main`; the merge never pushed, so `origin` silently drifted behind. Don't repeat it.)

## Language-specific conventions

@AGENTS_LANG.md
