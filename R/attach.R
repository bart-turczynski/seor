# The core members of the seor suite. These are attached when a user runs
# library(seor). Keep this list in sync with Imports: in DESCRIPTION.
#
# robotstxtr is a planned member: it is declared under Suggests (not yet on
# CRAN) and is only attached opportunistically once it is installed, so the
# suite does not fail to load without it.
core <- c(
  "rurl",      # URL parsing and manipulation
  "punycoder", # punycode / internationalized-domain conversion
  "pslr",      # public suffix list lookups
  "sitemapr",  # XML sitemap parsing
  "pagerankr"  # PageRank estimation
)

optional <- "robotstxtr"

#' The member packages of the seor suite
#'
#' @param include_optional Whether to append planned members (currently
#'   `robotstxtr`) that are only attached when already installed.
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

  suppressPackageStartupMessages(
    lapply(needed, library, character.only = TRUE, warn.conflicts = FALSE)
  )
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
