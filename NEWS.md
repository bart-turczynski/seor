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

* `CITATION.cff` and `.zenodo.json` now name that same host; both still pointed
  at the namespace-path address that returns 403, because the earlier fix
  touched `DESCRIPTION` and `_pkgdown.yml` and nothing looked at these two.
  `scripts/check-citation.py` is the check that would have caught it: it runs
  from the pre-push hook and from CI, and asserts that both files agree with
  `DESCRIPTION` on the version — under the rule in
  `design/adr/0001-citation-metadata-names-the-release.md` — and on the project
  URLs (SEOR-lreejxat).

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
* The OSS Index audit now asserts that every reported advisory has an explicit
  disposition rather than that the scan reports nothing, and the `security-audit`
  CI job fails when it cannot authenticate instead of skipping green. The
  allow-list in `tests/testthat/helper-security.R` is empty: measured 2026-09-11
  the hard dependency closure is 12 packages with zero advisories, and rule B
  fails a row that is not currently reported, so sitemapr's `curl` rows are not
  copied in ahead of the CRAN publication that would make them apply
  (SEOR-fkvlzltx, SEOR-sxvcbuia).
