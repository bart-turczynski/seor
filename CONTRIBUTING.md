# Contributing

Report bugs and request features in the GitLab issue tracker:
<https://gitlab.com/bart-turczynski/seor/-/work_items>. Report security issues
privately as described in `SECURITY.md`. Send changes as merge requests on
GitLab; the GitHub repository is a read-only mirror.

New code needs tests, and each user-facing change needs one `NEWS.md` bullet.
A merge request must pass the local gate below.

Install dependencies:

```sh
Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
```

Verification is fleet-ci's local gate, which runs in the fleet Docker image
(settings in `.fleet-ci.yml`; it needs Docker and a `docker login
registry.gitlab.com`). Install the hooks once per clone, from the package
root:

```sh
pre-commit install
.fleet-ci/pre-push --install
```

From then on the gate runs on every push, on each pushed ref's tip, followed
by the pre-commit pre-push hooks. `pre-commit install -f` (which installs
both hook types, from `.pre-commit-config.yaml`'s
`default_install_hook_types`) and `pre-commit install -f --hook-type
pre-push` replace that hook and drop the gate; re-run
`.fleet-ci/pre-push --install` after either. Without `-f`,
`pre-commit install` keeps the gate (pre-commit's migration mode). To run the
gate by hand on `HEAD`:

```sh
.fleet-ci/gate auto
```

The gate checks the committed tree, never uncommitted edits: commit the output
of `devtools::document()` before pushing. A docs-only change runs spelling and
`pkgdown::check_pkgdown()`; any other runs T0's checks, then lintr, the
docs-drift (`man/`, `NAMESPACE` and `DESCRIPTION` must match what the pinned
roxygen2 regenerates), URL, README, NEWS-heading, citation, BugReports and
logo-metadata checks, then `R CMD check --as-cran` with the testthat suite,
failing on any ERROR or WARNING.

The gate's check runs with CRAN incoming feasibility off, and so does seor's
`t2-ascran` in CI (`FLEET_INCOMING: "false"`). seor is a metapackage with
members that are not yet on CRAN, so that step always reports an ERROR
(non-mainstream dependencies, the `Remotes:` field, the archived `seoR` name
clash) — a permanent, known state rather than a regression. Every other
`--as-cran` check still runs. For the first CRAN submission, run the incoming
check separately (step 5 in the release deltas below). See
[`design/ci.md`](https://gitlab.com/bart-turczynski/seor/-/blob/main/design/ci.md)
for the tiers and what CI runs.

The source and test layout, and durable project context, live in
`ARCHITECTURE.md` and `design/`: the CRAN release deltas in
[`design/release-deltas.md`](https://gitlab.com/bart-turczynski/seor/-/blob/main/design/release-deltas.md),
and what to do when CI jobs sit in `pending` in
[`design/stuck-pending-runbook.md`](https://gitlab.com/bart-turczynski/seor/-/blob/main/design/stuck-pending-runbook.md).

Keep local-only planning state in `_scratch/`. Do not commit `_scratch/`, `.fp/`, secrets, dependency folders, build outputs, or generated caches.
