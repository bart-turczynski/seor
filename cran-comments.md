## Submission note

Not yet submittable to CRAN: the member packages `sitemapr`, `pagerankr` and
`robotstxtr` are not yet on CRAN, and a metapackage's hard dependencies must all
be on CRAN. Remove the `Remotes:` field and move any then-published members into
`Imports:` before the first CRAN submission.

## Name reuse

The name `seoR` was previously on CRAN (author Daniel Schmeh), archived
2018-06-02 for uncorrected check problems. This package is unrelated and reuses
the freed name (CRAN treats `seor` and `seoR` as the same name).

## R CMD check results

0 errors | 0 warnings | 1 note

* This is a new submission.

## Test environments

* local: macOS, R 4.6.0
* GitHub Actions: macOS, Windows, Ubuntu (R devel, release, oldrel-1)

## Downstream dependencies

None — this is a new package.
