---
status: accepted
date: 2026-10-29
tracking: SEOR-kisadphx
---

# ADR 0013: fleet-ci is private, so its images need authenticated pulls

## Context

[ADR 0012](0012-verification-tiers-replace-per-push-ci.md) put the fleet's
CI templates and images in fleet-ci, `bart-turczynski/fleet-ci`, and described
it as a public GitLab repository. It assumed that anyone could read the
template and pull the images anonymously. On 2026-10-29 the owner decided
that fleet-ci is a private project instead.

This ADR amends ADR 0012 in that one respect; it does not supersede it.
`scripts/check-design.py` has no partial form, and marking ADR 0012
superseded would wrongly retire the rest of it. ADR 0012's body still reads
"public"; this ADR is the correction.

## Decision

fleet-ci is a private GitLab project. Everything that reads it must
authenticate:

- **Images.** `registry.gitlab.com/bart-turczynski/fleet-ci/<variant>` needs
  an authenticated pull. Locally, run `docker login registry.gitlab.com` once;
  the owner needs the same login to push a rebuilt image. In a package's CI
  the runner authenticates with `CI_JOB_TOKEN`, which works only if fleet-ci's
  CI/CD job token allowlist admits the nine package projects. That allowlist
  is a project setting the owner makes in fleet-ci.
- **Template.** `include: project: bart-turczynski/fleet-ci` resolves only for
  a pipeline whose user can read fleet-ci. For the weekly runs that user is
  the schedule owner; for a release or tag pipeline it is whoever starts it.

## Consequences

- Forks and outside contributors cannot read the template or pull the images,
  so they cannot run T2 or T3, nor T1, which runs in the fleet image. Their
  changes are verified when the owner gates them.
- A package added to the fleet needs an entry in fleet-ci's job token
  allowlist before its CI can pull an image.
- A schedule whose owner loses read access to fleet-ci stops creating a
  working pipeline. A red or missing weekly run is a finding.
- Every other part of ADR 0012 stands: the tiers, the classifier, the pass
  stamp, the SHA pin, the event table, the job names and the switches.
- Revisit if fleet-ci is made public; that needs a new ADR superseding this
  one.
