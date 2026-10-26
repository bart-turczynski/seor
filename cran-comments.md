## Submission note

Not yet submittable to CRAN: the member packages `sitemapr`, `robotstxtr` and
`ssrfr` are not yet on CRAN, and a metapackage's hard dependencies must all be
on CRAN. Remove the `Remotes:` field before the first CRAN submission.

## Name reuse

The name `seoR` was previously on CRAN (author Daniel Schmeh), archived
2018-06-02 for uncorrected check problems. This package is unrelated and reuses
the freed name (CRAN treats `seor` and `seoR` as the same name).

## BugReports

`BugReports:` is `https://gitlab.com/bart-turczynski/seor/-/work_items`. The
incoming check suggests an `/issues` path instead ("which should likely
be ..."). On gitlab.com, `/-/issues` answers 404 to a non-browser client,
`tools::check_url_db()` included, while `/-/work_items` answers 200. On
2026-10-23 Uwe Ligges called this NOTE a bug in the check for GitLab and
invited the `/-/work_items` form on the pslr 1.2.2 submission, which CRAN
then published. Quote the local check's wording of the NOTE here when
submitting, and keep this paragraph in the submission comments (ADR 0011).

## R CMD check results

0 errors | 0 warnings | 1 note

* This is a new submission.

## Test environments

* local: macOS, R 4.6.0
* GitLab CI: Ubuntu (R release, oldrel-1)
* R-hub (rhub::rc_submit()): macOS, Windows, Linux (R devel)

## Downstream dependencies

None — this is a new package.
