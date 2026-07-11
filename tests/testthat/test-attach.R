test_that("seor_packages() returns the core members", {
  expect_setequal(
    seor_packages(),
    c("rurl", "punycoder", "pslr", "sitemapr", "pagerankr")
  )
})

test_that("include_optional only adds robotstxtr when it is installed", {
  pkgs <- seor_packages(include_optional = TRUE)
  expect_true(all(seor_packages() %in% pkgs))
  if (requireNamespace("robotstxtr", quietly = TRUE)) {
    expect_true("robotstxtr" %in% pkgs)
  } else {
    expect_false("robotstxtr" %in% pkgs)
  }
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
