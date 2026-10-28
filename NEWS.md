# seor (development version)

* `library(seor)` now installs and attaches `robotstxtr` and `ssrfr`, so installing seor needs libcurl >= 7.73.0; `seor_packages()` lists them and ignores `include_optional` (SEOR-qhpzspww).
* `citation("seor")` carries the Zenodo concept DOI, `10.5281/zenodo.23136687` (SEOR-dvbdsvuq).

# seor 0.1.0

* First release. It is not on CRAN: `robotstxtr` and `sitemapr` still install from GitLab, and its Zenodo DOI comes from a Release on the GitHub mirror (SEOR-dvbdsvuq).
* Initial metapackage scaffold.
* `library(seor)` installs and attaches `rurl`, `punycoder`, `pslr`, `sitemapr` and `pagerankr`, and attaches `robotstxtr` when it is installed.
* Added `seor_packages()` and `seor_conflicts()` helpers.
* `raddr` (IP address parsing and classification) joins the core members.
* `citation("seor")` and `DESCRIPTION` carry the maintainer's ORCID iD (SEOR-dvbdsvuq).
* `DESCRIPTION` has a `BugReports` field that points at the GitLab issue tracker (SEOR-oaqnafzs).
* `BugReports:` uses the `/-/issues` form CRAN's incoming check asks for, and the package help page links it (SEOR-ocbtrrnl).
* `pagerankr` is on CRAN (0.1.0), so only `robotstxtr` and `sitemapr` still install from GitLab (SEOR-wnbjpydq).
* `seor` now requires R 4.1.0 or later, as `pslr`, `punycoder`, `sitemapr` and `robotstxtr` do (SEOR-kqcbgsfc).
* Bart Turczynski is the copyright holder in `DESCRIPTION`, `LICENSE` and `LICENSE.md` (SEOR-kqcbgsfc).
* `remotes::install_gitlab("bart-turczynski/seor")` works in a clean library: `Remotes:` lists every non-CRAN dependency (SEOR-yaqhqkov).
* `remotes::install_gitlab("bart-turczynski/seor")` installs the CRAN releases of `rurl`, `pslr` and `punycoder`, not their development builds (SEOR-hqvzcfnc).
* The documentation site is `https://bart-turczynski.gitlab.io/seor/`; the earlier address `https://seor-272402.gitlab.io` no longer resolves (SEOR-cmoyxzky, SEOR-hcmtspmv).
* seor now appears in r-universe search (SEOR-zfamoutf).
