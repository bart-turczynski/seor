#!/bin/sh
# clean-tmp v2
# Empties tmp/ — logs, build output, agent working files. Everything under tmp/
# is deletable by definition, so this needs no policy and asks no questions.
#
# v2 changed observable behaviour, hence the bump: the reported count is now
# what was actually removed (top-level entries), and a clean that leaves
# anything behind exits 1 instead of printing success.
#
# Orchestration runs delete their own tmp/orchestrate/<run-id>/ on a green final
# gate; this is the backstop for runs that were abandoned instead of finished.
#
#   sh scripts/clean-tmp.sh
set -eu

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
tmp="$root/tmp"

if [ ! -d "$tmp" ]; then
  echo "nothing to clean: $tmp does not exist"
  exit 0
fi

# No globbing. `rm -rf tmp/* tmp/.[!.]*` looked complete and was not: `.[!.]*`
# matches dotfiles whose second character is not a dot, so a name beginning with
# TWO dots (`..foo`) matched neither pattern and survived - while the script
# still printed success. find has no such blind spot, and since $tmp is absolute
# (git rev-parse and pwd both return absolute paths) no argument can begin with
# `-` and be read by rm as an option.
before=$(find "$tmp" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')
# `|| true` so a partial failure still reaches the check below rather than
# aborting under `set -e`. rm's own stderr is deliberately NOT swallowed: the
# old `2>/dev/null` hid the one message that explains a failed clean.
find "$tmp" -mindepth 1 -maxdepth 1 -exec rm -rf {} + || true
after=$(find "$tmp" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')

# Report what was actually removed. The old count came from a `find` taken
# before the delete and counted recursively, so it over-reported even on a
# clean run and claimed success on entries it had left behind.
echo "cleaned $((before - after)) entries from tmp/"
if [ "$after" -ne 0 ]; then
  echo "clean-tmp: $after entries under tmp/ could not be removed" >&2
  exit 1
fi
