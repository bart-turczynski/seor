# seor (development version)

* seor has a logo, the fleet's black hex, in `man/figures/logo.svg` and
  `logo.png`. r-universe shows it on the package card and pkgdown in the site
  header, and the README heading carries it (SEOR-wxjuxbtu).
* The README is for users now: an Installation section with the r-universe
  command, and each member's site and `llms.txt` link. The development setup
  and verify command live in `CONTRIBUTING.md`, the layout in
  `ARCHITECTURE.md`. `DESCRIPTION` declares `X-schema.org-keywords` for
  r-universe (SEOR-kqmqosji, SEOR-nplcfbib).
* seor 0.1.0 is archived on Zenodo. `citation("seor")`, `CITATION.cff` and
  `codemeta.json` carry the concept DOI (`10.5281/zenodo.23136687`), `CITATION.cff` also
  carries the 0.1.0 version DOI, and the README shows the DOI and
  latest-release badges (SEOR-dvbdsvuq).
# seor 0.1.0

* First release. It is not on CRAN: `robotstxtr` and `sitemapr` still
  install from GitLab. Its Zenodo archive and DOI come from a GitHub
  Release on the mirror (SEOR-dvbdsvuq).
* Initial metapackage scaffold.
* `library(seor)` installs and attaches the member packages `rurl`,
  `punycoder`, `pslr`, `sitemapr` and `pagerankr`; the planned member
  `robotstxtr` is attached opportunistically when installed.
* Added `seor_packages()` and `seor_conflicts()` helpers.
* `raddr` (IP address parsing and classification) joins the core members.
* The maintainer's ORCID iD is now in `DESCRIPTION`, `citation("seor")`,
  `CITATION.cff`, `.zenodo.json` and `codemeta.json`. The README carries the OpenSSF Best
  Practices badge (project 14932) (SEOR-dvbdsvuq, SEOR-oaqnafzs).
* `DESCRIPTION` has a `BugReports` field that points at the GitLab issue
  tracker. `CONTRIBUTING.md` says where to report bugs and what a merge
  request needs. `SECURITY.md` names the private channels: a confidential
  GitLab issue or email. `.bestpractices.json` names GitLab as the tracker
  and CI instead of GitHub (SEOR-oaqnafzs, SEOR-wmtfrsjq).
* `BugReports:` now uses the `/-/issues` form CRAN's incoming check asks for,
  and the package help page links it. The files a person reads
  (`CONTRIBUTING.md`, `SECURITY.md`, `codemeta.json`, `.bestpractices.json`)
  keep pointing at `/-/work_items`, the address that does not 404.
  `scripts/check-bugreports.py` enforces the split on the pre-push hook and in
  the `citation-version` CI job (SEOR-ocbtrrnl).
* `pagerankr` is on CRAN (0.1.0), so `DESCRIPTION` no longer lists it in
  `Remotes:`; only `robotstxtr` and `sitemapr` still install from GitLab
  (SEOR-wnbjpydq).
* `seor` now requires R 4.1.0 or later, up from 4.0.0. It attaches every
  member, and `pslr`, `punycoder`, `sitemapr` and `robotstxtr` already require
  R 4.1.0, so seor could never install on R 4.0 (SEOR-kqcbgsfc).
* Bart Turczynski is the copyright holder, in `DESCRIPTION` (`cph` role),
  `LICENSE` and `LICENSE.md`, which named "seor authors" (SEOR-kqcbgsfc).

## Internal

* The verify gate (pre-push hook, CI `verify` and `full-check`) also fails when
  `R CMD check` exits non-zero. `rcmdcheck` reads a check that halted partway as
  0 errors, 0 warnings and 0 notes, so a halted check used to pass
  (`SEOR-maavnxdm`).
* seor no longer commits a `.claude/settings.json`. Agent permissions come from
  the user-level settings, as in the other fleet repositories; its extra `ask`
  entries (`git rebase`, `git commit --amend`) and a pre-allowed `gh pr merge`
  made seor behave differently from the rest of the fleet.
* The agent instructions point at the house `agent-workflow` and `fp` skills
  instead of carrying their own copy of the slice flow and the fp/git
  decoupling rule. `design/fleet.md` holds the fleet tracker convention and a
  measured table of how the nine repositories' gates differ (SEOR-ipwcbcov).
* CI's `readme` job ignores blank-line-only differences in `README.md`.
  pandoc versions disagree about the blank line after the badges marker, so a
  README rendered with a newer local pandoc passed the pre-push gate and then
  failed CI (SEOR-kaqtnovh).

* `CHANGELOG.md` is gone, along with its page on the pkgdown site. It was an
  empty stub from the project template, and `NEWS.md` is the changelog.

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

* The documentation site lives at `https://bart-turczynski.gitlab.io/seor/`,
  the namespace path every package in the family uses. `DESCRIPTION`,
  `_pkgdown.yml` and the citation and security metadata name it. The earlier
  unique-domain address `https://seor-272402.gitlab.io` no longer resolves
  (SEOR-cmoyxzky, SEOR-hcmtspmv).

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
* CI no longer writes to the repository or needs a write token. The
  `renovate` job and `renovate.json` are gone, and so is the `codemeta` job
  that committed to `main` with `CODEMETA_TOKEN`; `codemeta.json` is now
  maintained by hand (SEOR-tzxuisnf).
* `osv-audit` and `security-audit` run only on a pipeline schedule that sets
  `SCHEDULE_KIND=dependency-audit` (or when started by hand), so a schedule
  added for another purpose no longer fires them (SEOR-fftbjnpl).
* `CONTRIBUTING.md` explains that CI runs on self-hosted runners on the
  maintainer's Mac, so a job failing with `stuck_pending_no_matching_runners`
  is the machine being asleep or the runner stopped, not the code, and how
  to confirm and retry it (SEOR-hhtzaknn).
* The README spells "behavior" in US English, and `inst/WORDLIST` no longer
  accepts the British spelling. `design/fleet.md` states the fleet rule:
  prose is US English, and a British spelling is respelled, never added
  to the word list (SEOR-kfiqpymb).
* The README badge row follows the fleet standard (`design/fleet-standard.md`):
  r-universe in slot 1 instead of a CRAN badge that rendered an error for a
  package not on CRAN, plus docs, repostatus, Zenodo, license, last-commit and
  the FOSSA license and security badges (SEOR-kqcbgsfc).
* `SECURITY.md` uses the fleet's shared policy text, with a seor scope that
  sends member-package reports to the member. `CODE_OF_CONDUCT.md` names
  bartek@turczynski.pl as the enforcement contact (SEOR-kqcbgsfc).
* The pre-push gate has a `check-urls` hook (`scripts/check-urls.R`, copied
  from `punycoder`) that fetches every URL the package declares and fails on a
  dead one. seor's `R CMD check` runs with CRAN incoming off, so nothing else
  in the gate fetched them (SEOR-kqcbgsfc).
* CI meets the fleet standard. `readme` and `news-version` fold into one
  `gates` job (`scripts/gates.sh`, per `design/adr/0005`) that also runs the
  spelling gate; `coverage` fails below 95%; the deep-check schedule runs the
  current R release (4.6.1), the previous one (4.5.3) and R-devel in
  `full-check`, plus a best-effort R 4.1
  floor leg, `floor-check`; and a `fossa` job uploads a FOSSA license and
  security scan on every push to `main` (SEOR-kqcbgsfc).
