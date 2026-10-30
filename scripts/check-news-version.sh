#!/bin/sh
# The news-version gate, a cheap gate of the fleet-ci local gate
# (.fleet-ci.yml). The top NEWS.md heading must be "(development version)" or
# exactly the DESCRIPTION Version, which catches a stale heading left in at
# release. The `news-version` gate of the former scripts/gates.sh, which the
# CI `gates` job ran on every push to main, unchanged. Run it from the
# package root.
#
#   sh scripts/check-news-version.sh
set -eu

version="$(grep -E '^Version:' DESCRIPTION | head -n1 | sed -E 's/^Version:[[:space:]]*//')"
heading="$(grep -m1 -E '^# ' NEWS.md | sed -E 's/^#[[:space:]]+(seor[[:space:]]+)?//')"
echo "DESCRIPTION Version : '$version'"
echo "Top NEWS heading    : '$heading'"
if [ "$heading" = "(development version)" ] || [ "$heading" = "$version" ]; then
  echo "OK: NEWS heading and version are consistent."
else
  echo "Top NEWS.md heading ('$heading') is neither '(development version)' nor the DESCRIPTION Version ('$version'). Update NEWS.md before release."
  exit 1
fi
