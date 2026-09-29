# Fleet CRAN release checklist

The release procedure for every R package in the fleet (SEOR-ygfaewuo). Run
the steps in order.

**Deltas live in each package's `CONTRIBUTING.md`.** Its "CRAN release
checklist" section links here and lists only that package's extra or
different steps. Read it before starting; where it disagrees with this file,
it wins. punycoder, pslr and rurl still carry full checklists of their own;
moving them to this shape is SEOR-wmeqnoqz.

Who runs each step:

- **owner**: the maintainer, by hand. The owner keeps the release version
  bump, the CRAN submission and the tag.
- **agent+go**: an agent, only in a session where the owner has said go for
  this specific release. Never unattended (owner decision D4, SEOR-zfnbbujk).
- **agent**: an agent, as ordinary slice work through a merge request.

## Before submission

1. **agent** Check that the release is due and installable. CRAN asks for no
   more than one release every one to two months. Every dependency must be on
   CRAN at the floor `DESCRIPTION` declares, and the submitted `DESCRIPTION`
   carries no `Remotes:`.
2. **agent** If the package has reverse dependencies on CRAN, check each
   published one against a tarball of the release candidate, in a library
   holding only CRAN packages. Record the result in `cran-comments.md`.
3. **owner** Release-prep commit:
   - `DESCRIPTION` `Version:` drops the `.9000` suffix.
   - The top `NEWS.md` heading names the release, with every unreleased item
     under it.
   - `CITATION.cff` `version:` and `.zenodo.json` `"version"` match.
     `python3 scripts/check-citation.py` passes. Zenodo reads `.zenodo.json`
     from the tagged commit, so it has to be right here, not later.
   - `codemeta.json`'s version is edited by hand, not regenerated: it
     carries hand-set GitLab URLs.
4. **agent** Rewrite `cran-comments.md` for this submission.
5. **agent** Check the exact tarball. Build it from a clean export of `main`
   (`git archive`), then run `R CMD check --as-cran` on it with
   `_R_CHECK_CRAN_INCOMING_=true` and `_R_CHECK_CRAN_INCOMING_REMOTE_=true`,
   against a library holding only CRAN packages. Two NOTE items are expected
   fleet-wide: "New submission" (first release only) and the `BugReports:`
   `/-/issues` 404 (SEOR-ocbtrrnl). `cran-comments.md` explains every item
   that is not fixed.
6. **agent+go** Cross-platform checks, all on the same final SHA:
   - win-builder: `devtools::check_win_devel()`, `check_win_release()` and
     `check_win_oldrelease()`.
   - macOS builder: upload the tarball to
     <https://mac.r-project.org/macbuilder/submit.html>.
   - R-hub: `rhub::rc_submit()`, never `rhub::rhub_check()`, which needs
     GitHub Actions (`github-mirror.md` §7). The first use needs the owner's
     one-time `rhub::rc_new_token()` email validation.

   Write every platform and its result into `cran-comments.md`. A fix after
   these ran means running them again on the new SHA.

## Submission

7. **owner** Run `devtools::submit_cran()` from a clean clone of `main`, not
   a working copy, whose untracked files can reach the tarball. Then click
   CRAN's confirmation email.
8. **agent** Commit `CRAN-SUBMISSION`, and record the date, SHA and tarball
   SHA-256 in `cran-comments.md`.

## After CRAN accepts

9. **owner** Tag the submitted commit (the `SHA:` in `CRAN-SUBMISSION`) with
   an annotated `vX.Y.Z` and push the tag to GitLab. The `v*` protected-tag
   rule mirrors it to GitHub and makes it undeletable (`github-mirror.md`
   §2.8), so tag after acceptance, not at submission. Check
   `git merge-base --is-ancestor vX.Y.Z origin/main`.
10. **agent+go** Create the GitLab release from the tag
    (`glab release create vX.Y.Z`), with that version's `NEWS.md` section as
    the notes.
11. **agent** Diff the CRAN tarball
    (`https://cran.r-project.org/src/contrib/<pkg>_X.Y.Z.tar.gz`) against a
    build of the tag. Only the `DESCRIPTION` fields CRAN adds should differ.
12. **agent** Post-release commit: `Version:` becomes `X.Y.Z.9000`, `NEWS.md`
    gets a fresh `(development version)` top heading, and after a first
    release `URL:` gains `https://CRAN.R-project.org/package=<pkg>`.
13. **agent** Downstream, through a seor cascade issue (`fleet.md`): drop this
    package's `Remotes:` entries in the other fleet packages (seor's
    `DESCRIPTION` and its `ARCHITECTURE.md` CRAN table; sitemapr's pin on
    robotstxtr), and raise any floor that waited on this release.
14. **Archive the release on Zenodo and record its version DOI.** Zenodo
    deposits on a GitHub Release on the read-only mirror, not on the tag.
    Skip this and `CITATION.cff` keeps naming the previous version's DOI, or
    none. A package's first release through this step creates its first
    archive. Details and stall recovery: [`github-mirror.md` §5](github-mirror.md).
    - **owner** First archive only: check that the repository is ON in
      Zenodo's GitHub settings, which adds a `release` webhook to the mirror.
    - **agent** Check that the tag object matches on both forges:
      `git ls-remote --tags origin 'refs/tags/vX.Y.Z'`, then the same against
      `https://github.com/bart-turczynski/<pkg>.git`.
    - **owner** Create the GitHub Release from that tag, never letting GitHub
      create one: `gh release create vX.Y.Z --verify-tag -R bart-turczynski/<pkg>`.
    - **agent** Wait for the record. It takes minutes, not seconds. A release
      stuck at "Received" on Zenodo's GitHub page needs the §5.1 recovery,
      which the owner approves.
    - **agent** Check the record's version and title against the release;
      Zenodo reads both from `.zenodo.json` in the tagged archive:
      `curl -s 'https://zenodo.org/api/records?q=conceptrecid:<concept-recid>&allversions=true' | jq '.hits.hits[].metadata | [.version, .title]'`.
      Compare the archived zip with the tag by content, not checksum (§5.2).
    - **agent** Check that doi.org resolves both the concept DOI and the new
      version DOI: `curl -s -o /dev/null -w '%{http_code}\n' https://doi.org/<doi>`
      prints `302`. A `404` means DataCite has not registered it yet: wait,
      and don't commit it (§5.3).
    - **agent** In a follow-up commit, set the version-DOI entry in
      `CITATION.cff` `identifiers:` (value and description) and
      `date-released` to this release. On a first archive, also add `doi:`
      with the concept DOI and its `identifiers:` entry. `python3
      scripts/check-citation.py` must still pass.
