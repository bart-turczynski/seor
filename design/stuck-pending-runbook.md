# Stuck-pending runbook

CI for seor and its members runs on self-hosted Docker runners on the
maintainer's Mac, not on GitLab.com shared runners. When the Mac sleeps, or
`gitlab-runner` or Docker stops, jobs sit in `pending` and eventually fail
with `failure_reason: stuck_pending_no_matching_runners`, `runner: None` and
a long `queued_duration`. **That is infrastructure, not a code failure.**
Don't debug the code; bring the runner back and retry. To confirm from the
API, `glab api projects/:id/jobs/<job_id>` shows that `failure_reason` and
`"runner": null`; a job that ran and failed names its runner. Why the fleet
runs this way:
[ADR 0003](adr/0003-fleet-ci-runs-on-self-hosted-runners.md).

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
