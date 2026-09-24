# Cucumber step definitions. testthat sources `setup-*.R` before the test files,
# which registers these steps before `cucumber::run()` executes the features.
#
# Guarded on `cucumber` being installed so the suggests-only R CMD check
# (`_R_CHECK_DEPENDS_ONLY_=true`, which CRAN runs) degrades gracefully: with the
# package absent the steps simply are not registered and test-cucumber.R skips.
if (requireNamespace("cucumber", quietly = TRUE)) {
  library(cucumber)

  when("I ask for the seor packages", function(context) {
    context$packages <- seor_packages()
  })

  then("the core members are listed", function(context) {
    core_members <- c(
      "rurl",
      "punycoder",
      "pslr",
      "raddr",
      "sitemapr",
      "pagerankr"
    )
    expect_true(all(core_members %in% context$packages))
  })
}
