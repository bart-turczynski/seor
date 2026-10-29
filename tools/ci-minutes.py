# ci-minutes v2
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
  only (a pipeline is updated no earlier than it is created), then kept on the
  same `created_at` window. No upper bound, so the result does not depend on
  when the window is measured.

Offset pagination can repeat a row when new ones arrive mid-walk, so jobs and
pipelines are de-duplicated by id within each project.

Job-minutes are the sum of each job's `duration` (seconds of runner time, null
for a job that never ran) divided by 60. They are runner busy time, not
GitLab compute-minute billing. Each job is attributed to its pipeline's source
and ref, from the pipelines listing, falling back to the job's own `pipeline`
object. Output per project: minutes by job name and by pipeline source, push
pipelines on `main` and their minutes, failed and canceled minutes, totals.

SCOPE. The `fleet` block covers the nine packages only: totals, jobs,
pipelines, breakdowns, queue wait median and p90 (`queued_duration`) and peak
concurrency (most jobs running at once, from `started_at`/`finished_at`). The
`fleet_ci` block carries fleet-ci's figures with the same breakdown, and
`total_including_fleet_ci_minutes` adds the two.

WINDOW. `--since` is inclusive and `--until` exclusive, both dates at 00:00
UTC: `--since 2026-09-29 --until 2026-10-29` covers 2026-09-29 through
2026-10-28.

CALLS. Sequential GET requests only. HTTP 429 and 5xx answers sleep
(`Retry-After` when given, else BACKOFF_SECONDS) and retry a bounded number of
times. Every raw response body is written under `--out` (default
`tmp/ci-minutes/`, gitignored) in `<since>_<until>/`, which a live run clears
first, with a `manifest.json` listing the window, the pages read per endpoint
and the projects not found. `--cached` replays exactly the pages that manifest
lists, so the aggregation can be rerun offline; it refuses a missing manifest,
a manifest for another window and a listed page that is missing.

TOKEN. `GITLAB_TOKEN` from the environment, sent as a header; else each GET
goes through `glab api --include`, which reads glab's stored token (keyring or
config) itself. Either way the token is never printed or written.

    python3 tools/ci-minutes.py --since 2026-09-29 --until 2026-10-29
    python3 tools/ci-minutes.py --since ... --until ... --json > out.json
    python3 tools/ci-minutes.py --since ... --until ... \\
        --compare tools/ci-minutes-baseline.json [--per-day] [--json]
    python3 tools/ci-minutes.py --self-test

`--compare` measures the given window and prints, per project and in total,
the change in job-minutes against the baseline file's `measured` block (or
against a bare `--json` output). The two windows must be the same length,
unless `--per-day` normalizes both sides to job-minutes per day. With `--json`
the comparison is printed as JSON. Stdlib only.

Exit status: 0 on success, 1 on a failed self-test, an API or cache error or
a compare window mismatch, 2 on bad arguments.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
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
ENDPOINTS = ("jobs", "pipelines")
PER_PAGE = 100
BACKOFF_SECONDS = 30
MAX_429_RETRIES = 10
MAX_5XX_RETRIES = 3
MAX_RETRY_AFTER = 300
DEFAULT_BRANCH = "main"
FAILED_STATES = {"failed", "canceled"}
MANIFEST = "manifest.json"

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "tmp" / "ci-minutes"


class NotFound(Exception):
    """The project does not exist (HTTP 404)."""


class ApiError(Exception):
    """Any other non-2xx answer, or a transport failure."""


class CacheError(ApiError):
    """The `--cached` replay cannot be trusted for this window."""


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


def window_days(window: dict) -> float:
    span = parse_ts(window["until"]) - parse_ts(window["since"])
    return span.total_seconds() / 86400


# --- HTTP --------------------------------------------------------------------


def urllib_get(url: str, token: str | None,
               urlopen=urllib.request.urlopen) -> tuple[int, dict, bytes]:
    """One GET. Returns (status, lower-cased headers, body)."""
    req = urllib.request.Request(url)
    if token:
        req.add_header("PRIVATE-TOKEN", token)
    try:
        with urlopen(req, timeout=60) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, headers, resp.read()
    except urllib.error.HTTPError as err:
        headers = {k.lower(): v for k, v in (err.headers or {}).items()}
        return err.code, headers, err.read() or b""
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as err:
        raise ApiError(f"GET {url.split('?')[0]}: {err}") from err


def glab_get(url: str, _token: str | None, run=subprocess.run) -> tuple[int, dict, bytes]:
    """One GET through `glab api`, which reads its own stored token (keyring
    or config) so the token never passes through this process."""
    endpoint = url.removeprefix(API + "/")
    try:
        res = run(
            ["glab", "api", "--include", "--hostname", "gitlab.com",
             "--method", "GET", endpoint],
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        raise ApiError(f"glab api {endpoint}: {err}") from err
    if res.returncode:
        # glab exits non-zero on an HTTP error answer too; when it printed the
        # status line, that answer is the API's, so pass it on (404, 429, 5xx
        # are handled by the caller). Otherwise glab itself failed.
        try:
            status, headers, body = parse_include(res.stdout, endpoint)
        except ApiError:
            status = None
        if status is not None and status >= 400:
            return status, headers, body
        stderr = (res.stderr or b"").decode("utf-8", "replace").strip()[:200]
        raise ApiError(f"glab api {endpoint}: exit {res.returncode}: {stderr}")
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


def retry_after(headers: dict) -> float:
    value = (headers.get("retry-after") or "").strip()
    if value.isdigit():
        return min(float(value), MAX_RETRY_AFTER)
    return BACKOFF_SECONDS


def has_next(headers: dict, page: list) -> bool:
    nxt = headers.get("x-next-page")
    if nxt is not None:
        return nxt.strip() != ""
    # No header (a server that omits it): a full page may have a successor.
    return len(page) == PER_PAGE


def project_path(project: str, endpoint: str) -> str:
    pid = urllib.parse.quote(f"{NAMESPACE}/{project}", safe="")
    return f"projects/{pid}/{endpoint}"


def page_file(project: str, endpoint: str, page_no: int) -> str:
    return f"{project}/{endpoint}-{page_no:04d}.json"


class Client:
    """Sequential GETs with 429/5xx backoff. With `cache_dir` set, writes each
    raw body there and records the page in `pages` for the manifest.

    `http` and `sleep` are injectable so the self-test runs offline.
    """

    def __init__(self, token, http=None, sleep=time.sleep):
        self.token = token
        self.http = http or urllib_get
        self.sleep = sleep
        self.cache_dir: Path | None = None
        self.pages: dict[str, list] = {}

    def get(self, project: str, endpoint: str, page_no: int, params: dict):
        path = project_path(project, endpoint)
        url = f"{API}/{path}?{urllib.parse.urlencode({**params, 'page': page_no})}"
        throttled = server_errors = 0
        while True:
            status, headers, body = self.http(url, self.token)
            if status == 429:
                throttled += 1
                if throttled > MAX_429_RETRIES:
                    raise ApiError(
                        f"still HTTP 429 after {MAX_429_RETRIES} retries: {path}")
                self.sleep(retry_after(headers))
                continue
            if 500 <= status < 600:
                server_errors += 1
                if server_errors > MAX_5XX_RETRIES:
                    raise ApiError(
                        f"HTTP {status} after {MAX_5XX_RETRIES} retries: {path}")
                self.sleep(retry_after(headers))
                continue
            if status == 404:
                raise NotFound(path)
            if not 200 <= status < 300:
                raise ApiError(f"HTTP {status} for {path} {params}")
            page = json.loads(body)
            if self.cache_dir is not None:
                target = self.cache_dir / page_file(project, endpoint, page_no)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
                self.pages.setdefault(f"{project}/{endpoint}", []).append(
                    {"page": page_no, "last": not has_next(headers, page)})
            return page, headers


class CacheClient:
    """Replays the pages a previous live run's manifest lists, nothing else."""

    def __init__(self, window_dir: Path, since: datetime, until: datetime):
        self.dir = window_dir
        manifest_path = window_dir / MANIFEST
        if not manifest_path.exists():
            raise CacheError(f"no {MANIFEST} in {window_dir}: run without --cached first")
        self.manifest = json.loads(manifest_path.read_text())
        want = {"since": iso(since), "until": iso(until)}
        got = {k: self.manifest.get("window", {}).get(k) for k in want}
        if got != want:
            raise CacheError(f"{manifest_path} is for window {got}, not {want}")
        if self.manifest.get("projects") != PROJECTS:
            raise CacheError(f"{manifest_path} lists other projects than {PROJECTS}")
        self.not_found = set(self.manifest.get("not_found", []))
        self.listed = {
            key: {p["page"]: p["last"] for p in pages}
            for key, pages in self.manifest.get("endpoints", {}).items()
        }

    def get(self, project: str, endpoint: str, page_no: int, params: dict):
        if project in self.not_found:
            raise NotFound(project_path(project, endpoint))
        last = self.listed.get(f"{project}/{endpoint}", {}).get(page_no)
        if last is None:
            raise CacheError(
                f"{project} {endpoint} page {page_no} is not in {self.dir / MANIFEST}")
        target = self.dir / page_file(project, endpoint, page_no)
        if not target.exists():
            raise CacheError(f"{target} is listed in the manifest but missing")
        headers = {"x-next-page": "" if last else str(page_no + 1)}
        return json.loads(target.read_bytes()), headers


# --- fetching ----------------------------------------------------------------


def fetch_jobs(client, project: str, since: datetime, until: datetime) -> list:
    """Jobs created in [since, until), newest-first pages, stopping at the
    first page wholly older than `since`; de-duplicated by id."""
    kept: dict = {}
    page_no = 1
    while True:
        page, headers = client.get(project, "jobs", page_no, {"per_page": PER_PAGE})
        if not page:
            break
        for job in page:
            if in_window(job, since, until):
                kept.setdefault(job["id"], job)
        created = [parse_ts(j.get("created_at")) for j in page]
        if all(c is not None and c < since for c in created):
            break
        if not has_next(headers, page):
            break
        page_no += 1
    return list(kept.values())


def fetch_pipelines(client, project, since: datetime, until: datetime) -> list:
    params = {"per_page": PER_PAGE, "updated_after": iso(since)}
    kept: dict = {}
    page_no = 1
    while True:
        page, headers = client.get(project, "pipelines", page_no, params)
        if not page:
            break
        for pipe in page:
            if in_window(pipe, since, until):
                kept.setdefault(pipe["id"], pipe)
        if not has_next(headers, page):
            break
        page_no += 1
    return list(kept.values())


# --- aggregation -------------------------------------------------------------


def minutes(seconds: float) -> float:
    return round(seconds / 60, 1)


def job_seconds(job: dict) -> float:
    return float(job.get("duration") or 0)


def ranked(d: dict) -> dict:
    return {k: round(v, 1) for k, v in sorted(d.items(), key=lambda kv: -kv[1])}


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


def aggregate_group(per_project: dict, jobs_by_project: dict, names: list) -> dict:
    """Totals and breakdowns over `names`, each figure from the same projects."""
    ok = [n for n in names if per_project.get(n, {}).get("status") == "ok"]
    rows = [per_project[n] for n in ok]
    jobs = [j for n in ok for j in jobs_by_project.get(n, [])]
    by_name = defaultdict(float)
    by_source = defaultdict(float)
    for v in rows:
        for k, m in v["by_job_name"].items():
            by_name[k] += m
        for k, m in v["by_source"].items():
            by_source[k] += m
    total = round(sum(v["job_minutes"] for v in rows), 1)
    main_push_min = round(sum(v["main_push"]["minutes"] for v in rows), 1)
    queued = [float(j["queued_duration"]) for j in jobs
              if j.get("queued_duration") is not None]
    return {
        "projects": ok,
        "total_job_minutes": total,
        "jobs": sum(v["jobs"] for v in rows),
        "pipelines": sum(v["pipelines"] for v in rows),
        "main_push_pipelines": sum(v["main_push"]["pipelines"] for v in rows),
        "main_push_minutes": main_push_min,
        "main_push_share": round(main_push_min / total, 3) if total else None,
        "failed_canceled_minutes": round(
            sum(v["failed_canceled_minutes"] for v in rows), 1),
        "by_source": ranked(by_source),
        "by_job_name": ranked(by_name),
        "queue_wait_seconds": {
            "median": percentile(queued, 50),
            "p90": percentile(queued, 90),
        },
        "peak_concurrency": peak_concurrency(jobs),
    }


def measure(client, since: datetime, until: datetime) -> dict:
    per_project = {}
    jobs_by_project = {}
    for project in PROJECTS:
        try:
            jobs = fetch_jobs(client, project, since, until)
            pipelines = fetch_pipelines(client, project, since, until)
        except NotFound:
            per_project[project] = {"status": "not found"}
            continue
        per_project[project] = aggregate_project(jobs, pipelines)
        jobs_by_project[project] = jobs
    fleet = aggregate_group(per_project, jobs_by_project, PACKAGES)
    if per_project[FLEET_CI]["status"] == "ok":
        fleet_ci = {"status": "ok",
                    **aggregate_group(per_project, jobs_by_project, [FLEET_CI])}
    else:
        fleet_ci = {"status": per_project[FLEET_CI]["status"]}
    return {
        "tool": "tools/ci-minutes.py v2",
        "window": {
            "since": iso(since),
            "until": iso(until),
            "bounds": "since inclusive, until exclusive, on created_at",
        },
        "measured_at": iso(datetime.now(UTC)),
        "projects": per_project,
        "fleet": fleet,
        "fleet_ci": fleet_ci,
        "total_including_fleet_ci_minutes": round(
            fleet["total_job_minutes"] + fleet_ci.get("total_job_minutes", 0.0), 1),
    }


def window_dir(out: Path, since: datetime, until: datetime) -> Path:
    return out / f"{since:%Y-%m-%d}_{until:%Y-%m-%d}"


def measure_live(client: Client, since: datetime, until: datetime, out: Path) -> dict:
    """Measure over the network into a fresh `<out>/<since>_<until>/`; the
    manifest is written last, so an interrupted run leaves none."""
    wdir = window_dir(out, since, until)
    if wdir.exists():
        shutil.rmtree(wdir)
    wdir.mkdir(parents=True)
    client.cache_dir = wdir
    client.pages = {}
    result = measure(client, since, until)
    manifest = {
        "tool": result["tool"],
        "window": {"since": iso(since), "until": iso(until)},
        "projects": PROJECTS,
        "endpoints": client.pages,
        "not_found": [p for p, v in result["projects"].items()
                      if v["status"] == "not found"],
        "finished_at": iso(datetime.now(UTC)),
    }
    result["measured_at"] = manifest["finished_at"]
    (wdir / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")
    return result


def measure_cached(since: datetime, until: datetime, out: Path) -> dict:
    client = CacheClient(window_dir(out, since, until), since, until)
    result = measure(client, since, until)
    result["measured_at"] = client.manifest.get("finished_at")
    return result


# --- output ------------------------------------------------------------------


def render_group(label: str, f: dict) -> list:
    q = f["queue_wait_seconds"]
    return [
        f"## {label}: {f['total_job_minutes']} job-min, {f['jobs']} jobs,"
        f" {f['pipelines']} pipelines",
        f"   push on {DEFAULT_BRANCH}: {f['main_push_pipelines']} pipelines,"
        f" {f['main_push_minutes']} min ({f['main_push_share']});"
        f" failed/canceled {f['failed_canceled_minutes']} min",
        f"   queue wait median {q['median']} s, p90 {q['p90']} s;"
        f" peak concurrency {f['peak_concurrency']}",
        "   by source: " + ", ".join(f"{k} {v}" for k, v in f["by_source"].items()),
    ]


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
    lines += render_group("fleet (packages)", result["fleet"])
    lines.append("")
    fc = result["fleet_ci"]
    if fc["status"] == "ok":
        lines += render_group(FLEET_CI, fc)
    else:
        lines.append(f"## {FLEET_CI}: {fc['status']}")
    lines += ["", f"total including {FLEET_CI}:"
              f" {result['total_including_fleet_ci_minutes']} job-min"]
    return "\n".join(lines)


def pct_change(old: float | None, new: float | None) -> float | None:
    if old in (None, 0) or new is None:
        return None
    return round((new - old) / old * 100, 1)


def compare(baseline: dict, current: dict, per_day: bool) -> dict:
    """Per-project and total change; both windows must be the same length
    unless `per_day` normalizes each side to job-minutes per day."""
    base = baseline.get("measured", baseline)
    bdays, cdays = window_days(base["window"]), window_days(current["window"])
    if not per_day and bdays != cdays:
        raise ValueError(
            f"baseline window is {bdays:g} days, current {cdays:g} days;"
            " pass --per-day to compare job-minutes per day")

    def norm(value, days):
        if value is None:
            return None
        return round(value / days, 1) if per_day else value

    def proj(side, name):
        p = side["projects"].get(name, {})
        return p.get("job_minutes") if p.get("status") == "ok" else None

    def fleet_ci(side):
        return side.get("fleet_ci", {}).get("total_job_minutes")

    def total(side):
        return side.get("total_including_fleet_ci_minutes")

    rows = {}
    pairs = [(n, lambda s, n=n: proj(s, n)) for n in PACKAGES]
    pairs += [
        ("packages", lambda s: s["fleet"]["total_job_minutes"]),
        (FLEET_CI, fleet_ci),
        ("total", total),
    ]
    for name, get in pairs:
        b, c = norm(get(base), bdays), norm(get(current), cdays)
        rows[name] = {"baseline": b, "current": c, "pct": pct_change(b, c)}
    return {
        "baseline_window": base["window"],
        "current_window": current["window"],
        "unit": "job-minutes per day" if per_day else "job-minutes",
        "rows": rows,
    }


def render_compare(cmp: dict) -> str:
    bw, cw = cmp["baseline_window"], cmp["current_window"]
    lines = [
        f"Baseline {bw['since']} .. {bw['until']}"
        f"  vs  current {cw['since']} .. {cw['until']} ({cmp['unit']})",
        f"{'project':<12} {'baseline':>10} {'current':>10} {'change':>9}",
    ]
    for name, r in cmp["rows"].items():
        b = r["baseline"] if r["baseline"] is not None else "-"
        c = r["current"] if r["current"] is not None else "-"
        pct = f"{r['pct']:+.1f}%" if r["pct"] is not None else "n/a"
        lines.append(f"{name:<12} {b:>10} {c:>10} {pct:>9}")
    return "\n".join(lines)


# --- token -------------------------------------------------------------------


def make_client() -> Client:
    """`GITLAB_TOKEN` over urllib when set, else every GET through `glab api`.

    Not `glab config get token`: with the token in the OS keyring (the
    default for `glab auth login`), that returns a stale config value and the
    API answers 401. `glab api` reads the keyring itself.
    """
    token = os.environ.get("GITLAB_TOKEN", "").strip()
    if token:
        return Client(token)
    if shutil.which("glab") is None:
        print("warning: no GITLAB_TOKEN and no glab; reading anonymously",
              file=sys.stderr)
        return Client(None)
    return Client(None, http=glab_get)


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


def _run_main(argv: list) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def _fleet_http(since: datetime, rurl_jobs: list, fleet_ci_jobs: list):
    """A fake GitLab: rurl and fleet-ci exist, every other project is 404.
    rurl's single jobs page is marked last by `X-Next-Page: ""`."""
    def http(url, token):
        path = urllib.parse.urlparse(url).path
        page_no = int(urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["page"][0])
        for project, jobs in (("rurl", rurl_jobs), (FLEET_CI, fleet_ci_jobs)):
            if f"%2F{project}/" not in path:
                continue
            if path.endswith("/jobs"):
                body = jobs if page_no == 1 else []
            else:
                pids = sorted({j["pipeline"]["id"] for j in jobs})
                body = [{"id": p, "ref": "main", "source": "push",
                         "created_at": iso(since)} for p in pids] if page_no == 1 else []
            return 200, {"x-next-page": ""}, json.dumps(body).encode()
        return 404, {}, b"{}"
    return http


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
    # it. Page 2: straddles `since` (the one exactly at `since` is kept) and
    # repeats job 7, as offset pagination does when a new job arrives
    # mid-walk. Page 3: wholly older, so reading stops there. Page 4 must
    # never be read.
    job7 = _job(7, "2026-10-05T10:00:00Z", name="coverage", duration=300,
                status="failed", pipeline=sched, queued=100.0,
                started="2026-10-07T10:01:00Z", finished="2026-10-07T10:06:00Z")
    pages = {
        1: [
            _job(9, "2026-10-08T00:00:00Z", pipeline=push_main),  # == until: out
            _job(8, "2026-10-07T10:00:00Z", name="pages", duration=120,
                 pipeline=push_main, started="2026-10-07T10:00:00Z",
                 finished="2026-10-07T10:02:00Z"),
            job7,
        ],
        2: [
            job7,  # repeated row
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
    pipe_queries = []

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
            pipe_queries.append(query)
            body = [
                {"id": 1, "ref": "main", "source": "push", "created_at": "2026-10-07T09:59:00Z"},
                {"id": 10, "ref": "main", "source": "push", "created_at": "2026-10-02T00:00:00Z"},
                {"id": 2, "ref": "main", "source": "schedule", "created_at": "2026-10-05T09:59:00Z"},
                {"id": 3, "ref": "feature/x", "source": "push", "created_at": "2026-10-01T00:00:00Z"},
                {"id": 11, "ref": "main", "source": "push", "created_at": "2026-09-20T00:00:00Z"},
                # Repeated row (fix 2).
                {"id": 10, "ref": "main", "source": "push", "created_at": "2026-10-02T00:00:00Z"},
            ]
            return 200, {"x-next-page": ""}, json.dumps(body).encode()
        return 404, {}, b"{}"

    client = Client("t", http=fake_http, sleep=sleeps.append)
    jobs = fetch_jobs(client, "rurl", since, until)
    pipes = fetch_pipelines(client, "rurl", since, until)

    # Pagination stop: page 3 is wholly older, so page 4 is never read.
    check("pagination stops at the first wholly-older page", 4 not in requested)
    check("pagination reads through the straddling page", 3 in requested)
    # 429 backoff: one throttled answer, one 30 s sleep, then a retry.
    check("429 sleeps BACKOFF_SECONDS once", sleeps == [BACKOFF_SECONDS])
    check("429 retries the same page", requested.count(2) == 2)

    # Fix 3: updated_after only, no upper bound.
    check("pipelines updated_after sent",
          all(q.get("updated_after") == [iso(since)] for q in pipe_queries))
    check("pipelines: no updated_before bound",
          pipe_queries and not any("updated_before" in q for q in pipe_queries))

    # Window filter: since inclusive, until exclusive. Fix 2: de-duplicated.
    ids = sorted(j["id"] for j in jobs)
    check(f"window keeps jobs 6,7,8 once each (got {ids})", ids == [6, 7, 8])
    pids = sorted(p["id"] for p in pipes)
    check(f"pipelines window drops the old one, once each (got {pids})",
          pids == [1, 2, 3, 10])

    # Aggregation.
    agg = aggregate_project(jobs, pipes)
    check("total minutes", agg["job_minutes"] == 10.0)  # 120+300+180 s
    check("by job name", agg["by_job_name"] == {"coverage": 5.0, "check": 3.0, "pages": 2.0})
    check("by source", agg["by_source"] == {"schedule": 5.0, "push": 5.0})
    check("main push pipelines", agg["main_push"] == {"pipelines": 2, "minutes": 2.0})
    check("failed/canceled minutes", agg["failed_canceled_minutes"] == 8.0)

    fleet = aggregate_group({"rurl": agg}, {"rurl": jobs}, PACKAGES)
    check("fleet total", fleet["total_job_minutes"] == 10.0)
    check("queue median skips null", fleet["queue_wait_seconds"]["median"] == 55.0)
    check("peak concurrency", fleet["peak_concurrency"] == 2)

    # A 404 is "not found", not a failure.
    result = measure(Client("t", http=lambda u, t: (404, {}, b"")), since, until)
    check("404 reported as not found", result["projects"][FLEET_CI] == {"status": "not found"})
    check("fleet-ci block not found", result["fleet_ci"] == {"status": "not found"})

    # Fix 5: package totals exclude fleet-ci, consistently; fleet-ci has its
    # own block; the explicit total adds both.
    rurl_jobs = [
        _job(101, "2026-10-02T00:00:00Z", duration=600, queued=20.0,
             started="2026-10-02T00:00:00Z", finished="2026-10-02T00:10:00Z",
             pipeline={"id": 501, "ref": "main", "source": "push"}),
    ]
    fci_jobs = [
        _job(201 + i, "2026-10-02T00:00:00Z", name="fleet", duration=300,
             queued=900.0, started="2026-10-02T00:01:00Z",
             finished="2026-10-02T00:06:00Z",
             pipeline={"id": 601, "ref": "main", "source": "push"})
        for i in range(3)
    ]
    scoped = measure(Client("t", http=_fleet_http(since, rurl_jobs, fci_jobs)),
                     since, until)
    f, fc = scoped["fleet"], scoped["fleet_ci"]
    check("scope: packages total excludes fleet-ci", f["total_job_minutes"] == 10.0)
    check("scope: packages jobs exclude fleet-ci", f["jobs"] == 1)
    check("scope: packages pipelines exclude fleet-ci", f["pipelines"] == 1)
    check("scope: packages by_source excludes fleet-ci", f["by_source"] == {"push": 10.0})
    check("scope: packages by_job_name excludes fleet-ci", "fleet" not in f["by_job_name"])
    check("scope: packages queue wait excludes fleet-ci",
          f["queue_wait_seconds"] == {"median": 20.0, "p90": 20.0})
    check("scope: packages peak concurrency excludes fleet-ci", f["peak_concurrency"] == 1)
    check("scope: main_push_share packages only", f["main_push_share"] == 1.0)
    check("scope: fleet_ci block", fc.get("status") == "ok"
          and fc.get("total_job_minutes") == 15.0 and fc.get("jobs") == 3
          and fc.get("peak_concurrency") == 3
          and fc.get("queue_wait_seconds", {}).get("median") == 900.0)
    check("scope: total including fleet-ci",
          scoped.get("total_including_fleet_ci_minutes") == 25.0)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        wdir = window_dir(out, since, until)
        day = ["--since", "2026-10-01", "--until", "2026-10-08", "--out", tmp]

        # Fix 1: a live run clears its window directory, keys it by window
        # and writes a manifest.
        wdir.mkdir(parents=True)
        (wdir / "rurl").mkdir()
        (wdir / "rurl" / "jobs-0007.json").write_text("[]")
        (wdir / "rurl" / "NOT_FOUND").write_text("HTTP 404\n")
        full_page = [
            _job(1000 + i, "2026-10-03T00:00:00Z", duration=60,
                 pipeline={"id": 700, "ref": "main", "source": "push"})
            for i in range(PER_PAGE)
        ]
        live = measure_live(Client("t", http=_fleet_http(since, full_page, fci_jobs)),
                            since, until, out)
        check("cache: live run clears stale page files",
              not (wdir / "rurl" / "jobs-0007.json").exists())
        check("cache: live run clears NOT_FOUND markers",
              not (wdir / "rurl" / "NOT_FOUND").exists())
        manifest = (json.loads((wdir / MANIFEST).read_text())
                    if (wdir / MANIFEST).exists() else {})
        check("cache: manifest window",
              manifest.get("window") == {"since": iso(since), "until": iso(until)})
        check("cache: manifest pages and last flags",
              manifest.get("endpoints", {}).get("rurl/jobs") == [{"page": 1, "last": True}])
        check("cache: manifest not_found",
              manifest.get("not_found") == [p for p in PACKAGES if p != "rurl"])
        check("cache: manifest projects and finished_at",
              manifest.get("projects") == PROJECTS and manifest.get("finished_at"))

        # A leftover page file the manifest does not list is never read, even
        # when the last listed page is full.
        (wdir / "rurl" / "jobs-0002.json").write_text(json.dumps(
            [_job(9999, "2026-10-04T00:00:00Z", duration=6000)]))
        code, text, _ = _run_main([*day, "--cached", "--json"])
        replay = json.loads(text) if code == 0 else {}
        check(f"cache: replay succeeds (exit {code})", code == 0)
        check("cache: replay ignores unlisted page files, equals live",
              replay == live)

        # Refusals: no manifest for the window, a manifest for another
        # window, a listed page missing.
        code, _, err = _run_main(["--since", "2026-10-01", "--until", "2026-10-09",
                                  "--out", tmp, "--cached"])
        check("cache: --cached refuses a window with no manifest",
              code == 1 and MANIFEST in err)
        other = dict(manifest, window={"since": iso(since), "until": "2026-10-09T00:00:00Z"})
        (wdir / MANIFEST).write_text(json.dumps(other))
        code, _, err = _run_main([*day, "--cached"])
        check("cache: --cached refuses a manifest for another window",
              code == 1 and "window" in err)
        (wdir / MANIFEST).write_text(json.dumps(manifest))
        (wdir / "rurl" / "jobs-0001.json").unlink()
        code, _, err = _run_main([*day, "--cached"])
        check("cache: --cached refuses a missing listed page", code == 1 and "missing" in err)

        # Fix 4: compare. Rebuild the cache, then compare against baselines.
        live = measure_live(Client("t", http=_fleet_http(since, rurl_jobs, fci_jobs)),
                            since, until, out)
        same = json.loads(json.dumps(live))
        same["projects"]["rurl"]["job_minutes"] = 25.0
        base_path = out / "base.json"
        base_path.write_text(json.dumps({"measured": same}))
        code, text, _ = _run_main([*day, "--cached", "--compare", str(base_path)])
        check("compare: same length works, shows -60%", code == 0 and "-60.0%" in text)
        code, text, _ = _run_main([*day, "--cached", "--compare", str(base_path), "--json"])
        try:
            cmp = json.loads(text)
        except ValueError:
            cmp = {}
        check("compare --json emits the comparison",
              code == 0 and cmp.get("rows", {}).get("rurl", {}).get("pct") == -60.0
              and cmp.get("unit") == "job-minutes")

        longer = json.loads(json.dumps(live))
        longer["window"]["until"] = "2026-10-15T00:00:00Z"  # 14 days
        longer["projects"]["rurl"]["job_minutes"] = 20.0  # 2x current over 2x days
        base_path.write_text(json.dumps(longer))
        code, _, err = _run_main([*day, "--cached", "--compare", str(base_path)])
        check("compare refuses windows of different length", code == 1 and "--per-day" in err)
        code, text, _ = _run_main([*day, "--cached", "--compare", str(base_path),
                                   "--per-day", "--json"])
        try:
            cmp = json.loads(text)
        except ValueError:
            cmp = {}
        rurl_row = cmp.get("rows", {}).get("rurl", {})
        check(f"compare --per-day normalizes both sides (got {rurl_row})",
              code == 0 and rurl_row == {"baseline": 1.4, "current": 1.4, "pct": 0.0})

    # glab api --include parsing, including an empty X-Prev-Page.
    status, headers, body = parse_include(
        b"HTTP/2.0 200 OK\nX-Next-Page: 2\nX-Prev-Page: \n\n[{\"id\": 1}]", "x"
    )
    check("glab include parse", (status, headers.get("x-next-page"),
                                 headers.get("x-prev-page"), json.loads(body))
          == (200, "2", "", [{"id": 1}]))
    status, _, _ = parse_include(b"HTTP/2.0 404 Not Found\n\n{}", "x")
    check("glab include 404", status == 404)

    # Fix 6: glab failures become ApiError with stderr; an HTTP error answer
    # glab exits non-zero on is passed through.
    def run_with(returncode, stdout=b"", stderr=b"", exc=None):
        def run(*_a, **_k):
            if exc:
                raise exc
            return subprocess.CompletedProcess([], returncode, stdout, stderr)
        return run

    def raised(fn):
        try:
            fn()
        except ApiError as err:
            return str(err)
        except Exception as err:  # noqa: BLE001 - a wrong type is a failure
            return f"WRONG {type(err).__name__}"
        return None

    url = f"{API}/projects/x/jobs?page=1"
    msg = raised(lambda: glab_get(url, None, run=run_with(1, b"", b"glab: not logged in")))
    check(f"glab non-zero exit raises ApiError with stderr (got {msg})",
          msg is not None and "not logged in" in msg)
    msg = raised(lambda: glab_get(url, None, run=run_with(
        0, exc=subprocess.TimeoutExpired("glab", 120))))
    check(f"glab timeout raises ApiError (got {msg})",
          msg is not None and not msg.startswith("WRONG"))
    msg = raised(lambda: glab_get(url, None, run=run_with(0, exc=FileNotFoundError("glab"))))
    check(f"glab OSError raises ApiError (got {msg})",
          msg is not None and not msg.startswith("WRONG"))
    try:
        status = glab_get(url, None, run=run_with(
            1, b"HTTP/2.0 404 Not Found\n\n{}", b"glab: 404"))[0]
    except ApiError:
        status = None
    check("glab non-zero exit with an HTTP 404 answer passes 404 on", status == 404)

    # Fix 7: urllib transport errors become ApiError; 5xx retries, bounded,
    # honoring Retry-After.
    def urlopen_raising(exc):
        def urlopen(*_a, **_k):
            raise exc
        return urlopen

    msg = raised(lambda: urllib_get(url, None, urlopen=urlopen_raising(
        urllib.error.URLError("no route"))))
    check(f"urllib URLError raises ApiError (got {msg})",
          msg is not None and not msg.startswith("WRONG"))
    msg = raised(lambda: urllib_get(url, None, urlopen=urlopen_raising(socket.timeout("t"))))
    check(f"urllib timeout raises ApiError (got {msg})",
          msg is not None and not msg.startswith("WRONG"))

    answers = [(503, {"retry-after": "7"}, b""), (502, {}, b""),
               (200, {"x-next-page": ""}, b"[]")]
    sleeps5 = []
    try:
        Client("t", http=lambda u, t: answers.pop(0), sleep=sleeps5.append).get(
            "rurl", "jobs", 1, {})
        ok5 = True
    except ApiError:
        ok5 = False
    check(f"5xx retried with Retry-After then default (sleeps {sleeps5})",
          ok5 and sleeps5 == [7.0, BACKOFF_SECONDS])
    calls = []

    def always_503(u, t):
        calls.append(u)
        return 503, {}, b""

    msg = raised(lambda: Client("t", http=always_503, sleep=lambda s: None).get(
        "rurl", "jobs", 1, {}))
    check(f"5xx retries are bounded (calls {len(calls)}, {msg})",
          msg is not None and len(calls) == MAX_5XX_RETRIES + 1)
    sleeps429 = []
    seq = [(429, {"retry-after": "3"}, b""), (200, {"x-next-page": ""}, b"[]")]
    Client("t", http=lambda u, t: seq.pop(0), sleep=sleeps429.append).get(
        "rurl", "jobs", 1, {})
    check("429 honors Retry-After", sleeps429 == [3.0])

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
                    help="raw API response cache root (default tmp/ci-minutes)")
    ap.add_argument("--cached", action="store_true",
                    help="replay the pages the window's cache manifest lists")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--compare", type=Path, metavar="BASELINE",
                    help="print per-project change in percent against BASELINE")
    ap.add_argument("--per-day", action="store_true",
                    help="with --compare: compare job-minutes per day")
    ap.add_argument("--self-test", action="store_true", help="run the offline self-test")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.since or not args.until:
        ap.error("--since and --until are required")
    if args.per_day and not args.compare:
        ap.error("--per-day needs --compare")
    try:
        since, until = parse_day(args.since), parse_day(args.until)
    except ValueError as err:
        ap.error(str(err))
    if until <= since:
        ap.error("--until must be after --since")

    baseline = None
    if args.compare:
        baseline = json.loads(args.compare.read_text())
        base_window = baseline.get("measured", baseline)["window"]
        here = {"since": iso(since), "until": iso(until)}
        if not args.per_day and window_days(base_window) != window_days(here):
            print(f"error: baseline window is {window_days(base_window):g} days,"
                  f" current {window_days(here):g} days; pass --per-day to"
                  " compare job-minutes per day", file=sys.stderr)
            return 1

    try:
        if args.cached:
            result = measure_cached(since, until, args.out)
        else:
            result = measure_live(make_client(), since, until, args.out)
    except ApiError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if baseline is not None:
        cmp = compare(baseline, result, args.per_day)
        print(json.dumps(cmp, indent=2) if args.json else render_compare(cmp))
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
