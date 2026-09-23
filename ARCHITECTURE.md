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
- `tests/testthat/` — testthat tests plus the cucumber `.feature` specs, which
  run inside the normal `R CMD check` pass.
- `vignettes/` — long-form documentation.
- `inst/` — files that ship inside the installed package (`CITATION`, `WORDLIST`).
- `design/`, `ARCHITECTURE.md` — durable project context. Kept out of the CRAN
  tarball via `.Rbuildignore`.
- `scripts/` — repository hygiene checks that run from the pre-push hook.
  `check-design.py` owns design-doc hygiene; `check-citation.py` owns the
  agreement between `CITATION.cff`, `.zenodo.json` and `DESCRIPTION`. Both are
  offline and stdlib-only, so they also run as cheap CI jobs.
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
- **Optional members degrade quietly.** `robotstxtr` is declared under
  `Suggests` and attached only when already installed, so the suite still loads
  without it.
- **`R CMD check` reports one expected NOTE** — "Namespaces in Imports field not
  imported from" — because members are attached at runtime rather than
  `importFrom`'d. This is inherent to the metapackage pattern (`tidyverse` gets
  the same NOTE) and is safe to leave.
- **The verify gate suppresses CRAN incoming feasibility here, and only here.**
  Incoming always ERRORs for a metapackage whose members are off CRAN, so
  `_R_CHECK_CRAN_INCOMING_ = "false"` is deliberate and is not to be removed to
  fix a red gate. Every other repository in the fleet runs the check, because it
  is what surfaces dead `URL:`/`BugReports:` links — see
  [ADR 0004](design/adr/0004-cran-incoming-runs-everywhere-except-seor.md) for
  the boundary and how the rule is enforced across seven different gate
  implementations.

## Membership and CRAN status

The `On CRAN` column governs the `Declared in` column: a member on CRAN is
declared in `Imports:`/`Suggests:` only, and a member off CRAN is additionally
declared in `Remotes:`. When a member is published, its `Remotes:` line goes.

| Package     | Role            | On CRAN | Declared in        |
|-------------|-----------------|:-------:|--------------------|
| `rurl`      | core            |   yes   | Imports            |
| `punycoder` | core            |   yes   | Imports            |
| `pslr`      | core            |   yes   | Imports            |
| `sitemapr`  | core            |   no    | Imports + Remotes  |
| `pagerankr` | core            |   no    | Imports + Remotes  |
| `robotstxtr`| planned/optional|   no    | Suggests + Remotes |

**Key constraint:** a metapackage cannot be submitted to CRAN while any hard
dependency is off CRAN. Until `sitemapr` and `pagerankr` (and, for the optional
member, `robotstxtr`) are published, `seor` stays forge-only. `Remotes:` must be
absent from a CRAN tarball, so the last entries go at the first submission.

## Name history

`seoR` (author Daniel Schmeh) was on CRAN 2018-01-29, archived 2018-06-02 for
uncorrected check problems. `seor` reuses that freed name; CRAN treats the two
as identical (case-insensitive). See `cran-comments.md`.
