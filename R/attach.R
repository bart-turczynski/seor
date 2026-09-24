# The core members of the seor suite. These are attached when a user runs
# library(seor). Keep this list in sync with Imports: in DESCRIPTION.
#
# robotstxtr and ssrfr are planned members: they are declared under Suggests
# (not yet on CRAN) and are only attached opportunistically once installed, so
# the suite does not fail to load without them.
core <- c(
  "rurl", # URL parsing and manipulation
  "punycoder", # punycode / internationalized-domain conversion
  "pslr", # public suffix list lookups
  "raddr", # IP address parsing and classification
  "sitemapr", # XML sitemap parsing
  "pagerankr" # PageRank estimation
)

optional <- c("robotstxtr", "ssrfr")

#' The member packages of the seor suite
#'
#' @param include_optional Whether to append planned members (currently
#'   `robotstxtr` and `ssrfr`) that are only attached when already installed.
#'
#' @return A character vector of package names.
#'
#' @examples
#' seor_packages()
#'
#' @export
seor_packages <- function(include_optional = FALSE) {
  if (include_optional) {
    c(core, optional[vapply(optional, is_installed, logical(1))])
  } else {
    core
  }
}

.onAttach <- function(libname, pkgname) {
  attach_now <- c(core, optional[vapply(optional, is_installed, logical(1))])
  needed <- attach_now[!is_attached(attach_now)]

  packageStartupMessage(seor_attach_message(attach_now))

  # package_hooks_linter forbids altering the search path from .onAttach(),
  # which is sound for an ordinary package and is the one thing a metapackage
  # exists to do. tidyverse attaches its members the same way. The exception is
  # scoped to this call rather than switched off in .lintr, so the rule keeps
  # applying everywhere else.
  # nolint start: package_hooks_linter.
  suppressPackageStartupMessages(
    lapply(needed, library, character.only = TRUE, warn.conflicts = FALSE)
  )
  # nolint end
  invisible()
}

is_attached <- function(pkg) {
  paste0("package:", pkg) %in% search()
}

is_installed <- function(pkg) {
  requireNamespace(pkg, quietly = TRUE)
}

# Build the tidyverse-style attach banner: one line per member with its version.
seor_attach_message <- function(pkgs) {
  versions <- vapply(
    pkgs,
    function(p) as.character(packageVersion(p)),
    character(1)
  )
  entries <- paste0("  v ", format(pkgs), " ", versions)
  paste(c("-- Attaching seor packages --", entries), collapse = "\n")
}
