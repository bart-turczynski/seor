#' Report function-name conflicts involving seor packages
#'
#' Scans the attached search path for object names exported by more than one
#' package where at least one is a `seor` member, mirroring
#' `tidyverse::tidyverse_conflicts()`. This surfaces cases where, for example,
#' a member package masks a base function or two members export the same name.
#'
#' @return A named list, invisibly. Each name is a conflicting object and each
#'   value is the character vector of attached packages that export it, ordered
#'   as they appear on the search path (earliest = winner).
#'
#' @examples
#' seor_conflicts()
#'
#' @export
seor_conflicts <- function() {
  envs <- grep("^package:", search(), value = TRUE)
  pkgs <- sub("^package:", "", envs)

  exports <- lapply(envs, function(e) ls(as.environment(e)))
  names(exports) <- pkgs

  # Map each object name to the packages (search-path order) that export it.
  owners <- list()
  for (pkg in pkgs) {
    for (obj in exports[[pkg]]) {
      owners[[obj]] <- c(owners[[obj]], pkg)
    }
  }

  conflicted <- Filter(function(o) length(o) > 1, owners)
  involving_seor <- Filter(
    function(o) any(o %in% seor_packages(include_optional = TRUE)),
    conflicted
  )

  invisible(involving_seor[order(names(involving_seor))])
}
