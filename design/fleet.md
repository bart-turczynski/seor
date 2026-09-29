# Fleet conventions

The nine R repositories (seor, punycoder, raddr, robotstxtr, sitemapr,
pagerankr, rurl, pslr, ssrfr) share a git workflow and a tracker, not a
template. Git follows the house `agent-workflow` skill; fp status changes stay
decoupled from git (the `fp` skill's `references/decoupling.md`). This file
holds what is neither in the skills nor in any one repository: where fleet work
is tracked, which English the prose and exported names use, and what actually
differs between the repositories.

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
| punycoder | `host_normalize()`             | `host_normalise()`             | held until punycoder 1.3.0 is on CRAN (SEOR-zfnbbujk)                         |
| punycoder | `normalization_profile_info()` | `normalisation_profile_info()` | held, as above                                                                |

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
column measured 2026-09-29 on each `main` plus the SEOR-xtmnpmae branches:

| repo       | `AGENTS_LANG.md` | spelling gate                     | `.pre-commit-config.yaml` | pre-push verify entry                   | CRAN incoming in the gate | codespell hook          |
|------------|------------------|-----------------------------------|---------------------------|-----------------------------------------|---------------------------|-------------------------|
| seor       | yes              | yes (pre-commit `spelling` hook)  | yes                       | inline R                                | off: the named exception  | yes                     |
| punycoder  | no               | yes (pre-commit `spelling` hook)  | yes                       | inline R                                | on                        | yes                     |
| raddr      | no               | yes (`data-raw/verify.sh`)        | yes                       | `data-raw/verify.sh`                    | on                        | yes                     |
| robotstxtr | no               | yes (`dev/gates.R spelling`)      | yes                       | `dev/verify.sh`                         | on                        | yes                     |
| sitemapr   | no               | yes (`tools/verify.R` stage)      | yes                       | `tools/verify.R`                        | on                        | yes                     |
| pagerankr  | no               | yes (`.githooks/pre-push`)        | yes                       | `.githooks/pre-push`                    | on                        | yes                     |
| rurl       | no               | yes (`tools/verify.R` stage)      | yes                       | `tools/verify-on-push.sh`               | on                        | pending (SEOR-oytkybis) |
| pslr       | no               | yes (`tools/verify.sh`)           | yes                       | `tools/verify.sh standard`              | no check in the gate      | yes                     |
| ssrfr      | yes              | yes (`scripts/check-spelling.R`)  | yes                       | `Rscript scripts/verify.R`              | on (logs `incoming=on`)   | no (out of scope)       |

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
