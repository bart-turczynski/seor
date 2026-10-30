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
- `Rscript scripts/check-docs-drift.R .` — the local gate's full tier (a cheap gate in `.fleet-ci.yml`). Regenerates `man/`, `NAMESPACE` and `DESCRIPTION` with the pinned roxygen2 in the gate's export of the commit being pushed, and fails on any difference. It checks commits, not the working tree: commit a roxygen edit before it counts. Fix: `devtools::document()`, then commit.
- `sh scripts/clean-tmp.sh` — empties `tmp/`.
- Warns: `_scratch/` untouched 3+ days. Graduate or delete.

## Git hygiene

This project uses the [pre-commit](https://pre-commit.com) framework and fleet-ci's local gate. Their configs (`.pre-commit-config.yaml`, `.fleet-ci.yml`) are cloned with the repo; each clone enables the hooks once, in this order:

```bash
pre-commit install
.fleet-ci/pre-push --install
```

`pre-commit install` writes both hook types (`default_install_hook_types`); `.fleet-ci/pre-push --install` then replaces the pre-push one with fleet-ci's, which runs the gate and then pre-commit's pre-push stage. `pre-commit install -f`, and `pre-commit install -f --hook-type pre-push`, drop the gate again: re-run `.fleet-ci/pre-push --install` after either. Until it is installed, the warn-only `fleet-ci-hook-installed` hook prints a WARNING on every push. `design/ci.md` has the details.

`pre-commit` is a Python tool. For non-Python templates, install it with `uv tool install pre-commit` or `pipx install pre-commit`. The gate needs Docker and `docker login registry.gitlab.com` (fleet-ci is private, ADR 0013).

### Per-commit checks

On every commit, lightweight hooks run: end-of-file fixer, trailing-whitespace trimming, merge-conflict detection, YAML/TOML validation, mixed-line-ending and case-conflict guards, and `check-added-large-files` — a portable 5 MB size guard that blocks accidentally committing heavy blobs (a big blob bloats `.git` history even after deletion).

### Pre-push gate (T0 and T1)

On `git push`, fleet-ci's pre-push hook runs the local gate, `.fleet-ci/gate`, in the fleet Docker image, on each pushed ref's tip; then pre-commit's pre-push stage runs. Under the verification tiers ([ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md)) the gate is T0 when the classifier calls the diff against `main` docs-only, and T1 otherwise, on every push the hook sees, branch pushes included; CI runs only T2 and T3. GitLab Free does offer protected branches, so wire those up too, but they only gate what reaches the default branch; this local hook blocks a failing tree before it ever leaves your machine. The gate refuses a push when more than one ref targets `main`, or when it adds more than one first-parent merge to `main`.

**This hook is the merge gate, and on a branch it is the only gate that runs anywhere.** That is deliberate. It gates the branch push; the merged tree is covered because a merge takes only a gated head that already contains the target's current tip, rebased onto a moved target and gated again. CI is fleet-ci's template: its `workflow:` rules deny by default, so a push to `main`, a branch push, a merge request and an API call create no pipeline, and CI runs only the weekly `deep-check` schedule (T2), a `v*` tag push (full T3, with the `pages` deploy), and hand-started (`web`) runs with `RELEASE=1` on `main` or a `v*` tag, or `PAGES=1` on a `v*` tag; [`ci.md`](ci.md) has the event table. On a branch, do not read a clean pipeline list as a passing result: there is no result.

The `pages` job publishes rather than reports, and deploys only from a `v*` tag. It strips the agent instruction files first — pkgdown renders every top-level `.md`, so `AGENTS.md`, `CLAUDE.md` and the `FP_*.md` files were once published next to the function reference as `AGENTS.html`, `CLAUDE.html` and friends: internal working notes served as if they were user documentation (SEOR-pibdjanz). The job uses a **keep-list**, not a deny-list: before `build_site`, every top-level `.md` not named in `.fleet-ci.yml`'s `pages_keep` is moved out of the tree, so a new agent file of any name stays private without anyone remembering to list it (SEOR-wqxhftpv). The flip side: a new top-level `.md` meant for the public site is **not** published until you add it to `pages_keep` in the same commit. A `pages_keep` entry whose file is missing, or that names an agent file, fails the job.

### Slice flow

Branching, the merge request flow, merging, cleanup and the confirm-first list follow the house `agent-workflow` skill. fp status changes have no git side effects: the `fp` skill's `references/decoupling.md`. What is specific to this repository is above: the hooks, the local gate and the event table.
