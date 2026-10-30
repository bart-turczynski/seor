# seor's CRAN release deltas

Follow the fleet checklist, [`release-checklist.md`](release-checklist.md).
seor's deltas:

- **Step 1: every member is on CRAN first.** A metapackage cannot be
  submitted while any member it declares is off CRAN. When a member is
  published, its `Remotes:` line goes and the "Membership and CRAN status"
  table in `ARCHITECTURE.md` changes with it. The first submission drops
  `Remotes:` entirely.
- **Step 5: turn incoming on.** The local gate runs its check with incoming
  off, as for every package, and seor's `t2-ascran` sets
  `FLEET_INCOMING: "false"` on purpose
  ([ADR 0004](adr/0004-cran-incoming-runs-everywhere-except-seor.md), carried
  forward by [ADR 0012](adr/0012-verification-tiers-replace-per-push-ci.md)),
  so neither a green gate nor a green `RELEASE=1` pipeline says anything
  about incoming feasibility. Run step 5's check, with both incoming
  variables `true`, by hand. Leave `FLEET_INCOMING` alone: dropping it is
  ADR 0004's revisit condition, not a release step.
- **Step 4: keep the name-reuse and `BugReports:` sections** of
  `cran-comments.md`. CRAN treats `seor` and the archived `seoR` as the same
  name.
- **Step 14:** seor's first release is its first Zenodo archive
  (SEOR-dvbdsvuq).
