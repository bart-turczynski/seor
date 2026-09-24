
<!-- README.md is generated from README.Rmd. Please edit that file -->

# seor

<!-- badges: start -->
<!-- The lifecycle starts at "experimental" — bump it to "stable" once the API
     settles and the package is on CRAN, and add a CRAN downloads badge then.
     Coverage comes from GitLab's own badge, so it needs no account or token;
     the coverage job populates it on the first pipeline. Setup for OpenSSF
     Best Practices: design/badges.md. Snyk and FOSSA are omitted here —
     neither covers the CRAN/R ecosystem. -->

[![Pipeline](https://gitlab.com/bart-turczynski/seor/badges/main/pipeline.svg)](https://gitlab.com/bart-turczynski/seor/-/pipelines)
[![CRAN
status](https://www.r-pkg.org/badges/version/seor)](https://CRAN.R-project.org/package=seor)
[![Coverage](https://gitlab.com/bart-turczynski/seor/badges/main/coverage.svg)](https://gitlab.com/bart-turczynski/seor/-/pipelines)
[![Lifecycle:
experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
<!-- Register at https://www.bestpractices.dev/projects/new, replace PROJECT_ID,
     then uncomment the badge below.
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/PROJECT_ID/badge)](https://www.bestpractices.dev/projects/PROJECT_ID)
--> <!-- badges: end -->

`seor` bundles a suite of focused R packages for SEO and web-developer
workflows into a single metapackage. Installing `seor` installs every
member; `library(seor)` attaches them all at once, in the style of the
`tidyverse` metapackage.

## Members

| Package      | Purpose                                        | On CRAN |
|--------------|------------------------------------------------|:-------:|
| `rurl`       | URL parsing and manipulation                   |   yes   |
| `punycoder`  | Punycode / internationalized-domain conversion |   yes   |
| `pslr`       | Public Suffix List lookups                     |   yes   |
| `raddr`      | IP address parsing and classification          |   yes   |
| `sitemapr`   | XML sitemap parsing                            |   no    |
| `pagerankr`  | PageRank estimation                            |   no    |
| `robotstxtr` | `robots.txt` parsing (planned)                 |   no    |

Because some members are not yet on CRAN, `seor` is installed from
GitLab for now (a metapackage cannot go to CRAN until all of its hard
dependencies are on CRAN):

``` r
# install.packages("pak")
pak::pak("gitlab::bart-turczynski/seor")
```

`pak` reads the `Remotes:` field in `DESCRIPTION`, so the not-yet-CRAN
members are fetched automatically.

## Usage

``` r
library(seor)
#> -- Attaching seor packages --
#>   v rurl      ...
#>   v punycoder ...
#>   ...

seor_packages()    # the member packages
seor_conflicts()   # name collisions among attached packages
```

## Setup (development)

Install package dependencies (from `DESCRIPTION`, including the
`Remotes:` sources) plus the dev tooling used by the checks:

``` sh
Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
```

## Verification

``` sh
Rscript -e 'lints <- lintr::lint_package(); if (length(lints)) { print(lints); quit(status = 1) }' && Rscript -e 'rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning", env = c(callr::rcmd_safe_env(), "_R_CHECK_CRAN_INCOMING_" = "false"))'
```

`R CMD check` runs the testthat and cucumber specs, so the behaviour
specs are verified as part of the check.

The `env =` argument disables only the CRAN incoming-feasibility step.
seor is a metapackage with members that are not yet on CRAN, so that
step always reports an ERROR (non-mainstream dependencies, the
`Remotes:` field, the archived `seoR` name clash) — a permanent, known
state rather than a regression. Every other `--as-cran` check still
runs. Re-enable it for the first CRAN submission.

## Project Layout

- `R/` contains the package source (`attach.R` holds the load logic).
- `man/` contains generated help pages (regenerate with
  `devtools::document()`).
- `NAMESPACE` and `man/` are roxygen2-generated — edit the roxygen
  comments in `R/`, not these.
- `tests/testthat/` contains testthat tests and the cucumber feature
  specs.
- `vignettes/` contains long-form documentation.
- `_pkgdown.yml` configures the generated package website in `site/`.
- `DESCRIPTION` declares package metadata and dependencies.
- `ARCHITECTURE.md` is the living map of the project’s structure.
- `design/` holds specs (`design/specs/`) and decision records
  (`design/adr/`).
- `_scratch/` and `tmp/` are local-only and ignored by git.
