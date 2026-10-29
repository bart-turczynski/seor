# Agent workflow

Repository conventions moved out of the root `AGENTS.md`, which now points here.
Rules for specs and ADRs live in [`README.md`](README.md).

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

## ARCHITECTURE.md

- Coarse: directories, responsibilities, seams, invariants. No line numbers, no signatures.
- Name every top-level source dir — `check-design` fails on a missing one.
- Update on structure change, not code change.

## Checks

- `python3 scripts/check-design.py` — pre-push. ADR immutability, ARCHITECTURE coverage, frontmatter.
- `sh scripts/docs-drift.sh` — pre-push (`docs-drift` hook). Regenerates `man/`, `NAMESPACE` and `DESCRIPTION` with the pinned roxygen2 in a throwaway `git archive` export of the commit being pushed, and fails on any difference. It checks commits, not the working tree: commit a roxygen edit before it counts. Fix: `devtools::document()`, then commit.
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

**This hook is the merge gate, and on a branch it is the only gate that runs anywhere.** That is deliberate. Under the verification tiers ([ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md)) the `workflow:` rules deny by default: a push to `main`, a branch push, a merge request and an API call create no pipeline. CI runs only the weekly `deep-check` schedule (T2, plus pagerankr's `rurl-devel` schedule), a `v*` tag push (full T3, with the `pages` deploy), and hand-started (`web`) runs with `RELEASE=1` on `main` or a `v*` tag, or `PAGES=1` on a `v*` tag; the ADR's event table is the full list. Do not read a clean pipeline list as a passing result: there is no result. Until seor migrates to fleet-ci, its current `.gitlab-ci.yml` keeps its older rules (SEOR-bmgkzhvy). The `pages` job publishes rather than reports, and only from a `v*` tag. It strips the agent instruction files first — pkgdown renders every top-level `.md`, so `AGENTS.md`, `CLAUDE.md` and the `FP_*.md` files were being published next to the function reference as `AGENTS.html`, `CLAUDE.html` and friends: internal working notes served as if they were user documentation (SEOR-pibdjanz). The job uses a **keep-list**, not a deny-list: immediately before `build_site`, every top-level `.md` not named in its `KEEP` variable is moved out of the tree, so a new agent file of any name stays private without anyone remembering to list it (SEOR-wqxhftpv). The flip side: a new top-level `.md` meant for the public site is **not** published until you add it to `KEEP` in the same commit. A `KEEP` entry whose file is missing fails the job.

### Slice flow

Branching, the merge request flow, merging, cleanup and the confirm-first list follow the house `agent-workflow` skill. fp status changes have no git side effects: the `fp` skill's `references/decoupling.md`. What is specific to this repository is above: the hooks, the `verify` gate and the `workflow:` rules.
