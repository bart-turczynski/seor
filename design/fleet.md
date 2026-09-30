# Fleet conventions

The nine R repositories (seor, punycoder, raddr, robotstxtr, sitemapr,
pagerankr, rurl, pslr, ssrfr) share a git workflow and a tracker, not a
template. Git follows the house `agent-workflow` skill; fp status changes stay
decoupled from git (the `fp` skill's `references/decoupling.md`). This file
holds what is neither in the skills nor in any one repository: where fleet work
is tracked, which English the prose and exported names use, what actually
differs between the repositories, and when each one's scheduled pipelines run.

## Tracker convention

Written from the fleet groom of 2026-09-27 (SEOR-thpuncfl), and adopted in
SEOR-ipwcbcov. It replaces the "Tracker convention" section of SEOR-eqpdrqnl
as the written source.

- A repository's backlog holds work that changes that repository's files, or a
  decision only that repository cares about.
- seor's backlog holds three kinds of issue:
  - **Cascades:** an ordering across repositories, one issue per step. Each
    carries only the order, the gate and the IDs of the repository issues
    doing the work.
  - **Fleet sweeps:** the same change in three or more repositories with no
    per-repository judgment. One issue with a per-repository checklist, and no
    copies in the repositories.
  - **Owner-only settings across repositories:** one `[USER]` issue.
- fp dependencies cannot cross projects. A repository issue that waits on
  another repository's release carries `[USER]` (label `maintainer-gated`) and
  names the upstream issue in its description. A CRAN release is owner-gated,
  so the marker is honest.
- A repository issue never restates a seor ordering; it cites the SEOR id. A
  seor issue never restates implementation detail.
- Non-coding work (articles, analyses, brainstorming) is `[PARKED]`.

### Session ownership

Adopted by the owner on 2026-09-30, after the seor session shipped a punycoder
fix while the punycoder session held a release queue.

- When a session is live in a repository's folder, it is the only one that
  writes to that repository: branches, MRs, pipeline triggers and that
  repository's fp backlog.
- The seor session files and orders fleet sweeps and cascades. It does the
  work itself only in repositories with no live session. For a repository
  that has one, it messages that session with the SEOR id and the checklist
  line, then ticks the line from the evidence that session reports back.
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
| seor       | yes              | yes (pre-commit `spelling` hook)  | yes                       | inline R                                | off: the named exception  | yes                     |
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
  half back on. ADR 0004 records the CI setting as grandfathered.
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

A schedule pipeline on `main` also runs every job that runs on a push to `main`
(check, coverage, gates or verify, pages), because those jobs key on the branch,
not the pipeline source. pslr is the exception: its `workflow:` admits only the
two audits. So a schedule costs its own jobs plus one main pipeline.

### The schedule table

Times are Europe/Warsaw except where marked. "Runner time" is the sum of job
durations for one run: busy time on the Mac's runners. It is not GitLab compute
minutes, which self-hosted project runners don't draw on.

| repo       | kind             | jobs it adds to the main pipeline      | when              | id / status        | runner time |
|------------|------------------|----------------------------------------|-------------------|--------------------|-------------|
| pagerankr  | rurl-devel       | rurl-devel                             | Mon 05:00 UTC     | 4466631, active    | ~10 min     |
| punycoder  | dependency-audit | osv-audit, security-audit              | Mon 10:17         | 4427280, active    | ~7 min      |
| ssrfr      | deep-check       | full-check (4.4.3, 4.5.1), renovate    | Mon 10:43         | 4459714, active    | ~33 min     |
| punycoder  | deep-check       | full-check (3 legs), sanitizers        | Mon 21:00         | 4466444, active    | ~16 min     |
| raddr      | deep-check       | check:linux-devel (also on every push) | Tue 21:00         | 4467064, active    | ~6 min      |
| rurl       | dependency-audit | osv-audit, security-audit              | Tue 10:17         | proposed           | ~11 min     |
| robotstxtr | dependency-audit | osv-audit, security-audit              | Tue 11:17         | proposed           | ~10 min     |
| sitemapr   | dependency-audit | osv-audit, security-audit              | Wed 10:17         | proposed           | ~8 min      |
| pagerankr  | dependency-audit | osv-audit, security-audit              | Wed 11:17         | proposed           | ~12 min     |
| pagerankr  | deep-check       | check-oldrel                           | Wed 21:00         | proposed           | ~11 min     |
| pslr       | dependency-audit | osv-audit, security-audit only         | Thu 10:17         | proposed           | ~3 min      |
| seor       | dependency-audit | osv-audit, security-audit              | Thu 11:17         | proposed           | ~12 min     |
| seor       | deep-check       | full-check (4.5.1, 4.4.3)              | Thu 21:00         | proposed           | ~15 min     |

Total: about 71 min a week today, and about 2.6 runner-hours a week (about 11
a month) once the proposed rows exist. The host runs `concurrent = 4`, so this
is a small share of its week; the constraint is when it is awake, not capacity.

**The stagger.** One schedule per slot. Audits go in weekday working hours,
when the Mac is most likely awake. Deep checks go at 21:00 on distinct
weekdays, as punycoder's and raddr's already did. New slots are an hour apart,
longer than any one run takes, so no two scheduled pipelines queue against
each other or against the working day's merges on the same host. Minute 17
keeps them off the top of the hour. The one tighter pair, Mon 10:17 and 10:43,
predates this table and doesn't overlap: punycoder's audit pipeline finishes
in about 7 minutes.

**How the estimates were made** (2026-09-30, medians of each project's last
100 successful jobs). Measured: every main-pipeline job, punycoder's audits
(57 s, 60 s) and deep checks, ssrfr's full-check (486 s a leg), raddr's
`check:linux-devel` (190 s), pagerankr's `check-oldrel` (130 s) and
`rurl-devel` (120 s), and pslr's audits (100 s, 90 s). Estimated, with no run
on record: the audits elsewhere at 100 s each (pslr's figure), and seor's
full-check at about 200 s a leg (seor's `verify` job, which runs the same
`R CMD check`, takes 195 s). Each proposed schedule's first run replaces its
estimate with a measurement; update the row then.

**Open question, not decided.** About two-thirds of a proposed schedule's
runner time is the main pipeline rerunning on a commit that already passed.
Adding `$CI_PIPELINE_SOURCE != "schedule"` to each repository's on-main rules
would cut the week to about an hour, but a scheduled run would no longer
re-check `main` against moved dependencies. That re-check is useful for the
audits and deep checks, and it's why the rows above keep it.
