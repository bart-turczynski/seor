test_that("seor_packages() returns every member", {
  members <- c(
    "rurl",
    "punycoder",
    "pslr",
    "raddr",
    "sitemapr",
    "pagerankr",
    "robotstxtr",
    "ssrfr"
  )
  expect_setequal(seor_packages(), members)
})

test_that("include_optional no longer changes the member set", {
  expect_identical(seor_packages(include_optional = TRUE), seor_packages())
  expect_identical(seor_packages(include_optional = FALSE), seor_packages())
})

test_that("every member is a hard dependency in DESCRIPTION", {
  desc <- read.dcf(
    system.file("DESCRIPTION", package = "seor"),
    fields = c("Imports", "Suggests")
  )
  deps <- function(field) {
    x <- desc[, field]
    if (is.na(x)) {
      return(character())
    }
    x <- trimws(strsplit(x, ",", fixed = TRUE)[[1]])
    sub("[[:space:]]*\\(.*$", "", x)
  }
  # Every hard dependency but base R's utils is a member, and attached.
  expect_setequal(seor_packages(), setdiff(deps("Imports"), "utils"))
  expect_length(intersect(seor_packages(), deps("Suggests")), 0L)
})

test_that("the attach banner names every package with a version", {
  msg <- seor_attach_message("utils")
  expect_match(msg, "Attaching seor packages")
  expect_match(msg, "utils")
})

test_that("seor_conflicts() returns a named list without error", {
  conflicts <- seor_conflicts()
  expect_type(conflicts, "list")
})
