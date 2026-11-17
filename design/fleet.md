# Fleet conventions

The nine R repositories (seor, punycoder, raddr, robotstxtr, sitemapr,
pagerankr, rurl, pslr, ssrfr) share a git workflow and a tracker, not a
template. Git follows the house `agent-workflow` skill; fp status changes stay
decoupled from git (the `fp` skill's `references/decoupling.md`). This file
holds what is neither in the skills nor in any one repository: where fleet work
is tracked, which English the prose and exported names use, what actually
differs between the repositories, and when each one's scheduled pipelines run.
What every repository must carry is in [`fleet-standard.md`](fleet-standard.md).

## Tracker convention

Written from the fleet groom of 2026-09-27 (SEOR-thpuncfl), and adopted in
SEOR-ipwcbcov. It replaces the "Tracker convention" section of SEOR-eqpdrqnl
as the written source.

- A repository's backlog holds work that changes that repository's files, or a
  decision only that repository cares about.
- seor's backlog holds four kinds of issue:
  - **Cascades:** an ordering across repositories, one issue per step. Each
    carries only the order, the gate and the IDs of the repository issues
    doing the work.
  - **Fleet sweeps:** the same change in three or more repositories with no
    per-repository judgment. One issue with a per-repository checklist, and no
    copies in the repositories.
  - **Catch-ups:** one issue per package whose sweep lines wait on a CRAN
    review of that package. It depends on the cascade step that closes when
    CRAN accepts the package, so nothing in it lands while a resubmission
    could still be built from main. If CRAN sends the package back, the
    catch-up keeps waiting, and fixes CRAN asks for go into the resubmission.
    Once a sweep's only open lines wait on held packages, each held line
    moves: a line that must ship in the submission becomes its own issue,
    which the submission step depends on; a line that lands after acceptance
    goes to the package's catch-up issue. Either way it takes the sweep's
    acceptance checks with it. The sweep then closes as done, with a comment
    naming where each held line went. A catch-up is the one seor issue that
    carries one repository's implementation detail, because an issue in that
    repository could not depend on the seor cascade step. Adopted in the
    groom of 2026-10-06 (SEOR-cxetanvb).
  - **Owner-only settings across repositories:** one `[USER]` issue.
- fp dependencies cannot cross projects. A repository issue that waits on
  another repository's release carries `[USER]` (label `maintainer-gated`) and
  names the upstream issue in its description. A CRAN release is owner-gated,
  so the marker is honest.
- A repository issue never restates a seor ordering; it cites the SEOR id. A
  seor issue never restates implementation detail.
- Non-coding work (articles, analyses, brainstorming) is `[PARKED]`.
- A fleet request asks for a `NEWS.md` bullet only when the change meets the
  NEWS rule in seor's `AGENTS_LANG.md` (SEOR-adoxkmgi). A housekeeping sweep (logos,
  metadata, README, CI, gates) says "No NEWS bullet".

### Session ownership

Adopted by the owner on 2026-09-30, after the seor session shipped a punycoder
fix while the punycoder session held a release queue.

- When a session is live in a repository's folder, it is the only one that
  writes to that repository: branches, MRs, pipeline triggers and that
  repository's fp backlog.
- The seor session files and orders fleet sweeps, catch-ups and cascades. It
  does the work itself only in repositories with no live session. For a
  repository that has one, it messages that session with the SEOR id and the
  checklist line, then ticks the line from the evidence that session reports
  back.
- A seor `/burndown` run may write to every fleet repository (amended
  2026-10-03, SEOR-plnwieyf). Before each wave it checks `ListAgents` and
  skips any repository that has a live session, so the first rule above still
  holds.
- A question about another repository goes to that repository's session, not
  to seor.
- Check who is live before writing: `ListAgents` names each session and its
  folder.

## Prose language

Fleet prose is US English only (owner's rule, 2026-09-28; SEOR-kfiqpymb). Every
package declares `Language: en-US`, and its spelling gate checks against that.

- A British spelling the gate flags is respelled, never added to
  `inst/WORDLIST`. That includes historical NEWS entries.
- Before adding a word to a WORDLIST, check it against en_US. If en_GB accepts
  it and en_US rejects it, it is a respelling, not a new word:

  ```sh
  Rscript -e 'w <- readLines("inst/WORDLIST"); w[hunspell::hunspell_check(w, dict = hunspell::dictionary("en_GB")) & !hunspell::hunspell_check(w, dict = hunspell::dictionary("en_US"))]'
  ```

  Most of that command's output is dictionary noise: acronyms, technical terms,
  and US forms en_GB also accepts. Read it by hand.
- Exceptions are proper nouns and quoted upstream text (a spec's or an API's
  own spelling), and identifiers, which stay as written.
- Code, comments, string literals and tooling, which the spelling gate does not
  read, are gated by the codespell `--builtin en-GB_to_en-US` pre-commit hook
  at the commit and pre-push stages (SEOR-xtmnpmae). Legitimate British forms
  (quoted upstream text, the British alias identifiers) are excluded or
  allow-listed per repository, never respelled.

### British aliases

Exported names are US English, and a British spelling survives only as an
alias (owner's decision, 2026-09-28, tidyverse style). Functions are
SEOR-qwomlgjd; arguments are SEOR-oytkybis.

Function names:

- A name containing a word with a British variant also exports the British
  alias, defined as `british_name <- us_name`. This reverses dplyr's
  `summarize <- summarise`: the US name is primary. <!-- codespell:ignore summarise -->
- The alias is documented on the US name's help page (`@rdname`), and its NEWS
  bullet names both spellings.
- A new export follows the rule from the start.
- Out of scope: S3 methods, whose generics' names come from base R, and column
  or field names in returned data.

Argument names, after ggplot2's `colour`/`color` (dplyr aliases no ordinary <!-- codespell:ignore colour -->
argument):

- The US name is the documented argument. The British name is an extra formal
  defaulting to `NULL`, placed last in the signature so no existing positional
  call shifts.
- A supplied British name's value is used. Supplying both is an error that
  names both.
- Both share one `@param us_name,british_name` entry.
- One shared internal helper per package resolves the alias at the top of the
  function; internal functions receive the resolved value. Code that tests
  `missing()` on the US name must count a supplied alias as supplied.
- The risk is partial argument matching. With both spellings as formals, a
  prefix they share (`path_normali`) is ambiguous and errors, so adding an
  alias breaks any caller that abbreviates that way. Check callers first.

Current aliases, from the 2026-09-28 audit:

| package   | US name                        | British alias                  | note                                                                          |
|-----------|--------------------------------|--------------------------------|-------------------------------------------------------------------------------|
| rurl      | `serialize_url()`              | `serialise_url()`              |                                                                               |
| rurl      | `path_normalization` argument  | `path_normalisation`           | in `get_clean_url()`, `get_path()`, `safe_parse_url()`, `safe_parse_urls()`   |
| pagerankr | `analyze_pagerank_grid()`      | `analyse_pagerank_grid()`      |                                                                               |
| pagerankr | `sf_normalize_position()`      | `sf_normalise_position()`      |                                                                               |
| punycoder | `host_normalize()`             | `host_normalise()`             | on main (punycoder !41); first ships in 1.3.0                                 |
| punycoder | `normalization_profile_info()` | `normalisation_profile_info()` | on main (punycoder !41); first ships in 1.3.0                                 |

Identifiers carrying a British alias are legitimate British spellings in code,
and the codespell gate (SEOR-xtmnpmae) passes them rather than respelling them.
Its tokenizer reads an underscore-joined name as one word, so none of the names
above is flagged; a flagged one would be allow-listed in its repository.

## Instruction drift

Briefs written from a fleet-level template were wrong per repository, in ways
nobody noticed until an agent acted on them (SEOR-tullzdwb). Before a brief
asserts one of these facts about a repository, read its row here; before
relying on a row, re-measure it if the repository has changed its gate since.

Measured 2026-09-27 on each repository's `main`; the spelling-gate column
re-measured 2026-09-28, after SEOR-mtbzfroz gated every package; the codespell
column measured 2026-09-29 on each `main` plus the SEOR-xtmnpmae branches, and
ssrfr's re-measured 2026-09-30 after its own gate landed (SSRF-bdeefzlj):

| repo       | `AGENTS_LANG.md` | spelling gate                     | `.pre-commit-config.yaml` | pre-push verify entry                   | CRAN incoming in the gate | codespell hook          |
|------------|------------------|-----------------------------------|---------------------------|-----------------------------------------|---------------------------|-------------------------|
| seor       | yes              | yes (`.fleet-ci.yml` docs_gates)  | yes                       | `.fleet-ci/gate`                        | off: the named exception  | yes                     |
| punycoder  | no               | yes (pre-commit `spelling` hook)  | yes                       | inline R                                | on                        | yes                     |
| raddr      | no               | yes (`data-raw/verify.sh`)        | yes                       | `data-raw/verify.sh`                    | on                        | yes                     |
| robotstxtr | no               | yes (`dev/gates.R spelling`)      | yes                       | `dev/verify.sh`                         | on                        | yes                     |
| sitemapr   | no               | yes (`tools/verify.R` stage)      | yes                       | `tools/verify.R`                        | on                        | yes                     |
| pagerankr  | no               | yes (`.githooks/pre-push`)        | yes                       | `.githooks/pre-push`                    | on                        | yes                     |
| rurl       | no               | yes (`tools/verify.R` stage)      | yes                       | `tools/verify-on-push.sh`               | on                        | yes                     |
| pslr       | no               | yes (`tools/verify.sh`)           | yes                       | `tools/verify.sh standard`              | no check in the gate      | yes                     |
| ssrfr      | yes              | yes (`scripts/check-spelling.R`)  | yes                       | `Rscript scripts/verify.R`              | on (logs `incoming=on`)   | yes                     |

"Spelling gate" means a verify step that runs `spelling::spell_check_package()`
and fails on a hit; an `inst/WORDLIST` alone gates nothing. "Incoming" is the
`--as-cran` step `_R_CHECK_CRAN_INCOMING_` and `_R_CHECK_CRAN_INCOMING_REMOTE_`
switch off. "Codespell hook" is the pre-commit hook the "Prose language"
section describes.

Notes the table cannot carry:

- **pagerankr has a `.pre-commit-config.yaml`.** Its `verify` hook calls
  `.githooks/pre-push`. Older notes (SEOR-ipwcbcov's own description) say it
  has none and must be run by hand; that is no longer true.
- **pslr's pre-push gate runs no `R CMD check`.** The `standard` tier is lint,
  spelling and tests. The CI `check` job runs `--as-cran` with
  `_R_CHECK_CRAN_INCOMING_REMOTE_=false`, and the `cran` tier turns the remote
  half back on. ADR 0004 records the CI setting as grandfathered; under the
  tiers it carries forward as `FLEET_INCOMING_REMOTE="false"` in pslr's
  `t2-ascran` ([ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md)).
- **raddr's floor scripts** (`data-raw/check-r-floor.sh`,
  `data-raw/check-dep-floor.sh`) suppress incoming. They are hand-run, not the
  gate, and ADR 0004 puts them out of scope.

### The incoming decision

CRAN incoming feasibility runs in every repository's verify gate except
seor's: [ADR 0004](adr/0004-cran-incoming-runs-everywhere-except-seor.md). The
reason is the 2026-09-22 finding: punycoder's gate, which runs incoming, was
the only thing that noticed the fleet's `BugReports:` URLs returned 404. seor
is exempt because its members are not on CRAN, so incoming always errors
there. ssrfr, added to the fleet after the ADR, complies.

[ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md) supersedes it
and moves incoming out of the local gate into `t2-ascran`, in the weekly and
release runs. The template sets the two variables from `FLEET_INCOMING` and
`FLEET_INCOMING_REMOTE`, both `"true"` by default: seor sets
`FLEET_INCOMING="false"` (its named exception) and pslr
`FLEET_INCOMING_REMOTE="false"` (its grandfathered remote suppression). The
table above is the gates as measured before the tiers.

## Scheduled pipelines

Owner decision, 2026-09-23 (SEOR-ihmntqzm): expensive checks and dependency
audits run on **weekly, staggered** pipeline schedules, not nightly and not
`when: manual`. The only runner host is a Mac that can sleep (SEOR-hhtzaknn).
A nightly window would repeat that failure every night, and `when: manual` in
practice meant never. Before a release, check that the repository's scheduled
pipelines below are green. A red or missing run is a finding, not noise.

Schedules live in each project's settings (Build > Pipeline schedules), not in
`.gitlab-ci.yml`. Two rules hold everywhere:

- **Every schedule sets `SCHEDULE_KIND`**, and every scheduled job requires
  both `$CI_PIPELINE_SOURCE == "schedule"` and its kind, with `when: never` for
  any other schedule. The kinds are `dependency-audit` (`osv-audit`,
  `security-audit`), `deep-check` (release-shaped checks) and `rurl-devel`
  (pagerankr only). Set the variable on the schedule itself, never as a project
  variable, which every schedule would inherit.
- **Every schedule targets `main`.** Every repository's `workflow:` rules admit
  a schedule only through the default-branch rule, so a schedule on any other
  ref creates no pipeline.

Under the verification tiers
([ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md)) the
`deep-check` schedule runs T2, which includes the audits and, in rurl, seor
and ssrfr, `x-fossa`; `rurl-devel` runs pagerankr's suite against rurl's
`main` plus `coverage`; a `dependency-audit` schedule creates no pipeline,
and the owner deleted all nine on 2026-10-30 (SEOR-uldurjev). fleet-ci is
private ([ADR 0013](adr/0013-fleet-ci-is-private.md)), so a schedule's owner
must be able to read it, or the template include does not resolve. No
schedule re-runs the merge gate, which the pre-push hook already ran. Before
the migration, the schedules re-ran the main pipeline's jobs on an
already-tested commit; every package has migrated, and the runner times below
are T2 runs.

### The schedule table

"Cron" is the schedule's own setting, in Europe/Warsaw except where marked.
"Starts" is when the pipeline actually appears: the schedule's `next_run_at`,
plus a few minutes. In 2026-09 GitLab.com rounded `next_run_at` up to the
first full hour (on 2026-09-28, punycoder's 10:17 and ssrfr's 10:43 schedules
both started at 09:08 UTC). In 2026-11 the 22:30 crons started at 22:35, so the
minute now counts too. "Runner time" is the sum of job durations for one run:
busy time on the Mac's runners. It is not GitLab compute minutes, which
self-hosted project runners don't draw on.

Every deep-check runs the common T2 set: `t2-check-release`, `t2-check-oldrel`,
`t2-check-devel`, `t2-ascran`, `t2-locale`, `coverage`, `osv-audit`,
`security-audit` and `citation-version`. The third column lists the jobs it
runs beyond that set.

| repo       | kind       | jobs beyond the common T2 set                            | cron          | starts        | id      | pipeline   | runner time |
|------------|------------|----------------------------------------------------------|---------------|---------------|---------|------------|-------------|
| pagerankr  | rurl-devel | x-rurl-devel and `coverage` only, no T2                  | Mon 05:00 UTC | Mon 06:08     | 4466631 | 3072114139 | 4 min       |
| robotstxtr | deep-check | t2-sanitizers, x-floor, x-macos                          | Mon 21:00     | Mon 21:07     | 4472810 | 3075683946 | 176 min, red |
| sitemapr   | deep-check | x-floor, x-robotstxtr-head                               | Tue 21:00     | due Tue 21:00 | 4472811 | 3051678334 | 48 min      |
| pslr       | deep-check | t2-floor, t2-sanitizers, x-sanitizers-gcc, x-check-idn2  | Wed 21:00     | due Wed 21:00 | 4472812 | 3056414348 | 88 min      |
| seor       | deep-check | x-floor, x-fossa                                         | Thu 21:00     | Thu 21:06     | 4467484 | 3061522199 | 74 min      |
| rurl       | deep-check | t2-floor, x-check-idn2, x-fossa                          | Fri 21:00     | Fri 21:07     | 4472809 | 3066390204 | 147 min     |
| raddr      | deep-check | x-floor                                                  | Sat 21:00     | Sat 21:07     | 4467064 | 3068919973 | 61 min      |
| punycoder  | deep-check | t2-floor, t2-sanitizers                                  | Sat 22:30     | Sat 22:35     | 4466444 | 3069048848 | 180 min     |
| ssrfr      | deep-check | x-floor, x-renovate, x-fossa                             | Sun 21:00     | due Sun 21:00 | 4459714 | 3078378246 | 49 min      |
| pagerankr  | deep-check | t2-floor, x-rurl-floor                                   | Sun 22:30     | Sun 22:35     | 4467476 | 3071225620 | 94 min      |

Ten schedules are active (`pipeline_schedules` per project, 2026-11-17): one
weekly T2 per package, plus pagerankr's `rurl-devel`, the one schedule
exception in ADR 0012. On 2026-10-30 the owner deleted the nine
`dependency-audit` schedules and renamed each deep-check schedule "Weekly T2
(fleet standard)" (SEOR-uldurjev). Seven crons have moved since that day's
listing. sitemapr, pslr and ssrfr have not yet run at their new time, so their
"starts" is the `next_run_at` ("due"), and their pipeline ran at the old time;
ssrfr's ran on 2026-11-17 at 10:33 UTC, off its cron.

robotstxtr has had no green T2 run since it migrated. Of its five schedule
pipelines in the measurement window below, four failed and one was canceled.
Its last one, 3075683946, failed too: `x-floor`, `t2-sanitizers` and
`t2-ascran` failed, and `x-macos`, the audits and `coverage` were skipped. A
green run will take longer than its row. SEOR-ltilsdlz records why `t2-sanitizers` failed on
2026-10-31: a UBSan report from the `later` package's header, not
robotstxtr's code. Its newest green schedule pipeline on `main` (2993973423,
2026-10-27) predates the tiers, so it cannot stand in.

Total: about 15.3 runner-hours a week (about 66 per 30 days) for the ten rows,
against about 6.5 a week for the nineteen pre-tier rows of 2026-10-04. Each
weekly run got heavier, because T2 carries what the per-push pipelines did,
but nothing runs on a push any more ("CI minutes after the tiers", below). The
host runs `concurrent = 6`, with `limit = 4` on `seor-local-docker`, the
runner seven of the nine repositories share (both raised 2026-10-03 to clear
the fleet-standard queue), so this is a small share of its week; the
constraint is when it is awake, not capacity.

**The stagger.** One schedule per slot. Deep checks go at 21:00, one a day,
and the weekend adds two at 22:30: punycoder's on Saturday, after raddr's, and
pagerankr's on Sunday, after ssrfr's. Before the tiers, the audit schedules ran
in weekday working hours, when the Mac is most likely awake; the audits now
run inside T2. The old hour rounding once put punycoder's 10:17 audit and
ssrfr's 10:43 deep check in the same Mon 11:00 slot; ssrfr's moved to Mon
12:00 on 2026-09-30 (owner approved).

**How the runner times were measured** (2026-11-17, read-only through the
GitLab API; first done on 2026-10-04 on the pre-tier pipelines, whose rows
this file's history keeps). For each schedule, take its `last_pipeline`; if
that is not green, take the newest green schedule pipeline on `main` whose
jobs include the schedule's own. Sum `duration` over that pipeline's jobs,
read with `include_retried=false`, leaving out manual and skipped ones. The
pipelines used ran from 2026-11-10 to 2026-11-17; robotstxtr's is red (above).
Re-measure a row when its repository changes its scheduled jobs.

**The weekly re-check is T2.** The weekly `deep-check` schedule is the
re-check of `main` against moved dependencies, and it runs T2, not the merge
gate again ([ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md)).
Before the tiers, the owner kept the main pipeline re-running inside every
schedule for that re-check (2026-09-30); the 2026-10-04 measurements put the
re-run at about half of the schedules' runner time (2.7 of the seventeen
measured rows' 5.4 runner-hours).

### CI minutes after the tiers

Re-measured 2026-11-17 for the epic's target of at least 60% fewer CI minutes
(SEOR-iadkgvqq, SEOR-hojgvmhh). The window is 14 days from t0 = 2026-10-30,
the day the last package migrations merged and the owner deleted the dead
schedules (SEOR-uldurjev): `python3 tools/ci-minutes.py --since 2026-10-30
--until 2026-11-13 --json`, then `--cached --compare
tools/ci-minutes-baseline.json --per-day`. "Before" is the baseline's 30 days
(2026-09-29 to 2026-10-29); "after" is the window's job-minutes times 30/14.
The change is computed from the exact minutes, so it can differ by up to half a
point from `--compare`'s per-day printout. Commits are first-parent commits on
`main` (GitLab's commits API, `first_parent=true`), also per 30 days. Hook
times come from each migration's close comment: the old pre-push hook, then
the fleet-ci gate's docs tier (T0) and full tier (T1).

| package    | before (min) | after (min) | change | window pipelines by source | commits before → after | old hook | docs tier | full tier |
|------------|--------------|-------------|--------|----------------------------|------------------------|----------|-----------|-----------|
| rurl       | 2784.6       | 450.0       | -83.8% | 5 schedule                 | 157 → 17               | 663 s    | 13 s      | ~530 s    |
| ssrfr      | 1516.0       | 335.8       | -77.9% | 5 schedule, 1 web, 1 push  | 60 → 51                | 410 s    | 2.8 s     | 406 s     |
| seor       | 1309.4       | 378.2       | -71.1% | 5 schedule                 | 89 → 19                | 120 s    | 2.5 s     | ~65 s     |
| sitemapr   | 616.5        | 207.4       | -66.4% | 5 schedule                 | 52 → 24                | 204 s    | 43 s      | ~150 s    |
| punycoder  | 595.8        | 458.6       | -23.0% | 5 schedule                 | 52 → 17                | 146.7 s  | 3.6-9.7 s | 93-101 s  |
| pagerankr  | 598.6        | 516.4       | -13.7% | 7 schedule                 | 40 → 13                | 156 s    | 7.9 s     | 123-201 s |
| pslr       | 512.5        | 678.4       | +32.4% | 5 schedule                 | 48 → 13                | 120 s    | 3.6 s     | 175 s     |
| robotstxtr | 504.4        | 695.6       | +37.9% | 5 schedule                 | 36 → 171               | 140 s    | 4 s       | ~153 s    |
| raddr      | 278.9        | 142.5       | -48.9% | 5 schedule                 | 72 → 34                | 101 s    | 32 s      | 113-120 s |
| packages   | 8716.7       | 3862.9      | -55.7% | 47 schedule, 1 web, 1 push | 606 → 360              |          |           |           |
| fleet-ci   | none yet     | 18.9        | n/a    | 8 push                     |                        |          |           |           |
| total      | 8716.7       | 3881.8      | -55.5% |                            |                        |          |           |           |

**Verdict: the 60% target is missed.** The total including fleet-ci fell
55.5%, to 3881.8 minutes per 30 days against a target of at most 3486.7;
packages alone fell 55.7%. The biggest remaining consumers are `t2-check-devel`
(359.1 window minutes) and `t2-sanitizers` (358.7, of which robotstxtr's red
runs are 144.4).

- **Push minutes are gone.** No package pipeline ran on a push to `main`,
  against 558 pipelines and 5476.6 minutes in the baseline. ssrfr's one push
  pipeline, on `release/1.0.x`, was skipped (0 minutes), and its web pipeline
  (43.6 minutes) is a T3 release run, `t3-manual` included. Every other package minute is
  `schedule`. fleet-ci's 8.8 window minutes are its own self-tests on push to
  its `main`.
- **The window is not a quiet fortnight in disguise.** Commits fell in most
  packages, but under the tiers a commit costs no CI minutes, and robotstxtr's
  commits rose almost five times over while its minutes stayed all `schedule`.
- **The window holds extra runs.** Besides the weekly cadence, every package
  ran three schedule pipelines on 2026-10-30 (12:27 and 15:41 UTC) and
  2026-10-31 (04:35 UTC), 27 of the 47. The schedule table above gives the
  steady state instead: 920.9 runner-minutes a week, 3946.7 per 30 days, a
  54.7% fall. The miss is not an artifact of the extra runs.
- **Red runs cost minutes.** 342.3 of the packages' 1802.7 window minutes went
  to failed or canceled jobs, 250.4 of them robotstxtr's (above). In the two
  packages that rose, the sanitizers and the floor dominate: 197.1 of pslr's
  316.6 window minutes and 239.9 of robotstxtr's 324.6.
