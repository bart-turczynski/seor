---
status: accepted
date: 2026-10-29
tracking: SEOR-tirszysv
---

# ADR 0012: verification tiers replace per-push CI in the fleet standard

## Context

The maintainer's goal for the fleet's R packages has three parts: a very
thorough check before any CRAN submission, quality code in between, and tests
aimed at what a change can actually break. Until now the fleet standard
([`fleet-standard.md`](../fleet-standard.md)) pursued that by running the
whole CI suite on every push to `main`: `R CMD check --as-cran`, coverage, the
pkgdown `pages` deploy and the cheap gates
([ADR 0004](0004-cran-incoming-runs-everywhere-except-seor.md),
[ADR 0005](0005-cheap-ci-jobs-fold-into-one-gates-job.md),
[ADR 0007](0007-one-fleet-standard-for-badges-and-checks.md)).

Measured through the GitLab jobs API over 2026-09-29 to 2026-10-29:

- The R packages used about 8,800 CI job-minutes a month, all on self-hosted
  runners on the maintainer's laptop
  ([ADR 0003](0003-fleet-ci-runs-on-self-hosted-runners.md)).
- 551 push pipelines on `main` took 63% of those minutes.
- Many merges touched only `design/`, `worklog/`, `.fp/` or agent files: 67 of
  156 in rurl, 69 of 84 in seor, 37 of 59 in ssrfr. Each still ran the full
  suite.
- Setup (image pull, dependency install, cache restore) was 33% to 77% of each
  job.
- The weekly schedules re-ran the push suite on commits that had already
  passed it ([`fleet.md`](../fleet.md), "Kept for now").
- The same tree was checked about five times per merge: the pre-push hook on
  the branch, again on `main`, then the CI check, coverage and pages jobs.
- Nine hand-copied `.gitlab-ci.yml` files were kept in step by a large checker
  (`scripts/check-fleet-standard.py`) instead of by shared templates.

So most of the minutes went to re-checking trees that nothing had changed in a
way the check could see, while the release-shaped checks (old R, the floor,
sanitizers, URLs) ran only weekly.

## Decision

Verification runs in four tiers. The tier is chosen by what the change can
break and by the event, not by "a push happened".

| Tier | Trigger | Where | What runs |
|------|---------|-------|-----------|
| T0 docs | a push whose diff the classifier calls docs-only | pre-push hook | lint and fixers, spelling, docs drift, `pkgdown::check_pkgdown()` |
| T1 merge | any other push to `main` | pre-push hook, in the shared fleet image | the cheap gates, one `R CMD check` (`NOT_CRAN=true`; no incoming, no remote, no manual) and positive locale assertions |
| T2 weekly | the weekly schedule on `main` | CI | the R release, oldrel and devel matrix, the floor, sanitizers, the full locale legs, `--as-cran` with incoming and URLs, coverage of at least 95%, the audits |
| T3 release | before any CRAN submission, alongside `/cran`; and after acceptance, on the `v*` tag | CI | T2 plus the PDF manual, plus the `pages` deploy from a `v*` tag only |

T1 is the `Gate: local` merge gate of the `agent-workflow` skill: the full
local gate, run in a container from the shared fleet image so that it does
not depend on the maintainer's R library.

### The classifier

T0 applies only when a fail-closed classifier says the diff is docs-only. Any
path it does not know, a deletion, a rename, a type change, a missing base or
an empty diff classifies as full, so the push gets T1.

### The pass stamp

A passing local gate writes a stamp keyed on the tree, the classifier
version, the image digest and the hash of the resolved dependency lock. A
stamp matching all four lets a later push of the same tree skip the re-run;
any difference re-runs the gate.

### Shared templates and images

The CI templates and images live in fleet-ci, a public GitLab repository,
`bart-turczynski/fleet-ci` (being set up). Its own CI runs only its
self-tests, on GitLab shared runners. Each package pins fleet-ci by commit
SHA, which is immutable. The image digests are written in the template at that
SHA, so the one pin fixes both the template and the images. The images are
`registry.gitlab.com/bart-turczynski/fleet-ci/<variant>`, the variants being
`fleet-r`, `fleet-r-tex` and `fleet-r-idn2`.

An image rebuild is a deliberate fleet-ci change that publishes new digests
in the template. A package moves to them by bumping its fleet-ci SHA, never by
a floating tag.

### Which event runs what

Deny by default. The rows are evaluated in this order, and the first match
decides:

| Event / condition | Pipeline |
|-------------------|----------|
| `RELEASE=1` and `PAGES=1` together, on any event | rejected: the pipeline fails or does not run |
| Push to `main` | none |
| Schedule, `SCHEDULE_KIND=deep-check` | T2 |
| Schedule, `SCHEDULE_KIND=rurl-devel` (pagerankr only, the one allowed schedule exception) | its suite against rurl's `main` HEAD, plus `coverage` |
| Schedule, `SCHEDULE_KIND=dependency-audit`, any other value, or none | none (the audits run in T2) |
| Tag push `v*` | full T3: release checks and the `pages` deploy (post-acceptance verification and publication) |
| Web, `RELEASE=1`, on a `v*` tag ref | full T3, including the `pages` deploy |
| Web, `RELEASE=1`, on the default branch (`CI_COMMIT_BRANCH == CI_DEFAULT_BRANCH`) | release checks (T2 including `coverage`, plus `t3-manual`), no `pages` deploy: the owner-run pre-submission run |
| Web, `PAGES=1`, on a `v*` tag ref | `pages` only |
| Anything else (merge request events, pushes to other branches, API, web without an admitted mode and ref) | none |

The schedules select on the `SCHEDULE_KIND` variable they already set, so no
schedule object changes. A `dependency-audit` schedule left in place creates
no pipeline.

**The pre-submission identity rule.** The release candidate is the pipeline's
`CI_COMMIT_SHA`. The release-checks pipeline must pass for that exact SHA,
that same commit is submitted, and after acceptance the SHA recorded in
`CRAN-SUBMISSION` is tagged. A pass on an earlier commit of `main` does not
authorize submitting a newer one.

**`pages` publishes the released version.** It deploys only from a `v*` tag,
so the site describes what CRAN serves, not the tip of `main`.

**Every pipeline on `main` carries `coverage`.** The coverage badge reads the
latest successful pipeline on `main`, so a pipeline there without the job
would turn it "unknown".

### Job names

The template's jobs have fixed names: `t2-check-release`, `t2-check-oldrel`,
`t2-check-devel`, `t2-floor`, `t2-sanitizers`, `t2-locale`, `t2-ascran`,
`coverage`, `osv-audit`, `security-audit`, `t3-manual`, `pages` and
`citation-version`. `coverage`, `pages`, `osv-audit` and `security-audit` keep
today's names because badges and test messages name them (ssrfr's
`tests/testthat/test-security.R` names `security-audit`).

### What a package may vary

Capability switches are template-owned variables: `FLEET_SANITIZERS`,
`FLEET_FLOOR`, `FLEET_LOCALE`, `FLEET_DEVEL` and `FLEET_MANUAL`, each `"true"`
or `"false"`, with defaults in the template. The template's rules read them. A
package sets the variables; it never writes `rules` or `when`.

A package may add jobs named `x-*` that extend `.t2-job` or `.t3-job` and
inherit their rules. The ones known now:

- `x-fossa` in rurl, seor and ssrfr. `fossa analyze` moves from push time to
  the weekly and release runs, so a FOSSA project is refreshed at most weekly
  and at each release, not on every merge.
- pagerankr's rurl-devel suite, as `x-rurl-devel`. The template admits it
  on the `rurl-devel` schedule, the one schedule exception in the event table
  below.
- ssrfr's `renovate` job, as `x-renovate`. Today it runs on the `deep-check`
  schedule or by hand; it moves into the T2 runs.

### What this replaces in ADRs 0004, 0005 and 0007

All three are marked superseded, because the design check has no partial
form. This ADR carries forward what still holds:

- **ADR 0004.** Replaced: the rule that incoming feasibility runs in the
  pre-push verify gate and the CI job running the same chain. The local gate
  now runs `R CMD check` with no incoming, and incoming feasibility
  (`_R_CHECK_CRAN_INCOMING_`, remote half included) moves to T2 and T3, in
  `t2-ascran`. Still in force there: seor's named exception and its reason (it
  lapses when the members reach CRAN), suppressing the remote half counts as
  suppression, hand-run floor scripts stay out of scope, and the logged and
  asserted effective setting now applies to `t2-ascran`.
- **ADR 0005.** Replaced: the per-push `gates`, `check`, `coverage` and
  `pages` jobs. The cheap gates move into the local gate (T0 and T1); `check`
  becomes the T2 and T3 legs; `coverage` and `pages` run only where the event
  table says. Still in force: the harness runs every gate and then reports
  all failures, `citation-version` keeps its own job, and folding jobs folds
  images.
- **ADR 0007.** Replaced: only where its coverage gate and floor leg run,
  which was each package's own per-push and `deep-check` CI. Still in
  force: the coverage bar of at least 95% as a failure, never lowered (now in
  `coverage`, which every pipeline on `main` carries), the measured R floor
  (now `t2-floor`), the full badge set, the FOSSA allocation, the reversal of
  sitemapr's no-CI-badges rule and Best Practices at passing.

### Scope

This ADR describes the target state, which fleet-ci and the per-package
migrations implement. Until a package migrates, its current CI stays as it
is, and [`fleet-standard.md`](../fleet-standard.md) says which rules apply to
an unmigrated package.

Out of scope: moving the runners off the laptop, the non-R repositories,
the stages of `/cran`, and the 95% coverage bar itself.

## Consequences

- **A push to `main` creates no pipeline.** The local gate is the only check
  a merge gets, so it must run in the fleet image, not against whatever the
  maintainer's library holds. The pipeline badge on `main` now reports the
  latest weekly or release pipeline.
- **Docs-only merges cost a docs check, not an `R CMD check`.** The
  classifier fails closed, so a misclassification costs minutes, never a
  missed check.
- **The release-shaped checks run on every release candidate.** Old R, the
  floor, sanitizers, URLs and the PDF manual run for the exact commit
  submitted, not only on the last weekly run.
- **A dependency that moves breaks `main` silently for up to a week.** The
  weekly T2 run is the re-check of `main` against moved dependencies; a red
  T2 is a finding, not noise.
- **The site lags `main`.** pkgdown pages show the released version until the
  next `v*` tag.
- **One template, not nine files.** A CI change lands once in fleet-ci and
  reaches each package through a SHA bump. A package that writes `rules` or
  `when`, or names a job outside the fixed set and the `x-*` prefix, breaks
  the standard.
- Do not add a pipeline on push to `main` back, or let a schedule re-run the
  merge gate, without a new ADR. Revisit if the runners move off the laptop
  (setup cost and contention change), or if T2 regularly finds what a T1
  check could have caught at merge.
