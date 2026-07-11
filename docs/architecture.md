# Architecture

This document captures durable project context, constraints, and design decisions that should survive beyond temporary planning notes.

## What seor is

`seor` is a **metapackage** in the style of `tidyverse`. It defines no
analysis functions of its own. Its job is to (1) install the member packages
as dependencies and (2) attach them all on `library(seor)`.

## How it works

- `Imports:` in `DESCRIPTION` is what makes the member packages get *installed*
  with `seor`. `Remotes:` supplies GitHub sources for members not yet on CRAN.
- `.onAttach()` in `R/attach.R` is what makes them get *attached* (put on the
  search path). It calls `library()` on each member and prints a banner.
- The `core` vector in `R/attach.R` is the single source of truth for
  membership and must be kept in sync with `Imports:`.

`R CMD check` reports one expected NOTE — "Namespaces in Imports field not
imported from" — because members are attached at runtime rather than
`importFrom`'d. This is inherent to the metapackage pattern (`tidyverse` gets
the same NOTE) and is safe to leave.

## Membership and CRAN status

| Package     | Role            | On CRAN | Declared in |
|-------------|-----------------|:-------:|-------------|
| `rurl`      | core            |   yes   | Imports     |
| `punycoder` | core            |   yes   | Imports     |
| `pslr`      | core            |   yes   | Imports     |
| `sitemapr`  | core            |   no    | Imports + Remotes |
| `pagerankr` | core            |   no    | Imports + Remotes |
| `robotstxtr`| planned/optional|   no    | Suggests + Remotes |

## Key constraint: CRAN submission

A metapackage cannot be submitted to CRAN while any hard dependency is off
CRAN. Until `sitemapr`, `pagerankr` (and `robotstxtr`) are published, `seor`
stays GitHub-only. Before the first CRAN submission: drop `Remotes:`, and move
published members into `Imports:`.

## Name history

`seoR` (author Daniel Schmeh) was on CRAN 2018-01-29, archived 2018-06-02 for
uncorrected check problems. `seor` reuses that freed name; CRAN treats the two
as identical (case-insensitive). See `cran-comments.md`.

## Attach philosophy

`seor` *attaches* member packages rather than re-exporting their functions, so
each member remains a fully independent, standalone package. This matches
`tidyverse` and keeps the members usable without the umbrella.
