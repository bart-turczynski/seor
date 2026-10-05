#!/usr/bin/env Rscript
#
# Generated-docs drift gate: fails if man/, NAMESPACE or DESCRIPTION differ
# from what roxygen2 would regenerate from the roxygen comments in R/.
#
# Why this exists: a stale .Rd is still perfectly valid .Rd, so nothing else in
# the verify gate can see it. lintr::lint_package() reads R/ and never looks at
# man/; spelling::spell_check_package() reads man/ as it is; R CMD check
# --as-cran validates the Rd it is given, not whether that Rd still matches its
# source comment. The fleet's logo sweep added man/figures/logo.svg without
# re-running devtools::document(), so man/pslr-package.Rd went on describing a
# package with no logo; nothing in pslr's gate noticed, and it was fixed by
# hand in pslr !89 (SEOR-oopopupm). Regenerating and diffing is the only thing
# that catches it (SEOR-nwfmerhu). Ported from pslr's
# scripts/check-docs-drift.R, itself from robotstxtr's dev/check-docs-drift.R,
# written after the same failure there (ROBO-cbzemsnq).
#
# DESCRIPTION is watched too. roxygenise() owns two of its fields:
# Config/roxygen2/version (pinned below, so it cannot move here) and Collate,
# which it rewrites from @include tags. A stale Collate is drift like a stale
# .Rd.
#
# Roxygen runs through its default loader, the same one devtools::document()
# uses, so what this gate demands is exactly what the documented fix produces.
# seor has no src/, so that load compiles nothing.
#
# The pre-push gate never runs this in place: roxygenise() writes into the
# directory it is given, so on drift it rewrites man/, NAMESPACE and
# DESCRIPTION there. The pre-push hook (scripts/docs-drift.sh) therefore runs
# it against its own `git archive` export of the commit being pushed
# (PRE_COMMIT_TO_REF, else HEAD), never the working tree. CI's `docs-drift`
# job runs it in place, in a checkout of the pushed commit that nothing else
# uses (SEOR-fhrisfpt).
#
# Usage (from the package root):
#   Rscript scripts/check-docs-drift.R [package-dir]
#
# On drift the script prints the diff, exits 1, and LEAVES the regenerated
# files in place: run by hand against a working tree, the fix is then already
# applied and only needs committing. Run by scripts/docs-drift.sh, the
# regenerated files are in a throwaway export, so the working tree is never
# touched.
#
# Self-test: Rscript scripts/check-docs-drift.R --self-test

# --- self-test ---------------------------------------------------------------
#
# Runs this script, as its own process, against a throwaway fixture package:
# docs missing, in sync, changed and stale, with git on PATH and without it.
# It needs roxygen2 (any version: the fixture pins the installed one) and
# nothing else.

# The path of this script, as Rscript was given it.
self_test_script <- function() {
  file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  normalizePath(sub("^--file=", "", file_arg[[1L]]))
}

# A directory of links to every program on PATH except git, so a run with it
# as its whole PATH sees a machine with no git, as on a CI image that ships
# none (rocker/r-ver).
path_without_git <- function() {
  bin <- tempfile("docs-drift-no-git-")
  dir.create(bin)
  dirs <- strsplit(Sys.getenv("PATH"), .Platform$path.sep, fixed = TRUE)[[1L]]
  dirs <- unique(dirs[nzchar(dirs) & dir.exists(dirs)])
  progs <- unlist(lapply(dirs, list.files, full.names = TRUE))
  progs <- progs[!dir.exists(progs)]
  progs <- progs[!duplicated(basename(progs)) & basename(progs) != "git"]
  file.symlink(progs, file.path(bin, basename(progs)))
  bin
}

fixture_package <- function(roxygen_version) {
  pkg <- tempfile("docs-drift-fixture-")
  dir.create(file.path(pkg, "R"), recursive = TRUE)
  writeLines(
    c(
      "Package: docsdriftfixture",
      "Title: Docs-Drift Self-Test Fixture",
      "Version: 0.0.1",
      "Description: A fixture.",
      "License: MIT",
      "Encoding: UTF-8",
      paste0("Config/roxygen2/version: ", roxygen_version)
    ),
    file.path(pkg, "DESCRIPTION")
  )
  writeLines(
    c(
      "#' Add one",
      "#'",
      "#' @param x A number.",
      "#' @return x plus one.",
      "#' @export",
      "f <- function(x) x + 1"
    ),
    file.path(pkg, "R", "f.R")
  )
  pkg
}

copy_package <- function(pkg) {
  dest <- tempfile("docs-drift-case-")
  dir.create(dest)
  file.copy(list.files(pkg, full.names = TRUE), dest, recursive = TRUE)
  dest
}

edit_lines <- function(path, from, to) {
  writeLines(sub(from, to, readLines(path), fixed = TRUE), path)
}

# Run this script on `pkg` in its own process, with `path` as its PATH.
run_check <- function(script, pkg, path = Sys.getenv("PATH")) {
  out <- suppressWarnings(system2(
    file.path(R.home("bin"), "Rscript"),
    c(shQuote(script), shQuote(pkg)),
    stdout = TRUE,
    stderr = TRUE,
    env = paste0("PATH=", shQuote(path))
  ))
  status <- attr(out, "status")
  list(status = if (is.null(status)) 0L else status, out = out)
}

self_test <- function() {
  if (!requireNamespace("roxygen2", quietly = TRUE)) {
    stop("The self-test runs roxygen2, which is not installed.", call. = FALSE)
  }
  script <- self_test_script()
  no_git <- path_without_git()
  check <- function(tag, ok, res = NULL) {
    message(if (ok) "ok    " else "FAIL  ", tag)
    if (!ok && !is.null(res)) {
      message(paste0("      | ", res$out, collapse = "\n"))
    }
    stats::setNames(ok, tag)
  }
  has <- function(res, lines) all(lines %in% res$out)
  no_diff <- function(res) !any(startsWith(res$out, "diff --git "))

  base <- fixture_package(as.character(utils::packageVersion("roxygen2")))

  # Added: nothing roxygen generates is there yet. The run regenerates in
  # place, which leaves `base` in sync for the cases below.
  added <- run_check(script, base, no_git)
  in_sync <- run_check(script, base)

  changed_pkg <- copy_package(base)
  edit_lines(file.path(changed_pkg, "R", "f.R"), "Add one", "Add two")
  changed_git_pkg <- copy_package(changed_pkg)
  changed <- run_check(script, changed_pkg, no_git)
  changed_git <- run_check(script, changed_git_pkg)

  # Deleted: an Rd roxygen generated once, for a topic R/ no longer has.
  stale_pkg <- copy_package(base)
  rd <- readLines(file.path(stale_pkg, "man", "f.Rd"))
  writeLines(
    sub("{f}", "{g}", rd, fixed = TRUE),
    file.path(stale_pkg, "man", "g.Rd")
  )
  stale <- run_check(script, stale_pkg, no_git)

  verdicts <- c(
    check(
      "the no-git PATH has no git",
      !file.exists(file.path(no_git, "git"))
    ),
    check(
      "added, no git: exits 1, NAMESPACE and man/f.Rd listed as missing",
      added$status == 1L &&
        has(
          added,
          c(
            "  Missing (roxygen would create) (2):",
            "    NAMESPACE",
            "    man/f.Rd"
          )
        ) &&
        no_diff(added),
      added
    ),
    check(
      "in sync: exits 0 and says so",
      in_sync$status == 0L && any(startsWith(in_sync$out, "Docs in sync")),
      in_sync
    ),
    check(
      "changed, no git: exits 1, man/f.Rd listed as changed",
      changed$status == 1L &&
        has(changed, c("  Changed (1):", "    man/f.Rd")) &&
        no_diff(changed),
      changed
    ),
    check(
      "deleted, no git: exits 1, man/g.Rd listed as stale",
      stale$status == 1L &&
        has(stale, c("  Stale (roxygen would delete) (1):", "    man/g.Rd")) &&
        no_diff(stale),
      stale
    ),
    check(
      "changed, with git: exits 1 and prints the diff, paths package-relative",
      nzchar(Sys.which("git")[[1L]]) &&
        changed_git$status == 1L &&
        has(
          changed_git,
          c(
            "--- committed/man/f.Rd",
            "+++ regenerated/man/f.Rd",
            "-\\title{Add one}",
            "+\\title{Add two}"
          )
        ),
      changed_git
    ),
    # PIN (today's verdict): with no git the report does not say the diff
    # was left out.
    check(
      "no git: the report does not say the diff was omitted (today)",
      !any(grepl("diff is omitted", changed$out, fixed = TRUE)),
      changed
    )
  )
  if (all(verdicts)) {
    message(sprintf(
      "check-docs-drift self-test: %d checks ok",
      length(verdicts)
    ))
    return(0L)
  }
  message(sprintf(
    "check-docs-drift self-test: %d of %d checks FAILED",
    sum(!verdicts),
    length(verdicts)
  ))
  1L
}

args <- commandArgs(trailingOnly = TRUE)
if (identical(args, "--self-test")) {
  quit(status = self_test())
}
pkg <- if (length(args) > 0L) args[[1L]] else "."

desc_path <- file.path(pkg, "DESCRIPTION")
if (!file.exists(desc_path)) {
  stop(sprintf(
    "No DESCRIPTION at %s (run from the package root?)",
    normalizePath(pkg, mustWork = FALSE)
  ))
}

# Exact-equality version gate. roxygen2 changes its output formatting between
# releases, so an unpinned runner reports version skew as drift -- and when the
# installed version is the newer one, roxygen2 quietly rewrites
# Config/roxygen2/version in DESCRIPTION, which is itself an unwanted diff.
# Refusing to guess keeps every failure this gate reports a real one.
# scripts/check-toolchain.R (the check-toolchain pre-push hook) reports the
# same skew first, as a machine problem.
field <- "Config/roxygen2/version"
desc <- read.dcf(desc_path)
if (!field %in% colnames(desc)) {
  stop(sprintf(
    paste0(
      "DESCRIPTION has no %s field. This gate needs that pin to tell real doc ",
      "drift apart from roxygen2 version skew; it is written automatically by ",
      "running devtools::document() with the intended roxygen2 version."
    ),
    field
  ))
}
# unname(): indexing a read.dcf() matrix carries the column name along, and a
# named string is never identical() to the plain one from packageVersion().
pinned <- unname(trimws(desc[1L, field]))
installed <- as.character(utils::packageVersion("roxygen2"))
if (!identical(pinned, installed)) {
  stop(sprintf(
    paste0(
      "roxygen2 version skew: DESCRIPTION pins %s = %s, but roxygen2 %s is ",
      "installed. Either install the pinned version ",
      "(pak::pkg_install(\"roxygen2@%s\")), or adopt the newer roxygen2 ",
      "deliberately by running devtools::document() and committing the ",
      "resulting man/, NAMESPACE and DESCRIPTION changes together."
    ),
    field,
    pinned,
    installed,
    pinned
  ))
}

# The generated surface roxygen2 owns, relative to the package root.
# DESCRIPTION exists (checked above) and is listed whole: see the header.
watched_files <- function(root) {
  rd <- list.files(
    file.path(root, "man"),
    pattern = "[.]Rd$",
    recursive = TRUE
  )
  c(
    "DESCRIPTION",
    if (file.exists(file.path(root, "NAMESPACE"))) "NAMESPACE",
    if (length(rd) > 0L) file.path("man", rd)
  )
}

# Copy a set of package-relative paths into a flat mirror directory, so the two
# states can be diffed as trees.
mirror <- function(root, files, dest) {
  for (f in files) {
    target <- file.path(dest, f)
    dir.create(dirname(target), recursive = TRUE, showWarnings = FALSE)
    if (!file.copy(file.path(root, f), target)) {
      stop(sprintf("could not copy %s into %s", f, dest), call. = FALSE)
    }
  }
  dest
}

read_bytes <- function(path) readBin(path, "raw", file.size(path))

committed_files <- watched_files(pkg)
committed_dir <- mirror(pkg, committed_files, tempfile("docs-committed-"))

message(sprintf(
  "Regenerating man/, NAMESPACE and DESCRIPTION with roxygen2 %s ...",
  installed
))
roxygen2::roxygenise(pkg)

regenerated_files <- watched_files(pkg)
added <- setdiff(regenerated_files, committed_files)
removed <- setdiff(committed_files, regenerated_files)
changed <- Filter(
  function(f) {
    !identical(
      read_bytes(file.path(committed_dir, f)),
      read_bytes(file.path(pkg, f))
    )
  },
  intersect(committed_files, regenerated_files)
)

if (length(added) == 0L && length(removed) == 0L && length(changed) == 0L) {
  message(
    "Docs in sync: man/, NAMESPACE and DESCRIPTION match the roxygen comments ",
    "in R/."
  )
  quit(status = 0L)
}

regenerated_dir <- mirror(pkg, regenerated_files, tempfile("docs-regenerated-"))

report_paths <- function(label, paths) {
  if (length(paths) > 0L) {
    message(sprintf("  %s (%d):", label, length(paths)))
    message(paste0("    ", paths, collapse = "\n"))
  }
}

message("")
message("Generated documentation is out of date.")
report_paths("Changed", changed)
report_paths("Missing (roxygen would create)", added)
report_paths("Stale (roxygen would delete)", removed)

# git diff --no-index works outside a repository, which matters because this
# runs against a git-archive export that is not one. Exit status 1 just means
# "differences found", so the non-zero status warning is expected.
diff_out <- tryCatch(
  suppressWarnings(system2(
    "git",
    c(
      "diff",
      "--no-index",
      "--src-prefix=committed/",
      "--dst-prefix=regenerated/",
      "--",
      shQuote(committed_dir),
      shQuote(regenerated_dir)
    ),
    stdout = TRUE,
    stderr = TRUE
  )),
  error = function(e) character()
)
if (length(diff_out) > 0L) {
  # git renders a --no-index path as <prefix><absolute path minus its leading
  # slash>, so the temp directory sits between the side label and the
  # package-relative path. Strip it to leave "committed/man/foo.Rd".
  strip_dir <- function(x, dir) {
    gsub(paste0(sub("^/", "", dir), "/"), "", x, fixed = TRUE)
  }
  diff_out <- strip_dir(diff_out, committed_dir)
  diff_out <- strip_dir(diff_out, regenerated_dir)
  message("")
  message(paste(diff_out, collapse = "\n"))
}

message("")
message(
  "Fix: run devtools::document() and commit the resulting man/, NAMESPACE ",
  "and DESCRIPTION changes."
)
quit(status = 1L)
