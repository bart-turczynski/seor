#!/bin/sh
# scripts/docs-drift.sh -- the generated-docs drift gate, run by the pre-push
# `docs-drift` hook (SEOR-nwfmerhu). A stale .Rd is still valid .Rd, so
# neither lint, spelling nor R CMD check can see it. This regenerates man/,
# NAMESPACE and DESCRIPTION with roxygen and fails, printing the diff, when
# they differ from what is committed. The hook runs ahead of spelling and the
# URL check, which read man/ as it is.
#
# It checks the commit being pushed, in its OWN `git archive` export, never
# the working tree: roxygenise() writes into the directory it is given.
# pre-commit exports the pushed commit to a pre-push hook as
# PRE_COMMIT_TO_REF, so `git push origin other-branch` checks other-branch
# rather than whatever is checked out; outside a push (or for a push
# pre-commit hands no ref, such as a whole history down to its root commit)
# it is HEAD. An uncommitted roxygen edit is therefore not seen until it is
# committed.
#
# The check that runs is this checkout's scripts/check-docs-drift.R, not the
# exported commit's copy, so the gate is the one on the branch doing the
# pushing.
#
# The export lives in a subshell with its own EXIT trap, so it is removed on
# every way out: a pass, drift, a failed export, a roxygen error, Ctrl-C. The
# INT/TERM/HUP traps turn a signal into an ordinary exit, which is what runs
# the EXIT trap. Each step checks its own status.
#
# Run it from the package root (pre-commit does):
#   sh scripts/docs-drift.sh

ref="${PRE_COMMIT_TO_REF:-HEAD}"
check="$(pwd)/scripts/check-docs-drift.R"
status=0

echo "== generated docs in sync at ${ref} (scripts/check-docs-drift.R)"
if [ ! -f "$check" ]; then
  echo "docs-drift: $check not found (run from the package root)" >&2
  exit 2
fi

(
  if ! docsdir="$(mktemp -d "${TMPDIR:-/tmp}/seor-docs-drift.XXXXXX")"; then
    echo "docs-drift: could not create a temporary directory for the docs export" >&2
    exit 3
  fi
  trap 'rm -rf "$docsdir"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap 'exit 129' HUP
  # Archive to a file, then extract: POSIX sh has no pipefail, so in
  # `git archive | tar -x` a failed archive would hide behind tar's status.
  if ! git archive --format=tar -o "$docsdir/export.tar" "$ref"; then
    echo "docs-drift: could not export ${ref} with git archive" >&2
    exit 3
  fi
  if ! mkdir "$docsdir/pkg" || ! tar -x -f "$docsdir/export.tar" -C "$docsdir/pkg"; then
    echo "docs-drift: could not unpack the git archive of ${ref}" >&2
    exit 3
  fi
  Rscript "$check" "$docsdir/pkg"
) || status=$?

if [ "$status" -eq 3 ] || [ "$status" -ge 128 ]; then
  exit "$status"
elif [ "$status" -ne 0 ]; then
  echo "docs-drift: the generated docs at ${ref} are out of date (or the check could not run; see the output above) -- if they are stale, run devtools::document() and commit the result" >&2
  exit 1
fi
echo "docs-drift: man/, NAMESPACE and DESCRIPTION match the roxygen comments in R/"
