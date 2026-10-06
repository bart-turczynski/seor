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
  value a job installs would depend on where each sits. It is written as a
  plain scalar, `PANDOC_VERSION: "3.10"`, or a shell assignment, never in
  GitLab's expanded form (a mapping with `value:`, block or flow), which
  `check-toolchain.R` does not read: it stops and asks for the plain scalar.
  It parses `.gitlab-ci.yml` with the R yaml package
  ([ADR 0009](adr/0009-check-toolchain-reads-the-ci-pin-with-yaml.md)), so
  a key in any mapping, quoted or not, block or flow, behind an alias or a
  merge key, is read, and so is a shell assignment in a script item,
  wherever sh starts a command (after `if`, `while`, `time` or a `case`
  pattern too). An input a `spec:` header declares is not a variable. It
  stops when the file does not load (a duplicate `PANDOC_VERSION` key
  included, which GitLab reads as the last), and the same way when
  `.gitlab-ci.yml` uses `$PANDOC_VERSION` but holds no pin it reads, such
  as one only in an included file. And it stops on any `PANDOC_VERSION`
  value set in a spelling it does not read, whatever pin it reads elsewhere
  and even when the value matches: a block scalar, a `!reference`, an empty
  or computed value, an `env`, `local`, `for` or `read` setting, or any
  mention under `eval` but a use (`eval "echo $PANDOC_VERSION"` sets
  nothing). A job's `env PANDOC_VERSION=3.9 sh install.sh` beside a global
  `PANDOC_VERSION: "3.10"` would read as 3.10 while that command installs
  3.9. A null value (`PANDOC_VERSION:` bare, `~` or `null`) sets no
  version.
- The `.deb` comes from the pandoc GitHub release
  (`https://github.com/jgm/pandoc/releases/download/<version>/pandoc-<version>-1-<arch>.deb`),
  and `sha256sum -c` checks it against the release's published digest before
  `dpkg -i` installs it over apt's `pandoc`. The install has one of two
  shapes, and each step runs only when the one before it succeeded:

  - one script item holding `if <download to FILE> && <sha256sum -c of FILE>
    && dpkg -i FILE; then apt-mark hold pandoc; …; else <warn>; fi`, on one
    line or in a `- |` block, as seor's `.r` does; or
  - three script items in that order: the download, the `sha256sum -c`, the
    `dpkg -i`, and `apt-mark hold pandoc` in an item after them. GitLab ends
    the job when an item fails, so a mismatch stops it before the install.

  Each step is one command or one pipeline, read by its last command, whose
  exit status is the pipeline's: `… | sha256sum -c -` is a check, `sha256sum
  -c … | tee log` is not. The check reads the pinned digest line that names
  FILE, the digest a literal or a variable: on stdin from `echo` or `printf`
  (`echo "<digest>  FILE" | sha256sum -c -`), or as a here-string. A digest
  computed in the step, a line fetched or selected at run time, and
  `sha256sum -c FILE` (which reads FILE as a list of sums) do not count
  (SEOR-ltseyxpe). Nothing else counts, however it is chained: not
  `|| true`, `;` or a newline inside one item, and not `set -e`, so the rule does not depend on how the runner
  starts the shell. In the first shape a failed or mismatched download
  warns and leaves apt's pandoc in place, so every gate still runs and
  reports ([ADR 0005](adr/0005-cheap-ci-jobs-fold-into-one-gates-job.md)), but
  nothing unverified is installed, and README drift reported after that
  warning is suspect; in the second it fails the job. The download has a time
  limit, so a stalled CDN reaches that warning instead of hanging every R
  job: curl with `--max-time`, which bounds one attempt, plus, when it uses
  `--retry` with a count above 0, `--retry-max-time`, which ends the retries
  and makes curl skip a retry whose `Retry-After` wait would pass it; or curl
  or wget under `timeout N`. A limit of 0 means none and does not count.
  Between retries curl waits its own backoff, which stops growing at 600
  seconds, or a fixed `--retry-delay`, which counts only up to 600 seconds.
  The retry count is not capped, since a count does not bound the waits a
  server's `Retry-After` asks for. wget counts only under `timeout`: its
  `--timeout` and `-T` limit idle time, not the download. seor's curl sets
  them all (`--retry 3 --retry-delay 5 --retry-max-time 300
  --connect-timeout 20 --max-time 120`).
- The install holds pandoc: `apt-mark hold pandoc` runs right after a
  successful `dpkg -i`, in the `then` branch or in a script item after the
  three. Without it the pin lasts only until a later apt step: where apt's
  candidate pandoc is newer than the pin, as Debian's is on `r-base:latest`
  (testing, at priority 990), an `apt-get install` or upgrade that reaches
  pandoc replaces the `.deb` (SEOR-vzupmeqj). Only the success path holds:
  a hold before the install, after `fi`, in the else branch or in an item
  after the `if` also runs on the warn path and holds apt's pandoc, and none
  of them counts, and neither does one after an apt install or upgrade in
  that path, which may already have replaced the `.deb`. The hold is
  `apt-mark hold` with `pandoc` among its packages (options such as `-qq`
  or `-o Key=Value`, other packages, and a `sudo`, `env` or variable
  prefix allowed), a command of its own in that branch or item, or the
  first of an `&&`/`||` list, not one inside a nested `if`, group or
  function. seor's writes `apt-mark hold pandoc || echo "WARNING: …"`: a
  hold that fails only warns, as the rest of the block does, so it never
  stops a gate.
  `echo pandoc hold | dpkg --set-selections` sets the same selection but is
  not read: write `apt-mark`. A bump needs nothing for the hold: an
  explicit `dpkg -i` ignores it (dpkg(1), "hold": "When these actions are
  requested explicitly, the hold package selection state always gets
  ignored") and leaves the package unheld, so the line after it holds the
  new version, and every CI job starts from a fresh image anyway.
- Locally, `scripts/check-toolchain.R` reads `PANDOC_VERSION` from
  `.gitlab-ci.yml` and fails the pre-push gate when
  `rmarkdown::pandoc_version()` differs. rmarkdown takes the newest pandoc on
  `RSTUDIO_PANDOC`, `PATH` and `~/opt/pandoc`, so a Homebrew upgrade past the
  pin otherwise knits a README that CI then reports as drift. Reading the
  variable from the environment is not that check: nothing sets it locally.
  It needs the R package yaml 2.2.1 or later, which rmarkdown and knitr
  already import, and stops in one line naming it when it is missing or
  older.
  The script is vendored: every package carries seor's copy byte for byte,
  so a change to it is copied into each repository.

A bump moves together, in one change per repository: `PANDOC_VERSION`, the
two sha256 digests (amd64, arm64), a re-knit of `README.md`, and, once for
the fleet, `PANDOC_PIN` in `scripts/check-fleet-standard.py`.

Each repository carries the install block in its own `.gitlab-ci.yml`; it
is not shared through a GitLab `include:` of seor's file. rurl's
`tools/local-ci-plan.R` reads the CI file without following `include:`, so
its local runs would lose the install, and a cross-project include makes
every package's pipeline depend on seor at CI time. The fleet checker keeps
the copies in step instead.

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

Also added: a generated-docs drift check (SEOR-nwfmerhu). A stale `.Rd` is
still valid `.Rd`, so lint, spelling and `R CMD check` all pass it; the logo
sweep left `man/<pkg>-package.Rd` stale in several packages with every gate
green. The check exports the commit being pushed (`PRE_COMMIT_TO_REF`, else
`HEAD`) with `git archive` into a throwaway directory, never the working
tree. There it runs roxygen2 at exactly the version `Config/roxygen2/version`
pins and fails, printing the diff, when `man/`, `NAMESPACE` or `DESCRIPTION`
differ from what is committed. It runs the checkout's copy of the check, and
seor's wrapper removes the export on every exit, signals included. CI runs it
too, under the pinned roxygen2, in each package's own job: a `docs-drift` job
in seor, rurl, pslr and ssrfr, the `gates` job in punycoder, pagerankr and
robotstxtr, `check:linux-release` in raddr and `check` in sitemapr
(2026-10-05, SEOR-fhrisfpt, SEOR-yufxgcre; robotstxtr's and sitemapr's on the
vendored script since 2026-10-06).

The check is one script: seor's `scripts/check-docs-drift.R`, which every
package vendors byte for byte at that path (SEOR-lyciowif). A fix goes into
seor's copy and is copied out, never into a fork. Its one argument is the
package directory (default `.`), and it reads no environment variable of its
own; where it runs, an export or a CI checkout used in place, is the caller's
choice. It exits 0 in sync and 1 on drift, and refuses with an R error when
roxygen2 is missing or not the pinned version, naming the install. git only
prints the diff: without git the report still lists the changed, missing and
stale files and says the diff is omitted. `--self-test` runs it on fixture
packages, with git and without. rurl, pslr, punycoder, raddr, pagerankr and
ssrfr vendor it (2026-10-05), and robotstxtr and sitemapr since 2026-10-06
(robotstxtr !53, sitemapr !88). Both were under a CRAN hold; the owner allowed
changes to their `.Rbuildignore`d tooling paths only, so nothing that ships
changed. robotstxtr's fork `dev/check-docs-drift.R` and sitemapr's in-place
`tools/check-docs.R` are gone (SEOR-lyciowif, SEOR-zxyztpbr).

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
- `NEWS.md`, its bullets per the NEWS rule in seor's `AGENTS_LANG.md`: only
  changes a package user notices, one terse line each, no housekeeping.

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
  The files' metadata (every link, the screen-reader description "Logo of
  the <pkg> library for R, white text on a black background", and the
  Dublin Core, XMP, IPTC, PLUS and EXIF fields) is written by seor's
  `scripts/logo-metadata.py` from one table, never by hand; `--check`
  reports drift (SEOR-eyfiidrv), and the fleet checker runs that same check
  on each package's `logo.svg` and `logo.png` (SEOR-seobtecv).
  The keywords (XMP and RDF `dc:subject`, PNG Keywords, EXIF XPKeywords)
  come from the package's `DESCRIPTION`, not from that table: the
  `X-schema.org-keywords` tags r-universe indexes, written verbatim after
  the fixed prefix "R", "rstats", "R package", with duplicates dropped
  case-insensitively (SEOR-qoqmestu). A package without that field gets no
  logo metadata until it has one. The tag `seo`, in any case, belongs to
  seor and its members only; the script refuses it on any other package.
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
file and prints a gap table per package. Run it from seor, with a Python that
has PyYAML (`python3 -m pip install pyyaml==6.0.3`, the version the pre-push
hook pins; ADR 0008). Without PyYAML it exits 2 with that hint:

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
not judged. It exits 1 on any gap, and 2 when there is no gap but the run is
incomplete: a probe failed, a file could not be read, `.gitlab-ci.yml` did not
load, or a pandoc pin assignment sits where the script cannot see. Each of
those is listed as not judged, never as a gap. What `--offline` leaves out is
listed too, but leaves the run complete.

It reads `.gitlab-ci.yml` with PyYAML, as YAML 1.1 (an unquoted `3.10` is
3.1), and resolves `extends:`, `default:`, `inherit:` and the rules as GitLab
does. The file is one config document, or a `spec:` header document and then
the config. A file that does not load, an unknown tag such as `!reference`, a
value its tag cannot hold, a recursive alias, an `extends:` that names no
block, or a `rules:if` that does not read (an empty one included) leaves every
CI rule of that package not judged; the other areas are still judged.
`include:` is not followed.

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
  that replaces or hides it. `logo.svg` and `logo.png` pass
  `scripts/logo-metadata.py --check`, run on the files as read: each is
  byte for byte what the script writes, so a `logo.png` left behind when
  `logo.svg` was regenerated, or any field edited by hand, is a gap
  (SEOR-seobtecv). When the keywords are what differs, the gap names the
  missing and extra tags (SEOR-uwpnkqnb). The artwork is not judged.
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
  trailing comment (GitLab's expanded `value:` form is reported, and so is
  any value set in a spelling `check-toolchain.R` does not read and stops on,
  such as a block scalar, a `!reference`, a computed or empty value, or, in
  a script, any mention of the name that is not the pin, a use, a bare
  `export` or a comment, echoed text included
  ([ADR 0010](adr/0010-check-toolchain-allows-shell-mentions-it-reads.md)), as its
  `--pandoc-unread` names the lines, each to be rewritten as a plain scalar,
  the expanded form among them where it sits deeper than the global or a
  job's own `variables:`, such as in a `rules:` entry, and a file its YAML parser does not load though PyYAML does, such as one
  with a duplicate key), one value wherever it is assigned, in a line
  the job sees, and never in a `parallel: matrix` entry, which pins per leg. An
  assignment is one sh would run and keep for the commands after it, plain
  or through `export`, `readonly`, `declare` or `typeset`: not the same text
  in a comment (in an `echo` or a here-document it is refused), and not one anywhere in a
  subshell, a pipeline stage or a backgrounded compound command, or in a
  command's prefix (`PANDOC_VERSION=3.10 curl …`). One in a function's body,
  or under `eval`, `sh -c` or `$(...)`, is not judged. The pin is read by
  running `check-toolchain.R`'s own reader
  (`--pandoc-assignments`), so the two scripts cannot disagree on it; that
  needs `Rscript`, run with `--no-save --no-restore --no-init-file` so that
  `~/.Renviron` (and a library such as `R_LIBS_USER` set there) is read and
  `~/.Rprofile` is not. The install has one of the two shapes above, read
  from the job's script items (a `- |` block, a folded or plain item, or a flow
  sequence `[a, b]`): curl or wget saves the `.deb` to a file, a `sha256sum
  -c` (or `shasum -a 256 -c`) reads a pinned digest line naming that file
  (from `echo` or `printf`, or a here-string), and `dpkg -i` installs that
  same file, paths compared as whole words; a checksum of some other
  download, a checked `.deb` never installed, a step that goes on when the
  one before it failed, and a download with no time
  limit do not count. An install with no `apt-mark hold pandoc` where only
  its success leads (the `then` branch, or an item after the three) is a gap
  of its own, naming the line to add; a download with no time limit is
  reported first. The install counts only in the `before_script` or
  `script` the job ends up with, its own or its template's; one only in
  `default: before_script` is reported, to move into the template. A job's
  commands are read as text, together with the variables it sees and the R,
  shell and YAML scripts that text names, so `--as-cran` passed in `$ARGS`
  counts, and a script that skips a gate it contains reads as running it. A
  setting such as `_R_CHECK_CRAN_INCOMING_` is off as R reads it: `false`,
  `no` or `0`, in any case.
- **Local gate.** The pre-commit config, or an R or shell script its hooks
  call, runs a URL check, and one such script both calls
  `rmarkdown::pandoc_version()` and reads `PANDOC_VERSION` from
  `.gitlab-ci.yml`: the comparison with the CI pin. A `pandoc_version()` call
  alone, such as a minimum-version check, is not it, and neither is
  `Sys.getenv("PANDOC_VERSION", …)`. `scripts/check-toolchain.R` is
  there and matches seor's copy (line endings aside). The docs-drift check: some script in
  that chain runs roxygen2 (`roxygenise` or `roxygenize`) and some script
  runs `git archive`. That the two belong together, and that it diffs, is a
  review item. `scripts/check-docs-drift.R` is there and matches seor's
  copy (line endings aside); a missing copy is a gap too.
- **Schedules.** One active `deep-check` and one `dependency-audit` schedule,
  on `main`, with `SCHEDULE_KIND` set on each schedule.

It does not check whether a tag pipeline fails on "already on CRAN", how the
URL check treats zero URLs or the `BugReports:` 404, how `security-audit`
treats missing OSS Index credentials, the GitLab project badges, or employer
names. Review those by hand. The pre-push hook runs `--self-test`, in an
environment with the pinned PyYAML, whenever the script or `check-toolchain.R`
changes.
