---
status: accepted
date: 2026-09-23
tracking: SEOR-tullzdwb, SEOR-ocbtrrnl
---

# ADR 0004: CRAN incoming feasibility runs in every repo except seor

## Context

`R CMD check --as-cran` runs a "CRAN incoming feasibility" step that resolves
every URL in `DESCRIPTION` and the `man/` pages, among other submission-time
checks. `_R_CHECK_CRAN_INCOMING_ = "false"` suppresses it. Whether each repo
suppresses it had never been recorded, and the fleet's written beliefs about it
were wrong in both directions.

### The check is not theoretical: it is the only thing that found the 404

punycoder's gate runs incoming. On 2026-09-22 that is the *only* reason anyone
discovered that the fleet's `BugReports:` URLs were dead — GitLab moved issues
to `/-/work_items` and every `/-/issues` link began returning 404. It unwound
into SEOR-ocbtrrnl and five repo-tier repoint tickets.

It is still the only thing reporting it. Measured on untouched `main` on
2026-09-23, punycoder's verify gate exits 0 with exactly one NOTE:

    checking CRAN incoming feasibility ... NOTE
    Found the following (possibly) invalid URLs:
      URL: https://gitlab.com/bart-turczynski/punycoder/-/issues
        From: DESCRIPTION
              man/punycoder-package.Rd
        Status: 404

A repo that suppresses incoming would have shipped that 404 indefinitely.

### seor genuinely cannot run it

seor is a metapackage whose members are not on CRAN. Incoming feasibility
therefore always ERRORs there — it is checking for a submission that cannot
succeed yet. `AGENTS_LANG.md` already carries the standing instruction not to
drop the suppression to fix a red gate, and that instruction is correct.

### What the fleet actually does, measured 2026-09-23

The gate is spelled seven different ways across the eight repos. There is no
fleet-level verify command, and any document asserting one is false in seven
repos:

    repo        gate implementation
    seor        inline R in .pre-commit-config.yaml
    punycoder   inline R in .pre-commit-config.yaml
    rurl        tools/verify-on-push.sh -> tools/verify.R
    sitemapr    tools/verify.R
    pslr        tools/verify.sh
    raddr       data-raw/verify.sh
    robotstxtr  dev/verify.sh
    pagerankr   .githooks/pre-push

Grepping each of those for `_R_CHECK_CRAN_INCOMING_` gives the real picture:
**seor is the only repo whose verify gate suppresses it.** Every other repo
already complies with the decision below.

Two findings that a grep over `.pre-commit-config.yaml` alone would have
reported wrongly, and that the enforcement below has to survive:

- **raddr suppresses incoming in two files that are not its gate.**
  `data-raw/check-r-floor.sh` and `data-raw/check-dep-floor.sh` both set
  `_R_CHECK_CRAN_INCOMING_=false`, with a comment giving the reason (the image
  carries no LaTeX). These are hand-run floor checks against old R and old
  dependency versions, not the pre-push gate. A naive repo-wide grep flags
  raddr as non-compliant when its gate is compliant.
- **pslr suppresses a different variable.** `tools/verify.sh` and
  `.gitlab-ci.yml` set `_R_CHECK_CRAN_INCOMING_REMOTE_`, which disables only
  the *network* half of incoming — the URL resolution — while leaving the local
  checks on. That is the half that found the 404. pslr therefore reads as
  compliant on the variable this ADR names while being exempt from the specific
  check that justifies it.

## Decision

CRAN incoming feasibility runs in the verify gate of every repository in the
fleet **except seor**.

seor keeps `_R_CHECK_CRAN_INCOMING_ = "false"` and keeps the reason recorded in
`AGENTS_LANG.md`. That is a named exception, not an untidied inconsistency, and
it is not to be "fixed".

The boundary, stated precisely:

- **In scope:** the pre-push verify gate, and the CI job that runs the same
  chain. These are what the rule governs.
- **Out of scope:** hand-run diagnostic scripts that check an old R or an old
  dependency floor (raddr's two floor scripts). They may suppress incoming, and
  must say why in a comment at the suppression.
- **Also covered:** `_R_CHECK_CRAN_INCOMING_REMOTE_`. Suppressing the remote
  half defeats the URL resolution that is the entire justification for this
  ADR, so it counts as suppression and needs the same exception handling.
  pslr's existing use of it is grandfathered pending a decision under its own
  ticket, and is recorded here so it is not mistaken for compliance.

A further exception is added only after a package demonstrates a reproducible
incoming failure that cannot be corrected and is irrelevant to CRAN
feasibility.

## Consequences

**Enforcement tests the policy, not the config text.** Because the gate is
spelled seven ways, a grep over `.pre-commit-config.yaml` is not enforcement —
it would pass six repos that the grep cannot see into, and fail raddr for two
files the rule does not govern. The gate wrapper logs its effective setting
(`incoming=on` or `incoming=off`), refuses `off` for any package but the named
exception, and requires the exception's reason to be present. CI asserts on the
logged value. A gate that cannot state what it ran is not evidence that it ran.

**Expect this to surface work rather than close it.** Turning a check on where
it has never run is the same class of measurement as attaching a runner to a
project whose pipelines had never executed — punycoder hid a CI defect for two
weeks that way. The measurement above says every repo already runs incoming, so
the surprise budget here is small; the real work is the enforcement that keeps
it true.

**"Pipeline on main is green" remains a meaningless acceptance criterion.**
Eight repos with seven gates and a 2-to-12 spread of CI jobs do not mean the
same thing by it. Acceptance criteria across this backlog should name the job
that proves the claim.

**Revisit if** the members reach CRAN, which removes seor's exception entirely
and makes this ADR a fleet-uniform rule with no carve-out.
