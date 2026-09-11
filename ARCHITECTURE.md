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
  with `seor`. `Remotes:` supplies GitLab/GitHub sources for members not yet on
  CRAN.
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
  [ADR 0001](design/adr/0001-citation-metadata-names-the-release.md): they name
  the release the `DESCRIPTION` version names, except before a package's first
  release, when they mirror the development version and claim no release date
  and no DOI.

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

## Membership and CRAN status

| Package     | Role            | On CRAN | Declared in       |
|-------------|-----------------|:-------:|-------------------|
| `rurl`      | core            |   yes   | Imports           |
| `punycoder` | core            |   yes   | Imports           |
| `pslr`      | core            |   yes   | Imports           |
| `sitemapr`  | core            |   no    | Imports + Remotes |
| `pagerankr` | core            |   no    | Imports + Remotes |
| `robotstxtr`| planned/optional|   no    | Suggests + Remotes|

**Key constraint:** a metapackage cannot be submitted to CRAN while any hard
dependency is off CRAN. Until `sitemapr`, `pagerankr` (and `robotstxtr`) are
published, `seor` stays forge-only. Before the first CRAN submission: drop
`Remotes:`, and move published members into `Imports:`.

## Name history

`seoR` (author Daniel Schmeh) was on CRAN 2018-01-29, archived 2018-06-02 for
uncorrected check problems. `seor` reuses that freed name; CRAN treats the two
as identical (case-insensitive). See `cran-comments.md`.
