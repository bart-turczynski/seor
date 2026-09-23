---
status: accepted
date: 2026-09-23
tracking: SEOR-hhtzaknn, SEOR-pgammbgo
---

# ADR 0003: CI caching needs a backend AND a writable library path

## Context

Every claim here was verified live on 2026-09-23, because the fleet's written
beliefs about its own CI were wrong in both directions and had already been
reasoned from twice.

### The runners are ours, not GitLab's

The eight repos run on self-hosted Docker runners on one Mac, registered from
`~/.gitlab-runner/config.toml`:

    seor        seor-local-docker          pslr        pslr-local-docker
    pagerankr   pagerankr-local-docker     rurl        seor-local-docker
    punycoder   seor-local-docker          raddr       seor-local-docker
    sitemapr    seor-local-docker          robotstxtr  seor-local-docker

Resolved from `runner.runner_type == "project_type"` on jobs that actually ran.
Several files across the fleet describe "the fleet's shared concurrency-1
runner" as a platform constraint (SEOR-gpafxhua). It is neither shared nor
capped at 1: it is `concurrent` in a local config file, which was 2.

This also re-explains SEOR-pgammbgo's headline number. The ~2 minutes per job
it measured as 58% of CI wall time is local runner pickup latency and slot
contention on one machine, not GitLab queue time. Pickup measured at 151s.

### The cache was broken twice over

**First:** no cache backend was configured. `[runners.cache.s3]`, `.gcs` and
`.azure` were all empty, so every job logged

    No URL provided, cache will not be downloaded from shared cache server.

and cached to its own container, which was then destroyed.

**Second, and the one that actually mattered:** even with a backend, the
package library was never in the cache. The `.r` template sets
`R_LIBS_USER: "$CI_PROJECT_DIR/.r-lib"` and caches `.r-lib`, with a comment
claiming that moves R's library somewhere cacheable. It does not.
rocker/r-ver's `Renviron.site` puts `/usr/local/lib/R/site-library` FIRST in
`.libPaths()` and `R_LIBS_USER` third:

    $ docker run --rm -e R_LIBS_USER=/tmp/rlib rocker/r-ver:4.5.1 \
        Rscript -e '.libPaths()'
    [1] "/usr/local/lib/R/site-library" "/usr/local/lib/R/library"
    [3] "/tmp/rlib"

R installs into the first writable entry, so every package went into the
image's site-library and died with the container. Overriding `R_LIBS_SITE` in
the environment does not help — `Renviron.site` is read later and wins.

Measured directly from the cache archive after a full seor pipeline:

    .pak-cache   1185 entries   77.8 MiB    pak's downloaded sources
    .r-lib          1 entry      0.0 MiB    the installed library: EMPTY

So the cache carried downloads but not builds. On arm64 that is the wrong
half: p3m publishes binaries only for amd64, so this fleet compiles from
source and the build is the expensive part.

### What that cost, measured on seor

Five full `main` pipelines, same commit, job-duration sums:

    baseline    no cache,       concurrent=2   24.5m compute   33.1m wall
    backend     cold cache,     concurrent=4   29.2m compute   30.1m wall
    backend     warm cache,     concurrent=4   26.9m compute   28.2m wall
    + libPaths  populating run, concurrent=4   12.5m compute
    + libPaths  fully warm,     concurrent=4    5.5m compute    9.7m wall

The backend alone made compute **worse** — 10% worse than no cache even fully
warm — because each job paid to download and re-upload a 71 MiB archive whose
useful half was missing. The wall-time improvement at that stage came from
`concurrent`, not from caching.

With the library path fixed the archive grew from 71 MiB to 208 MiB
(`.r-lib`: 1 empty entry → 9445 entries, 273.4 MiB uncompressed) and the
picture inverted: **78% less compute and 71% less wall time than the
no-cache baseline.** Per job, warm against baseline:

    verify    333.8s ->  95.9s      coverage  290.0s -> 67.7s
    readme    418.4s ->  72.2s      pages     420.3s -> 84.2s

## Decision

**Three changes, of which only the third makes the cache pay.**

1. **A cache backend.** MinIO on the runner host provides S3 storage:

       container  gitlab-runner-cache   quay.io/minio/minio
       volume     gitlab-runner-cache-data
       published  127.0.0.1:9000 (API), 127.0.0.1:9001 (console)
       bucket     runner-cache

   Loopback-bound; reachable from job containers as `host.docker.internal:9000`.
   `[runners.cache]` uses `Type = "s3"` with `Shared = false` on the three
   runners that serve R repos. `Shared = false` keeps the cache path namespaced
   per project, which matters because one runner serves six repos with
   different closures — verified in the observed key,
   `runner/E0IOwCyfb/project/85027484/...`.

2. **`concurrent` raised from 2 to 4.**

3. **The library path moved for real**, by appending to `Rprofile.site` in
   `before_script` rather than by setting an environment variable:

       echo '.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))' \
         >> "${R_HOME}/etc/Rprofile.site"

   Verified in the image: `.libPaths()[1]` becomes the cached directory and
   `install.packages("jsonlite")` lands in it. site-library stays on the path
   behind it, so the image's own packages (docopt, littler) remain visible.

**Boundary.** (1) and (2) are host-side and apply to all eight repos at once.
(3) is a `.gitlab-ci.yml` change and is applied **to seor only** in this ADR.
The other seven repos carry the same latent no-op and each needs the same
line; that is tracked separately, not assumed done. The four unrelated Docker
runners on the host and the shell runner are deliberately untouched.

## Consequences

The cache now carries the built library, so a job whose `DESCRIPTION` has not
changed since the last upload skips the source builds rather than repeating
them. This is the change that was always intended; the two earlier layers were
prerequisites that did nothing on their own.

**Parallel jobs in the same stage cannot warm each other.** Cache upload
happens at job end, so with `concurrent = 4` jobs that start together all start
cold. Measured: `verify` uploaded at 10:38:04, `readme` started 10:37:24 and
missed. The cache pays across *stages* and across *pipelines*, not within a
stage — and raising `concurrent` trades some of the caching win for wall time.
Do not tune one of these without re-measuring the other.

**Raising `concurrent` makes individual jobs slower.** Four jobs on one Mac
contend for CPU: `verify` went 333.8s to 475.9s while sharing the machine with
`readme`. Pipeline wall time still fell. Judge this dial on wall time, never on
job duration.

**It may also make jobs flakier.** One `news-version` failure during this work
was an Alpine package index fetch timing out; it passed on retry. Four jobs
competing for network makes that class of flake more likely, so treat a lone
network timeout as a retry candidate before a regression.

**The cache is an optimisation, not a guarantee.** The key is `DESCRIPTION`;
any dependency change invalidates it and the next pipeline is cold. Do not read
a slow pipeline as a regression before checking whether the key moved.

**Do not trust `R_LIBS_USER` to place an R library.** Setting it is necessary
but not sufficient in a rocker image, and it fails silently — the variable is
set, the directory exists, the cache uploads, and nothing is in it. If a future
image changes its `Renviron.site`, re-verify with `.libPaths()` rather than
assuming the variable took effect.

**The single point of failure is unchanged and is now the main risk.** CI for
eight repos depends on one laptop being awake, with no alarm. Jobs queue for
111 minutes and then redden `main` with `stuck_pending_no_matching_runners`,
which reads like a code failure and is not (SEOR-hhtzaknn).

**Do not diagnose a stuck pipeline from the compute quota.** The namespace is
over its Free allowance (406/400), which produces the same symptom on shared
runners, and the two coincided on 2026-09-23. Self-hosted minutes do not count
against the quota. Always resolve `runner_type` on a job that actually ran
before blaming a runner pool.

**Revisit if** the runners move off the laptop, a second host joins, or p3m
starts serving arm64 binaries — the last would make the build cost that
justifies this caching largely disappear.
