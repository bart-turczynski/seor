# Fleet standard

What every R package in the fleet carries: the README badge row and contents,
the CI and scheduled pipelines, the local gate, the files, the `DESCRIPTION`
fields, the r-universe metadata and the identities behind them. The owner asked on 2026-10-03 for the same badges
and checks in all nine packages (SEOR-plnwieyf). Each package's "meets the
fleet standard" issue cites this file instead of restating it.
[ADR 0007](adr/0007-one-fleet-standard-for-badges-and-checks.md) records why
the load-bearing choices went the way they did.

This is a living reference. Edit it when a fact changes. A change to a choice
ADR 0007 records needs a new ADR first.

**Scope (owner, 2026-10-03).** These are single-maintainer hobby projects. The
point is that all nine look and work the same; best effort is enough. Meet the
standard and stop there: no extra process, no polish beyond it. Where the
standard and a package's own habits differ, align the package; where meeting
a rule would take disproportionate work, say so on the package's issue and
move on.

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
[![FOSSA license](https://app.fossa.com/api/projects/custom%2B62973%2Fgit%2Bgitlab.com%2Fbart-turczynski%2F<pkg>.svg?type=shield&issueType=license)](https://app.fossa.com/projects/custom%2B62973%2Fgit%2Bgitlab.com%2Fbart-turczynski%2F<pkg>?ref=badge_shield&issueType=license)
[![FOSSA security](https://app.fossa.com/api/projects/custom%2B62973%2Fgit%2Bgitlab.com%2Fbart-turczynski%2F<pkg>.svg?type=shield&issueType=security)](https://app.fossa.com/projects/custom%2B62973%2Fgit%2Bgitlab.com%2Fbart-turczynski%2F<pkg>?ref=badge_shield&issueType=security)
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
- **The FOSSA locator carries the organization.** Measured 2026-10-03 on
  rurl's first `fossa analyze` (job 16914055629, fossa-cli 3.20.0, green):
  the upload landed under `custom+62973/git+gitlab.com/bart-turczynski/rurl`,
  62973 being the account's FOSSA organization. The badge under that locator
  answers 200; the bare `git+gitlab.com/...` form answers 404. ssrfr's and
  seor's projects appear when their first `fossa analyze` job uploads.

## README contents

The README is for users, and for the agents that read it for them. pkgdown
2.2 builds each site's `llms.txt` from the README, followed by the reference
and article indexes, so whatever the README says reaches an agent asked to
"install this" (SEOR-krxsaudb). Maintainer notes in it reach the agent too:
raddr's `llms.txt` carried its Setup and Verification sections on 2026-10-04.

`README.Rmd` carries, in this order:

1. The heading with the logo (see r-universe, below), in this form:

   ```markdown
   # <pkg> <img src="man/figures/logo.png" align="right" height="139" alt="hex logo, white on black" />
   ```

2. The badge row (above).
3. A short what and why: what the package does and who it is for, in a
   paragraph or two.
4. `## Installation`, with copy-paste commands:
   - `install.packages("<pkg>")` once the package is on CRAN;
   - the r-universe command, always:

     ```r
     install.packages(
       "<pkg>",
       repos = c("https://bart-turczynski.r-universe.dev", "https://cloud.r-project.org")
     )
     ```

   - the system requirements a source install needs, such as libidn2 for
     punycoder's native backend or a C++17 toolchain for robotstxtr.
5. A small example.
6. Links to the vignettes or the pkgdown site.

Other user-facing sections (how it compares, citation, code of conduct,
license) may follow. A section repeating the reference index, such as a table
of every exported function, adds nothing: `llms.txt` already appends that
index.

**Not in the README.** Maintainer content goes to `CONTRIBUTING.md`,
`ARCHITECTURE.md`, `design/` or a vignette. The checker treats these headings,
at any level, as maintainer content: Setup, Development, Verification,
Project or Repository layout or structure, Current state, Status and
Dependencies. A "Dependencies" section that a user needs belongs inside
Installation as system requirements. A function index is a reference index
under another name: Function overview and Key functions are banned too.

**`llms.txt`.** It is the pkgdown site's job. No package keeps a hand-written
`llms.txt` at its root, and the pkgdown config never turns `llm-docs` off.
`https://bart-turczynski.gitlab.io/<pkg>/llms.txt` answered 200 for all nine
packages on 2026-10-04.

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

**pandoc 3.10, pinned in the shared R setup.** pandoc's markdown writer
reflows text and pads tables differently between versions, so `README.md` is
byte-stable only under the pandoc that knit it, and the README drift gate is
only as good as the pin (SEOR-egfbijyi). apt's pandoc on the CI images is
3.1.3; it reported drift in seor's README that 3.10 does not write.

- Every job that runs R installs pandoc 3.10 in the setup they share: the
  `before_script` of the template every R job extends. seor's `.r` template
  is the model. One job pinning it for the readme gate is not enough: the
  check, `coverage` and `pages` jobs render with it too. Not in `default:`:
  the install needs Debian, `dpkg` and `curl`, and `default:` hands it to
  every job, including ones on other images (seor's `citation-version` runs
  on `python:3.13-alpine`).
- The version is recorded once, as the `PANDOC_VERSION` CI variable. A
  second assignment with another value, in any job, is a defect even where it
  would win: a shell assignment overrides `variables:` at run time, so which
  value a job installs would depend on where each sits.
- The `.deb` comes from the pandoc GitHub release
  (`https://github.com/jgm/pandoc/releases/download/<version>/pandoc-<version>-1-<arch>.deb`),
  and `sha256sum -c` checks it against the release's published digest before
  `dpkg -i` installs it over apt's `pandoc`. The install has one of two
  shapes, and each step runs only when the one before it succeeded:

  - one script item holding `if <download to FILE> && <sha256sum -c of FILE>
    && dpkg -i FILE; then …; else <warn>; fi`, on one line or in a `- |`
    block, as seor's `.r` does; or
  - three script items in that order: the download, the `sha256sum -c`, the
    `dpkg -i`. GitLab ends the job when an item fails, so a mismatch stops
    it before the install.

  Each step is one command or one pipeline, read by its last command, whose
  exit status is the pipeline's: `… | sha256sum -c -` is a check, `sha256sum
  -c … | tee log` is not. The check names FILE, or reads on stdin the digest
  line that names it (`echo "<digest>  FILE" | sha256sum -c -`). Nothing else
  counts, however it is chained: not `|| true`, `;` or a newline inside one
  item, and not `set -e`, so the rule does not depend on how the runner
  starts the shell. In the first shape a failed or mismatched download
  warns and leaves apt's pandoc in place, so every gate still runs and
  reports ([ADR 0005](adr/0005-cheap-ci-jobs-fold-into-one-gates-job.md)), but
  nothing unverified is installed, and README drift reported after that
  warning is suspect; in the second it fails the job. The download has a time
  limit (curl `--max-time`, wget `--timeout` with `--tries` of 5 or fewer,
  or `timeout`), so a stalled CDN reaches that warning instead of hanging
  every R job. A limit of 0 means none and does not count, and wget's own
  default of 20 tries makes its `--timeout` a limit per try, not on the
  download. seor's curl also retries, with the retries bounded too
  (`--retry 3 --retry-delay 5 --retry-max-time 300 --connect-timeout 20
  --max-time 120`).
- Locally, `scripts/check-toolchain.R` reads `PANDOC_VERSION` from
  `.gitlab-ci.yml` and fails the pre-push gate when
  `rmarkdown::pandoc_version()` differs. rmarkdown takes the newest pandoc on
  `RSTUDIO_PANDOC`, `PATH` and `~/opt/pandoc`, so a Homebrew upgrade past the
  pin otherwise knits a README that CI then reports as drift. Reading the
  variable from the environment is not that check: nothing sets it locally.

A bump moves together, in one change per repository: `PANDOC_VERSION`, the
two sha256 digests (amd64, arm64), a re-knit of `README.md`, and, once for
the fleet, `PANDOC_PIN` in `scripts/check-fleet-standard.py`.

Every pipeline a schedule creates on `main`, `deep-check` and
`dependency-audit` alike, runs the coverage job too. The coverage badge reads
the latest successful pipeline on `main`, so a green schedule pipeline without
it turns the badge "unknown" (pslr and raddr, 2026-10-03). The fleet runs the
other push-to-`main` jobs there as well.

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

A project lives under `custom+62973/git+gitlab.com/bart-turczynski/<pkg>`,
the locator `fossa analyze` uploads to with the account's API key.
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

Also added: `check-toolchain`'s pandoc check, which compares the local pandoc
with the CI pin (see the pandoc rule under "CI on every push to `main`").

## Files every package carries

- `README.Rmd`, knitted into `README.md`.
- `CODE_OF_CONDUCT.md` and `CONTRIBUTING.md`. `CONTRIBUTING.md` opens with
  seor's two opening paragraphs, the package name swapped in: where to report
  bugs, security issues privately per `SECURITY.md`, changes as GitLab merge
  requests (the GitHub copy is a read-only mirror), new code needs tests, a
  `NEWS.md` bullet per user-facing change, and the verify command must pass.
  The OpenSSF `contribution` criterion reads that paragraph.
- `SECURITY.md`: ssrfr's, the package name swapped in (email
  `bartek@turczynski.pl`, or a confidential GitLab issue). The same text in
  every package; the OpenSSF vulnerability-reporting criteria read it.
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
- No employer appears as copyright holder or funder (owner, 2026-10-03,
  SEOR-tahlljtx), although some past commits used a work address.
- `URL:` lists, in this order, the Pages site
  (`https://bart-turczynski.gitlab.io/<pkg>/`), the GitLab project
  (`https://gitlab.com/bart-turczynski/<pkg>`), the r-universe page
  (`https://bart-turczynski.r-universe.dev/<pkg>`), and
  `https://CRAN.R-project.org/package=<pkg>` once the package is on CRAN.
- `Language: en-US`.
- `X-schema.org-keywords` (see r-universe, below).

## r-universe

The fleet builds on `https://bart-turczynski.r-universe.dev` from GitLab,
under the owner `gitlab-bart-turczynski`. Researched 2026-10-04
(SEOR-rpklojdh, <https://docs.r-universe.dev/publish/metadata.html>):

- **The `URL:` entry is load-bearing.** Packages built from GitLab appear in
  the universe's search only because `DESCRIPTION` `URL:` names
  `https://bart-turczynski.r-universe.dev/<pkg>`. Dropping that entry hides
  the package, even though it still builds.
- **Keywords come only from `X-schema.org-keywords`.** GitHub topics apply
  only to GitHub-hosted packages, and the read-only mirror is not where the
  registry builds from. Every package declares the field: at least five
  specific, comma-separated tokens, five to ten being the aim. r-universe drops
  `r`, `rstats`, `r-stats` and `r-package`, so none of them counts and none is
  listed. Writing R Extensions §1.1.1 allows extra `DESCRIPTION` fields, and
  the CRAN copies of rurl, punycoder, pslr and raddr already carry this one.
  An edit reaches CRAN only with that package's next release.
- **Logo.** One fleet look, chosen by the owner on 2026-10-04
  (SEOR-wxjuxbtu): a black hex with the package name set in IBM Plex Mono.
  Each package carries `man/figures/logo.svg` and `man/figures/logo.png`.
  r-universe shows the logo on the package card and in search, and pkgdown
  puts it in the site header; both find it there. The source artwork, with
  `logo-480.png` and `logo-print.svg`, stays outside the repositories.
  The README heading's `<img>` carries `alt="hex logo, white on black"`,
  without the package name. The `<img>` sits inside the `# <pkg>` heading,
  so its alt joins the heading's accessible name, which reads "<pkg> hex
  logo, white on black" with the name once. GitLab and GitHub wrap a README
  image in a link to the file, and the alt is that link's name, so it is not
  empty. pkgdown replaces the heading's logo with its own, `alt=""`, in the
  site header (SEOR-wfleahtg).
  `man/figures/` ships in the tarball, so a package on hold for CRAN adds its
  logo only after the accepted release.

## Identities

The owner decided these on 2026-10-03 (SEOR-tahlljtx):

- **Email:** `bartek@turczynski.pl` is the public contact and the commit
  address for new commits: `DESCRIPTION` Maintainer, `SECURITY.md`, the Code
  of Conduct contact, and the global git `user.email`. There is no separate
  security alias. Commit history stays as it is.
- **Forge:** GitLab first. Account `bart-turczynski` on GitLab. GitHub, under
  the same name, is used only for the read-only mirror, Zenodo (DOIs through
  mirror releases) and the r-universe registry; no badge reads from it. One
  account per service, reused for every package.
- **ORCID:** 0000-0002-8788-7980. The Zenodo "all software" badge searches on
  it.
- **Docs URL:** the GitLab Pages site, `https://bart-turczynski.gitlab.io/<pkg>/`.
- **r-universe:** `https://bart-turczynski.r-universe.dev`.
- **FOSSA:** the allocation above.

## Checking conformance

`scripts/check-fleet-standard.py` (SEOR-myokihrl) tests packages against this
file and prints a gap table per package. Run it from seor:

```sh
python3 scripts/check-fleet-standard.py                  # all nine
python3 scripts/check-fleet-standard.py --repo rurl      # one package
python3 scripts/check-fleet-standard.py --repo rurl --local ~/Projects/rurl
python3 scripts/check-fleet-standard.py --repo rurl --local ~/Projects/rurl --offline
python3 scripts/check-fleet-standard.py --self-test      # offline fixtures
```

By default it reads each package's `main` on GitLab through `glab api`, since
a local checkout may be stale. `--local` reads a checkout's files instead and
still asks GitLab and the web for live state. `--offline` touches no network:
the badge images, the conditional slots and the schedules are then listed as
not judged. It exits 1 on any gap, and 2 when there is no gap but a probe
failed, so the run is incomplete. A network failure is never a gap.

What it checks, section by section:

- **Badge row.** Every slot the package's live state calls for, in order, and
  nothing else, with image and link URLs matched against the templates (the
  per-package values as patterns). It reads the CRAN state from crandb, the
  GitLab Release from the releases API, the DOI from `CITATION.cff` (doi.org
  must resolve it and Zenodo must call it the concept DOI), and the FOSSA
  project from its badge endpoint under the `custom+62973` locator. A badge shown while its condition does not
  hold is a gap. So is a package missing from r-universe.
- **Badge images.** Each image answers 200 and does not read "unknown", "not
  found", "invalid", "not set up", "inaccessible" or "no releases found".
- **README.** `README.Rmd` has an `## Installation` section that holds the
  r-universe command (an `install.packages()` call naming
  `bart-turczynski.r-universe.dev`) and, on CRAN only,
  `install.packages("<pkg>")`. No heading outside code chunks is one of the
  banned ones. No root `llms.txt`, and `llm-docs` is not off in any pkgdown
  config file.
- **Logo.** `man/figures/logo.svg` and `man/figures/logo.png` exist, and the
  first level-1 heading of `README.Rmd` is `# <pkg>` with an `<img>` whose
  `src` is `man/figures/logo.png` (bare, or inside a link as
  `usethis::use_logo()` writes it) and whose `alt` is `hex logo, white on
  black`, with no `aria-label`, `aria-labelledby`, `aria-hidden` or `role`
  that replaces or hides it. The artwork is not judged.
- **Files.** The list above. `LICENSE` names Bart Turczynski, `LICENSE.md` is
  the MIT text, `SECURITY.md` and `CODE_OF_CONDUCT.md` name the public email,
  and a `SECURITY.md` under ten non-blank lines counts as a stub.
- **`DESCRIPTION`.** The aut, cre and cph roles, the ORCID, the email, `URL:`
  in order, `Language: en-US`, a declared R floor, and
  `X-schema.org-keywords` with at least five tokens besides the four
  r-universe drops, and none of those four.
- **CI.** It evaluates `workflow:` and job `rules:` for a push to `main`, each
  schedule kind and a tag. On a push it looks for `R CMD check --as-cran`
  through `rcmdcheck` with `error_on = "warning"`, with incoming off only as
  ADR 0004 allows. It also looks for a coverage job with a regex, a cobertura
  report, a threshold of at least 95 and no `allow_failure`, that runs on both
  schedule kinds as well, for `pages`, and for the cheap gates. On the
  `deep-check` schedule alone it wants release, oldrel, devel and floor legs,
  read from image tags, plus sanitizer legs where required. The audits run on the `dependency-audit` schedule alone, with
  seor's disposition-row test files, and `fossa analyze` runs where FOSSA is
  allocated. Every job that runs R on a push downloads pandoc from its GitHub
  release at `$PANDOC_VERSION`, which `.gitlab-ci.yml` sets to 3.10 in a
  `variables:` entry or a shell assignment, quoted or not, with or without a
  trailing comment, one value wherever it is assigned, in a line the job
  sees, and never in a `parallel: matrix` entry, which pins per leg. An
  assignment is one sh would run, not the same text in a comment or an
  `echo`. The pin is read by running `check-toolchain.R`'s own reader
  (`--pandoc-assignments`), so the two scripts cannot disagree on it; that
  needs `Rscript`. The install has one of the two shapes above, read from the
  job's script items (a `- |` block, a folded or plain item, or a flow
  sequence `[a, b]`): curl or wget saves the `.deb` to a file, a `sha256sum
  -c` (or `shasum -a 256 -c`) names that file, and `dpkg -i` installs that
  same file, paths compared as whole words; a checksum of some other
  download, a checked `.deb` never installed, a step that goes on when the
  one before it failed, and a download with no time
  limit do not count. The install counts only in the `before_script` or
  `script` the job ends up with, its own or its template's; one only in
  `default: before_script` is reported, to move into the template. A job's
  commands are read as text, along with the R, shell and YAML scripts it
  names, so a script that skips a gate it contains reads as running it.
- **Local gate.** The pre-commit config, or an R or shell script its hooks
  call, runs a URL check, and one such script both calls
  `rmarkdown::pandoc_version()` and reads `PANDOC_VERSION` from
  `.gitlab-ci.yml`: the comparison with the CI pin. A `pandoc_version()` call
  alone, such as a minimum-version check, is not it, and neither is
  `Sys.getenv("PANDOC_VERSION", …)`.
- **Schedules.** One active `deep-check` and one `dependency-audit` schedule,
  on `main`, with `SCHEDULE_KIND` set on each schedule.

It does not check whether a tag pipeline fails on "already on CRAN", how the
URL check treats zero URLs or the `BugReports:` 404, how `security-audit`
treats missing OSS Index credentials, the GitLab project badges, or employer
names. Review those by hand. The pre-push hook runs `--self-test` whenever the
script changes.
