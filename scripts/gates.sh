#!/bin/sh
# scripts/gates.sh -- the cheap verify-stage checks, folded into one CI job
# (`gates` in .gitlab-ci.yml) per design/adr/0005: README drift, spelling and
# news-version. `lint` stays in `verify`, whose chain mirrors the pre-push
# hook; `citation-version` keeps its own python image (ADR 0005, condition 2).
#
# Every gate runs whatever an earlier one did, then ONE verdict line names
# every failure, and only then does the script exit nonzero (ADR 0005,
# condition 1). It installs nothing: the `gates` job does that first. Run it
# from the package root.

failed=""

run_gate() {
  name="$1"
  shift
  echo "== gate: $name"
  if "$@"; then
    echo "-- $name: PASS"
  else
    echo "-- $name: FAIL"
    failed="$failed $name"
  fi
}

# README.md is knit from README.Rmd, so a hand-edit to the markdown is lost on
# the next render. Blank-line-only differences don't count: pandoc versions
# disagree about the blank line after `<!-- badges: start -->`, and the image's
# git 2.43 still exits 1 on a blank-only diff under --ignore-blank-lines, so
# the test is on the diff's output (SEOR-oaqnafzs, SEOR-kaqtnovh).
gate_readme() {
  Rscript -e 'devtools::build_readme()' || return 1
  readme_diff=$(git diff --ignore-blank-lines -- README.md)
  if [ -n "$readme_diff" ]; then
    printf '%s\n' "$readme_diff"
    echo "README.md is out of sync with README.Rmd. Run devtools::build_readme() and commit the result."
    return 1
  fi
}

# The same command as the pre-push `spelling` hook (SEOR-mtbzfroz).
gate_spelling() {
  Rscript -e 'bad <- spelling::spell_check_package(); if (nrow(bad)) { print(bad); quit(status = 1) }'
}

# The top NEWS.md heading must be "(development version)" or exactly the
# DESCRIPTION Version, which catches a stale heading left in at release.
gate_news_version() {
  version="$(grep -E '^Version:' DESCRIPTION | head -n1 | sed -E 's/^Version:[[:space:]]*//')"
  heading="$(grep -m1 -E '^# ' NEWS.md | sed -E 's/^#[[:space:]]+(seor[[:space:]]+)?//')"
  echo "DESCRIPTION Version : '$version'"
  echo "Top NEWS heading    : '$heading'"
  if [ "$heading" = "(development version)" ] || [ "$heading" = "$version" ]; then
    echo "OK: NEWS heading and version are consistent."
  else
    echo "Top NEWS.md heading ('$heading') is neither '(development version)' nor the DESCRIPTION Version ('$version'). Update NEWS.md before release."
    return 1
  fi
}

run_gate readme gate_readme
run_gate spelling gate_spelling
run_gate news-version gate_news_version

if [ -n "$failed" ]; then
  echo "VERDICT: FAIL --$failed"
  exit 1
fi
echo "VERDICT: PASS -- readme, spelling, news-version"
