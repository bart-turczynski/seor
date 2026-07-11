# seor

`seor` bundles a suite of focused R packages for SEO and web-developer
workflows into a single metapackage. Installing `seor` installs every member;
`library(seor)` attaches them all at once, in the style of the `tidyverse`
metapackage.

## Members

| Package     | Purpose                                        | On CRAN |
|-------------|------------------------------------------------|:-------:|
| `rurl`      | URL parsing and manipulation                   |   yes   |
| `punycoder` | Punycode / internationalized-domain conversion |   yes   |
| `pslr`      | Public Suffix List lookups                     |   yes   |
| `sitemapr`  | XML sitemap parsing                            |   no    |
| `pagerankr` | PageRank estimation                            |   no    |
| `robotstxtr`| `robots.txt` parsing (planned)                 |   no    |

Because some members are not yet on CRAN, `seor` is installed from GitHub for
now (a metapackage cannot go to CRAN until all of its hard dependencies are on
CRAN):

```r
# install.packages("pak")
pak::pak("bart-turczynski/seor")
```

`pak` reads the `Remotes:` field in `DESCRIPTION`, so the not-yet-CRAN members
are fetched from GitHub automatically.

## Usage

```r
library(seor)
#> -- Attaching seor packages --
#>   v rurl      ...
#>   v punycoder ...
#>   ...

seor_packages()    # the member packages
seor_conflicts()   # name collisions among attached packages
```

## Setup (development)

Install package dependencies (from `DESCRIPTION`, including the `Remotes:`
sources) plus the dev tooling used by the checks:

```sh
Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
```

## Verification

```sh
Rscript -e 'lints <- lintr::lint_package(); if (length(lints)) { print(lints); quit(status = 1) }' && Rscript -e 'rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning")'
```

`R CMD check` runs the testthat and cucumber specs, so the behaviour specs are
verified as part of the check.

## Project Layout

- `R/` contains the package source (`attach.R` holds the load logic).
- `man/` contains generated help pages (regenerate with `devtools::document()`).
- `NAMESPACE` and `man/` are roxygen2-generated — edit the roxygen comments in `R/`, not these.
- `tests/testthat/` contains testthat tests and the cucumber feature specs.
- `vignettes/` contains long-form documentation.
- `DESCRIPTION` declares package metadata and dependencies.
- `docs/architecture.md` contains durable project context.
- `_scratch/` is local-only planning space and is ignored by git.
