# seor 0.0.0.9000

* Initial metapackage scaffold.
* `library(seor)` installs and attaches the member packages `rurl`,
  `punycoder`, `pslr`, `sitemapr` and `pagerankr`; the planned member
  `robotstxtr` is attached opportunistically when installed.
* Added `seor_packages()` and `seor_conflicts()` helpers.

## Internal

* The documentation URL in `DESCRIPTION` and `_pkgdown.yml` names the host
  that actually serves the site. GitLab has unique-domain Pages enabled on this
  project, so its canonical address is `https://seor-272402.gitlab.io`, not the
  namespace-path form `https://bart-turczynski.gitlab.io/seor/` — that address
  belongs to no project here and returned 403 to every client. `R CMD check
  --as-cran` fetches declared URLs, so this was a latent submission blocker as
  well as a wrong address. Measured 2026-09-10 after the Pages access level was
  set to `enabled`: the unique domain returns 200 (SEOR-cmoyxzky).

* The OSS Index dependency audit in `tests/testthat/test-security.R` scopes to
  hard dependencies (`Depends` + `Imports`) instead of the `Suggests` tree.
  `oysteR::expect_secure()` audits `Suggests` too, which pulled in oysteR's own
  recursive dependencies -- `curl` among them -- and failed the pre-push gate on
  a vulnerability in the auditor rather than in anything seor ships. Scoped to
  hard dependencies the audit covers 12 packages and is clean; the old scope
  covered 87 (SEOR-sxvcbuia).
* CI now appends CRAN behind the pinned Posit Package Manager snapshot, so a
  dependency published to CRAN too recently for p3m to have synced still
  resolves (SEOR-arofvftg).
* The `pages`, `osv-audit` and `security-audit` CI jobs no longer hand
  `local::.` to pak, the pattern that made pak build seor's tarball before
  its members were installed (SEOR-fijlyqch).
