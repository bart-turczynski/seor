# Contributing

Install dependencies:

```sh
Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
```

Run verification:

```sh
Rscript -e 'lints <- lintr::lint_package(); if (length(lints)) { print(lints); quit(status = 1) }' && Rscript -e 'rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning", env = c(callr::rcmd_safe_env(), "_R_CHECK_CRAN_INCOMING_" = "false"))'
```

The `env =` argument disables only the CRAN incoming-feasibility step. seor is a
metapackage with members that are not yet on CRAN, so that step always reports an
ERROR (non-mainstream dependencies, the `Remotes:` field, the archived `seoR` name
clash) — a permanent, known state rather than a regression. Every other
`--as-cran` check still runs. Re-enable it for the first CRAN submission.

See the project README for the source, behavior-specification, and test layout.
Durable project context lives in `ARCHITECTURE.md` and `design/`.

Keep local-only planning state in `_scratch/`. Do not commit `_scratch/`, `.fp/`, secrets, dependency folders, build outputs, or generated caches.
