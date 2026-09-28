## Submission note

Not yet submittable to CRAN: the member packages `sitemapr` and `robotstxtr`
are not yet on CRAN, and a metapackage's hard dependencies must all
be on CRAN. Remove the `Remotes:` field and move any then-published members into
`Imports:` before the first CRAN submission.

## Name reuse

The name `seoR` was previously on CRAN (author Daniel Schmeh), archived
2018-06-02 for uncorrected check problems. This package is unrelated and reuses
the freed name (CRAN treats `seor` and `seoR` as the same name).

## BugReports

`BugReports:` is `https://gitlab.com/bart-turczynski/seor/-/issues`, the form
the incoming check asks for. GitLab now serves that address as a 404 to a
signed-out, non-browser client, so the URL check reports it as possibly
invalid; a browser is redirected to the tracker at `/-/work_items`. The
alternative, declaring `/-/work_items`, draws the incoming NOTE instead: a
sibling package's first 1.2.1 upload (pslr) was archived at the pretest for
it, and its resubmission with `/-/issues` was accepted, as rurl 3.0.1 and
raddr 0.1.2 were. So the field keeps `/-/issues`, and every file a person
reads points at `/-/work_items` (SEOR-ocbtrrnl). Expect the 404 NOTE and keep
this paragraph in the submission comments.

## R CMD check results

0 errors | 0 warnings | 1 note

* This is a new submission.

## Test environments

* local: macOS, R 4.6.0
* GitLab CI: Ubuntu (R release, oldrel-1)
* R-hub (rhub::rc_submit()): macOS, Windows, Linux (R devel)

## Downstream dependencies

None — this is a new package.
