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

## CI runners

seor's CI does not run on GitLab.com's shared runners. Its jobs run on
self-hosted Docker runners on the maintainer's Mac (`seor-local-docker`,
`pslr-local-docker`, `pagerankr-local-docker`), which serve the whole fleet.
The namespace's 400-minute GitLab Free quota governs only the shared-runner
fallback, and that quota is exhausted, so nothing else picks a job up when
those runners are away. See
[ADR 0003](https://gitlab.com/bart-turczynski/seor/-/blob/main/design/adr/0003-fleet-ci-runs-on-self-hosted-runners.md).

**A job that sits `pending` and then fails with
`stuck_pending_no_matching_runners` is an infrastructure failure, not a code
failure.** The Mac was asleep or the runner was stopped. Do not debug the
change it ran against.

To confirm, read the job from the API (from a checkout of this repo, `:id`
resolves to the project):

```sh
glab api projects/:id/jobs/<job_id>
```

An infrastructure failure has `"failure_reason": "stuck_pending_no_matching_runners"`,
`"runner": null` and a long `"queued_duration"`. A job that ran and failed
names its runner and has a different `failure_reason`.

To fix it, wake the Mac and check the runner with `gitlab-runner status`
(start it with `gitlab-runner start` if it is stopped), then retry the job:
`glab ci retry <job_id>`, or **Retry** on the job page.

See the project README for the source, behavior-specification, and test layout.
Durable project context lives in `ARCHITECTURE.md` and `design/`.

Keep local-only planning state in `_scratch/`. Do not commit `_scratch/`, `.fp/`, secrets, dependency folders, build outputs, or generated caches.
