---
status: accepted
date: 2026-09-11
tracking: SEOR-lreejxat
---

# ADR 0001: citation metadata names the release, not the development version

## Context

`CITATION.cff` and `.zenodo.json` both carry a version number copied from
`DESCRIPTION`. Nothing asserts that the copy is right, the release checklist
does not mention either file, and the fleet had drifted in both directions
under **two conflicting conventions with no decision between them**
(`SEOR-lreejxat`).

Measured across the eight repositories on 2026-09-11 (re-measured; `rurl` had
moved since the table in the issue was taken on 2026-09-09):

| package      | `DESCRIPTION` | `CITATION.cff` | `.zenodo.json` |
|--------------|---------------|----------------|----------------|
| `rurl`       | 3.0.1.9000    | 3.0.1          | 3.0.1          |
| `pslr`       | 1.2.0         | 1.1.0          | 1.1.0          |
| `punycoder`  | 1.2.1.9000    | 1.2.0          | 1.2.1          |
| `raddr`      | 0.1.2.9000    | (absent)       | (absent)       |
| `pagerankr`  | 0.1.0         | 0.1.0          | 0.1.0          |
| `sitemapr`   | 0.0.0.9000    | 0.0.0.9000     | 0.0.0.9000     |
| `robotstxtr` | 0.2.0.9000    | 0.2.0.9000     | 0.2.0          |
| `seor`       | 0.0.0.9000    | 0.0.0.9000     | 0.0.0.9000     |

The two conventions in the tree are:

- **Mirror `DESCRIPTION` verbatim**, `.9000` suffix included — `sitemapr`,
  `seor`, and `robotstxtr`'s `CITATION.cff`. This is what `cffr` generates,
  because `cffr` reads `DESCRIPTION`.
- **Name the last release** — `punycoder`'s `.zenodo.json`, `pslr`.

Both are defensible, and they disagree. `robotstxtr` manages to disagree with
*itself*: `CITATION.cff` 0.2.0.9000 against `.zenodo.json` 0.2.0.

The tie-breaker is what else these files claim. `CITATION.cff` carries
`date-released` and, where one exists, a version DOI. Neither can honestly
accompany `X.Y.Z.9000`: a development version has no release date and no
deposit. A citation is a pointer to something a reader can obtain, and nobody
can obtain `0.2.0.9000`.

The counter-force is real but weaker: `cffr::cff_write()` regenerates
`version:` from `DESCRIPTION` verbatim, so regeneration silently reimposes the
other rule.

There is no evidence this drift is self-correcting. The same shape — a file
that matters at release time with no assertion attached to it — produced
`tools/cran-comments-gate.R` in `rurl`, which exists because `cran-comments.md`
had drifted **eleven releases** unnoticed. Nothing comparable was written for
these two files.

## Decision

**`CITATION.cff`'s `version:` and `.zenodo.json`'s `"version"` carry the
release that the `DESCRIPTION` `Version:` names.**

- `X.Y.Z` → `X.Y.Z`.
- `X.Y.Z.9000` (any fourth component ≥ 9000) → `X.Y.Z`. A development cycle
  still cites the release it descends from.
- **Exception — a package that has never released.** When the release a
  version names is `0.0.0`, there is no release to name, so both files carry
  the `DESCRIPTION` version verbatim (`0.0.0.9000`) and **must carry no
  `date-released` and no DOI**. This is the only case where the files mirror a
  development version, and it is honest precisely because there is nothing else
  in them to contradict.

This is the same phase rule `rurl`'s `tools/cran-comments-gate.R` already
applies to `cran-comments.md` (`release_named_by()`), which is a second reason
to prefer it: one rule, two gates, no third convention.

**The rule is enforced by `scripts/check-citation.py`**, in the family of
`tools/cran-comments-gate.R`: offline, stdlib-only, run from the pre-push hook
and from a CI job. Alongside the version it checks that every URL those two
files declare also appears in `DESCRIPTION`'s `URL:` field — the same class of
defect, a fact duplicated out of `DESCRIPTION` with nothing asserting the copy.

**Boundary — what this ADR does not decide.** It says nothing about *whether*
`.zenodo.json` should exist, or about the DOI route. Deposits are minted by
Zenodo's webhook on a GitHub release; that account is permanently suspended, so
no deposit has been minted since the move to GitLab. Whether to seed manual
deposits or drop the DOI ambition is an owner decision, open in `SEOR-lreejxat`
and `SITE-knuqpfaf`. While it is open, this rule keeps the files from claiming
anything untrue: `seor` has no release, so it carries no DOI and no release
date, and the gate fails if one appears.

It also does not decide whether `raddr` should have these files at all. It has
neither, and the gate treats absence as nothing to check rather than as a
violation.

## Consequences

- **`cffr` output needs one edit after regeneration** for any released package.
  `cff_write()` will write `3.0.1.9000` where the rule wants `3.0.1`. The gate
  is what catches it; without the gate, regeneration silently reverts the rule.
  Do not "fix" a gate failure by changing the rule to match the generator.
- **These files change at the start of a release, not the end.** The version
  they carry becomes correct when `DESCRIPTION` is bumped to `X.Y.Z`, which is
  release-checklist step 2, not step 8. During the development cycle that
  follows, the bump to `X.Y.Z.9000` leaves them untouched and still correct.
- **A package's first release is the one moment both files must change under
  the exception.** `0.0.0.9000` → `0.1.0` moves them off the verbatim mirror
  and lets `date-released` and a DOI appear for the first time.
- **Under this rule, `seor` is already conformant** and three of the seven
  repositories carrying the files are not (`pslr`, `punycoder`,
  `robotstxtr`) — a remainder recorded on `SEOR-lreejxat` rather than fixed
  here, since each lives in its own tree.
- Revisit if the DOI question is settled by removing `.zenodo.json` entirely,
  in which case half of this rule has nothing left to govern; or if a citation
  consumer is found that requires the development version, which would be
  evidence the honesty argument above is wrong.
