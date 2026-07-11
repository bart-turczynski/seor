#' seor: install and load the SEO and developer tool suite
#'
#' `seor` is a metapackage. It does not define analysis functions of its own;
#' instead it bundles a curated set of focused packages so that a single
#' `install.packages("seor")` pulls them in and a single `library(seor)`
#' attaches them all, the way `tidyverse` does for its members.
#'
#' Use [seor_packages()] to see the member packages and [seor_conflicts()] to
#' inspect function-name collisions on the search path.
#'
#' @keywords internal
#' @importFrom utils packageVersion
"_PACKAGE"
