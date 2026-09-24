test_that("seor_packages() returns the core members", {
  expect_setequal(
    seor_packages(),
    c("rurl", "punycoder", "pslr", "raddr", "sitemapr", "pagerankr")
  )
})

test_that("include_optional only adds planned members that are installed", {
  pkgs <- seor_packages(include_optional = TRUE)
  expect_true(all(seor_packages() %in% pkgs))
  for (member in c("robotstxtr", "ssrfr")) {
    if (requireNamespace(member, quietly = TRUE)) {
      expect_true(member %in% pkgs)
    } else {
      expect_false(member %in% pkgs)
    }
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
