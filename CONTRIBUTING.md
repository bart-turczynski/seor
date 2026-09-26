# Contributing

Install dependencies:

```sh
Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
```

Run verification:

```sh
Rscript -e 'lints <- lintr::lint_package(); if (length(lints)) { print(lints); quit(status = 1) }' && Rscript -e 'rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning", env = c(callr::rcmd_safe_env(), "_R_CHECK_CRAN_INCOMING_" = "false"))'
```

The `env =` argument disables only the CRAN incoming-feasibility step. seor is a
metapackage with members that are not yet on CRAN, so that step always reports an
ERROR (non-mainstream dependencies, the `Remotes:` field, the archived `seoR` name
clash) — a permanent, known state rather than a regression. Every other
`--as-cran` check still runs. Re-enable it for the first CRAN submission.

## Stuck-pending runbook

CI for seor and its members runs on self-hosted Docker runners on the
maintainer's Mac, not on GitLab.com shared runners. When the Mac sleeps, or
`gitlab-runner` or Docker stops, jobs sit in `pending` and eventually fail
with `failure_reason: stuck_pending_no_matching_runners`, `runner: None` and
a long `queued_duration`. **That is infrastructure, not a code failure.**
Don't debug the code; bring the runner back and retry.

The `runner-heartbeat` Worker checks every 15 minutes. When a fleet job has
been pending for more than 20 minutes, it opens a `stuck-runner` issue in
`bart-turczynski/runner-heartbeat`, and that issue is the alert. To recover:

1. Wake the Mac and start Docker Desktop if it isn't running
   (`docker info` should succeed).
2. Start the runner: `brew services start gitlab-runner`. Confirm that it is
   polling: `glab api "projects/:id/runners?type=project_type"` should show
   the project's `*-local-docker` runner `online`.
3. Pending jobs are usually picked up within a minute. Retry the ones that
   already failed: `glab ci retry <job-id>`, or
   `glab api --method POST "projects/:id/pipelines/<pipeline-id>/retry"` for
   a whole pipeline.
4. Close the `stuck-runner` issue. No new alert opens while one is open.

See the project README for the source, behavior-specification, and test layout.
Durable project context lives in `ARCHITECTURE.md` and `design/`.

Keep local-only planning state in `_scratch/`. Do not commit `_scratch/`, `.fp/`, secrets, dependency folders, build outputs, or generated caches.
