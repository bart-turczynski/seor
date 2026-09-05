This is an R package built the way CRAN verifies it. Follow the tidyverse
[style guide](https://style.tidyverse.org) and
[design guide](https://design.tidyverse.org).

### Dev loop

Install the dev tools locally (`devtools`, `lintr`, `rcmdcheck`); they are not
package dependencies, so they are not in `DESCRIPTION`.

- Load for interactive work: `devtools::load_all()` (or `pkgload::load_all()`).
- Run tests: `testthat::test_local(reporter = "check")`; a single file with
  `testthat::test_local(filter = "matcher")` (matches `test-matcher.R`).
- Regenerate docs: `devtools::document()` — rebuilds `man/` and `NAMESPACE` from
  the roxygen comments in `R/`.
- Verify gate (mirrors CI; the pre-push hook runs exactly this):

  ```sh
  Rscript -e 'lints <- lintr::lint_package(); if (length(lints)) { print(lints); quit(status = 1) }' \
    && Rscript -e 'rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning")'
  ```

- When no R REPL is available, run snippets with `Rscript -e "..."`.

### Formatting

Format R code with [Air](https://posit-dev.github.io/air/):

```bash
air format .
```

Air is a fast, R-free formatter configured in `air.toml` (80 columns, 2-space
indent — the tidyverse style this package targets). The `air-format` pre-commit
hook runs it on every commit and bootstraps its own binary, so you do not need a
global install.

Air owns **layout**; `lintr` owns **logic and best-practice** lints — the two do
not overlap. Do not reformat code unrelated to your change: keep the diff to the
lines you actually touched.

### The linter set

`.lintr` is intentionally aligned with the linter set `goodpractice::gp()` runs
(`goodpractice:::linters_to_lint()`), so the local and CI `lintr::lint_package()`
gate surfaces the same findings as the goodpractice report reviewers run. Without
that alignment a package passes its own lint gate and then trips a pile of
goodpractice findings later. Regenerate the list after a goodpractice upgrade,
comparing against `names(goodpractice:::linters_to_lint())`.

**Keep `.lintr` free of `#` comments.** It is parsed with `read.dcf()`, which
only learned to skip comment lines in R 4.6. On R 4.5 and older a single comment
makes `lint_package()` abort with `Invalid DCF format`, so the rationale lives
here instead. Keep it ASCII too: a non-ASCII byte in `.lintr` comes back
`bytes`-encoded on older R and makes any config error surface as a confusing
`sprintf()` failure instead of the real message.

Documented deviations from the goodpractice set — test-idiom and public-API
reasons a real package hits as it grows past this scaffold:

- `object_name_linter` / `object_usage_linter`: not part of the goodpractice set
  and deliberately NOT added. The cucumber DSL (`when`/`then`/`context`) and the
  testthat helpers read as undefined globals to `object_usage_linter`, and
  packages commonly expose mixed-case or dotted public parameters plus
  `._`-prefixed internal helpers that `object_name_linter` would flag.
- `expect_identical_linter`: off. Suites routinely rely on `expect_equal()`'s
  numeric tolerance (`expect_equal(nrow(x), 2)` compares integer vs double) and
  its string-encoding normalization, both of which `identical()` rejects; a
  wholesale swap means retyping literals for no behavioral gain.
- `implicit_assignment_linter`: off. Tests use the standard
  `expect_warning(res <- f(), "msg")` idiom to capture both the warning and the
  return value (`expect_warning()` returns the condition, not the value).
- `library_require_linter`: off. `tests/testthat.R` and vignette setup chunks
  legitimately call `library()`.
- `undesirable_operator_linter`: configured to keep flagging `<<-`/`->>` but
  allow `:::`, which tests use to reach internal (unexported) functions.
- `strings_as_factors_linter`: off. It flags every `data.frame()` /
  `as.data.frame()` call that omits `stringsAsFactors=`, a portability guard for
  the pre-R-4.0 default. The fleet targets R >= 4.0 where
  `stringsAsFactors = FALSE` is already the default, so every hit is a no-op
  annotation with no behavioral risk. (Dropped 2026-07-18; see pagerankr
  PAGE-iiqjlfxl for the evidence.)

### Code style

- Base pipe `|>`, never magrittr `%>%`.
- `\(x) ...` for one-line anonymous functions; `function(x) { ... }` otherwise.
- `snake_case` for functions and arguments; explicit `pkg::fn()` prefixes.
- Layout is automated by Air (see [Formatting](#formatting)) — don't restyle
  code unrelated to your change, and don't modify deprecated functions.

### Tests

- testthat edition 3. `R/foo.R` is tested by `tests/testthat/test-foo.R`.
- Keep all code inside `test_that()` blocks; shared setup lives in `helper-*.R` /
  `setup-*.R`.
- Prefer specific expectations over `expect_true()` / `expect_false()`.
- Use `expect_snapshot()` for printed output and `expect_snapshot(error = TRUE)`
  for errors.
- Behavior specs are Cucumber `.feature` files under `tests/testthat/`, with
  steps in `setup-steps.R` run via `test-cucumber.R`; `R CMD check` exercises
  them, so there is no separate BDD step.
- New code requires tests.

### Documentation

- Roxygen2 with markdown (`Roxygen: list(markdown = TRUE)`). `man/` and
  `NAMESPACE` are **generated — never edit them by hand**; edit the roxygen
  comments in `R/` and re-run `devtools::document()`.
- Every exported function needs a title, a `@param` per argument, `@return`, and
  runnable `@examples`. Internal helpers stay unexported and undocumented.
- Wrap roxygen comments at 80 columns. Add new help topics to `_pkgdown.yml`;
  do not hand-edit the generated site in `site/`.

### New functions

Ship each new user-facing function with: runnable examples, tests, full argument
docs, `snake_case` arguments with sensible defaults, and argument validation.
Where a `...` separates required from optional arguments, guard it against
unexpected (e.g. misspelled) arguments — for instance with
`rlang::check_dots_empty()`.

### NEWS and generated files

- Add a `NEWS.md` bullet for every user-facing change — one line, no wrapping,
  with the issue/PR number in parentheses. Internal-only refactors go under an
  `## Internal` heading or are omitted. The `news-version` workflow checks that
  the top `NEWS.md` heading matches the `DESCRIPTION` `Version`, so bump both
  together.
- Never hand-edit generated files: `NAMESPACE` or anything under `man/`. Edit
  the roxygen source in `R/` and re-run `devtools::document()`.
