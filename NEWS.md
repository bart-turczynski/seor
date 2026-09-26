# seor 0.0.0.9000

* Initial metapackage scaffold.
* `library(seor)` installs and attaches the member packages `rurl`,
  `punycoder`, `pslr`, `sitemapr` and `pagerankr`; the planned member
  `robotstxtr` is attached opportunistically when installed.
* Added `seor_packages()` and `seor_conflicts()` helpers.
* `raddr` (IP address parsing and classification) joins the core members.
* The maintainer's ORCID iD is now in `DESCRIPTION`, `citation("seor")`,
  `CITATION.cff` and `.zenodo.json`. The README carries the OpenSSF Best
  Practices badge (project 14932) (SEOR-dvbdsvuq, SEOR-oaqnafzs).
* `DESCRIPTION` has a `BugReports` field that points at the GitLab issue
  tracker. `CONTRIBUTING.md` says where to report bugs and what a merge
  request needs. `SECURITY.md` names the private channels: a confidential
  GitLab issue or email. `.bestpractices.json` names GitLab as the tracker
  and CI instead of GitHub (SEOR-oaqnafzs, SEOR-wmtfrsjq).

## Internal

* CI's `readme` job ignores blank-line-only differences in `README.md`.
  pandoc versions disagree about the blank line after the badges marker, so a
  README rendered with a newer local pandoc passed the pre-push gate and then
  failed CI (SEOR-kaqtnovh).

* `scripts/bestpractices-url.py` turns `.bestpractices.json` into
  bestpractices.dev edit links, because the site does not read the file from a
  GitLab repository. `--check` verifies the live entry against the file
  (SEOR-oaqnafzs). The script is vendored into the member packages, and an
  implementation digest, checked on every run, catches a copy that drifts.

* `.bestpractices.json` answers all 67 passing-level OpenSSF criteria, plus
  six silver-level ones the member packages also answer. `SECURITY.md` now commits
  to acknowledging a report within 7 days, as the members' policies do
  (SEOR-oaqnafzs).

* `CONTRIBUTING.md` has a stuck-pending runbook. A job that fails with
  `stuck_pending_no_matching_runners` means the self-hosted runner was
  offline, not that the code is broken. The runbook covers bringing the
  runner back, retrying, and closing the `runner-heartbeat` alert
  (SEOR-hhtzaknn).

* CI jobs now reuse the built package library instead of recompiling it. Two
  faults had to be fixed together: the runners had no cache backend, and
  `R_LIBS_USER` was a silent no-op because rocker/r-ver's `Renviron.site` puts
  `site-library` first in `.libPaths()`, so packages installed into the image
  and the cached `.r-lib` was empty. `before_script` now prepends the cached
  library via `Rprofile.site` (SEOR-pgammbgo).

* `DESCRIPTION`'s `URL:` now lists the package's r-universe page. r-universe
  records this repository's upstream owner as `gitlab-bart-turczynski` because
  it is hosted on GitLab, which does not match the `bart-turczynski` universe,
  so the package was built and served but hidden from r-universe search. The
  URL claims it (SEOR-zfamoutf).

* The pkgdown site no longer publishes the repository's agent instruction
  files. pkgdown renders every top-level `.md`, so `AGENTS.html`,
  `CLAUDE.html` and `AGENTS_LANG.html` were being served next to the function
  reference; the `pages` job now strips them with a glob before `build_site`
  (SEOR-pibdjanz).

* That filter now fails closed. The `pages` job keeps an explicit list of the
  top-level `.md` files meant for the site and moves every other one aside, so
  an agent file with a new name is private by default instead of published.
  Every page that was live when the change landed is on the list, so nothing
  already published was taken down (SEOR-wqxhftpv).

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
* `Remotes:` now lists every non-CRAN hard dependency. It named `pagerankr`,
  `robotstxtr` and `sitemapr` but not `pslr`, `punycoder` or `rurl`, so
  `remotes::install_gitlab("bart-turczynski/seor")` into a clean library failed
  on the three it omitted -- none of the members are on CRAN, so nothing else
  could resolve them. Installing from the r-universe repository was unaffected,
  because a universe resolves its own members and ignores `Remotes:`, which is
  why the gap stayed invisible. `robotstxtr` stays listed although it is only a
  `Suggests:`; it is the sole non-CRAN entry there, so every non-CRAN
  dependency is now declared by the same rule (SEOR-yaqhqkov).
* `Remotes:` no longer pins `rurl`, `pslr` and `punycoder` to their GitLab
  sources. All three are on CRAN (`rurl` 3.0.1, `pslr` 1.2.1, `punycoder`
  1.2.1, re-verified 2026-09-22), and `Remotes:` takes precedence over CRAN, so
  `remotes::install_gitlab("bart-turczynski/seor")` was resolving them to
  development builds instead of the released versions -- the side of the
  `punycoder` profile mismatch that made `pslr`'s `psl_diff()` example 213x
  slower. `pagerankr`, `sitemapr` and `robotstxtr` stay listed because they are
  still off CRAN, so the rule that every non-CRAN dependency is declared in
  `Remotes:` is unchanged (SEOR-hqvzcfnc).
* CI now runs only the pipeline on `main`: a top-level `workflow:` block
  suppresses both the merge-request pipeline and the branch pipeline, so a
  merged slice produces one pipeline instead of up to three. A feature-branch
  push, and an API-triggered pipeline on a non-default branch, now get no CI
  at all. Hand-starting one from Build > Pipelines > Run pipeline still works
  on any ref, and runs the full gate there; `pages` is the one job pinned to
  `main`, so a branch can be verified but never published (SEOR-bmgkzhvy).
