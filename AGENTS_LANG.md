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
- Verify gate: `.fleet-ci/gate auto`, fleet-ci's local gate, which the
  pre-push hook runs in the fleet image (`CONTRIBUTING.md`, `design/ci.md`).
  Its checks are listed in `.fleet-ci.yml`.

  Its `R CMD check --as-cran` runs with CRAN incoming feasibility off, and
  seor's `t2-ascran` does too (`FLEET_INCOMING: "false"`), because that step
  always ERRORs for this metapackage while its members are off CRAN. Every
  other `--as-cran` check still runs. Do not turn it on to "fix" anything —
  see the comment in `.gitlab-ci.yml`.

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
  and deliberately NOT added. The testthat helpers read as undefined globals to
  `object_usage_linter`, and packages commonly expose mixed-case or dotted
  public parameters plus `._`-prefixed internal helpers that
  `object_name_linter` would flag.
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
- `case_folding_linter`: an addition (fleet sweep SEOR-rxxuzhmc). It bans
  `tolower()`, `toupper()` and `casefold()`, which follow `LC_CTYPE`: a Turkish
  or Azeri locale maps `I` to a dotless `ı`. Map ASCII letters with `chartr()`
  instead. Tests are not exempt: lintr 3.4 turns a directory key in
  `exclusions` into a whole-file exclusion for every linter.

`strings_as_factors_linter` is off, as in goodpractice, which dropped it in 1.2.0
(ropensci-review-tools/goodpractice#321). It only guarded the pre-R-4.0
`data.frame()` default, and the fleet targets R >= 4.0. A package whose R floor
is below 4.0 keeps it on and documents that as a deviation (punycoder). The
fleet turned it off on 2026-07-18, before goodpractice did (pagerankr
PAGE-iiqjlfxl).

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

- A `NEWS.md` bullet is one terse line, only for a change a package user acts
  on or notices, with at most one issue or MR reference; no housekeeping and
  no `## Internal` section. The full rule is the fleet standard's
  ("`NEWS.md` bullets" in `design/fleet-standard.md`), and the `news-terse`
  pre-push hook (`scripts/check-news.py NEWS.md`) refuses a bullet that
  breaks it.
- The `news-version` gate (`scripts/check-news-version.sh`, a cheap gate of
  the local gate) passes when the top `NEWS.md`
  heading reads "(development version)" or names the `DESCRIPTION`
  `Version`; the release checklist renames it at release.
- Never hand-edit generated files: `NAMESPACE` or anything under `man/`. Edit
  the roxygen source in `R/` and re-run `devtools::document()`.

### A red gate on an untouched tree

The gate runs in the image the fleet-ci pin names, so this machine's R
library cannot turn it red. A dependency that moved on CRAN can: the gate
resolves the dependencies afresh on every run. The pre-push `check-toolchain`
hook (`scripts/check-toolchain.R`) still checks this machine: roxygen2's
installed version against this package's `Config/roxygen2/version`, any
installed package built under a newer R than the one running, and the local
pandoc against the fleet image's, so a local `devtools::document()` or
`build_readme()` writes what the gate accepts (SEOR-tcytizic).

If the gate is red on a tree you have not touched, say so and keep the
evidence (`FLEET_GATE_KEEP=<dir>` keeps the container's output) rather than
assuming your change caused it.
