---
status: accepted
date: 2026-10-03
tracking: SEOR-plnwieyf, SEOR-tahlljtx, SITE-kgpdfhoh
---

# ADR 0007: one fleet standard for badges and checks

## Context

The nine R packages grew their README badges, CI jobs and schedules one at a
time, and an audit of each one's `main` on 2026-10-03 found no two alike.
Measured on the live READMEs that day:

- rurl, punycoder and pslr show CRAN and DOI badges but no pipeline or
  coverage badge. seor, robotstxtr and pagerankr show a pipeline badge; seor's
  README comment says FOSSA is omitted because it does not cover R.
- sitemapr shows only lifecycle, Zenodo and Best Practices badges. A README
  comment forbids CI badges "permanently" (SITE-kgpdfhoh). The rule was
  written when sitemapr's CI badges all rendered from GitHub Actions on a
  repository that was then private, and its workflows had been deleted. Its CI
  now runs on GitLab, so the reason no longer holds.
- pslr shows FOSSA badges under a `git+github.com` locator, the read-only
  mirror. FOSSA's free plan allows five projects per account.
- Six packages' CI sets a GitLab coverage regex; rurl, raddr and sitemapr set
  none. robotstxtr's coverage badge read 95.29%.
- The declared R floors (`Depends: R (>= ...)`) range from 3.5.0 (punycoder)
  to 4.1.0, and the fleet had no shared rule for choosing one.

The owner asked for "everything everywhere": the same badges and checks in all
nine. That needs one written standard the per-package issues cite and a checker
can test, and a record of the choices in it that were contested.

## Decision

[`design/fleet-standard.md`](../fleet-standard.md) is the standard. The choices
it rests on:

1. **The full badge set, in every package.** Seventeen slots in a fixed order,
   the same on the README and as GitLab project badges. A badge whose subject
   does not exist yet (a CRAN release, a GitLab Release, a DOI) is added when
   it does, by a release-checklist step, not left out by choice. Excluded:
   contributor counts (they count bot and agent identities), stars and forks,
   anything rendered from the GitHub mirror, OpenSSF Scorecard (no public
   results for GitLab projects since 2023-11-20) and the shields CRAN
   monthly-downloads badge (it renders "404: badge not found").
2. **Coverage of at least 95%, as a CI failure.** The threshold is strict and
   never lowered (owner decision 3). A package under it adds tests.
3. **FOSSA allocation.** The five free projects go to rurl, ssrfr and seor,
   then two held for the non-R repositories, then raddr and pslr if a slot
   frees up. Locators are on `gitlab.com`, never the mirror.
4. **sitemapr's "no CI badges" rule is reversed.** It answered a private
   repository and GitHub Actions workflows that no longer exist.
   SITE-kgpdfhoh's comment goes when sitemapr meets the standard.
5. **OpenSSF Best Practices stays at passing.** Silver is out of scope.
6. **The R floor is measured, not assumed** (owner decision 2). A package's
   floor is the oldest R minor version on which it installs and passes
   `R CMD check` with its dependencies, probed at minor granularity. `Depends`
   is set to it, raised or lowered, with a NEWS bullet, and a `deep-check` leg
   tests it. No member declares a floor below its fleet dependencies' highest,
   so seor's is the highest in the fleet.

## Consequences

- **Badges show bad news.** A red pipeline, a failing license scan or a
  coverage drop is now on every README. That is the point; fix the cause, never
  remove the badge.
- **Each package gets a "meets the fleet standard" issue**, and those issues
  cite fleet-standard.md instead of copying it. A conformance checker
  (SEOR-myokihrl) tests against the same file.
- **Raising coverage comes first in some packages.** The gate goes in with the
  tests that clear it, not with a lower number.
- **Floors move both ways.** A package may lower its declared floor when the
  probe shows it works there, and the order of floor changes across the fleet
  matters: dependencies first.
- **FOSSA projects under GitHub locators** (rurl, pslr and punycoder answered
  on 2026-10-03) use slots the allocation needs. Retiring them takes the
  owner's FOSSA login.
- Do not add a badge outside the seventeen, or drop one, without a new ADR.
  Revisit the FOSSA allocation if the plan's project limit changes, and
  Scorecard if its public results for GitLab resume.
