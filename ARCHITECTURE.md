# seor architecture

The living map of how this project is put together: directories, responsibilities,
seams, and invariants. Unlike a spec, this file must be true *right now* — it
describes the current structure, not a plan or a history.

Keep it coarse. Name directories and what they own; do not cite line numbers or
function signatures, which rot on the first refactor. Update it when the
structure changes, not when code changes.

For *why* a load-bearing choice was made, see the Architecture Decision Records
in [`design/adr/`](design/adr/). For *what* was built and to which requirements,
see [`design/specs/`](design/specs/).

## Overview

`seor` is a **metapackage** in the style of `tidyverse`. It defines no analysis
functions of its own. Its job is to (1) install the member packages as
dependencies and (2) attach them all on `library(seor)`.

- `Imports:` in `DESCRIPTION` is what makes the member packages get *installed*
  with `seor`. `Remotes:` supplies a GitLab source for exactly those members
  that are not on CRAN yet — no more and no fewer. A missing entry breaks the
  direct-from-GitLab install; a stale entry for a member that has since been
  published silently overrides CRAN and hands every user a development build.
- `.onAttach()` in `R/attach.R` is what makes them get *attached* (put on the
  search path). It calls `library()` on each member and prints a banner.

## Layout

- `R/` — the package source. `attach.R` owns membership and the attach banner;
  `conflicts.R` owns search-path collision reporting; `seor-package.R` is the
  package-level roxygen block.
- `man/`, `NAMESPACE` — roxygen2 output. Never edited by hand; regenerate with
  `devtools::document()`.
- `tests/testthat/` — testthat tests, run inside the normal `R CMD check` pass.
- `vignettes/` — long-form documentation.
- `inst/` — files that ship inside the installed package (`CITATION`, `WORDLIST`).
- `design/`, `ARCHITECTURE.md` — durable project context. Kept out of the CRAN
  tarball via `.Rbuildignore`. Two documents here are fleet-wide rather than
  seor-specific, because seor is where fleet decisions are recorded:
  [`design/github-mirror.md`](design/github-mirror.md), the procedure for
  mirroring a GitLab repo to GitHub as proven on the eight R packages, and
  [`design/badges.md`](design/badges.md). What every member carries (badges,
  CI, schedules, files, `DESCRIPTION` fields) is `design/fleet-standard.md`;
  [ADR 0012](design/adr/0012-verification-tiers-replace-per-push-ci.md),
  which supersedes ADR 0007, records its load-bearing choices: verification
  tiers instead of per-push CI, with each package's CI moving to fleet-ci's
  shared template, pinned by SHA.
  [ADR 0013](design/adr/0013-fleet-ci-is-private.md) amends it: fleet-ci is
  private, so its template and images need authenticated reads.
- `.gitlab-ci.yml`, `.fleet-ci.yml`, `.fleet-ci/` — CI and the local gate
  ([`design/ci.md`](design/ci.md)). `.gitlab-ci.yml` includes fleet-ci's
  template at a pinned SHA and sets only seor's switches and its `x-*` jobs;
  `.fleet-ci.yml` holds the local gate's settings; `.fleet-ci/` is fleet-ci's
  vendored gate, rewritten only by fleet-ci's `bin/vendor`.
- `scripts/` — repository hygiene checks that run from the pre-push hooks and
  the local gate, and the fleet's shared tooling.
  `check-design.py` owns design-doc hygiene; `check-citation.py` owns the
  agreement between `CITATION.cff`, `.zenodo.json` and `DESCRIPTION`. Both are
  offline and stdlib-only pre-push hooks, and T2's `citation-version` job runs
  `check-citation.py` too.
  `check-bugreports.py`, also offline and stdlib-only, holds `BugReports:`,
  the package help page and every tracker link on `/-/work_items`, and
  `check-urls.R` fetches every declared URL with no exemption
  ([ADR 0011](design/adr/0011-bugreports-names-work-items.md)).
  `check-docs-drift.R` fails when `man/`, `NAMESPACE` or `DESCRIPTION` differ
  from what the pinned roxygen2 regenerates; the local gate runs it, with
  `check-urls.R`, `check-readme-drift.sh` and `check-news-version.sh`, on
  its export of the pushed commit. `check-fleet-hook.sh` warns when a
  clone's pre-push hook is not fleet-ci's.
  `bestpractices-url.py` is a maintainer tool, not a check. It turns
  `.bestpractices.json` into bestpractices.dev edit links and verifies the live
  entry against the file. It reads the network, and only its offline
  `--self-test` runs from the hook. Like `check-citation.py`, it is vendored
  into the member packages, and its `IMPLEMENTATION_DIGEST` catches a copy
  that drifts.
  `check-citation-nonr.py` is the citation gate for the non-R repositories
  (cc-cream, cf-crawl, linklint, unbreak). seor holds the reference copy
  they vendor, with a digest of its own, and runs only its offline
  `--self-test`, from the hook, when the script changes. Each repository
  declares where its release version lives (`--source package-json` or
  `--source git-tag`); see
  [ADR 0006](design/adr/0006-non-r-citation-metadata-has-its-own-gate.md)
  for why it is not part of `check-citation.py`.
  `check-fleet-standard.py` is not stdlib-only: it reads CI with PyYAML
  ([ADR 0008](design/adr/0008-fleet-checker-reads-ci-with-pyyaml.md)). It
  follows one include, fleet-ci's template at a `v*`-tagged SHA, expanded
  locally from a fleet-ci clone, and no other
  ([ADR 0014](design/adr/0014-fleet-checker-follows-the-fleet-ci-include.md),
  amending ADR 0008).
  `check-toolchain.R`, which every member vendors, is not base R only either:
  it reads the pandoc pin in `.gitlab-ci.yml` with the yaml package
  ([ADR 0009](design/adr/0009-check-toolchain-reads-the-ci-pin-with-yaml.md)),
  and refuses any shell mention of it that is not a pin, a use, a bare
  `export` or `readonly`, or a comment
  ([ADR 0010](design/adr/0010-check-toolchain-allows-shell-mentions-it-reads.md)).
  `logo-metadata.py` writes every member's logo metadata, keywords copied
  from `DESCRIPTION`. Its `--self-test` and `--check seor man/figures`, which
  fails when seor's own logo has drifted from `DESCRIPTION`, run from the
  pre-push hooks.
- `CITATION.cff`, `.zenodo.json` — publication metadata, kept out of the CRAN
  tarball via `.Rbuildignore`. The version they carry is governed by
  [ADR 0002](design/adr/0002-citation-urls-are-the-ones-about-this-package.md),
  which supersedes ADR 0001: they name the release the `DESCRIPTION` version
  names, except before a package's first release, when they mirror the
  development version and claim no release date and no DOI. The URLs they
  declare *about this package* must appear in `DESCRIPTION`'s `URL:`; a
  `.zenodo.json` related identifier pointing at a dependency or an upstream
  source is not one of those and is not cross-checked.

## Invariants

- **The `core` vector in `R/attach.R` is the single source of truth for
  membership, and must stay in sync with `Imports:` in `DESCRIPTION`.** A member
  in one and not the other either fails to install or fails to attach.
- **Members are attached, never re-exported.** `seor` puts each member on the
  search path rather than re-exporting its functions, so every member stays a
  fully independent, standalone package usable without the umbrella. This
  matches `tidyverse`.
- **`R CMD check` reports one expected NOTE** — "Namespaces in Imports field not
  imported from" — because members are attached at runtime rather than
  `importFrom`'d. This is inherent to the metapackage pattern (`tidyverse` gets
  the same NOTE) and is safe to leave.
- **seor's `t2-ascran` runs with CRAN incoming feasibility off, and only
  seor's.** Incoming always ERRORs for a metapackage whose members are off
  CRAN, so `FLEET_INCOMING: "false"` in `.gitlab-ci.yml` is deliberate and is
  not to be removed to fix a red pipeline. Every other repository in the fleet
  runs the check there, because it is what surfaces dead `URL:`/`BugReports:`
  links; for seor, the local gate's `check-urls.R` is the only URL check. The
  exception was decided in
  [ADR 0004](design/adr/0004-cran-incoming-runs-everywhere-except-seor.md),
  now superseded by
  [ADR 0012](design/adr/0012-verification-tiers-replace-per-push-ci.md), which
  carries it forward. The local gate runs no incoming check for any package.
- **CI is fleet-ci's template, not jobs of seor's own.** A push to `main`, a
  branch push and a merge request create no pipeline; the merge gate is the
  local gate, and CI runs only T2 (the weekly `deep-check` schedule) and T3
  (release runs). seor adds only `x-floor` and `x-fossa`, and never writes
  `rules`, `when` or `workflow` (ADR 0012). ADR 0005's rule that a job
  carrying its own `image:` cannot be folded into one that does not still
  holds for those two.

## Membership and CRAN status

The `On CRAN` column governs the `Declared in` column: a member on CRAN is
declared in `Imports:` only, and a member off CRAN is additionally declared in
`Remotes:`. When a member is published, its `Remotes:` line goes. Every member
is core: `library(seor)` installs and attaches all of them (owner, 2026-10-21;
`ssrfr` joined on 2026-10-22).

| Package      | Role | On CRAN | Declared in       |
|--------------|------|:-------:|-------------------|
| `rurl`       | core |   yes   | Imports           |
| `punycoder`  | core |   yes   | Imports           |
| `pslr`       | core |   yes   | Imports           |
| `raddr`      | core |   yes   | Imports           |
| `sitemapr`   | core |   no    | Imports + Remotes |
| `pagerankr`  | core |   yes   | Imports           |
| `robotstxtr` | core |   no    | Imports + Remotes |
| `ssrfr`      | core |   no    | Imports + Remotes |

**Key constraint:** a metapackage cannot be submitted to CRAN while any hard
dependency is off CRAN. Until `sitemapr`, `robotstxtr` and `ssrfr` are
published, `seor` stays forge-only. `Remotes:` must be
absent from a CRAN tarball, so the last entries go at the first submission.

## Name history

`seoR` (author Daniel Schmeh) was on CRAN 2018-01-29, archived 2018-06-02 for
uncorrected check problems. `seor` reuses that freed name; CRAN treats the two
as identical (case-insensitive). See `cran-comments.md`.
