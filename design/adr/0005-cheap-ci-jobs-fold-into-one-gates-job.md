---
status: accepted
date: 2026-09-24
tracking: SEOR-pgammbgo, SEOR-ihmntqzm
---

# ADR 0005: Cheap verify jobs fold into one `gates` job, for wall time only

## Context

[ADR 0003](0003-fleet-ci-runs-on-self-hosted-runners.md) recorded the cache half
of this work. This is the other half, and it needs writing down for the same
reason: the decision and its per-repo reasoning live in eight `.gitlab-ci.yml`
headers and eight `NEWS.md` files, which is not where an agent preparing a
release looks. Every number below was measured from the GitLab jobs API on a
real pipeline, not estimated.

### The tax is real, and larger than first recorded

SEOR-pgammbgo opened on a fleet-wide measurement: 63.1 minutes of compute
spread across 149.0 minutes of wall time, so **86 minutes — 58% — was time
between jobs rather than work.** Re-measured on 2026-09-23 the per-job figure
was at or above two minutes, not below it:

    pagerankr  pid 2873246622  9 jobs  compute 7.3m  wall 31.1m  overhead 23.8m
    punycoder  pid 2873134629  9 jobs  compute 6.7m  wall 24.2m  overhead 17.5m

pagerankr's wall time had *grown* from the 26.5m first recorded. The extreme
case was rurl: two jobs totalling 42 seconds of compute, 13.6 minutes of wall.

### Two premises the original ticket reasoned from were wrong

Both were corrected by ADR 0003 and both matter here, because they are the
reasons the obvious conclusion — "cut job count to cut cost" — does not follow.

1. **These are not GitLab SaaS shared runners.** They are self-hosted Docker
   runners on one Mac. The ~2-minute gap is local pickup latency and slot
   contention (measured at 151s), not queue time in a shared pool, and
   `concurrent` is a number in a local config file rather than a platform cap.
2. **Job count was never the dominant cost.** The dominant cost was every job
   recompiling the same dependency closure because the cache never held the
   built library. Fixing that took seor from 24.5m to 5.5m of compute
   **without consolidating anything** — still six jobs.

So consolidation had to be re-justified on wall time alone, after the cache
work had already taken the compute win it was originally credited with.

### What consolidation is actually worth, measured

The clean read is each repo's pipeline immediately *before* its fold against
the one immediately *after* — same day, same `concurrent`, cache already fixed,
only the fold differing:

    repo        jobs RUN   compute        wall          overhead
    robotstxtr     9 -> 5   6.1->5.9m   13.3-> 9.4m   7.2->3.6m  (-50%)
    pagerankr      8 -> 7   6.2->6.8m   13.5->12.2m   7.3->5.4m  (-26%)

(Jobs *run in that pipeline*, which is not the declared count below — several
jobs in each repo are rules-gated to tags, schedules or hand-started runs.)

**Overhead and wall move; compute does not** — flat in one repo, 10% worse in
the other. A fleet-wide before/after table exists on SEOR-dyzgzyot but is not a
clean read on this question: rurl, which was neither cache-fixed nor
consolidated, posts a 76% overhead improvement by itself, so the `concurrent`
2->4 raise and machine load confound every comparison taken across that
morning. Each row above is also a single sample on a high-variance machine —
raddr's `check:linux-devel` measured 410.9s, 165.3s and 68.2s the same day — so
the compute column supports "not a compute win" and nothing finer.

## Decision

**Fold each repo's cheap verify-stage jobs (`lint`, `readme`, `news-version`,
`codemeta`) into a single `gates` job on rurl's shape. Keep `check`, `coverage`
and `pages` separate** — they are genuinely different concerns with different
failure meanings. Decided by the owner on 2026-09-23.

Four conditions bound it.

**1. The harness must run every gate, then report.** A verdict list replaces
five red/green signals with one, and that is only an acceptable trade if the
single run still tells you everything the five would have. So the harness runs
*every* gate, captures each exit status, prints one final summary naming all
failures, and exits nonzero afterwards. A fail-fast harness that stops at the
first failure guts the mitigation: you trade five signals for one and still
re-run to find the second failure.

This was verified against rurl's `tools/verify.R` before porting (stages are
independent, results accumulate, `VERDICT: FAIL -- <labels>` prints before
`quit(status = 1)`), and then **proved by mutation in each new harness by
breaking two gates at once** and requiring both to be named in one summary:

    robotstxtr  81-char line + stray byte in a vendored LICENSE
                -> "VERDICT: FAIL -- lint, vendor-fidelity:yandex", 6/6 ran
    pagerankr   corrupted NEWS.md heading + codemeta.json version
                -> "VERDICT: FAIL -- news-version, codemeta", lint ran between
    punycoder   81-char line + bad NEWS.md heading
                -> "VERDICT: FAIL -- lint, news-version", readme ran between

A fail-fast harness passes a single-failure test. That is why the mutation
breaks two.

**2. `citation-version` does not fold.** It keeps its own `python:3.13-alpine`
job. See the consequence below — this is the boundary that a folding agent gets
wrong.

**3. Fold on pipeline frequency, not job count.** The tax is paid per pipeline.
A repo that creates no pipeline on merge has nothing to save however many jobs
it declares.

**4. Never fold for compute or quota reasons.** The table above is the standing
refusal.

### As applied

Counted as jobs DECLARED in each `.gitlab-ci.yml`, verified by grep on
2026-09-24 rather than taken from the ticket, which was wrong on two rows:

    repo        declared      MR    state
    robotstxtr    9 ->  5     !20   merged
    pagerankr    10 ->  8     !37   merged
    punycoder    12 -> 10     !26   parked on an owner action, see below
    raddr         4 ->  4     !54   merged; no-fold rationale recorded in-file
    seor         11            n/a  not folded; the cache took its win instead
    pslr         12            n/a  not a candidate
    rurl          4            n/a  already this shape; the shape was ported FROM it
    sitemapr      3            n/a  below the threshold worth folding

SEOR-pgammbgo records robotstxtr as `10 -> 5` and pslr as 15 jobs. Neither
matches the files: robotstxtr declared 9 before its fold (`73b97c1^`) and pslr
declares 12. The corrected figures are above; the conclusions drawn from them
are unaffected, since both rows were about direction, not magnitude.

Two candidates were removed on measurement rather than on reading the file.
**pagerankr's `rurl-floor` is not release-shaped** — 4/4 recent runs `success`
at 60-85s, so it already runs on every push; guarding it would have removed a
working check. `check-oldrel` is 4/4 `manual` at 0.0s, never executed, and was
the real candidate. **pslr is not a candidate despite declaring twelve jobs,
among the most in the fleet**, because its `workflow:` block creates no
pipeline on a push,
a branch, a merge request, a tag or a schedule — only two hand-started runs.

punycoder's fold is written and reviewed but **must not merge** until pipeline
schedule 4427280 carries `SCHEDULE_KIND=dependency-audit`; the same branch
tightens `osv-audit`/`security-audit` to require it, and the live schedule
carries `variables: []`, so merging first would silently quiet the fleet's only
working security schedule (SEOR-ihmntqzm). It therefore carries the worst
overhead in the fleet, 12.3m, which is what the park costs.

## Consequences

**Folding jobs is folding IMAGES, not just commands.** This is the defect this
work nearly shipped, twice, independently. Two repos each produced a branch
that folded `citation-version` into a `gates` job on the R image. `rocker/r-ver`
ships no python3, so the command was preserved verbatim and the interpreter was
not:

    docker run --rm -v "$PWD":/w -w /w rocker/r-ver:4.6 \
      sh -c 'python3 scripts/check-citation.py --self-test'   -> exit 127

**`glab ci lint` passes on this bug.** It validates YAML, not whether a binary
exists in the image, so the only check that catches it is executing the gate
inside the image the job really uses. Installing python3 into the R image was
measured at ~6.1s and rejected anyway: it would give the folded job a network
and apt dependency its other members do not have, so an apt hiccup would take
unrelated checks down with it. `check-citation.py` is stdlib-only and offline by
design, which is exactly why it had a minimal image.

The risk class is bounded and worth stating so a future fold can be scoped
quickly: **it exists only where a folded job carried its own `image:` override.**
Jobs inheriting the default image cannot have an interpreter swapped out.

**Diagnosis costs a log read.** One red `gates` job replaces five named ones, so
the pipeline view no longer says which concern failed. Condition 1 is what keeps
that to a log read rather than a re-run.

**Parallelism inside the stage is spent, deliberately.** The folded gates run
serially in one runner acquisition. That is the trade: one pickup latency
instead of five, against no in-stage overlap. ADR 0003 notes the related tension
— parallel jobs in the same stage cannot warm each other's cache — so the two
dials must not be tuned without re-measuring both.

**Do not cite this ADR for a compute or quota argument.** Consolidation is a
wall-time fix and nothing else. A future proposal to fold jobs to save compute
should be refused on the table above.

**Revisit if** post-change measurement shows the lost parallelism lengthens the
critical path, if failures routinely need the whole bundle re-run to diagnose an
intermittent check, or if the runners move off the single laptop — the last
would change the pickup latency this entire decision is priced against.
