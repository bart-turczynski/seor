---
status: accepted
date: 2026-10-30
tracking: SEOR-jlsdnsjd
---

# ADR 0015: every package includes fleet-ci, and the checker judges no other shape

## Context

[ADR 0014](0014-fleet-checker-follows-the-fleet-ci-include.md) taught
`scripts/check-fleet-standard.py` to follow fleet-ci's include while the
fleet migrated. It kept the old shape alive beside it: Decision 3 read
`!reference` only for a package that includes fleet-ci, Decision 4 read
every other `.gitlab-ci.yml` as [ADR 0008](0008-fleet-checker-reads-ci-with-pyyaml.md)
decides, with the hand-written CI checks that went with it, and its
consequences said both shapes are judged until every package migrates.

That has happened. All nine packages include fleet-ci's
`templates/r-package.yml` at a pinned SHA (each `.gitlab-ci.yml` read
2026-10-30). SEOR-jlsdnsjd removes the old-shape half of the checker:
its hand-written job checks, its pandoc-pin reading through
`check-toolchain.R --pandoc-assignments`, and the self-test rows for both.

`scripts/check-design.py` has no partial form, so this ADR supersedes ADR
0014 as a whole and carries forward the decisions of it that still hold.

## Decision

1. **Every package includes fleet-ci.** A `.gitlab-ci.yml` that includes
   fleet-ci's project is judged as ADR 0014's Decisions 1 and 2 decide,
   carried forward unchanged: the include is exactly one entry,
   `templates/r-package.yml`, at a 40-hex SHA a `v*` tag of the fleet-ci
   clone points at; the template is read at that SHA and the package's
   file merged over it locally; fleet-ci's `bin/rules-sim`, `bin/vendor`
   and `bin/classify --config-json` at that SHA judge what they own.
2. **`!reference` loads everywhere.** Every `.gitlab-ci.yml` the checker
   reads loads with `!reference` kept as an unresolved value; it is
   still never resolved. Every other unknown tag is still a load error.
   This replaces ADR 0014's Decision 3.
3. **No other shape is judged.** A file whose include is not fleet-ci's,
   or that has no fleet-ci include at all, is one gap, a CI gap: its CI
   and local gate are not judged further, and the run stays complete. A
   file with fleet-ci's include beside another entry is a gap too
   (Decision 1), and the rest of its CI is not judged. A file that does
   not load leaves its CI and local gate not judged and the run
   incomplete. This replaces ADR 0014's Decision 4.
4. **The self-test skips only what needs the clone.** The CI and
   local-gate rows build a fixture fleet-ci from the clone and need git
   and Ruby. Without them the self-test fails, naming the fix, unless
   `SEOR_SKIP_FLEET_CI_SELFTEST=1`, which reports those rows as skipped,
   loudly, and passes. The package-content rows (badges, README, logo,
   files, `DESCRIPTION`, seor's own logos as the logo-metadata anchor)
   need no clone and run either way. This replaces ADR 0014's Decision 5.

## Consequences

- The checker holds one CI shape. A package that drops the include is
  reported as a gap at once, not judged by rules for a shape the fleet no
  longer has.
- Judging any package's CI needs a fleet-ci clone with its `v*` tags, git
  and Ruby, as ADR 0014 said for a migrated one; fleet-ci is private
  ([ADR 0013](0013-fleet-ci-is-private.md)).
- A machine without the clone still runs the content half of the
  self-test, so a change to the badge, README, logo or `DESCRIPTION`
  rules is tested there too.
- `check-toolchain.R` keeps its `.gitlab-ci.yml` pin reader and its
  `--pandoc-assignments` and `--pandoc-unread` flags; the checker no
  longer calls them. A package's pandoc pin is `.fleet-ci/toolchain`.
- ADR 0008's other standing rules hold: no line-based reading of
  `.gitlab-ci.yml`, no rule matched against raw YAML text.
- Standing rule: do not follow any other include, resolve `!reference`,
  or bring back an old-shape check without a new ADR. Revisit if fleet-ci's
  template starts including files of its own, or if a package needs a
  second include.
