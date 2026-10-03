# Fleet standard

What every R package in the fleet carries: the README badge row, the CI and
scheduled pipelines, the local gate, the files, the `DESCRIPTION` fields and
the identities behind them. The owner asked on 2026-10-03 for the same badges
and checks in all nine packages (SEOR-plnwieyf). Each package's "meets the
fleet standard" issue cites this file instead of restating it.
[ADR 0007](adr/0007-one-fleet-standard-for-badges-and-checks.md) records why
the load-bearing choices went the way they did.

This is a living reference. Edit it when a fact changes. A change to a choice
ADR 0007 records needs a new ADR first.

## Operating rule

Owner decision 1, 2026-10-03. An agent working on a package's fleet-standard
issue does, through an API or CLI (`glab`, `gh`, `curl`), whatever is part of
that work, without asking. That includes the GitLab project badges, pipeline
schedules, CI/CD variables, Pages settings, the project description and
topics, and playing a schedule to verify a repository
(`POST /projects/:id/pipeline_schedules/:schedule_id/play`). The owner is asked
only for a step that needs their login, a secret only they hold, or a
decision. A dashboard is the fallback when no API does the job.

The house `agent-workflow` skill still governs git and the forge: what it lists
as confirm-first stays confirm-first.

## Badge row

Every README carries the badges below, in this order, between the
`<!-- badges: start -->` and `<!-- badges: end -->` markers of `README.Rmd`.
The GitLab project badges (Settings > Badges, or the `projects/:id/badges`
API) carry the same set, with the same image and link URLs.

| #  | badge                          | shown when                                    |
|----|--------------------------------|-----------------------------------------------|
| 1  | CRAN version                   | on CRAN. Off CRAN, the r-universe badge takes this slot |
| 2  | CRAN downloads                 | on CRAN                                       |
| 3  | CRAN checks                    | on CRAN                                       |
| 4  | r-universe                     | always (in slot 1 while off CRAN)             |
| 5  | GitLab pipeline                | always                                        |
| 6  | GitLab coverage                | always                                        |
| 7  | docs                           | always                                        |
| 8  | latest release                 | once a GitLab Release exists                  |
| 9  | lifecycle                      | always                                        |
| 10 | repostatus                     | always                                        |
| 11 | DOI                            | once a concept DOI exists and doi.org resolves it |
| 12 | Zenodo "all software"          | always                                        |
| 13 | OpenSSF Best Practices         | always                                        |
| 14 | license                        | always                                        |
| 15 | dependencies (tinyverse)       | on CRAN                                       |
| 16 | last commit                    | always                                        |
| 17 | FOSSA license and security     | rurl, ssrfr and seor only                     |

A package off CRAN shows the r-universe badge once, in slot 1, and none of
slots 2, 3 or 15. On first CRAN acceptance, slot 1 becomes the three CRAN
badges and r-universe moves back to slot 4
([`release-checklist.md`](release-checklist.md), step 12).

The templates, in order. `<pkg>` is the package name. Four values differ per
package and are not derived from the name: `<stage>` and `<color>` for the
lifecycle badge (`experimental`/`orange`, `stable`/`brightgreen`,
`superseded`/`blue`, `deprecated`/`orange`, as usethis's
`use_lifecycle_badge()` pairs them), `<concept-doi>` (the Zenodo
concept DOI, `10.5281/zenodo.NNN`, never a version DOI) and `<bp-id>` (the
bestpractices.dev project number).

```markdown
[![CRAN status](https://www.r-pkg.org/badges/version/<pkg>)](https://CRAN.R-project.org/package=<pkg>)
[![CRAN downloads](https://cranlogs.r-pkg.org/badges/<pkg>)](https://CRAN.R-project.org/package=<pkg>)
[![CRAN checks](https://badges.cranchecks.info/worst/<pkg>.svg)](https://cran.r-project.org/web/checks/check_results_<pkg>.html)
[![r-universe](https://bart-turczynski.r-universe.dev/<pkg>/badges/version)](https://bart-turczynski.r-universe.dev/<pkg>)
[![Pipeline](https://gitlab.com/bart-turczynski/<pkg>/badges/main/pipeline.svg)](https://gitlab.com/bart-turczynski/<pkg>/-/pipelines)
[![Coverage](https://gitlab.com/bart-turczynski/<pkg>/badges/main/coverage.svg)](https://gitlab.com/bart-turczynski/<pkg>/-/pipelines)
[![Docs](https://img.shields.io/website?url=https%3A%2F%2Fbart-turczynski.gitlab.io%2F<pkg>%2F&label=docs&logo=gitlab&logoColor=white&up_message=pkgdown&up_color=1f75cb)](https://bart-turczynski.gitlab.io/<pkg>/)
[![Latest release](https://img.shields.io/gitlab/v/release/bart-turczynski%2F<pkg>)](https://gitlab.com/bart-turczynski/<pkg>/-/releases)
[![Lifecycle: <stage>](https://img.shields.io/badge/lifecycle-<stage>-<color>.svg)](https://lifecycle.r-lib.org/articles/stages.html#<stage>)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![DOI](https://zenodo.org/badge/DOI/<concept-doi>.svg)](https://doi.org/<concept-doi>)
[![Zenodo](https://img.shields.io/badge/Zenodo-all_software-1682D4?logo=zenodo&logoColor=white)](https://zenodo.org/search?q=metadata.creators.person_or_org.identifiers.identifier:0000-0002-8788-7980)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/<bp-id>/badge)](https://www.bestpractices.dev/projects/<bp-id>)
[![License](https://img.shields.io/gitlab/license/bart-turczynski%2F<pkg>)](https://gitlab.com/bart-turczynski/<pkg>/-/blob/main/LICENSE.md)
[![Dependencies](https://tinyverse.netlify.app/badge/<pkg>)](https://CRAN.R-project.org/package=<pkg>)
[![Last commit](https://img.shields.io/gitlab/last-commit/bart-turczynski%2F<pkg>)](https://gitlab.com/bart-turczynski/<pkg>/-/commits/main)
[![FOSSA license](https://app.fossa.com/api/projects/git%2Bgitlab.com%2Fbart-turczynski%2F<pkg>.svg?type=shield&issueType=license)](https://app.fossa.com/projects/git%2Bgitlab.com%2Fbart-turczynski%2F<pkg>?ref=badge_shield&issueType=license)
[![FOSSA security](https://app.fossa.com/api/projects/git%2Bgitlab.com%2Fbart-turczynski%2F<pkg>.svg?type=shield&issueType=security)](https://app.fossa.com/projects/git%2Bgitlab.com%2Fbart-turczynski%2F<pkg>?ref=badge_shield&issueType=security)
```

### Excluded, and why

- **Contributors.** The count includes bot and agent identities.
- **Stars and forks.**
- **Anything from GitHub.** GitHub holds a read-only mirror
  ([`github-mirror.md`](github-mirror.md)); its counts and statuses describe
  the copy, not the project. That includes a FOSSA locator on `github.com`.
- **OpenSSF Scorecard.** Public results for GitLab projects stopped on
  2023-11-20 ([`badges.md`](badges.md)). For rurl the shields badge reads
  "invalid repo path".
- **The shields CRAN monthly-downloads badge** (`img.shields.io/cran/dm/<pkg>`).
  It renders "404: badge not found"; slot 2 uses cranlogs instead.

### Checked live, 2026-10-03

Each template above was filled in and its image URL fetched. All returned 200
and a real state:

- **rurl:** CRAN `3.1.0`, downloads `734/month`, CRAN checks `OK`, r-universe
  `3.1.0.9000`, pipeline `passed`, docs `pkgdown`, release `v3.1.0`, lifecycle
  `stable`, repostatus `Active`, DOI `10.5281/zenodo.20972584` (rurl's concept
  DOI, `conceptrecid` 20972584 on the Zenodo API), Zenodo `all software`,
  OpenSSF Best Practices `passing` (project 13394), license `MIT License`,
  dependencies `3/6`, last commit `yesterday`. Every link target answered 200
  or redirected to its canonical page.
- **robotstxtr**, for the states rurl lacks: coverage `95.29%` (rurl's reads
  `unknown`: its CI sets no coverage regex yet), and r-universe `0.3.0` in
  slot 1, where the CRAN version badge answers 500 for a package not on CRAN.

What the conditions rest on:

- **Dependencies is CRAN-only.** tinyverse reads CRAN: it renders `unknown` for
  robotstxtr, sitemapr and seor, and `1/1` for punycoder.
- **CRAN checks is CRAN-only.** For robotstxtr the URL returns an HTML page,
  not an image.
- **Latest release waits for a Release.** robotstxtr's renders
  `no releases found`.
- **The last-commit badge takes no branch segment.**
  `.../last-commit/bart-turczynski%2Frurl/main` renders `project not found`.
- **The FOSSA template is unverified.** No project exists under a
  `git+gitlab.com` locator yet: the API returns 404 for rurl, ssrfr and seor.
  The same URL shape renders under the GitHub locators that exist today (rurl:
  "license scan: failing"; pslr: "passing"). It is checked when the first
  `fossa analyze` job uploads.

## CI on every push to `main`

Every push to `main` runs:

- `R CMD check --as-cran` through `rcmdcheck` with `error_on = "warning"`.
  CRAN incoming feasibility stays on, with the two exceptions
  [ADR 0004](adr/0004-cran-incoming-runs-everywhere-except-seor.md) names:
  seor turns it off, and pslr's `_R_CHECK_CRAN_INCOMING_REMOTE_=false` stays
  grandfathered.
- A coverage job: a `coverage:` regex for the badge, a cobertura
  `coverage_report` artifact for the diff annotations, and a failure below
  95% total coverage. The threshold is never lowered; a package under it adds
  tests ([ADR 0007](adr/0007-one-fleet-standard-for-badges-and-checks.md)).
- The pkgdown `pages` deploy.
- The cheap gates: README drift (`README.md` matches a fresh knit of
  `README.Rmd`), news-version, citation-version, lint and spelling.

A tag pipeline must not fail only because that version is already on CRAN.
rurl's `v3.1.0` tag pipeline (#209, 2026-10-02) failed exactly that way: its
`check` job stopped on a WARNING from "checking CRAN incoming feasibility" for
a version CRAN had already accepted.

## Scheduled pipelines

The schedule rules in [`fleet.md`](fleet.md) hold: weekly and staggered,
`SCHEDULE_KIND` set on the schedule itself, every schedule on `main`. Every
package has both kinds below.

### `deep-check`

- Legs for R release, oldrel and devel.
- A leg at the declared R floor (owner decision 2, 2026-10-03):
  - The floor is the oldest R minor version where the package installs and
    `R CMD check` passes with its dependencies. Probe likely minors (4.0, 4.1,
    4.2, and so on) with rocker/r-ver images on the arm64 runner, or a local
    install. Don't chase patch releases.
  - Set `Depends: R (>= x.y)` to that minor, raising or lowering it, with a
    NEWS bullet. The floor leg tests that version.
  - Never declare a floor below what a dependency needs. A member's floor is
    at least the highest floor among its fleet dependencies (ssrfr imports
    pslr; seor attaches every member), so seor's floor is the highest in the
    fleet. Order the changes so that no member declares a floor its own
    dependencies cannot install on.
  - Old R needs dependency versions that still support it, from a dated Posit
    Package Manager snapshot, for example. The floor leg must not pin anything
    that conflicts with what the release and devel legs install.
- ASAN/UBSAN sanitizer legs for the packages with compiled code: punycoder,
  pslr and robotstxtr.

### `dependency-audit`

`osv-audit` and `security-audit`, in seor's shape: each advisory reported needs
an explicit disposition row, and a row nobody reports any more fails
(`tests/testthat/helper-security.R`, SEOR-fkvlzltx). The jobs run only on a
schedule that sets `SCHEDULE_KIND=dependency-audit` (SEOR-fftbjnpl).
`security-audit` fails when its OSS Index credentials are missing instead of
skipping green. Never add an allow-list row ahead of the advisory it answers:
an anticipatory row fails as stale on the day it lands.

## FOSSA

The free plan allows five projects per account. Owner allocation, 2026-10-03:

1. rurl, ssrfr and seor, each with a `fossa analyze` CI job and the slot-17
   badges.
2. Two slots held for the non-R repositories.
3. raddr, then pslr, if a slot frees up.

FOSSA's R analysis reads `DESCRIPTION` for direct dependencies and finds
deeper ones only through `renv.lock` ([`badges.md`](badges.md)). The
`FOSSA_API_KEY` CI/CD variable is a secret only the owner holds.

Measured 2026-10-03: FOSSA badge endpoints answer for rurl, pslr and punycoder
under `git+github.com` locators, which use slots and show the mirror. Moving
to the allocation means retiring those, which takes the owner's FOSSA login.

## Local pre-push gate

The shared set all nine repositories already run, measured 2026-10-03 on each
`.pre-commit-config.yaml`: the seven per-commit hygiene hooks, codespell with
`--builtin en-GB_to_en-US`, `check-toolchain`, and `verify`, whose chain
includes the spelling gate (its row in [`fleet.md`](fleet.md)'s drift table
says how each repository spells it). Most also run `check-citation` and
`check-bugreports`.

Added by this standard: a URL check shaped like sitemapr's `urls` stage in
`tools/verify.R`. It fetches every URL the package declares and fails on a
dead one, because `--as-cran` reports a dead link only as a NOTE. It fails when
it checked zero URLs, and the only exemption is the `BugReports:` `/-/issues`
URL answering exactly 404 (SEOR-ocbtrrnl).

## Files every package carries

- `README.Rmd`, knitted into `README.md`.
- `CODE_OF_CONDUCT.md` and `CONTRIBUTING.md`.
- `SECURITY.md`, with a real contact and a real process.
- `SECURITY-INSIGHTS.yml`.
- `LICENSE` (the two-line CRAN stub) and `LICENSE.md` (the full MIT text, for
  the forge's license detector).
- `inst/CITATION`, `CITATION.cff`, `.zenodo.json` and `codemeta.json`.
- A root `ARCHITECTURE.md`. It may point into `docs/`.
- `.gitlab/issue_templates/` and `.gitlab/merge_request_templates/`.
- `NEWS.md`.

## `DESCRIPTION`

- `Authors@R`: Bart Turczynski, roles `aut`, `cre` and `cph`, with
  `comment = c(ORCID = "0000-0002-8788-7980")`. Third parties whose bundled
  code or data the package ships keep their own `cph` entry, as raddr's
  web-platform-tests contributors do.
- The `LICENSE` copyright holder is Bart Turczynski.
- The `cph` rule waits on the employer answer in SEOR-tahlljtx; if that answer
  changes it, this section and the per-package issues change with it.
- `URL:` lists, in this order, the Pages site
  (`https://bart-turczynski.gitlab.io/<pkg>/`), the GitLab project
  (`https://gitlab.com/bart-turczynski/<pkg>`), the r-universe page
  (`https://bart-turczynski.r-universe.dev/<pkg>`), and
  `https://CRAN.R-project.org/package=<pkg>` once the package is on CRAN.
- `Language: en-US`.

## Identities

The owner's identity decisions are recorded in SEOR-tahlljtx. What the fleet
uses, measured 2026-10-03:

- **Maintainer email:** `bartek@turczynski.pl`, in every `DESCRIPTION`.
- **Forge:** GitLab first. Account `bart-turczynski` on GitLab, and the same
  name on GitHub for the read-only mirrors. One account per service.
- **ORCID:** 0000-0002-8788-7980. The Zenodo "all software" badge searches on
  it.
- **Docs URL:** the GitLab Pages site, `https://bart-turczynski.gitlab.io/<pkg>/`.
- **r-universe:** `https://bart-turczynski.r-universe.dev`.
- **FOSSA:** the allocation above.

## Checking conformance

`scripts/check-fleet-standard.py` (SEOR-myokihrl, not yet written) will test a
repository against this file. Until it exists, conformance is checked by hand
against the sections above. What it checks, and how to run it, goes here when
it lands.
