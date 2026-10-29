# ci-minutes v1
"""Measure the fleet's GitLab CI job-minutes over a date window.

WHY THIS EXISTS. The CI-tier epic (SEOR-iadkgvqq) promises at least 60% fewer
R-package CI minutes after the migration. A claim like that needs a baseline
measured the same way as the re-measure, so the measurement is this committed
script and the baseline is its own `--json` output, kept beside it in
`tools/ci-minutes-baseline.json` (SEOR-mrndirpd).

WHAT IT MEASURES. For each fleet package under `bart-turczynski/`, plus
`bart-turczynski/fleet-ci` (reported as "not found" while it does not exist),
it reads two read-only GitLab API listings:

- `projects/:id/jobs`, which has no date filter: pages are read newest first
  and reading stops at the first page whose jobs were all created before the
  window. Jobs are then kept when `since <= created_at < until`.
- `projects/:id/pipelines`, filtered server-side with `updated_after=since`
  and `updated_before=until + PIPELINE_SLACK_DAYS` (a pipeline created in the
  window can be updated after it), then kept on the same `created_at` window.

Job-minutes are the sum of each job's `duration` (seconds of runner time, null
for a job that never ran) divided by 60. They are runner busy time, not
GitLab compute-minute billing. Each job is attributed to its pipeline's source
and ref, from the pipelines listing, falling back to the job's own `pipeline`
object. Output per project: minutes by job name and by pipeline source, push
pipelines on `main` and their minutes, failed and canceled minutes, totals;
fleet-wide: total, queue wait median and p90 (`queued_duration`), and peak
concurrency (most jobs running at once, from `started_at`/`finished_at`).

WINDOW. `--since` is inclusive and `--until` exclusive, both dates at 00:00
UTC: `--since 2026-09-29 --until 2026-10-29` covers 2026-09-29 through
2026-10-28.

CALLS. Sequential GET requests only; an HTTP 429 sleeps BACKOFF_SECONDS and
retries. Every raw response body is written to the `--out` cache directory
(default `tmp/ci-minutes/`, gitignored). `--cached` re-reads that cache
instead of the network, so the aggregation can be rerun offline.

TOKEN. `GITLAB_TOKEN` from the environment, sent as a header; else each GET
goes through `glab api --include`, which reads glab's stored token (keyring or
config) itself. Either way the token is never printed or written.

    python3 tools/ci-minutes.py --since 2026-09-29 --until 2026-10-29
    python3 tools/ci-minutes.py --since ... --until ... --json > out.json
    python3 tools/ci-minutes.py --since ... --until ... \\
        --compare tools/ci-minutes-baseline.json
    python3 tools/ci-minutes.py --self-test

`--compare` measures the given window and prints, per project and in total,
the change in job-minutes against the baseline file's `measured` block (or
against a bare `--json` output). Stdlib only.

Exit status: 0 on success, 1 on a failed self-test or an API error, 2 on bad
arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

API = "https://gitlab.com/api/v4"
NAMESPACE = "bart-turczynski"
# The nine fleet packages, as design/fleet.md lists them, then the shared CI
# project the tier migration introduces.
PACKAGES = [
    "rurl",
    "ssrfr",
    "seor",
    "sitemapr",
    "punycoder",
    "pagerankr",
    "pslr",
    "robotstxtr",
    "raddr",
]
FLEET_CI = "fleet-ci"
PROJECTS = [*PACKAGES, FLEET_CI]
PER_PAGE = 100
BACKOFF_SECONDS = 30
MAX_429_RETRIES = 10
PIPELINE_SLACK_DAYS = 7
DEFAULT_BRANCH = "main"
FAILED_STATES = {"failed", "canceled"}

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "tmp" / "ci-minutes"


class NotFound(Exception):
    """The project does not exist (HTTP 404)."""


class ApiError(Exception):
    """Any other non-2xx answer."""


# --- time --------------------------------------------------------------------


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_day(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def in_window(item: dict, since: datetime, until: datetime) -> bool:
    created = parse_ts(item.get("created_at"))
    return created is not None and since <= created < until


# --- HTTP --------------------------------------------------------------------


def urllib_get(url: str, token: str | None) -> tuple[int, dict, bytes]:
    """One GET. Returns (status, lower-cased headers, body)."""
    req = urllib.request.Request(url)
    if token:
        req.add_header("PRIVATE-TOKEN", token)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, headers, resp.read()
    except urllib.error.HTTPError as err:
        headers = {k.lower(): v for k, v in (err.headers or {}).items()}
        return err.code, headers, err.read() or b""


def glab_get(url: str, _token: str | None) -> tuple[int, dict, bytes]:
    """One GET through `glab api`, which reads its own stored token (keyring
    or config) so the token never passes through this process."""
    endpoint = url.removeprefix(API + "/")
    res = subprocess.run(
        ["glab", "api", "--include", "--hostname", "gitlab.com",
         "--method", "GET", endpoint],
        capture_output=True,
        timeout=120,
        check=False,
    )
    return parse_include(res.stdout, endpoint)


def parse_include(raw: bytes, endpoint: str) -> tuple[int, dict, bytes]:
    """Split `glab api --include` output into status, headers and body."""
    raw = raw.replace(b"\r\n", b"\n")
    head, _, body = raw.partition(b"\n\n")
    lines = head.decode("utf-8", "replace").split("\n")
    try:
        status = int(lines[0].split()[1])
    except (IndexError, ValueError):
        raise ApiError(f"glab api gave no HTTP status for {endpoint}") from None
    headers = {}
    for line in lines[1:]:
        key, sep, value = line.partition(":")
        if sep:
            headers[key.strip().lower()] = value.strip()
    return status, headers, body


class Client:
    """Sequential GETs with 429 backoff; caches each raw body under `out`.

    `http` and `sleep` are injectable so the self-test runs offline.
    """

    def __init__(self, token, out: Path | None, http=None, sleep=time.sleep):
        self.token = token
        self.out = out
        self.http = http or urllib_get
        self.sleep = sleep
        self.requests = 0

    def get(self, path: str, params: dict, cache_name: str):
        url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
        for _attempt in range(MAX_429_RETRIES + 1):
            self.requests += 1
            status, headers, body = self.http(url, self.token)
            if status == 429:
                self.sleep(BACKOFF_SECONDS)
                continue
            if status == 404:
                raise NotFound(path)
            if not 200 <= status < 300:
                raise ApiError(f"HTTP {status} for {path} {params}")
            if self.out is not None:
                target = self.out / cache_name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            return json.loads(body), headers
        raise ApiError(f"still HTTP 429 after {MAX_429_RETRIES} retries: {path}")


class CacheClient:
    """Replays the raw bodies a previous run wrote under `out`."""

    def __init__(self, out: Path):
        self.out = out
        self.requests = 0

    def get(self, path: str, params: dict, cache_name: str):
        target = self.out / cache_name
        missing = self.out / (cache_name.split("/")[0] + "/NOT_FOUND")
        if missing.exists():
            raise NotFound(path)
        if not target.exists():
            return [], {}
        self.requests += 1
        return json.loads(target.read_bytes()), {}


def has_next(headers: dict, page: list, page_no: int) -> bool:
    nxt = headers.get("x-next-page")
    if nxt is not None:
        return nxt.strip() != ""
    # No header (cache replay, or a server that omits it): a full page may
    # have a successor.
    return len(page) == PER_PAGE


# --- fetching ----------------------------------------------------------------


def fetch_jobs(client, project: str, since: datetime, until: datetime) -> list:
    """Jobs created in [since, until), newest-first pages, stopping at the
    first page wholly older than `since`."""
    pid = urllib.parse.quote(f"{NAMESPACE}/{project}", safe="")
    kept = []
    page_no = 1
    while True:
        page, headers = client.get(
            f"projects/{pid}/jobs",
            {"per_page": PER_PAGE, "page": page_no},
            f"{project}/jobs-{page_no:04d}.json",
        )
        if not page:
            break
        kept.extend(j for j in page if in_window(j, since, until))
        created = [parse_ts(j.get("created_at")) for j in page]
        if all(c is not None and c < since for c in created):
            break
        if not has_next(headers, page, page_no):
            break
        page_no += 1
    return kept


def fetch_pipelines(client, project, since: datetime, until: datetime) -> list:
    pid = urllib.parse.quote(f"{NAMESPACE}/{project}", safe="")
    params = {
        "per_page": PER_PAGE,
        "updated_after": iso(since),
        "updated_before": iso(until + timedelta(days=PIPELINE_SLACK_DAYS)),
    }
    kept = []
    page_no = 1
    while True:
        page, headers = client.get(
            f"projects/{pid}/pipelines",
            {**params, "page": page_no},
            f"{project}/pipelines-{page_no:04d}.json",
        )
        if not page:
            break
        kept.extend(p for p in page if in_window(p, since, until))
        if not has_next(headers, page, page_no):
            break
        page_no += 1
    return kept


# --- aggregation -------------------------------------------------------------


def minutes(seconds: float) -> float:
    return round(seconds / 60, 1)


def job_seconds(job: dict) -> float:
    return float(job.get("duration") or 0)


def aggregate_project(jobs: list, pipelines: list) -> dict:
    by_pid = {p["id"]: p for p in pipelines}
    by_name = defaultdict(float)
    by_source = defaultdict(float)
    by_status = defaultdict(float)
    main_push_ids = set()
    main_push_secs = 0.0
    total = 0.0
    for job in jobs:
        secs = job_seconds(job)
        total += secs
        jp = job.get("pipeline") or {}
        pipe = by_pid.get(jp.get("id"), jp)
        source = pipe.get("source") or "unknown"
        ref = pipe.get("ref") or jp.get("ref") or job.get("ref")
        by_name[job.get("name", "?")] += secs
        by_source[source] += secs
        by_status[job.get("status", "?")] += secs
        if source == "push" and ref == DEFAULT_BRANCH:
            main_push_secs += secs
    for pipe in pipelines:
        if pipe.get("source") == "push" and pipe.get("ref") == DEFAULT_BRANCH:
            main_push_ids.add(pipe["id"])
    failed = sum(v for k, v in by_status.items() if k in FAILED_STATES)

    def table(d):
        return {k: minutes(v) for k, v in sorted(d.items(), key=lambda kv: -kv[1])}

    return {
        "status": "ok",
        "jobs": len(jobs),
        "pipelines": len(pipelines),
        "job_minutes": minutes(total),
        "by_job_name": table(by_name),
        "by_source": table(by_source),
        "by_status": table(by_status),
        "main_push": {
            "pipelines": len(main_push_ids),
            "minutes": minutes(main_push_secs),
        },
        "failed_canceled_minutes": minutes(failed),
    }


def peak_concurrency(jobs: list) -> int:
    events = []
    for job in jobs:
        start = parse_ts(job.get("started_at"))
        end = parse_ts(job.get("finished_at"))
        if start and end and end > start:
            events.append((start, 1))
            events.append((end, -1))
    # An end sorts before a start at the same instant: back-to-back jobs do
    # not overlap.
    events.sort(key=lambda e: (e[0], e[1]))
    running = peak = 0
    for _, delta in events:
        running += delta
        peak = max(peak, running)
    return peak


def percentile(values: list, pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct / 100
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo), 1)


def aggregate_fleet(per_project: dict, all_jobs: list) -> dict:
    ok = {k: v for k, v in per_project.items() if v["status"] == "ok"}
    pkg = {k: v for k, v in ok.items() if k in PACKAGES}
    by_name = defaultdict(float)
    by_source = defaultdict(float)
    for v in pkg.values():
        for k, m in v["by_job_name"].items():
            by_name[k] += m
        for k, m in v["by_source"].items():
            by_source[k] += m
    pkg_total = sum(v["job_minutes"] for v in pkg.values())
    main_push_min = sum(v["main_push"]["minutes"] for v in pkg.values())
    queued = [
        float(j["queued_duration"])
        for j in all_jobs
        if j.get("queued_duration") is not None
    ]
    fleet_ci = per_project.get(FLEET_CI, {})
    return {
        "packages_job_minutes": round(pkg_total, 1),
        "fleet_ci_job_minutes": fleet_ci.get("job_minutes", 0.0),
        "total_job_minutes": round(
            pkg_total + fleet_ci.get("job_minutes", 0.0), 1
        ),
        "jobs": sum(v["jobs"] for v in ok.values()),
        "pipelines": sum(v["pipelines"] for v in ok.values()),
        "main_push_pipelines": sum(v["main_push"]["pipelines"] for v in pkg.values()),
        "main_push_minutes": round(main_push_min, 1),
        "main_push_share": round(main_push_min / pkg_total, 3) if pkg_total else None,
        "failed_canceled_minutes": round(
            sum(v["failed_canceled_minutes"] for v in pkg.values()), 1
        ),
        "by_source": {
            k: round(v, 1) for k, v in sorted(by_source.items(), key=lambda kv: -kv[1])
        },
        "by_job_name": {
            k: round(v, 1) for k, v in sorted(by_name.items(), key=lambda kv: -kv[1])
        },
        "queue_wait_seconds": {
            "median": percentile(queued, 50),
            "p90": percentile(queued, 90),
        },
        "peak_concurrency": peak_concurrency(all_jobs),
    }


def measure(client, since: datetime, until: datetime, out: Path | None) -> dict:
    per_project = {}
    all_jobs = []
    for project in PROJECTS:
        try:
            jobs = fetch_jobs(client, project, since, until)
            pipelines = fetch_pipelines(client, project, since, until)
        except NotFound:
            per_project[project] = {"status": "not found"}
            if out is not None:
                (out / project).mkdir(parents=True, exist_ok=True)
                (out / project / "NOT_FOUND").write_text("HTTP 404\n")
            continue
        per_project[project] = aggregate_project(jobs, pipelines)
        all_jobs.extend(jobs)
    return {
        "tool": "tools/ci-minutes.py v1",
        "window": {
            "since": iso(since),
            "until": iso(until),
            "bounds": "since inclusive, until exclusive, on created_at",
        },
        "measured_at": iso(datetime.now(UTC)),
        "projects": per_project,
        "fleet": aggregate_fleet(per_project, all_jobs),
    }


# --- output ------------------------------------------------------------------


def render(result: dict, top: int = 12) -> str:
    lines = [
        f"Window {result['window']['since']} .. {result['window']['until']}"
        f" ({result['window']['bounds']})",
        "",
    ]
    for name, p in result["projects"].items():
        if p["status"] != "ok":
            lines.append(f"## {name}: {p['status']}")
            lines.append("")
            continue
        lines.append(
            f"## {name}: {p['job_minutes']} job-min, {p['jobs']} jobs,"
            f" {p['pipelines']} pipelines"
        )
        mp = p["main_push"]
        lines.append(
            f"   push pipelines on {DEFAULT_BRANCH}: {mp['pipelines']},"
            f" {mp['minutes']} min; failed/canceled: {p['failed_canceled_minutes']} min"
        )
        lines.append("   by source: " + ", ".join(f"{k} {v}" for k, v in p["by_source"].items()))
        names = list(p["by_job_name"].items())
        lines.append(
            "   by job: "
            + ", ".join(f"{k} {v}" for k, v in names[:top])
            + (f", ... ({len(names) - top} more)" if len(names) > top else "")
        )
        lines.append("")
    f = result["fleet"]
    q = f["queue_wait_seconds"]
    lines += [
        "## fleet",
        f"   packages {f['packages_job_minutes']} job-min + fleet-ci"
        f" {f['fleet_ci_job_minutes']} = {f['total_job_minutes']}",
        f"   {f['jobs']} jobs, {f['pipelines']} pipelines;"
        f" push on {DEFAULT_BRANCH}: {f['main_push_pipelines']} pipelines,"
        f" {f['main_push_minutes']} min ({f['main_push_share']})",
        f"   failed/canceled {f['failed_canceled_minutes']} min;"
        f" queue wait median {q['median']} s, p90 {q['p90']} s;"
        f" peak concurrency {f['peak_concurrency']}",
        "   by source: " + ", ".join(f"{k} {v}" for k, v in f["by_source"].items()),
    ]
    return "\n".join(lines)


def pct_change(old: float | None, new: float | None) -> str:
    if old in (None, 0) or new is None:
        return "n/a"
    return f"{(new - old) / old * 100:+.1f}%"


def render_compare(baseline: dict, current: dict) -> str:
    base = baseline.get("measured", baseline)
    lines = [
        f"Baseline {base['window']['since']} .. {base['window']['until']}"
        f"  vs  current {current['window']['since']} .. {current['window']['until']}",
        f"{'project':<12} {'baseline':>10} {'current':>10} {'change':>9}",
    ]
    for name in PROJECTS:
        b = base["projects"].get(name, {})
        c = current["projects"].get(name, {})
        bm = b.get("job_minutes") if b.get("status") == "ok" else None
        cm = c.get("job_minutes") if c.get("status") == "ok" else None
        lines.append(
            f"{name:<12} {bm if bm is not None else '-':>10}"
            f" {cm if cm is not None else '-':>10} {pct_change(bm, cm):>9}"
        )
    for label, key in (("packages", "packages_job_minutes"),
                       ("total", "total_job_minutes")):
        bm, cm = base["fleet"][key], current["fleet"][key]
        lines.append(f"{label:<12} {bm:>10} {cm:>10} {pct_change(bm, cm):>9}")
    return "\n".join(lines)


# --- token -------------------------------------------------------------------


def make_client(out: Path) -> Client:
    """`GITLAB_TOKEN` over urllib when set, else every GET through `glab api`.

    Not `glab config get token`: with the token in the OS keyring (the
    default for `glab auth login`), that returns a stale config value and the
    API answers 401. `glab api` reads the keyring itself.
    """
    token = os.environ.get("GITLAB_TOKEN", "").strip()
    if token:
        return Client(token, out)
    if shutil.which("glab") is None:
        print("warning: no GITLAB_TOKEN and no glab; reading anonymously",
              file=sys.stderr)
        return Client(None, out)
    return Client(None, out, http=glab_get)


# --- self-test ---------------------------------------------------------------


def _job(jid, created, name="check", status="success", duration=60.0,
         pipeline=None, queued=10.0, started=None, finished=None):
    return {
        "id": jid,
        "name": name,
        "status": status,
        "created_at": created,
        "started_at": started,
        "finished_at": finished,
        "duration": duration,
        "queued_duration": queued,
        "pipeline": pipeline or {"id": 1, "ref": "main", "source": "push"},
    }


def self_test() -> int:
    failures = []

    def check(label, cond):
        if not cond:
            failures.append(label)

    since = parse_day("2026-10-01")
    until = parse_day("2026-10-08")
    push_main = {"id": 1, "ref": "main", "source": "push"}
    sched = {"id": 2, "ref": "main", "source": "schedule"}
    branch = {"id": 3, "ref": "feature/x", "source": "push"}

    # Newest-first pages. Page 1: one job after the window (excluded), two in
    # it. Page 2: straddles `since` (the one exactly at `since` is kept).
    # Page 3: wholly older, so reading stops there. Page 4 must never be read.
    pages = {
        1: [
            _job(9, "2026-10-08T00:00:00Z", pipeline=push_main),  # == until: out
            _job(8, "2026-10-07T10:00:00Z", name="pages", duration=120,
                 pipeline=push_main, started="2026-10-07T10:00:00Z",
                 finished="2026-10-07T10:02:00Z"),
            _job(7, "2026-10-05T10:00:00Z", name="coverage", duration=300,
                 status="failed", pipeline=sched, queued=100.0,
                 started="2026-10-07T10:01:00Z", finished="2026-10-07T10:06:00Z"),
        ],
        2: [
            _job(6, "2026-10-01T00:00:00Z", duration=180, status="canceled",
                 pipeline=branch, queued=None),  # == since: in
            _job(5, "2026-09-30T23:59:59Z", duration=999),  # before: out
        ],
        3: [_job(4, "2026-09-29T00:00:00Z", duration=999)],
        4: [_job(3, "2026-10-03T00:00:00Z", duration=999)],  # unreachable
    }
    requested = []
    sleeps = []
    throttled = {"left": 1}

    def fake_http(url, token):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        page_no = int(query["page"][0])
        if "/jobs" in url:
            requested.append(page_no)
            if page_no == 2 and throttled["left"]:
                throttled["left"] -= 1
                return 429, {}, b"{}"
            nxt = "" if page_no == 4 else str(page_no + 1)
            return 200, {"x-next-page": nxt}, json.dumps(pages[page_no]).encode()
        if "/pipelines" in url:
            check("pipelines updated_after sent", query.get("updated_after") == [iso(since)])
            check("pipelines updated_before sent", "updated_before" in query)
            body = [
                {"id": 1, "ref": "main", "source": "push", "created_at": "2026-10-07T09:59:00Z"},
                {"id": 10, "ref": "main", "source": "push", "created_at": "2026-10-02T00:00:00Z"},
                {"id": 2, "ref": "main", "source": "schedule", "created_at": "2026-10-05T09:59:00Z"},
                {"id": 3, "ref": "feature/x", "source": "push", "created_at": "2026-10-01T00:00:00Z"},
                {"id": 11, "ref": "main", "source": "push", "created_at": "2026-09-20T00:00:00Z"},
            ]
            return 200, {"x-next-page": ""}, json.dumps(body).encode()
        return 404, {}, b"{}"

    with tempfile.TemporaryDirectory() as tmp:
        client = Client("t", Path(tmp), http=fake_http, sleep=sleeps.append)
        jobs = fetch_jobs(client, "rurl", since, until)
        pipes = fetch_pipelines(client, "rurl", since, until)

        # Pagination stop: page 3 is wholly older, so page 4 is never read.
        check("pagination stops at the first wholly-older page", 4 not in requested)
        check("pagination reads through the straddling page", 3 in requested)
        # 429 backoff: one throttled answer, one 30 s sleep, then a retry.
        check("429 sleeps BACKOFF_SECONDS once", sleeps == [BACKOFF_SECONDS])
        check("429 retries the same page", requested.count(2) == 2)
        check("raw bodies cached", (Path(tmp) / "rurl" / "jobs-0001.json").exists())

        # Window filter: since inclusive, until exclusive.
        ids = sorted(j["id"] for j in jobs)
        check(f"window keeps jobs 6,7,8 (got {ids})", ids == [6, 7, 8])
        check("pipelines window drops the old one", sorted(p["id"] for p in pipes) == [1, 2, 3, 10])

        # Aggregation.
        agg = aggregate_project(jobs, pipes)
        check("total minutes", agg["job_minutes"] == 10.0)  # 120+300+180 s
        check("by job name", agg["by_job_name"] == {"coverage": 5.0, "check": 3.0, "pages": 2.0})
        check("by source", agg["by_source"] == {"schedule": 5.0, "push": 5.0})
        check("main push pipelines", agg["main_push"] == {"pipelines": 2, "minutes": 2.0})
        check("failed/canceled minutes", agg["failed_canceled_minutes"] == 8.0)

        fleet = aggregate_fleet(
            {"rurl": agg, FLEET_CI: {"status": "not found"}}, jobs
        )
        check("fleet total", fleet["total_job_minutes"] == 10.0)
        check("queue median skips null", fleet["queue_wait_seconds"]["median"] == 55.0)
        check("peak concurrency", fleet["peak_concurrency"] == 2)

        # A 404 is "not found", not a failure.
        result = measure(Client("t", None, http=lambda u, t: (404, {}, b"")), since, until, None)
        check("404 reported as not found", result["projects"][FLEET_CI] == {"status": "not found"})

        # Compare: percent change per project.
        base = {"measured": result}
        base["measured"]["projects"]["rurl"] = {"status": "ok", "job_minutes": 100.0}
        cur = json.loads(json.dumps(result))
        cur["projects"]["rurl"] = {"status": "ok", "job_minutes": 40.0}
        check("compare shows -60%", "-60.0%" in render_compare(base, cur))

        # glab api --include parsing, including an empty X-Prev-Page.
        status, headers, body = parse_include(
            b"HTTP/2.0 200 OK\nX-Next-Page: 2\nX-Prev-Page: \n\n[{\"id\": 1}]", "x"
        )
        check("glab include parse", (status, headers.get("x-next-page"),
                                     headers.get("x-prev-page"), json.loads(body))
              == (200, "2", "", [{"id": 1}]))
        status, _, _ = parse_include(b"HTTP/2.0 404 Not Found\n\n{}", "x")
        check("glab include 404", status == 404)

    for label in failures:
        print(f"FAIL {label}", file=sys.stderr)
    print("self-test: " + ("FAILED" if failures else "ok"))
    return 1 if failures else 0


# --- main --------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", help="first day, YYYY-MM-DD, inclusive (00:00 UTC)")
    ap.add_argument("--until", help="end day, YYYY-MM-DD, exclusive (00:00 UTC)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="raw API response cache directory (default tmp/ci-minutes)")
    ap.add_argument("--cached", action="store_true",
                    help="read the --out cache instead of the network")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--compare", type=Path, metavar="BASELINE",
                    help="print per-project change in percent against BASELINE")
    ap.add_argument("--self-test", action="store_true", help="run the offline self-test")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.since or not args.until:
        ap.error("--since and --until are required")
    try:
        since, until = parse_day(args.since), parse_day(args.until)
    except ValueError as err:
        ap.error(str(err))
    if until <= since:
        ap.error("--until must be after --since")

    if args.cached:
        client = CacheClient(args.out)
    else:
        client = make_client(args.out)
    try:
        result = measure(client, since, until, None if args.cached else args.out)
    except ApiError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if args.compare:
        baseline = json.loads(args.compare.read_text())
        print(render_compare(baseline, result))
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
