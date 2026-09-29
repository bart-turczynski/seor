---
status: accepted
date: 2026-09-29
tracking: SEOR-vbmcrubx
---

# ADR 0006: non-R citation metadata has its own gate

## Context

`scripts/check-citation.py` keeps `CITATION.cff` and `.zenodo.json` in step
with `DESCRIPTION` in the R packages, under the rule in
[ADR 0002](0002-citation-urls-are-the-ones-about-this-package.md). It is
vendored into eight repositories behind an `IMPLEMENTATION_DIGEST`, and a change
to its implementation means re-blessing that digest in all eight in one change
(SEOR-tssbiedr). Measured 2026-09-29, all eight copies carry the same digest,
`f6f0e5a8b5cb6218`.

The non-R repositories joining Zenodo have no such gate. The files would then
drift from the version they name, the same way they did before the R gate
existed: four of the seven R repositories carrying them had drifted
(SEOR-lreejxat).

The R script cannot simply be pointed at them. It is built around
`DESCRIPTION`: it reads the version from a DCF file, maps a `.9000`
development version to the release it descends from, cross-checks URLs against
`DESCRIPTION`'s `URL:` field, and stops with an error when `DESCRIPTION` is
missing. None of that exists in a Node or Swift repository, which keep their
version elsewhere. Measured live on 2026-09-29 (read-only, local clones, with
the unbreak and linklint tags confirmed against their remotes):

| repo | stack | where the release version lives | citation files today |
|---|---|---|---|
| cc-cream | Node | `package.json` `version` 0.5.4 (tag v0.5.4 agrees) | neither |
| cf-crawl | Node | `package.json` `version` 4.0.0 (tag v4.0.0 agrees) | neither |
| linklint | Node | `package.json` is a `0.0.0` placeholder; the release is meant to be the git tag, and no `v*` tag exists yet | `CITATION.cff` with no `version:` |
| unbreak | Swift | git tags only, newest v0.7.2 (lightweight and annotated mixed) | neither |

The table the ticket was written from had unbreak at v0.1.2; it has released
six times since.

Three options were on the table:

1. **Teach the vendored R script the new sources.** `package.json` and git-tag
   readers would ship as dead code in eight R repositories, and adding them
   would force a second eight-repository re-bless for code none of those eight
   run.
2. **A separate, smaller vendored script for the non-R repositories.**
3. **No gate, a release-checklist line only.** This is the state in which the
   SEOR-lreejxat drift happened: a copied fact with nothing asserting it.

## Decision

**Option 2**, decided by the owner on 2026-09-29. `scripts/check-citation.py`
and its digest are left untouched.

**The script is `scripts/check-citation-nonr.py`.** seor holds the reference
copy. Vendoring it into cc-cream, cf-crawl, linklint and unbreak is each
repository's own ticket (CREAM-uubecjqz, CFCR-wfoyztca, LINK-tuabtnsv,
CLAU-jyxeovab). It carries its own `IMPLEMENTATION_DIGEST` on the R script's
mechanism: the digest covers every byte below the module docstring, `main()`
verifies it on every run, and the self-test proves it ignores prose and catches
code. The two scripts are re-blessed independently.

**Each repository declares its version source; the gate never guesses.**
`--source` is required and has no default, so it sits on the hook entry:

- `--source package-json`: the `version` field of the root `package.json`.
  For cc-cream and cf-crawl.
- `--source git-tag`: the highest `vX.Y.Z` tag merged into HEAD, compared as
  numbers, with the `v` stripped. Tags that are not exactly `vX.Y.Z` (release
  candidates, two-part versions, `vendor-snapshot`) do not count. For unbreak, and
  for linklint, whose `package.json` placeholder is never read.

**In step means the files equal the release the source names, at every
point in the cycle.** A Node repository leaves `package.json` at the last
release between releases, so its files do not move until the next bump. A
tag-sourced repository's files keep naming the latest tag, the counterpart of
an R package's `X.Y.Z.9000` still citing `X.Y.Z`.

**A repository that has never released cites nothing.** When the source names
no release (`package.json` at `0.0.0`, or no `vX.Y.Z` tag merged into HEAD),
neither file may carry a version, a `date-released` or a DOI. It is ADR 0002's
honesty clause, without its verbatim-development-version half, because these
sources have no development version to mirror.

**Boundary.** Like the R gate, this one checks nothing about whether a
repository should carry the files at all, or the DOI route. Unlike the R gate,
it checks no URLs: there is no single field here that URLs are copied out of,
and inventing one would be a rule nobody decided. It changes nothing about the
R rule. seor itself runs only the new script's self-test, from the pre-push
hook, whenever the script changes. seor is an R package and keeps
`check-citation.py`.

## Consequences

- **A rule the two scripts share has to change twice.** The honesty clause
  lives in both. Changing it in one is a decision about one fleet, not a fix to
  both.
- **A tag-sourced repository tags its release commit before pushing it.** The
  gate reads local tags, so the order is: bump the files, commit, tag, push.
  Pushing the bump before the tag exists fails the gate, because the files then
  name a release that does not exist yet.
- **A tag-sourced repository's CI needs git and the tags.** A shallow or
  tagless clone looks like a repository that has never released. It fails
  loudly rather than passing, but it fails. Use `GIT_DEPTH: 0` or a full fetch,
  and an image that ships git. The bare Python image seor's `citation-version`
  job uses does not, so this script's self-test is not wired there; ADR 0005's
  image lesson applies.
- **linklint is conformant today only because it cites nothing.** It has no tag
  and its `CITATION.cff` has no `version:`. Its first `v*` tag is what lets a
  version appear in the file. If linklint decides to cite its workspace
  packages' version (0.1.0 today) instead of a tag, that is a new source and a
  new decision, not a flag value.
- **Adding a source re-blesses only the non-R copies**, which is the point of
  the split. Do not add one to `check-citation.py`.
- Revisit if a third stack joins with a version source neither reader covers,
  or if the R gate's rule changes in a way the non-R repositories should
  follow. A drift between the two rules nobody chose is the failure this split
  risks.
