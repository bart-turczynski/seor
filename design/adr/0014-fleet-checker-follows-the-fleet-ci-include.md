---
status: accepted
date: 2026-10-29
tracking: SEOR-sehpgsww, SEOR-qgjkyppc
---

# ADR 0014: the fleet checker follows one include, fleet-ci's template

## Context

[ADR 0008](0008-fleet-checker-reads-ci-with-pyyaml.md) made
`scripts/check-fleet-standard.py` read `.gitlab-ci.yml` with PyYAML and fail
closed. It refused `!reference` as an unknown tag, did not follow `include:`,
and set a standing rule: "A `!reference` resolver or `include:` support needs
a new ADR." It named its own revisit trigger: the fleet starting to depend on
`!reference` or `include:`.

[ADR 0012](0012-verification-tiers-replace-per-push-ci.md) fired that trigger.
A migrated package's CI is fleet-ci's template, `templates/r-package.yml`,
pulled in by `include: project:` and pinned by commit SHA, with the package's
own file reduced to settings and `x-*` jobs. The template uses `!reference`
(31 times, checked 2026-10-29), and a package's file may. Judged on the package's file alone, a migrated package has no
jobs to check, so the checker could only report its CI as not judged.
SEOR-sehpgsww (merged in !144) taught the checker to follow that one include.
This ADR records the rule it follows.

This ADR amends ADR 0008 in that one respect; it does not supersede it.
`scripts/check-design.py` has no partial form, and marking ADR 0008
superseded would wrongly retire its parser, fail-closed and resolved-job
decisions, which still hold. ADR 0008's body still says `include:` is not
followed; this ADR is the correction, as
[ADR 0013](0013-fleet-ci-is-private.md) is for ADR 0012.

## Decision

1. **One include is followed, and only in one shape.** A `.gitlab-ci.yml`
   whose `include:` names fleet-ci's project is a migrated package. Its
   include must be exactly one entry, `templates/r-package.yml`, at a 40-hex
   commit SHA. More entries, another file, or a branch or tag name as `ref`
   is a gap. The SHA must be a commit the fleet-ci clone holds, and a `v*`
   tag of the clone must point at it; a clone with no `v*` tags at all
   leaves that one judgment not judged rather than a gap.
2. **The merge is expanded locally.** The template is read at the pinned SHA
   from a fleet-ci clone (`--fleet-ci`, else `FLEET_CI_DIR`), checked out in
   a temporary directory, never in the clone. The package's file is merged
   over it as GitLab merges an include, and the CI rules judge that merged
   configuration. GitLab's CI lint is not asked. fleet-ci's own tools at the
   same SHA judge what they own: `bin/rules-sim` the event table,
   `bin/vendor` the `.fleet-ci/` directory, which must be byte for byte its
   output and nothing else, and `bin/classify --config-json` the
   package's `.fleet-ci.yml`, which must load as that classifier reads it.
3. **`!reference` is read, not resolved, on that path alone.** A migrated
   package's file and the template load with `!reference` kept as an
   unresolved value. Every other file still refuses it as ADR 0008 says.
4. **Every other include is not followed.** A package whose include is not
   fleet-ci's, or whose file does not load with `!reference` allowed, is
   read exactly as ADR 0008 decides.
5. **The self-test fails closed without fleet-ci.** It builds its fixture
   fleet-ci from a clone and needs git and Ruby. Without them it fails,
   naming the fix, unless `SEOR_SKIP_FLEET_CI_SELFTEST=1`, which reports the
   migrated rows as skipped, loudly, and passes.

## Consequences

- Judging a migrated package needs a fleet-ci clone with its `v*` tags, git
  and Ruby, on top of PyYAML. A pinned SHA the clone lacks is a gap (an
  unknown fleet-ci commit: fetch the clone) and leaves the rest of that
  package's CI not judged, so a stale clone is reported, never read as a
  pass.
- fleet-ci is private ([ADR 0013](0013-fleet-ci-is-private.md)), so only a
  machine that can read fleet-ci can judge a migrated package.
- The check is transitional. Both shapes are judged until every package
  migrates; the old-shape checks go under SEOR-jlsdnsjd. For a migrated
  package `scripts/check-toolchain.R` is not compared with seor's copy,
  pending SEOR-bkwtrvhh.
- ADR 0008's other standing rules hold for both shapes: no line-based reading
  of `.gitlab-ci.yml`, no rule matched against raw YAML text.
- Standing rule: do not follow any other include, or resolve `!reference`,
  without a new ADR. Revisit if fleet-ci's template starts including files
  of its own, or if a package needs a second include.
