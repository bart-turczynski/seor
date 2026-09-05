# Contributing

Install dependencies:

```sh
Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
```

Run verification:

```sh
Rscript -e 'lints <- lintr::lint_package(); if (length(lints)) { print(lints); quit(status = 1) }' && Rscript -e 'rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning")'
```

See the project README for the language-specific source, behavior-specification,
and test layout. Durable project context lives in `docs/`.

Keep local-only planning state in `_scratch/`. Do not commit `_scratch/`, `.fp/`, secrets, dependency folders, build outputs, or generated caches.
