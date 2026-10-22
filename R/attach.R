# The members of the seor suite. These are attached when a user runs
# library(seor). Keep this list in sync with Imports: in DESCRIPTION.
core <- c(
  "rurl", # URL parsing and manipulation
  "punycoder", # punycode / internationalized-domain conversion
  "pslr", # public suffix list lookups
  "raddr", # IP address parsing and classification
  "sitemapr", # XML sitemap parsing
  "pagerankr", # PageRank estimation
  "robotstxtr", # robots.txt parsing
  "ssrfr" # server-side request forgery guard for outbound requests
)

#' The member packages of the seor suite
#'
#' @param include_optional Ignored. Every member is a hard dependency, so
#'   there are no optional members left to include; the argument stays so
#'   existing calls keep working.
#'
#' @return A character vector of package names.
#'
#' @examples
#' seor_packages()
#'
#' @export
seor_packages <- function(include_optional = FALSE) {
  core
}

.onAttach <- function(libname, pkgname) {
  needed <- core[!is_attached(core)]

  packageStartupMessage(seor_attach_message(core))

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
