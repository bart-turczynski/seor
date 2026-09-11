---
status: accepted
date: 2026-09-11
tracking: SEOR-jxzjhbef
---

# ADR 0002: citation URLs are the ones about this package

Supersedes [ADR 0001](0001-citation-metadata-names-the-release.md). The version
rule is carried over unchanged; only the URL rule narrows.

## Context

ADR 0001 decided two things and `scripts/check-citation.py` enforces both. The
first — `CITATION.cff` `version:` and `.zenodo.json` `"version"` name the
release `DESCRIPTION`'s `Version:` names — is sound and is restated below
verbatim. The second is not, and was found the first time the gate left the
repository it was written in.

ADR 0001's URL rule reads:

> Alongside the version it checks that every URL those two files declare also
> appears in `DESCRIPTION`'s `URL:` field — the same class of defect, a fact
> duplicated out of `DESCRIPTION` with nothing asserting the copy.

The implementation took "every URL those two files declare" literally and
walked `.zenodo.json`'s `related_identifiers`, returning every http(s)
`identifier` without ever reading its `relation`.

`related_identifiers` are Zenodo/DataCite **relationship** declarations. Some
assert something about this package; others point at an entirely different
artifact — a dependency, an upstream source. Requiring the latter to appear in
`DESCRIPTION`'s `URL:` — a field meaning "URLs about this package" — is a
category error, and `R CMD check --as-cran` would fetch them as if the package
claimed them.

Measured 2026-09-11, porting the gate to the six sibling repositories:

| repo | related identifiers | failing | the failing identifiers |
|---|---|---|---|
| `seor` | 1 | 0 | |
| `pagerankr` | 2 | 0 | |
| `rurl` | 3 | 2 | CRAN pages of `pslr`, `punycoder` |
| `pslr` | 4 | 2 | CRAN pages of `rurl`, `punycoder` |
| `punycoder` | 2 | 1 | CRAN page of `rurl` |
| `sitemapr` | 3 | 1 | `gitlab.com/bart-turczynski/rurl` |
| `robotstxtr` | 2 | 1 | `github.com/google/robotstxt` |

**Five of seven repositories fail, and the two that pass are the two the gate
was written against.** That is the whole mechanism: `seor` and `pagerankr`
happen to carry only self-referential identifiers, so the overbreadth was
invisible at the point of authorship. It is the third instance in this fleet of
a rule derived from one repository's configuration and asserted of all eight —
the others being the `_R_CHECK_CRAN_INCOMING_=false` claim and
`AGENTS.md`'s claim about `.claude/settings.json`.

The split by `relation` is clean, and that is a measurement rather than a
reading of the DataCite vocabulary:

    isDocumentedBy   5 identifiers   5 declared in DESCRIPTION   0 not
    isIdenticalTo    3               3                           0
    isSupplementTo   2               2                           0
    requires         4               0                           4
    isRequiredBy     2               0                           2
    isDerivedFrom    1               0                           1

Seventeen entries, no counterexample in either direction.

## Decision

**1. The version rule of ADR 0001 stands, unchanged.** `CITATION.cff`'s
`version:` and `.zenodo.json`'s `"version"` carry the release that the
`DESCRIPTION` `Version:` names: `X.Y.Z` → `X.Y.Z`; `X.Y.Z.9000` (any fourth
component ≥ 9000) → `X.Y.Z`. The exception for a package that has never
released — the named release is `0.0.0`, so the files carry the development
version verbatim and must carry no `date-released` and no DOI — stands with
it, as does the reasoning in ADR 0001's Context and Consequences.

**2. The URL rule narrows to URLs about this package.** A URL in these two
files is cross-checked against `DESCRIPTION`'s `URL:` only when it asserts
something about *this* package:

- In `CITATION.cff`: the `url`, `repository-code`, `repository` and
  `repository-artifact` scalars. Unchanged — every one of these is
  self-referential by definition.
- In `.zenodo.json`: a `related_identifiers` entry whose `relation` is in
  `SELF_REFERENTIAL_RELATIONS` — today `isIdenticalTo`, `isDocumentedBy`,
  `isSupplementTo`.

Any other `relation` is exempt. It points at a different artifact, so there is
no duplicated fact to keep honest.

**3. The exemption is an allowlist of what to check, not a denylist of what to
skip, and an unrecognized `relation` is exempt.** The costs are not symmetric.
A false positive reds this gate in every repository at once — it did, in five
of seven, which is how the defect surfaced. A false negative misses one
duplicated URL, and `CITATION.cff`'s own `url:` / `repository-code:` fields
still cross-check the same surface. Fail open.

**Boundary.** This ADR decides only which URLs are cross-checked. It does not
revisit anything ADR 0001 left open: whether `.zenodo.json` should exist, the
DOI route, or whether `raddr` should carry these files. Those remain owner
decisions on `SEOR-lreejxat` and `SITE-knuqpfaf`.

## Consequences

- **Adding a `relation` to `SELF_REFERENTIAL_RELATIONS` is a decision, not a
  tweak.** The set is small and measured. Widening it re-checks identifiers
  that no repository currently declares in `DESCRIPTION`, so it will red the
  gate somewhere — do it deliberately, with the fleet re-measured.
- **The gate no longer notices a dependency pointer that rots.** If
  `.zenodo.json` says a package `requires` a URL that dies, nothing here
  complains. That is accepted: it is a claim about another artifact, which
  `DESCRIPTION` never duplicated and `--as-cran` never fetches.
- **`scripts/check-citation.py` carries a `# check-citation vN` marker on its
  first line.** It is copied verbatim into each repository, so the marker is
  the only way to tell at a glance which repositories have the narrowed rule.
  Bump it whenever the rule changes, and re-copy to all of them.
- **Porting the script needs `^scripts$` in the destination's
  `.Rbuildignore`.** Measured 2026-09-11: `seor` is the only repository of the
  eight with a `scripts/` directory, and the only one ignoring it. Without the
  ignore, `R CMD check --as-cran` reports `Non-standard file/directory found at
  top level: 'scripts'` — verified on a real `--as-cran` run against
  `pagerankr`, where it was a new NOTE on a package being prepared for CRAN.
- Revisit if a citation consumer is found that reads `related_identifiers` as
  project URLs, which would be evidence the category distinction above is
  wrong; or if `.zenodo.json` is dropped entirely, in which case rule 2's
  second clause has nothing left to govern.
