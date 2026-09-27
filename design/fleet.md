# Fleet conventions

The nine R repositories (seor, punycoder, raddr, robotstxtr, sitemapr,
pagerankr, rurl, pslr, ssrfr) share a git workflow and a tracker, not a
template. Git follows the house `agent-workflow` skill; fp status changes stay
decoupled from git (the `fp` skill's `references/decoupling.md`). This file
holds the two things that are neither in the skills nor in any one repository:
where fleet work is tracked, and what actually differs between the repositories.

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

## Instruction drift

Briefs written from a fleet-level template were wrong per repository, in ways
nobody noticed until an agent acted on them (SEOR-tullzdwb). Before a brief
asserts one of these facts about a repository, read its row here; before
relying on a row, re-measure it if the repository has changed its gate since.

Measured 2026-09-27 on each repository's `main`:

| repo       | `AGENTS_LANG.md` | spelling gate                     | `.pre-commit-config.yaml` | pre-push verify entry                   | CRAN incoming in the gate |
|------------|------------------|-----------------------------------|---------------------------|-----------------------------------------|---------------------------|
| seor       | yes              | no (`inst/WORDLIST` only)         | yes                       | inline R                                | off: the named exception  |
| punycoder  | no               | no (`inst/WORDLIST` only)         | yes                       | inline R                                | on                        |
| raddr      | no               | yes (`data-raw/verify.sh`)        | yes                       | `data-raw/verify.sh`                    | on                        |
| robotstxtr | no               | no                                | yes                       | `dev/verify.sh`                         | on                        |
| sitemapr   | no               | no                                | yes                       | `tools/verify.R`                        | on                        |
| pagerankr  | no               | yes (`.githooks/pre-push`)        | yes                       | `.githooks/pre-push`                    | on                        |
| rurl       | no               | no (`inst/WORDLIST` only)         | yes                       | `tools/verify-on-push.sh`               | on                        |
| pslr       | no               | no (`inst/WORDLIST` only)         | yes                       | `tools/verify.sh standard`              | no check in the gate      |
| ssrfr      | yes              | no                                | yes                       | `Rscript scripts/verify.R`              | on (logs `incoming=on`)   |

"Spelling gate" means a verify step that runs `spelling::spell_check_package()`
and fails on a hit; an `inst/WORDLIST` alone gates nothing. "Incoming" is the
`--as-cran` step `_R_CHECK_CRAN_INCOMING_` and `_R_CHECK_CRAN_INCOMING_REMOTE_`
switch off.

Notes the table cannot carry:

- **pagerankr has a `.pre-commit-config.yaml`.** Its `verify` hook calls
  `.githooks/pre-push`. Older notes (SEOR-ipwcbcov's own description) say it
  has none and must be run by hand; that is no longer true.
- **pslr's pre-push gate runs no `R CMD check`.** The `standard` tier is lint
  and tests. The CI `check` job runs `--as-cran` with
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
