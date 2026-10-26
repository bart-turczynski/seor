# Contributing

Report bugs and request features in the GitLab issue tracker:
<https://gitlab.com/bart-turczynski/seor/-/work_items>. Report security issues
privately as described in `SECURITY.md`. Send changes as merge requests on
GitLab; the GitHub repository is a read-only mirror.

New code needs tests, and each user-facing change needs one `NEWS.md` bullet.
A merge request must pass the verification command below.

Install dependencies:

```sh
Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
```

Run verification:

```sh
Rscript -e 'lints <- lintr::lint_package(); if (length(lints)) { print(lints); quit(status = 1) }' && Rscript -e 'res <- rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning", env = c(callr::rcmd_safe_env(), "_R_CHECK_CRAN_INCOMING_" = "false")); if (!identical(as.integer(res$status), 0L)) stop("R CMD check exited with status ", res$status, "; the run did not complete.", call. = FALSE)'
```

The `env =` argument disables only the CRAN incoming-feasibility step. seor is a
metapackage with members that are not yet on CRAN, so that step always reports an
ERROR (non-mainstream dependencies, the `Remotes:` field, the archived `seoR` name
clash) — a permanent, known state rather than a regression. Every other
`--as-cran` check still runs. Re-enable it for the first CRAN submission.

See the project README for the source and test layout.
Durable project context lives in `ARCHITECTURE.md` and `design/`: the CRAN
release deltas in `design/release-deltas.md`, and what to do when CI jobs sit
in `pending` in `design/stuck-pending-runbook.md`.

Keep local-only planning state in `_scratch/`. Do not commit `_scratch/`, `.fp/`, secrets, dependency folders, build outputs, or generated caches.
