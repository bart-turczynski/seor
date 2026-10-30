# Continuous integration

seor runs fleet-ci's tiered CI ([ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md))
since the fleet-ci migration (`SEOR-hqiiccma`, 2026-10-30). `.gitlab-ci.yml`
includes fleet-ci's `templates/r-package.yml`, pinned by commit SHA (v1.2.4),
and sets only package variables plus two `x-*` jobs, `x-floor` and `x-fossa`;
`.fleet-ci.yml` holds the local gate's settings, and `.fleet-ci/` is
fleet-ci's vendored gate (re-run fleet-ci's `bin/vendor`, never edit it). The
job names below are the template's. The former shape was a `verify` pre-push
hook (lintr plus `R CMD check --as-cran`) with `docs-drift`, `check-urls` and
`spelling` hooks beside it, and a pipeline on every push to `main` running
`verify`, `citation-version`, `gates` (`scripts/gates.sh`), `coverage`,
`docs-drift`, `pages` and `fossa`.

| Tier | Where | What runs |
| --- | --- | --- |
| hygiene hooks | pre-commit, at commit and at push | `.pre-commit-config.yaml`. At commit: the whitespace fixers (`.fleet-ci/` excluded), the large-file, merge-conflict, YAML and case-conflict checks, Air and codespell. At push: codespell again, `check-design.py`, the NEWS-terseness and toolchain checks, the `fleet-ci-hook-installed` check (refuses the push when fleet-ci's hook is not installed), and each shared fleet script's offline self-test when that script changes (`check-fleet-standard.py`, `check-news.py`, `bestpractices-url.py`, `check-citation.py`, `check-bugreports.py`, `check-citation-nonr.py`, `logo-metadata.py`, `check-docs-drift.R`, `check-urls.R`) |
| T0 | every push whose diff against `main` is docs-only (every path on the classifier's `DOCS_ALLOWLIST`, `.fleet-ci/classify`, minus `.fleet-ci.yml`'s `docs_exclude`), locally, the pre-push hook | the gate's docs tier, `.fleet-ci/gate` in the fleet image (`fleet-r`): spelling, the pkgdown destination check and `pkgdown::check_pkgdown()` |
| T1 | every other push, locally, the pre-push hook | the gate's full tier: T0's checks, then lintr, docs drift (`scripts/check-docs-drift.R`), the URL check (`scripts/check-urls.R`), README drift (`scripts/check-readme-drift.sh`), the NEWS heading (`scripts/check-news-version.sh`), and one `R CMD check --as-cran --no-manual` (`NOT_CRAN=true`, incoming checks off) that fails on an ERROR, a WARNING, a failed test or a skip not on `allowed_skips`. Before the container step, the citation, BugReports and logo-metadata checks run on the host as `host_gates`, in a worktree of the pushed commit |
| T2 | the weekly `deep-check` schedule; every T3 run | `t2-check-release`, `t2-check-oldrel`, `t2-check-devel`, `x-floor` (R 4.1.3, in place of `t2-floor`), `t2-locale` (`R CMD check` under `LC_ALL=C`), `t2-ascran` (incoming off: `FLEET_INCOMING: "false"`), `coverage` (fails below 95%), `osv-audit`, `security-audit`, `citation-version`, `x-fossa` |
| T3 | a `RELEASE=1` web pipeline on `main`; a `v*` tag | all of T2 plus `t3-manual` (the PDF manual); the tag, or `RELEASE=1` on a tag, adds `pages` |

Pushes to `main` or a branch, merge requests and API pipelines (`glab ci run`)
create no pipeline at all, and neither does a web pipeline without
`RELEASE=1` (or `PAGES=1` on a tag). An empty pipeline list is not a pass:
the merge gate is the local gate (T0 or T1), run before the branch leaves the
machine.

## Before a CRAN release

seor cannot be submitted while a member is off CRAN (`release-deltas.md`).
When it can:

1. Start T3 on `main` from **Build > Pipelines > Run pipeline**, ref `main`,
   variable `RELEASE=1`, as `release-checklist.md` says. API pipelines create
   nothing. `PAGES=1` on a `v*` tag runs `pages` alone.
2. Run the incoming check by hand: neither the gate nor `t2-ascran` runs it
   for seor (`release-deltas.md`, step 5).

## The hook, once per clone

```sh
pre-commit install
.fleet-ci/pre-push --install
```

`pre-commit install` writes both hook types (`default_install_hook_types`);
`.fleet-ci/pre-push --install` then replaces the pre-push one with
fleet-ci's, which runs the gate on each pushed ref's tip and then the
pre-commit pre-push stage. Two commands drop it: `pre-commit install -f`, and
`pre-commit install -f --hook-type pre-push`; re-run the install after
either. Without `-f`, `pre-commit install` (with or without
`--hook-type pre-push`) moves the hook to `hooks/pre-push.legacy`
(pre-commit's migration mode), which still runs the gate first; `-f
--hook-type pre-commit` leaves it alone. `.fleet-ci/gate auto` runs the gate
by hand on `HEAD`. A pass is stamped by tree, tier, classifier version, image
and (full tier) resolved dependency lock, and a stamped commit is skipped.
The gate refuses a push carrying more than one ref to `main`, and a push to
`main` that adds more than one first-parent merge.

The gate checks the pushed commit, exported from git, never the working
tree, so an uncommitted fix cannot pass it (the former `docs-drift` hook
worked on a `git archive` export for the same reason). It needs a running
Docker daemon and the registry login (`docker login registry.gitlab.com`;
[ADR 0013](adr/0013-fleet-ci-is-private.md)). seor has no local mirror
remote; the gate would skip a push to one (a remote whose URL is a path).

## The NOTE policy

An `R CMD check` NOTE fails nothing, as before: the former `verify` hook
failed on an ERROR or a WARNING only (`error_on = "warning"`, no NOTE list),
so `.fleet-ci.yml` sets no `allowed_notes`. That holds in T1 and in the three
T2 legs that would apply the list (`t2-check-release`, `t2-check-oldrel`,
`t2-check-devel`); `t2-ascran`, `t2-locale`, `t3-manual` and `x-floor` never
apply it. The gate's check reports one NOTE, the same one the former hook
did: "Namespaces in Imports field not imported from", which every
metapackage gets (`ARCHITECTURE.md`, "Invariants").

## Project settings CI depends on, which are not in this repository

These live in GitLab's project settings, so a clone does not carry them:

- **Pipeline schedule 4467484** (Build > Pipeline schedules), "Weekly deep
  check (full-check)", `0 21 * * 4` Europe/Warsaw on `main`, carrying
  `SCHEDULE_KIND=deep-check` (read back 2026-10-30). Required: it is T2's
  only unattended run, and every pipeline on `main` carries `coverage`, so
  the coverage badge reads it.
- **Pipeline schedule 4467483**, `SCHEDULE_KIND=dependency-audit` (read back
  2026-10-30). The template starts no pipeline for it any more (the audits
  run in T2); its removal is owner-gated (SEOR-uldurjev).
- **`OSSINDEX_USER` / `OSSINDEX_TOKEN`** (Settings > CI/CD > Variables;
  `OSSINDEX_TOKEN` masked; the user is the literal `x`). `security-audit`
  sets `OSSINDEX_AUDIT_REQUIRED=true`, so without them it fails rather than
  passing having audited nothing.
- **`FOSSA_API_KEY`** (masked), which `x-fossa` uploads with; without it the
  job fails rather than skipping green.
- **fleet-ci's job token allowlist** must admit seor, or every fleet image
  pull fails (fleet-ci README, "The registry is private").
- **Shared runners off** (`shared_runners_enabled: false`, read back
  2026-10-30). The template's jobs carry no `tags:`, so the project runner,
  which accepts untagged jobs, is the only place they can land.
- **`pages_access_level: enabled`**: the site lives at
  `https://bart-turczynski.gitlab.io/seor/`, which `_pkgdown.yml` and
  `DESCRIPTION` name. `pages` publishes pkgdown's `destination`, `site/`,
  with only the top-level `.md` files on `.fleet-ci.yml`'s `pages_keep`; the
  gate's docs tier checks that destination too.

Never set `SCHEDULE_KIND` as a project or group variable: every schedule
would inherit it.

## Gaps accepted in the fleet-ci migration

- **The floor leg is `x-floor`, not the template's `t2-floor`
  (`FLEET_FLOOR: "false"`).** `t2-floor` installs every dependency from one
  dated snapshot, and seor's closure cannot come from one: sitemapr,
  robotstxtr and ssrfr are off CRAN, punycoder and rurl need their R 4.1
  fixes from the r-universe, and the bare `rocker/r-ver:4.1.3` has no curl
  binary for curl's static libcurl. `x-floor` (on `.t2-job`) keeps the former
  `floor-check` install and runs `R CMD check --as-cran` with incoming off and
  a `Status:` guard; `.gitlab-ci.yml` has the detail. It keeps no library
  cache, so each weekly run builds the closure from source, and it is
  unproven on the template until its first T2 run.
- **No sanitizer leg (`FLEET_SANITIZERS: "false"`).** seor has no compiled
  code; the former CI had none either.
- **`--as-cran` runs on R release only.** The former `full-check` legs ran
  the `verify` chain, so `R CMD check --as-cran`, under R release, oldrel
  (4.5) and devel. The template's `t2-check-release`, `t2-check-oldrel` and
  `t2-check-devel` run `--no-manual` without `--as-cran`, so on a current R
  only `t2-ascran` (release) runs `--as-cran`; besides it, only `x-floor`
  (R 4.1.3) does. An `--as-cran`-only finding on oldrel or devel now
  surfaces at win-builder, or at CRAN.
- **No incoming check anywhere in CI, as before.** seor's named exception
  (ADR 0004) is `FLEET_INCOMING: "false"`, so `t2-ascran` runs `--as-cran`
  with incoming off, as the former `verify` did; the remote half
  (`FLEET_INCOMING_REMOTE`) is left at the template's default, which
  `_R_CHECK_CRAN_INCOMING_=false` makes moot. `scripts/check-urls.R` in T1
  is seor's only URL check.
- **The live OSS Index audit runs in every suite-running job with
  `NOT_CRAN=true`, not only in `security-audit`.** The T2 check legs set
  `NOT_CRAN=true`, where the former `verify` left it unset, so
  `skip_on_cran()` no longer keeps `test-security.R`'s audit test out. In
  `t2-check-release`, `t2-check-oldrel`, `t2-check-devel`, `t2-locale` and
  `t3-manual` it finds `OSSINDEX_USER` and `OSSINDEX_TOKEN` (project
  variables reach every job they are not scoped away from) and calls OSS
  Index, and `test-osv.R` calls osv.dev. An OSS Index outage, an HTTP 429,
  a new advisory, or the shutdown of the endpoint oysteR 0.1.4 calls
  (2026-12-31) turns all of them red, and on a `v*` tag that blocks
  `pages`. Scoping the credentials to the audit job is a fleet follow-up
  (SEOR-yrsmlrvp).
- **T1 drops `test-security.R`'s two offline tests.** `exclude_tests` drops
  the whole file, so the allow-list well-formedness test and the validator's
  rejection test no longer run before a push (the former `verify` ran them);
  they run in T2. Moving them into a file of their own changes `tests/`, so
  it is a follow-up.
- **No server-side drift checks.** The former `verify`, `citation-version`,
  `gates` and `docs-drift` jobs ran lintr, `R CMD check`, the citation,
  BugReports, logo-metadata and NEWS-terseness checks with their self-tests,
  README drift, spelling, the NEWS heading and docs drift on every push to
  `main`, which caught a web edit, a server-side merge and a `--no-verify`
  push. Those runs are gone. The local gate runs the checks themselves
  (T1's `cheap_gates` and `host_gates`, spelling in T0 too, NEWS
  terseness as a pre-push hook); the pre-push hooks run the self-tests, each
  only when its script changes; and T2's `citation-version` runs
  `check-citation.py` alone, without its self-test. The
  scripts only the former shape called are retired with it:
  `scripts/gates.sh` (its README, spelling and NEWS-heading gates are now
  `check-readme-drift.sh`, `docs_gates` and `check-news-version.sh`) and
  `scripts/docs-drift.sh` (the gate's export replaces its `git archive`).
- **No runner tag.** The former CI's `default: tags: [local-docker]` is
  gone: the template sets no `tags`, and rules-sim refuses a package
  `default:`. That is safe because shared runners are off for seor
  (`shared_runners_enabled: false`, read back with a project GET on
  2026-10-30): an untagged job has only the project runner to land on, and
  that runner accepts untagged jobs. If shared runners were ever enabled,
  jobs could land on GitLab's SaaS runners instead.
- **The NOTE policy is unchanged, so no NOTE fails anything** (see "The
  NOTE policy" above).
- **The PDF manual is checked in T3 only.** The former hook built it on
  every push (the host has LaTeX); the gate checks `--no-manual` (`fleet-r`
  has no TeX), and `t3-manual` builds it in `fleet-r-tex`.
- **macOS is no longer checked before a push.** The former hook ran on the
  macOS host; the gate runs in a Linux container. Release-time macOS checks
  are `release-checklist.md`'s macOS builder step.
- **`t2-locale`'s leg runs under `LC_ALL=C`**, the template's default, which
  the former CI never ran (it had no locale leg, and neither did the hook).
  It is unproven until the first T2 run. The gate itself runs no locale leg,
  to keep T1 at one `R CMD check`.
- **`pages` deploys from a `v*` tag only**, not on every push to `main`, so
  the site documents the release, and lags `main` until seor's first tag.
- **No CI run of a branch.** The former web pipeline on any ref ran
  `verify` against a branch (SEOR-bmgkzhvy); the template admits a web
  pipeline only with `RELEASE=1` on `main` or a tag.
- **The dependency audits run weekly in T2 and in every release pipeline**,
  no longer on their own `dependency-audit` schedule, which now starts no
  pipeline.
- **`fossa analyze` runs weekly and at each release** (`x-fossa`, ADR
  0012), no longer on every push to `main`, so the FOSSA badges can lag a
  merge by up to a week.
- **`x-fossa` and `x-floor` run on `v*` tags and block `pages`.** Both are
  on `.t2-job`, so a tag pipeline runs them, and `pages` (stage `deploy`)
  waits on every `check` job; if either fails, the site is not deployed.
  The recovery is a `PAGES=1` web pipeline on the tag, which runs `pages`
  alone.
- **The audits have no no-skip or zero-result guard** (SEOR-hpodlopi): an
  `osv-audit` or `security-audit` run that skips its test, or audits
  nothing, passes green. This stays until fleet-ci fixes it and seor
  re-pins.
- **Comments in `tests/` still name the former hook and jobs**
  (`test-osv.R`, `test-security.R`); a CI migration edits no `tests/`.
- **Pandoc** comes from the fleet image (`.fleet-ci/toolchain`, 3.10), which
  reproduces the committed `README.md`. `scripts/check-toolchain.R` checks a
  local pandoc against it, so a local `build_readme()` writes what the gate
  accepts.
