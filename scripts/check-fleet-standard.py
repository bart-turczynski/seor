# check-fleet-standard v4
"""Test fleet packages against design/fleet-standard.md and list each gap.

WHY THIS EXISTS. The nine per-package "meets the fleet standard" issues run
unattended, so their acceptance has to be a command, not a reading. Repositories
have also drifted from fleet-level briefs before without anyone noticing
(SEOR-tullzdwb). This reads one package, or all nine, and prints a gap table per
package against the standard (SEOR-myokihrl).

    python3 scripts/check-fleet-standard.py                   # all nine
    python3 scripts/check-fleet-standard.py --repo rurl       # one package
    python3 scripts/check-fleet-standard.py --repo rurl --local ~/Projects/rurl
    python3 scripts/check-fleet-standard.py --repo rurl --local ~/Projects/rurl --offline
    python3 scripts/check-fleet-standard.py --self-test       # offline fixtures

Exit status: 0 when nothing is missing, 1 on any gap, 2 when there is no gap
but a probe failed (a network error, glab refusing), so the run is incomplete.
A probe that fails is reported under "not judged", never as a gap.

WHERE IT READS. By default each package's `main` on GitLab, through `glab api`
(the repository tree, raw files, releases and pipeline schedules), because a
local checkout may be stale or on another branch. `--local PATH` reads the
files from a checkout instead and still asks GitLab and the web for live state.
`--offline` (needs `--local`) touches no network at all: the badge images, the
conditional badge slots and the schedules are then listed as not judged.

WHAT IT CHECKS, by section of the standard.

* Badges. The block between `<!-- badges: start -->` and
  `<!-- badges: end -->` in README.Rmd holds the standard's templates, in
  order, and nothing else. Image and link URLs are matched against the
  templates; `<stage>`/`<color>`, `<concept-doi>` and `<bp-id>` are matched as
  patterns. Alt text is not compared. The conditional slots are judged from
  live state: on CRAN (crandb), a GitLab Release (`releases` API), a concept
  DOI (CITATION.cff's top-level `doi:`, else the badge row; doi.org must
  resolve it and Zenodo must call it the concept DOI), and, for the FOSSA
  slots, a FOSSA project under the `custom+<org>/git+gitlab.com` locator
  that fossa-cli uploads to (FOSSA_ORG_ID). A badge shown
  while its condition does not hold is a gap. r-universe is not conditional in
  the standard: a package missing from r-universe is a gap.
* Badge images. Every image URL in the row answers 200 with an image whose
  text does not read "unknown", "not found", "invalid", "not set up",
  "inaccessible" or "no releases found".
* README. README.Rmd has a level-2 `## Installation` section holding an
  `install.packages()` call with the r-universe repository and, on CRAN,
  `install.packages("<pkg>")`. No heading outside fenced code and chunks, at
  any level, is maintainer content (BANNED_HEADING_RE, matched against the
  whole heading, so "Development version" passes and "Setup (development)"
  does not). No root `llms.txt`, and `llm-docs` not off in any pkgdown config.
* Logo. `man/figures/logo.svg` and `man/figures/logo.png` are in the tree, and
  README.Rmd's first level-1 heading is `# <pkg>` followed by an `<img>` whose
  `src` is `man/figures/logo.png` and whose `alt` is present and empty, with no
  title, aria-label, aria-labelledby or role that names it again: the <img>
  sits inside the heading, so a name would repeat the package name in the
  heading's accessible name. A link-wrapped <img> is a gap, since an empty alt
  leaves the link unnamed. The artwork itself is not judged.
* Files. The list in "Files every package carries", plus: LICENSE names Bart
  Turczynski as holder, LICENSE.md is the full MIT text, SECURITY.md and
  CODE_OF_CONDUCT.md name the public contact, and SECURITY.md is more than a
  stub (fewer than 10 non-blank lines is a stub).
* DESCRIPTION. Bart Turczynski with roles aut, cre and cph, the ORCID comment
  and the public email; `URL:` in the standard's order (trailing slashes
  ignored); `Language: en-US`; a declared R floor; `X-schema.org-keywords`
  with at least five tokens besides `r`, `rstats`, `r-stats` and `r-package`,
  which r-universe drops, and none of those four.
* .gitlab-ci.yml. R CMD check with `--as-cran` and `error_on = "warning"` on
  every push to main, with CRAN incoming switched off only where ADR 0004
  allows; a coverage job on push with a `coverage:` regex, a cobertura report,
  a threshold of at least 95 and no `allow_failure`, which also runs in both
  schedule pipelines (the coverage badge reads the latest successful pipeline
  on main); `pages` on push; the
  cheap gates (README drift, news-version, citation-version, lint, spelling);
  deep-check legs for R release, oldrel, devel and the DESCRIPTION floor;
  ASAN/UBSAN legs for punycoder, pslr and robotstxtr; `osv-audit` and
  `security-audit` on the dependency-audit schedule, with seor's
  disposition-row test files; a `fossa analyze` job for rurl, ssrfr and seor;
  the pandoc pin (PANDOC_PIN, SEOR-egfbijyi): every job that runs R on a
  push to main downloads pandoc from its GitHub release
  (`github.com/jgm/pandoc/releases/download/<version>/pandoc-`), names that
  version as `$PANDOC_VERSION`, which .gitlab-ci.yml sets to PANDOC_PIN, one
  value however many times it is assigned, in a line the job sees (its
  variables, the global ones or its setup) and never in `parallel: matrix`.
  The pin is read by running check-toolchain.R's own reader
  (`--pandoc-assignments`, SEOR-xhyrogfm), so the two never disagree on it;
  this needs Rscript, and without it the pin is not judged. The install has
  the standard's shape (pandoc_install_state): `if <download> && <sha256sum
  -c> && dpkg -i FILE; then ...; else ...; fi` in one script item, or the three
  steps as three script items in that order, each one command or pipeline
  judged by its last command. The download saves the release to FILE with
  curl or wget, the check names FILE (or reads its digest from stdin beside
  it), paths compared as whole words, and the download has a time limit: curl
  `--max-time` or `-m`, wget `--timeout` with `--tries` of 5 or fewer, or
  `timeout`. The install counts in the `before_script` or `script` the job
  ends up with (its own, else the template's that GitLab merges last), not in
  `default:`, which also reaches jobs on images without dpkg or curl; a pin
  found only there is reported, to move into the template.
* Local gate. The pre-commit config, or a script its hooks call, runs a URL
  check (`check_url_db`, `url_db_from_package_sources` or urlchecker), and
  one of them calls `rmarkdown::pandoc_version()` and reads `PANDOC_VERSION`
  from `.gitlab-ci.yml`, comparing the local pandoc with the CI pin
  (check-toolchain.R). Reading the variable from the environment does not
  count: nothing sets it locally.
* Schedules. A `deep-check` and a `dependency-audit` schedule, each active,
  on `main`, with `SCHEDULE_KIND` set on the schedule itself; no schedule
  without a `SCHEDULE_KIND` or off `main`.

HOW IT READS CI, AND WHERE THAT STOPS. seor's scripts are stdlib-only and read
YAML with small fixed-shape readers rather than a YAML library (check-citation,
bestpractices-url), so this does too. `.gitlab-ci.yml` is split into its
top-level blocks; `extends:` is followed, a job's own `rules:` replace the
template's, `variables:` merge, and YAML anchors (`*name`) pull in the block
that defines them. `default: before_script` (or the top-level one) joins every
job that sets no `before_script` of its own and does not turn it off with
`inherit: default:`. A job's text joins every block it extends; the pandoc
rule alone reads the one `before_script` and `script` a job ends up with,
since GitLab replaces arrays along `extends`. `rules:if` and `workflow:rules`
are evaluated for real (a
small evaluator for `==`, `!=`, `=~`, `!~`, `&&`, `||`, presence and
parentheses) in four pipelines: a push to main, a `deep-check` schedule, a
`dependency-audit` schedule and a tag. A job "runs" in a pipeline when the
workflow admits it and its first matching rule is not `never` or `manual`.
A deep-check leg is an R CMD check job that runs in the deep-check schedule and
in neither a push to main nor the dependency-audit schedule (design/fleet.md:
every scheduled job requires its kind). Its R version comes from its image tag,
expanded through `parallel:matrix` and variables, and is compared by minor
version with the current release and oldrel (api.r-hub.io) and the DESCRIPTION
floor. What a job does is read textually, from the job and from every
repository R, shell or YAML script it names (two levels deep, comment lines
dropped, and R stage tables' `default = FALSE` entries dropped, since those
stages are opt-in). Python scripts are not followed: the citation scripts a job
names quote `R CMD check --as-cran` in their prose.
So a gate is "present" when its call appears in that text; a script that takes
the call but skips it at run time reads as present. Not checked: whether a tag
pipeline fails on "already on CRAN", whether the URL check fails on zero URLs
and exempts only the BugReports 404, how security-audit treats missing OSS
Index credentials, the GitLab project badges, and that no employer is named as
copyright holder or funder. Those stay review items.

Stdlib only. `glab` must be on PATH and authenticated unless `--offline`, and
`Rscript` for the pandoc pin (the self-test included).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

OWNER = "bart-turczynski"
FLEET = ("rurl", "pslr", "punycoder", "raddr", "ssrfr", "pagerankr", "sitemapr", "seor", "robotstxtr")
FOSSA_PACKAGES = frozenset({"rurl", "ssrfr", "seor"})
# The account's FOSSA organization. `fossa analyze` with the API key uploads to
# `custom+<org>/git+gitlab.com/<owner>/<pkg>`; the bare `git+gitlab.com/...`
# locator answers 404 (rurl's first upload, 2026-10-03).
FOSSA_ORG_ID = "62973"
SANITIZER_PACKAGES = frozenset({"punycoder", "pslr", "robotstxtr"})
ORCID = "0000-0002-8788-7980"
CONTACT = "bartek@turczynski.pl"
COVERAGE_MIN = 95.0
# The fleet's pandoc (design/fleet-standard.md, "CI on every push to `main`";
# SEOR-egfbijyi). Each repository records its own pin once, as PANDOC_VERSION
# in .gitlab-ci.yml, which its CI installs and its check-toolchain.R reads;
# this is the standard's value, so a repository that pins another is a gap.
# A bump moves it together with each repository's PANDOC_VERSION, the two
# sha256 digests beside it and a re-knit of its README.md.
PANDOC_PIN = "3.10"
SECURITY_STUB_LINES = 10
BAD_BADGE_TEXT = ("unknown", "not found", "invalid", "not set up", "inaccessible", "no releases found")
LIFECYCLE = {"experimental": "orange", "stable": "brightgreen", "superseded": "blue", "deprecated": "orange"}
SCHEDULE_KINDS = ("deep-check", "dependency-audit")
# README headings the standard treats as maintainer content, matched against the whole
# heading text, lower-cased, with backticks and a trailing parenthetical dropped.
BANNED_HEADING_RE = re.compile(
    r"setup|development|verification|(?:project|repository) (?:layout|structure)|current state|status"
    r"|dependencies|function overview|key functions")
# Keyword tokens r-universe drops, so they never count and never belong.
DROPPED_KEYWORDS = frozenset({"r", "rstats", "r-stats", "r-package"})
MIN_KEYWORDS = 5
USER_AGENT = "seor-check-fleet-standard"

REQUIRED_FILES = (
    "README.Rmd",
    "README.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SECURITY-INSIGHTS.yml",
    "LICENSE",
    "LICENSE.md",
    "inst/CITATION",
    "CITATION.cff",
    ".zenodo.json",
    "codemeta.json",
    "ARCHITECTURE.md",
    "NEWS.md",
)
REQUIRED_DIRS = (".gitlab/issue_templates", ".gitlab/merge_request_templates")
AUDIT_TEST_FILES = (
    "tests/testthat/helper-security.R",
    "tests/testthat/test-osv.R",
    "tests/testthat/test-security.R",
)


# --- results -------------------------------------------------------------------


@dataclass
class Report:
    pkg: str
    gaps: list[tuple[str, str]] = field(default_factory=list)
    unjudged: list[tuple[str, str]] = field(default_factory=list)

    def gap(self, area: str, text: str) -> None:
        self.gaps.append((area, text))

    def skip(self, area: str, text: str) -> None:
        self.unjudged.append((area, text))

    def render(self) -> str:
        lines = [f"## {self.pkg}: {len(self.gaps)} gap(s)", ""]
        if self.gaps:
            lines += ["| area | gap |", "|------|-----|"]
            lines += [f"| {area} | {text.replace('|', '/')} |" for area, text in self.gaps]
        else:
            lines.append("No gaps.")
        if self.unjudged:
            lines += ["", "Not judged:"]
            lines += [f"- {area}: {text}" for area, text in self.unjudged]
        return "\n".join(lines) + "\n"


class ProbeError(Exception):
    """A network or glab failure: reported as not judged, never as a gap."""


# --- sources -------------------------------------------------------------------


class DictSource:
    """Files held in memory: the self-test's fixtures."""

    def __init__(self, files: dict[str, str]):
        self.files = dict(files)

    def tree(self) -> set[str]:
        return set(self.files)

    def read(self, path: str) -> str | None:
        return self.files.get(path)


class LocalSource:
    """A checkout on disk, read-only. Skips VCS and build directories."""

    SKIP_DIRS = {".git", "node_modules", "renv", ".Rproj.user", "_scratch", "tmp", ".fp", ".r-lib"}

    def __init__(self, root: Path):
        self.root = root
        self._tree: set[str] | None = None

    def tree(self) -> set[str]:
        if self._tree is None:
            found = set()
            for dirpath, dirnames, filenames in os.walk(self.root):
                dirnames[:] = [d for d in dirnames if d not in self.SKIP_DIRS and not d.endswith(".Rcheck")]
                rel = Path(dirpath).relative_to(self.root)
                found.update((rel / name).as_posix() for name in filenames)
            self._tree = {p[2:] if p.startswith("./") else p for p in found}
        return self._tree

    def read(self, path: str) -> str | None:
        target = self.root / path
        if not target.is_file():
            return None
        return target.read_text(encoding="utf-8", errors="replace")


def glab_api(path: str, paginate: bool = False) -> object:
    command = ["glab", "api", *(["--paginate"] if paginate else []), path]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)  # noqa: S603
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ProbeError(f"glab api {path}: {error}") from error
    if result.returncode:
        raise ProbeError(f"glab api {path}: {result.stderr.strip()[:200]}")
    if not paginate:
        return json.loads(result.stdout)
    decoder, text, items, at = json.JSONDecoder(), result.stdout.strip(), [], 0
    while at < len(text):
        chunk, at = decoder.raw_decode(text, at)
        items.extend(chunk if isinstance(chunk, list) else [chunk])
        while at < len(text) and text[at].isspace():
            at += 1
    return items


def project_ref(pkg: str) -> str:
    return urllib.parse.quote(f"{OWNER}/{pkg}", safe="")


class GitLabSource:
    """A package's `main` on GitLab, through glab api."""

    def __init__(self, pkg: str, ref: str = "main"):
        self.project = project_ref(pkg)
        self.ref = ref
        self._tree: set[str] | None = None
        self._cache: dict[str, str | None] = {}

    def tree(self) -> set[str]:
        if self._tree is None:
            entries = glab_api(
                f"projects/{self.project}/repository/tree?ref={self.ref}&recursive=true&per_page=100",
                paginate=True,
            )
            self._tree = {e["path"] for e in entries if e.get("type") == "blob"}
        return self._tree

    def read(self, path: str) -> str | None:
        if path not in self.tree():
            return None
        if path not in self._cache:
            quoted = urllib.parse.quote(path, safe="")
            command = ["glab", "api", f"projects/{self.project}/repository/files/{quoted}/raw?ref={self.ref}"]
            for _ in range(3):  # GitLab answers the odd TLS handshake timeout
                result = subprocess.run(command, capture_output=True, timeout=120)  # noqa: S603
                if not result.returncode:
                    break
            if result.returncode:
                raise ProbeError(f"reading {path}: {result.stderr.decode(errors='replace').strip()[:200]}")
            self._cache[path] = result.stdout.decode("utf-8", errors="replace")
        return self._cache[path]


# --- live state ------------------------------------------------------------------


@dataclass
class State:
    """What the conditional parts of the standard depend on. None = unknown."""

    on_cran: bool | None = None
    on_runiverse: bool | None = None
    doi_resolves: bool | None = None
    doi_is_concept: bool | None = None
    has_release: bool | None = None
    fossa_project: bool | None = None
    schedules: list[dict] | None = None
    r_release: str | None = None
    r_oldrel: str | None = None
    errors: list[tuple[str, str]] = field(default_factory=list)


def http_get(url: str, timeout: int = 30) -> tuple[int, str, bytes]:
    """(status, content type, body). HTTP errors return their status; others raise."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("Content-Type", "") if error.headers else "", error.read() or b""
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProbeError(f"{url}: {getattr(error, 'reason', error)}") from error


def minor(version: str) -> str:
    return ".".join(version.split(".")[:2])


def probe_state(pkg: str, concept_doi: str | None) -> State:
    state = State()

    def attempt(area: str, func: Callable[[], None]) -> None:
        try:
            func()
        except (ProbeError, ValueError, KeyError) as error:
            state.errors.append((area, str(error)))

    def cran() -> None:
        status, _, body = http_get(f"https://crandb.r-pkg.org/{pkg}")
        if status == 404:
            state.on_cran = False
        elif status == 200:
            state.on_cran = not json.loads(body).get("archived", False)
        else:
            raise ProbeError(f"crandb answered {status}")

    def runiverse() -> None:
        status, _, _ = http_get(f"https://{OWNER}.r-universe.dev/api/packages/{pkg}")
        if status not in (200, 404):
            raise ProbeError(f"r-universe answered {status}")
        state.on_runiverse = status == 200

    def doi() -> None:
        if not concept_doi:
            return
        status, _, _ = http_get(f"https://doi.org/api/handles/{concept_doi}")
        if status not in (200, 404):
            raise ProbeError(f"doi.org answered {status}")
        state.doi_resolves = status == 200
        m = re.fullmatch(r"10\.5281/zenodo\.(\d+)", concept_doi)
        if state.doi_resolves and m:
            status, _, body = http_get(f"https://zenodo.org/api/records/{m.group(1)}")
            if status != 200:
                raise ProbeError(f"Zenodo record {m.group(1)} answered {status}")
            state.doi_is_concept = json.loads(body).get("conceptdoi", "").lower() == concept_doi.lower()

    def release() -> None:
        state.has_release = bool(glab_api(f"projects/{project_ref(pkg)}/releases?per_page=1"))

    def fossa() -> None:
        if pkg not in FOSSA_PACKAGES:
            return
        status, _, _ = http_get(fossa_image(pkg, "license"))
        if status not in (200, 404):
            raise ProbeError(f"FOSSA answered {status}")
        state.fossa_project = status == 200

    def schedules() -> None:
        found = []
        for item in glab_api(f"projects/{project_ref(pkg)}/pipeline_schedules", paginate=True):
            found.append(glab_api(f"projects/{project_ref(pkg)}/pipeline_schedules/{item['id']}"))
        state.schedules = found

    def rversions() -> None:
        for kind, attr in (("release", "r_release"), ("oldrel/1", "r_oldrel")):
            status, _, body = http_get(f"https://api.r-hub.io/rversions/resolve/{kind}")
            if status != 200:
                raise ProbeError(f"rversions answered {status}")
            setattr(state, attr, minor(json.loads(body)["version"]))

    for area, func in (
        ("badges", cran), ("badges", runiverse), ("badges", doi), ("badges", release),
        ("badges", fossa), ("schedules", schedules), ("ci", rversions),
    ):
        attempt(area, func)
    return state


# --- small readers ----------------------------------------------------------------


def read_dcf(text: str) -> dict[str, str]:
    """Flat DCF fields, joining continuation lines."""
    fields: dict[str, str] = {}
    key = None
    for line in text.splitlines():
        if not line.strip():
            key = None
        elif line[0].isspace():
            if key is not None:
                fields[key] += " " + line.strip()
        else:
            name, sep, value = line.partition(":")
            key = name.strip() if sep else None
            if key:
                fields[key] = value.strip()
    return fields


def cff_doi(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(r"^doi:\s*[\"']?(10\.[^\s\"']+)", text, re.M)
    return m.group(1) if m else None


def strip_comment_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def r_spans(text: str) -> list[tuple[int, int, int]]:
    """(open, close, depth) for each parenthesis pair, skipping strings and comments."""
    spans, stack, i, n = [], [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'":
            i += 1
            while i < n and text[i] != ch:
                i += 2 if text[i] == "\\" else 1
        elif ch == "#":
            while i < n and text[i] != "\n":
                i += 1
        elif ch == "(":
            stack.append(i)
        elif ch == ")" and stack:
            start = stack.pop()
            spans.append((start, i, len(stack)))
        i += 1
    return spans


def drop_opt_in_stages(text: str) -> str:
    """Remove `name = list(...)` entries of an R stage table that say `default = FALSE`."""
    spans = r_spans(text)
    drop = []
    for start, end, _ in spans:
        head = re.search(r"[\w.]+\s*=\s*list\s*$", text[max(0, start - 80):start])
        if not head:
            continue
        body = text[start + 1:end]
        inner = [(s - start - 1, e - start - 1) for s, e, _ in spans if start < s and e < end]
        flat = list(body)
        for s, e in inner:
            for k in range(s, e + 1):
                flat[k] = " "
        if re.search(r"\bdefault\s*=\s*FALSE\b", "".join(flat)):
            drop.append((start - len(head.group(0)), end + 1))
    for start, end in sorted(drop, reverse=True):
        if not any(s <= start and end <= e and (s, e) != (start, end) for s, e in drop):
            text = text[:start] + text[end:]
    return text


PATH_TOKEN = re.compile(r"(?<![\w$/.-])((?:\.?[\w-]+/)+[\w.-]+)")
# Python is not followed: the seor-family scripts a job names (check-citation,
# check-bugreports) quote `R CMD check --as-cran` in their prose.
SCRIPT_SUFFIXES = {"", ".R", ".r", ".sh", ".yml", ".yaml"}


def inline_scripts(text: str, source, depth: int = 2, seen: set[str] | None = None) -> list[tuple[str, str]]:
    """(path, text) for each repository script `text` names, followed `depth` levels."""
    seen = set() if seen is None else seen
    out = []
    tree = source.tree()
    for token in PATH_TOKEN.findall(text):
        if token in seen or token not in tree or Path(token).suffix not in SCRIPT_SUFFIXES:
            continue
        if token == ".gitlab-ci.yml":
            continue
        seen.add(token)
        try:
            body = source.read(token) or ""
        except ProbeError:
            continue
        if len(body) > 400_000:
            continue
        body = strip_comment_lines(body)
        if Path(token).suffix in (".R", ".r"):
            body = drop_opt_in_stages(body)
        out.append((token, body))
        if depth > 1:
            out += inline_scripts(body, source, depth - 1, seen)
    return out


# --- CI: blocks, extends, rules ---------------------------------------------------

TOP_KEY = re.compile(r"^([^\s#-][^\n]*?):(?=\s|$)")
RESERVED = {"stages", "default", "variables", "workflow", "include", "image", "services",
            "cache", "before_script", "after_script"}


def split_blocks(text: str) -> dict[str, list[str]]:
    """Top-level key -> its lines (key line first), comment lines dropped."""
    blocks: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = TOP_KEY.match(line)
        if m:
            current = m.group(1).strip().strip("\"'")
            blocks[current] = [line]
        elif current is not None:
            blocks[current].append(line)
    return blocks


def children(lines: list[str]) -> dict[str, tuple[str, list[str]]]:
    """Immediate child keys of a block: key -> (inline value, deeper lines)."""
    out: dict[str, tuple[str, list[str]]] = {}
    body = [line for line in lines[1:] if line.strip()]
    if not body:
        return out
    indent = len(body[0]) - len(body[0].lstrip())
    key = None
    for line in body:
        level = len(line) - len(line.lstrip())
        if level == indent and not line.lstrip().startswith("- "):
            m = re.match(r"\s*([\w.-]+):\s*(.*)$", line)
            if m:
                key = m.group(1)
                out[key] = (m.group(2).strip(), [])
                continue
        if key is not None and level >= indent:
            out[key][1].append(line)
    return out


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        inner = value[1:-1]
        return inner.replace("''", "'") if value[0] == "'" else inner
    return value


def list_values(inline: str, lines: list[str]) -> list[str]:
    if inline.startswith("["):
        return [unquote(v) for v in inline.strip("[]").split(",") if v.strip()]
    if inline:
        return [unquote(inline)]
    return [unquote(line.strip()[2:]) for line in lines if line.strip().startswith("- ")]


def parse_rules(lines: list[str]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    body = [line for line in lines if line.strip()]
    if not body:
        return rules
    item_indent = min(len(line) - len(line.lstrip()) for line in body if line.lstrip().startswith("- "))
    for line in body:
        level = len(line) - len(line.lstrip())
        stripped = line.strip()
        if level == item_indent and stripped.startswith("- "):
            rules.append({})
            stripped = stripped[2:]
        if not rules:
            continue
        m = re.match(r"([\w-]+):\s*(.*)$", stripped)
        if m and level <= item_indent + 2:
            rules[-1][m.group(1)] = unquote(m.group(2))
    return rules


EXPR_TOKEN = re.compile(r"\s*(?:(\$\{?\w+\}?)|(\"[^\"]*\"|'[^']*')|(==|!=|=~|!~|&&|\|\||\(|\))|(null)\b)")


def evaluate(expr: str, env: dict[str, str]) -> bool:
    """Evaluate a GitLab `rules:if` expression against variables in `env`."""
    tokens: list[tuple[str, str]] = []
    i = 0
    while i < len(expr):
        if expr[i].isspace():
            i += 1
            continue
        if tokens and tokens[-1] == ("op", "=~") or tokens and tokens[-1] == ("op", "!~"):
            m = re.compile(r"/((?:\\.|[^/])*)/([a-z]*)").match(expr, i)
            if not m:
                raise ValueError(f"bad regex in {expr!r}")
            tokens.append(("re", m.group(1) + ("\x00i" if "i" in m.group(2) else "")))
            i = m.end()
            continue
        m = EXPR_TOKEN.match(expr, i)
        if not m or m.end() == i:
            raise ValueError(f"cannot read rule {expr!r}")
        var, string, op, null = m.groups()
        if var:
            tokens.append(("var", var.strip("${}")))
        elif string:
            tokens.append(("str", string[1:-1]))
        elif op:
            tokens.append(("op", op))
        else:
            tokens.append(("null", ""))
        i = m.end()

    pos = 0

    def value(token: tuple[str, str]) -> str | None:
        kind, text = token
        if kind == "var":
            return env.get(text)
        if kind == "str":
            return text
        return None

    def atom() -> bool:
        nonlocal pos
        token = tokens[pos]
        if token == ("op", "("):
            pos += 1
            result = disjunction()
            pos += 1
            return result
        pos += 1
        if pos < len(tokens) and tokens[pos][0] == "op" and tokens[pos][1] in ("==", "!=", "=~", "!~"):
            op = tokens[pos][1]
            right = tokens[pos + 1]
            pos += 2
            left = value(token)
            if op in ("==", "!="):
                equal = left == value(right)
                return equal if op == "==" else not equal
            pattern, _, flag = right[1].partition("\x00")
            hit = left is not None and re.search(pattern, left, re.I if flag else 0) is not None
            return hit if op == "=~" else not hit
        return bool(value(token))

    def conjunction() -> bool:
        nonlocal pos
        result = atom()
        while pos < len(tokens) and tokens[pos] == ("op", "&&"):
            pos += 1
            right = atom()
            result = result and right
        return result

    def disjunction() -> bool:
        nonlocal pos
        result = conjunction()
        while pos < len(tokens) and tokens[pos] == ("op", "||"):
            pos += 1
            right = conjunction()
            result = result or right
        return result

    return disjunction()


def first_match(rules: list[dict[str, str]], env: dict[str, str]) -> str | None:
    """The `when` of the first rule that matches, or None when none matches."""
    for rule in rules:
        if "if" not in rule or evaluate(rule["if"], env):
            return rule.get("when", "on_success")
    return None


PIPELINES = {
    "push": {"CI_PIPELINE_SOURCE": "push", "CI_COMMIT_BRANCH": "main", "CI_COMMIT_REF_NAME": "main"},
    "deep-check": {"CI_PIPELINE_SOURCE": "schedule", "CI_COMMIT_BRANCH": "main",
                   "CI_COMMIT_REF_NAME": "main", "SCHEDULE_KIND": "deep-check"},
    "dependency-audit": {"CI_PIPELINE_SOURCE": "schedule", "CI_COMMIT_BRANCH": "main",
                         "CI_COMMIT_REF_NAME": "main", "SCHEDULE_KIND": "dependency-audit"},
    "tag": {"CI_PIPELINE_SOURCE": "push", "CI_COMMIT_TAG": "v9.9.9", "CI_COMMIT_REF_NAME": "v9.9.9"},
}


@dataclass
class Job:
    name: str
    attrs: dict[str, tuple[str, list[str]]]
    text: str
    variables: dict[str, str]
    runs: dict[str, bool] = field(default_factory=dict)
    scripts: list[tuple[str, str]] = field(default_factory=list)
    inherits_default_before: bool = False

    def full_text(self) -> str:
        return "\n".join([self.text] + [body for _, body in self.scripts])

    def chunks(self) -> list[str]:
        return [self.text] + [body for _, body in self.scripts]


def yaml_scalar(raw: str) -> str:
    """A one-line YAML scalar's value: quotes removed, a trailing `# comment` dropped.

    An unquoted decimal is read as YAML reads it, a float: `3.10` is 3.1 to
    GitLab's parser as to PyYAML (SEOR-egfbijyi). PANDOC_VERSION is not read
    here but by check-toolchain.R, whose `yaml_scalar()` does the same
    (pandoc_assignments(); SEOR-xhyrogfm).
    """
    raw = raw.strip()
    quoted = re.match(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^']|'')*'", raw)
    if quoted:
        return unquote(quoted.group(0))
    value = re.sub(r"\s+#.*$", "", raw)
    if re.fullmatch(r"[-+]?\d+\.\d+", value):
        return str(float(value))
    return value


def scalar_map(lines: list[str]) -> dict[str, str]:
    out = {}
    for line in lines:
        m = re.match(r"\s*([\w.-]+):\s*(\S.*)$", line)
        if m:
            out[m.group(1)] = yaml_scalar(m.group(2))
    return out


class CI:
    def __init__(self, text: str, source):
        self.text = text
        self.blocks = split_blocks(text)
        self.source = source
        self.global_vars = scalar_map(self.blocks.get("variables", [])[1:])
        default = children(self.blocks.get("default", ["default:"]))
        self.default_image = default.get("image", ("", []))[0]
        # `default: before_script` runs in every job that sets none of its own.
        # The top-level `before_script:` is the deprecated spelling of the same.
        self.default_before = default.get("before_script")
        if self.default_before is None and "before_script" in self.blocks:
            self.default_before = ("", self.blocks["before_script"][1:])
        if "image" in self.blocks:
            self.default_image = self.blocks["image"][0].partition(":")[2].strip()
        workflow = children(self.blocks.get("workflow", ["workflow:"]))
        self.workflow_rules = parse_rules(workflow["rules"][1]) if "rules" in workflow else None
        self.anchors = {}
        for name, lines in self.blocks.items():
            for line in lines:
                for anchor in re.findall(r"&([\w-]+)", line.split("#")[0]):
                    self.anchors.setdefault(anchor, name)
        self.jobs = {name: self.job(name) for name in self.blocks
                     if name not in RESERVED and not name.startswith(".")}

    def env(self, pipeline: str) -> dict[str, str]:
        env = dict(self.global_vars)
        env.update({"CI_DEFAULT_BRANCH": "main"})
        env.update(PIPELINES[pipeline])
        return env

    def admitted(self, pipeline: str) -> bool:
        if self.workflow_rules is None:
            return True
        return first_match(self.workflow_rules, self.env(pipeline)) not in (None, "never")

    def resolve(self, name: str, seen: set[str]) -> tuple[dict, list[str], dict[str, str]]:
        """(attributes, text blocks, variables) of a block with its extends applied."""
        lines = self.blocks.get(name)
        if lines is None or name in seen:
            return {}, [], {}
        seen = seen | {name}
        own = children(lines)
        attrs: dict = {}
        texts: list[str] = []
        variables: dict[str, str] = {}
        parents = list_values(*own["extends"]) if "extends" in own else []
        for parent in parents:
            p_attrs, p_texts, p_vars = self.resolve(parent, seen)
            attrs.update(p_attrs)
            texts += p_texts
            variables.update(p_vars)
        attrs.update(own)
        variables.update(scalar_map(own.get("variables", ("", []))[1]))
        texts.append("\n".join(lines))
        for anchor in re.findall(r"\*([\w-]+)", "\n".join(lines)):
            holder = self.anchors.get(anchor)
            if holder and holder != name:
                texts.append("\n".join(self.blocks[holder]))
        return attrs, texts, variables

    def job(self, name: str) -> Job:
        attrs, texts, variables = self.resolve(name, set())
        inherits = bool(self.default_before) and "before_script" not in attrs and self.inherits_default_before(attrs)
        if inherits:
            inline, lines = self.default_before
            texts.insert(0, "\n".join(["before_script: " + inline] + lines))
        text = "\n".join(dict.fromkeys(texts))
        job = Job(name, attrs, text, variables, inherits_default_before=inherits)
        rules = parse_rules(attrs["rules"][1]) if "rules" in attrs else None
        job_when = attrs.get("when", ("on_success", []))[0] or "on_success"
        for pipeline in PIPELINES:
            if not self.admitted(pipeline):
                job.runs[pipeline] = False
                continue
            when = first_match(rules, self.env(pipeline)) if rules is not None else job_when
            job.runs[pipeline] = when in ("on_success", "always", "delayed")
        job.scripts = inline_scripts(text, self.source)
        return job

    @staticmethod
    def inherits_default_before(attrs: dict) -> bool:
        """False when `inherit: default:` is false or a list without before_script."""
        if "inherit" not in attrs:
            return True
        inherit = children(["inherit:"] + attrs["inherit"][1])
        if "default" not in inherit:
            return True
        value = inherit["default"][0]
        if value in ("true", "false"):
            return value == "true"
        return "before_script" in list_values(*inherit["default"])

    def setup_text(self, job: Job) -> str:
        """The job's effective `before_script` and `script`, `default:` left out.

        Unlike `job.text`, which joins every block the job extends, this takes
        the one `before_script` and `script` the job ends up with: its own, or
        else the template's merged last, as GitLab replaces arrays along
        `extends`. The anchor blocks they pull in are added.
        """
        parts = []
        for key in ("before_script", "script"):
            if key in job.attrs:
                inline, lines = job.attrs[key]
                parts.append("\n".join([f"{key}: {inline}"] + lines))
        text = "\n".join(parts)
        for anchor in dict.fromkeys(re.findall(r"\*([\w-]+)", text)):
            holder = self.anchors.get(anchor)
            if holder:
                text += "\n" + "\n".join(self.blocks[holder])
        return text

    def default_before_text(self) -> str:
        if not self.default_before:
            return ""
        inline, lines = self.default_before
        return "\n".join(["before_script: " + inline] + lines)

    def images(self, job: Job) -> list[str]:
        """The job's image(s), expanded through parallel:matrix and variables."""
        inline, lines = job.attrs.get("image", ("", []))
        image = unquote(inline) if inline else ""
        if not image:
            name = scalar_map(lines).get("name", "")
            image = name or self.default_image
        image = unquote(image)
        matrix: dict[str, list[str]] = {}
        if "parallel" in job.attrs:
            plines = job.attrs["parallel"][1]
            current = None
            for line in plines:
                m = re.match(r"\s*(?:- )?([A-Z_][A-Z0-9_]*):\s*(.*)$", line)
                if m:
                    current = m.group(1)
                    matrix.setdefault(current, []).extend(list_values(m.group(2), []) if m.group(2) else [])
                elif current and line.strip().startswith("- "):
                    matrix[current].append(unquote(line.strip()[2:]))
        out = [image]
        for _ in range(3):
            expanded = []
            for img in out:
                m = re.search(r"\$\{?(\w+)\}?", img)
                if not m:
                    expanded.append(img)
                    continue
                var = m.group(1)
                values = matrix.get(var) or [job.variables.get(var) or self.global_vars.get(var) or ""]
                expanded += [img[:m.start()] + v + img[m.end():] for v in values]
            out = expanded
        return [img for img in out if img]


CHECK_RE = re.compile(r"rcmdcheck::rcmdcheck\s*\(|\bR CMD check\b|\"CMD\",\s*\"check\"")
AS_CRAN_RE = re.compile(r"--as-cran")
ERROR_ON_RE = re.compile(r"error_on\s*=\s*\\?[\"']warning\\?[\"']")
INCOMING_OFF_RE = re.compile(r"_R_CHECK_CRAN_INCOMING_[\"']?\s*[=:]\s*[\"']?(?:false|FALSE|0)\b")
INCOMING_REMOTE_OFF_RE = re.compile(r"_R_CHECK_CRAN_INCOMING_REMOTE_[\"']?\s*[=:]\s*[\"']?(?:false|FALSE|0)\b")
URL_CHECK_RE = re.compile(r"check_url_db|url_db_from_package_sources|urlchecker::url_check|\burl_check\s*\(")
SANITIZER_IMAGE_RE = re.compile(r"-san\b|clang-asan|gcc-asan|r-debug|asan|ubsan", re.I)
R_JOB_RE = re.compile(r"\bRscript\b|\bR CMD\b")
PANDOC_URL_RE = re.compile(r"github\.com/jgm/pandoc/releases/download/([^/\s\"']+)/pandoc-")
# The pin itself is read by check-toolchain.R, the fleet's only reader of its
# spellings: pandoc_assignments() runs it (SEOR-xhyrogfm). The download must
# name its version through PANDOC_VERSION, the variable that script reads.
TOOLCHAIN_R = Path(__file__).resolve().with_name("check-toolchain.R")
PANDOC_VAR_TOKEN_RE = re.compile(r"\$\{?PANDOC_VERSION\}?")
PANDOC_DEB_URL_RE = re.compile(r"https?://github\.com/jgm/pandoc/releases/download/[^\s\"']+")
# The install's three steps, each matched against the last command of its
# pipeline, whose exit status is the pipeline's.
DOWNLOAD_STAGE_RE = re.compile(r"^(?:timeout\s.*?\s)?(curl|wget)\s")
SHA256_STAGE_RE = re.compile(r"^(?:sha256sum\b.*\s(?:-c|--check)\b|shasum\b.*-a\s*256\b.*\s(?:-c|--check)\b)")
DPKG_STAGE_RE = re.compile(r"^dpkg\b.*\s(?:-i|--install)\s")
# The one-item shape, read on a Shell mask: `if A && B && C; then …; else …; fi`.
IF_INSTALL_RE = re.compile(r"(?:^|[;&|(\n]|\b(?:then|else|do)\b)\s*if\s(.*?)[;\n]\s*then\s.*?\belse\s.*?\bfi\b", re.S)
# A download with no time limit hangs on a stalled CDN instead of failing into
# the warn fallback. Every pattern of the tool must match; a limit of 0 means
# none to curl, wget and timeout(1) alike. curl `--max-time`/`-m` (bundled
# too, `-fsSLm 300`) bounds an attempt, and its `--retry` count is finite.
# wget's `--timeout`/`--read-timeout`/`-T` bounds one try, but wget tries 20
# times by default, waiting between tries, and `--tries=0` is forever, so a
# limit counts only with `--tries` of 5 or fewer: about the ceiling of seor's
# curl (4 attempts of 120 s).
DOWNLOAD_BOUND_RE = {
    "curl": (re.compile(r"(?:^|\s)(?:--max-time(?:\s+|=)|-[A-Za-z]*m\s*)0*[1-9]"),),
    "wget": (re.compile(r"(?:^|\s)(?:--(?:read-)?timeout(?:\s+|=)|-[A-Za-z]*T\s*)0*[1-9]"),
             re.compile(r"(?:^|\s)(?:--tries(?:\s+|=)|-[A-Za-z]*t\s*)0*[1-5](?![\d.])")),
}
# `timeout 300 curl …` bounds the whole download, retries included.
TIMEOUT_WRAPPER_RE = re.compile(
    r"(?:^|\s)timeout\s+(?:(?:-[ks]|--kill-after|--signal)\s+\S+\s+|-\S+\s+)*"
    r"0*(?:[1-9]\d*(?:\.\d*)?|\.\d*[1-9]\d*)[smhd]?\s+(?:\S*/)?(?:curl|wget)\b")
PANDOC_LOCAL_RE = re.compile(r"\bpandoc_version\s*\(")
PANDOC_PIN_READ_RE = re.compile(r"\bPANDOC_VERSION\b")
# The local check reads the pin from .gitlab-ci.yml, named as a string (or, in
# a shell script, a bare word). An environment read does not count: nothing
# sets PANDOC_VERSION locally, so it compares with its default.
PANDOC_CI_FILE_RE = re.compile(r"[\"'](?:[^\"'\n]*/)?\.gitlab-ci\.yml[\"']")
PANDOC_CI_FILE_WORD_RE = re.compile(r"(?:^|\s)(?:\./)?\.gitlab-ci\.yml(?=[\s;|)]|$)", re.M)
PANDOC_ENV_READ_RE = re.compile(r"Sys\.getenv\(\s*[\"']PANDOC_VERSION[\"'][^)]*\)|\$\{?PANDOC_VERSION\b")
GATES = {
    "README drift": (re.compile(r"build_readme\s*\(|render\(\s*[\"']README\.Rmd"),),
    "news-version": (re.compile(r"NEWS\.md"), re.compile(r"development version", re.I)),
    "citation-version": (re.compile(r"check-citation\.py"),),
    "lint": (re.compile(r"lint_package\s*\(|lintr::lint\s*\(|lint_dir\s*\("),),
    "spelling": (re.compile(r"spell_check_package\s*\(|spell_check_files\s*\(|check-spelling"),),
}
THRESHOLD_RES = (
    re.compile(r"(?:percent_coverage\([^)]*\)|\b(?:pct|percent|coverage|cov|total)\w*)\s*(?:<=?|>=?)\s*(\d+(?:\.\d+)?)", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s*(?:<=?|>=?)\s*(?:covr::)?(?:percent_coverage|pct|percent|coverage|total)", re.I),
    re.compile(r"\b(?:\w*threshold|\w*fail_under|cov\w*_min\w*|min\w*_cov\w*|COVERAGE_MIN\w*)[\"']?\s*(?:[:=]|<-)\s*[\"']?(\d+(?:\.\d+)?)", re.I),
)


def coverage_thresholds(text: str) -> list[float]:
    found = []
    for pattern in THRESHOLD_RES:
        found += [float(v) for v in pattern.findall(text)]
    return [v for v in found if 1 <= v <= 100]


PIN_READS: dict[str, tuple[tuple[int, str], ...]] = {}


def read_pandoc_assignments(texts: list[str]) -> None:
    """Read each .gitlab-ci.yml text's PANDOC_VERSION assignments into PIN_READS.

    check-toolchain.R reads them: this runs its `--pandoc-assignments` instead
    of parsing the spellings a second way, so the two scripts cannot disagree
    on a pin (SEOR-xhyrogfm). It is the copy beside this script, which the
    fleet's copies match. The texts go in one Rscript run, separated by a line
    holding a form feed, so the self-test's fixtures cost one run, not one
    each. A ProbeError when Rscript cannot run it.
    """
    todo = [text for text in dict.fromkeys(texts) if text not in PIN_READS]
    if not todo:
        return
    stdin = "\n\f\n".join("\n".join(re.split(r"\r\n|\r|\n", text)) for text in todo) + "\n"
    command = ["Rscript", "--vanilla", str(TOOLCHAIN_R), "--pandoc-assignments"]
    try:
        run = subprocess.run(command, input=stdin, capture_output=True, encoding="utf-8", timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ProbeError(f"Rscript {TOOLCHAIN_R.name} --pandoc-assignments: {error}") from error
    if run.returncode:
        raise ProbeError(f"Rscript {TOOLCHAIN_R.name} --pandoc-assignments exited {run.returncode}: "
                         f"{run.stderr.strip()[-200:]}")
    found: dict[int, list[tuple[int, str]]] = {}
    for m in re.finditer(r"^(\d+)\t(\d+)\t(.*)$", run.stdout, re.M):
        found.setdefault(int(m.group(1)), []).append((int(m.group(2)), m.group(3)))
    for k, text in enumerate(todo, 1):
        PIN_READS[text] = tuple(found.get(k, ()))


def pandoc_assignments(text: str) -> tuple[tuple[int, str], ...]:
    """(line number, value) of each PANDOC_VERSION assignment in a .gitlab-ci.yml."""
    read_pandoc_assignments([text])
    return PIN_READS[text]


def script_entries(text: str) -> list[str]:
    """The shell text of each list item in a YAML `before_script`/`script` text.

    GitLab fails the job when an item exits non-zero. A `- |` block is one
    item, its lines joined by newlines; a `- >` block or a plain scalar over
    several lines is one line; a flow sequence, `script: [a, "b"]`, is an item
    per element.
    """
    lines = text.splitlines()
    entries: list[str] = []
    i = 0
    while i < len(lines):
        flow = re.match(r"\s*(?:before_script|script):\s*(\[.*)$", lines[i])
        m = re.match(r"(\s*)- (.*)$", lines[i])
        i += 1
        if flow:
            seq = flow.group(1).strip()
            while not seq.endswith("]") and i < len(lines):
                seq += " " + lines[i].strip()
                i += 1
            for item in re.findall(r"\s*(\"(?:[^\"\\]|\\.)*\"|'(?:[^']|'')*'|[^,]+?)\s*(?:,|$)", seq[1:-1]):
                entries.append(re.sub(r"\\(.)", r"\1", item[1:-1]) if item.startswith('"') else unquote(item))
            continue
        if not m:
            continue
        indent, head = len(m.group(1)), m.group(2).strip()
        body = []
        while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
            body.append(lines[i])
            i += 1
        block = re.fullmatch(r"([|>])[-+]?\d*", head)
        if block:
            margin = min((len(line) - len(line.lstrip()) for line in body if line.strip()), default=0)
            body = [line[margin:] for line in body]
            entries.append("\n".join(body) if block.group(1) == "|" else " ".join(line for line in body if line))
        else:
            entries.append(unquote(" ".join([head] + [line.strip() for line in body if line.strip()])))
    return entries


class Shell:
    """A shell text beside its mask: the same text with quoted strings, `$(…)`
    and escapes blanked. Operators and keywords are looked for in the mask, so
    only where sh reads them; words and paths are read from the text. Comments
    are blanked in both, and backslash-newlines joined."""

    def __init__(self, text: str, mask: str | None = None):
        if mask is None:
            text = re.sub(r"\\\n", " ", text)
            mask = re.sub(r"\"(?:[^\"\\]|\\.)*\"|'[^']*'|`[^`]*`|\$\((?:[^()]|\([^()]*\))*\)|\\.",
                          lambda m: "_" * len(m.group(0)), text)
            for m in re.finditer(r"(?:^|(?<=\s))#.*", mask, re.M):
                blank = " " * len(m.group(0))
                text = text[:m.start()] + blank + text[m.end():]
                mask = mask[:m.start()] + blank + mask[m.end():]
        self.text, self.mask = text, mask

    def split(self, sep: str) -> list[Shell]:
        """The pieces between the matches of `sep` in the mask."""
        cuts = [0] + [i for m in re.finditer(sep, self.mask) for i in m.span()] + [len(self.text)]
        return [Shell(self.text[a:b], self.mask[a:b]) for a, b in zip(cuts[::2], cuts[1::2])]

    def simple(self) -> bool:
        """One pipeline: no `;`, `&`, `&&`, `||` or newline, and no `!` before it."""
        return not re.search(r"[;\n]|&&|\|\||(?<![<>|])&(?!>)|^!", self.mask.strip())

    def last_stage(self) -> str:
        """The pipeline's last command, whose exit status is the pipeline's."""
        return self.split(r"(?<!>)\|&?")[-1].text.strip()


def install_steps(entries: list[str]) -> list[list[Shell]]:
    """The (download, check, install) candidates in a job's script items, in
    the standard's two shapes, each step one pipeline that runs only when the
    one before it succeeded: `if A && B && C; then …; else …; fi` inside one
    item, or three consecutive items, since a failing item ends the job.
    Nothing else is read as an install, `set -e` included (SEOR-xhyrogfm)."""
    shells = [Shell(entry) for entry in entries]
    found = []
    for sh in shells:
        for m in IF_INSTALL_RE.finditer(sh.mask):
            steps = Shell(sh.text[m.start(1):m.end(1)], sh.mask[m.start(1):m.end(1)]).split(r"&&")
            if len(steps) == 3 and all(step.simple() for step in steps):
                found.append(steps)
    triples = zip(shells, shells[1:], shells[2:])
    return found + [list(steps) for steps in triples if all(step.simple() for step in steps)]


def dpkg_installs(entries: list[str], path: str) -> int:
    """How many commands in the script items run `dpkg -i` on `path`."""
    count = 0
    for entry in entries:
        for piece in Shell(entry).split(r"&&|\|\||[;\n]|(?<![<>|])&(?!>)"):
            command = re.sub(r"^(?:(?:if|then|else|elif|do|!)\s+|[{(]\s*)*", "", piece.text.strip())
            if DPKG_STAGE_RE.match(command) and path in path_tokens(command):
                count += 1
    return count


def shell_path(text: str) -> str:
    """A path or command as compared here: `${X}` read as `$X`, quotes and `./` dropped."""
    text = re.sub(r"\$\{(\w+)\}", r"$\1", text).replace('"', "").replace("'", "")
    return re.sub(r"(?<![\w.$/-])\./", "", text)


def path_tokens(command: str) -> set[str]:
    """The words of a command, as shell_path() reads them: a path matches whole."""
    return set(re.split(r"[\s|;&<>()]+", shell_path(command))) - {""}


def stdout_redirect(command: str) -> str | None:
    """The file a command's stdout is redirected to, the last `>`, `>>`, `>|` or `1>`.

    `2>`, `&>` and `>&` redirect stderr or duplicate a descriptor, so they are
    skipped. Digits glued to a word belong to it: `x.deb2>f` redirects stdout.
    """
    target = None
    for m in re.finditer(r"(&|\d+)?(>\||>>?)(&)?\s*[\"']?([^\s\"'&|;<>]*)", command):
        fd, _, dup, path = m.groups()
        if fd and fd.isdigit() and m.start() and not command[m.start() - 1].isspace():
            fd = None
        if fd in (None, "1") and not dup and path:
            target = path
    return target


def download_target(command: str, url_vars: set[str]) -> tuple[str, str] | None:
    """(tool, file) when a curl or wget command saves the pandoc release to a file, else None.

    The command names the release URL, or a variable assigned it earlier. The
    file is the `-o`/`--output` argument (curl), the `-O`/`--output-document`
    one (wget); when that is `-` or absent, stdout's redirect; else, with no
    `-`, the URL's own file name (`curl -O`, wget's default).
    """
    tool = DOWNLOAD_STAGE_RE.match(command)
    url = PANDOC_DEB_URL_RE.search(command)
    named = any(re.search(rf"\$\{{?{var}\b", command) for var in url_vars)
    if not tool or not (url or named):
        return None
    if tool.group(1) == "curl":
        flag = r"-[A-Za-z]*o\s*|--output(?:\s+|=)"
    else:
        flag = r"-[A-Za-z]*O\s*|--output-document(?:\s+|=)"
    out = re.search(rf"(?:^|\s)(?:{flag})[\"']?([^\s\"']+)", command)
    target = out.group(1) if out else None
    if target in (None, "-"):
        named_file = url.group(0).rsplit("/", 1)[-1] if url and target is None else None
        target = stdout_redirect(command) or named_file
    return (tool.group(1), shell_path(target)) if target else None


def download_bounded(tool: str, command: str) -> bool:
    return bool(TIMEOUT_WRAPPER_RE.search(command)) or all(p.search(command) for p in DOWNLOAD_BOUND_RE[tool])


INSTALL_STATES = ("noncanonical", "unbounded", "installed")


def pandoc_install_state(entries: list[str]) -> str:
    """How a job's script items install the pandoc .deb, one of INSTALL_STATES.

    `installed` needs one of install_steps()' shapes whose download saves the
    release to a file, whose `sha256sum -c` (or `shasum -a 256 -c`) names that
    file or reads its digest from stdin beside it, and whose `dpkg -i`
    installs it, and no other command installs that file. Paths compare as
    whole words. That shape with a download that sets no time limit is
    `unbounded`; anything else is `noncanonical` (SEOR-egfbijyi,
    SEOR-xhyrogfm).
    """
    url_vars = set(re.findall(r"\b(\w+)=[\"']?https?://github\.com/jgm/pandoc/releases/download/", "\n".join(entries)))
    best = "noncanonical"
    for steps in install_steps(entries):
        download, check, install = (step.last_stage() for step in steps)
        saved = download_target(download, url_vars)
        if (saved and SHA256_STAGE_RE.match(check) and saved[1] in path_tokens(steps[1].text)
                and DPKG_STAGE_RE.match(install) and saved[1] in path_tokens(install)
                and dpkg_installs(entries, saved[1]) == 1):
            if download_bounded(saved[0], download):
                return "installed"
            best = "unbounded"
    return best


def check_pandoc_pin(on_push: list[Job], ci: CI, report: Report) -> None:
    """Every R job on push installs PANDOC_PIN from the release, sha256-checked.

    The install must reach the job through its own `before_script` or `script`
    (in practice the template the R jobs extend), not through `default:`: the
    install block needs Debian, dpkg and curl, and `default:` hands it to every
    job, including those on other images (seor's citation-version runs on
    python:3.13-alpine).

    The pin is what check-toolchain.R reads (pandoc_assignments()): one value
    in all of .gitlab-ci.yml. A shell assignment overrides `variables:` at run
    time, so with two values the one a job installs depends on where each
    sits; two are a gap, as they are an error to check-toolchain.R. A job
    must also see an assignment: in its variables, the global ones, or a line
    of its setup. A `parallel: matrix` entry is a gap of its own: a pin per
    leg is not one pin.
    """
    matrix = [job.name for job in ci.jobs.values()
              if "PANDOC_VERSION" in "\n".join(job.attrs.get("parallel", ("", []))[1])]
    if matrix:
        report.gap("ci", f"{', '.join(matrix)}: sets PANDOC_VERSION in `parallel: matrix`; record the pin once, in "
                         "`variables:` or the shared setup, so every leg installs the same pandoc")
    unpinned, in_default, unrecorded, candidates = [], [], {}, []
    for job in on_push:
        if not R_JOB_RE.search(job.full_text()):
            continue
        setup = ci.setup_text(job)
        bodies = [body for _, body in inline_scripts(setup, ci.source)]
        tokens = {t for chunk in [setup] + bodies for t in PANDOC_URL_RE.findall(chunk)}
        if not tokens:
            if job.inherits_default_before and PANDOC_URL_RE.search(ci.default_before_text()):
                in_default.append(job.name)
            else:
                unpinned.append(job.name)
            continue
        literal = sorted(t for t in tokens if not PANDOC_VAR_TOKEN_RE.fullmatch(t))
        if literal:
            unrecorded.setdefault(", ".join(literal), []).append(job.name)
            continue
        candidates.append((job, setup, bodies))
    values: list[str] | None = None
    assigning: set[str] = set()
    if candidates:
        try:
            found = pandoc_assignments(ci.text)
            values = list(dict.fromkeys(value for _, value in found))
            lines = re.split(r"\r\n|\r|\n", ci.text)
            assigning = {lines[n - 1] for n, _ in found if 0 < n <= len(lines)}
        except ProbeError as error:
            report.skip("ci", f"the pandoc pin was not read, only the install steps (probe failed: {error})")
    if values and len(values) > 1:
        report.gap("ci", f".gitlab-ci.yml assigns PANDOC_VERSION more than once, with different values "
                         f"({', '.join(values)}); keep one pin, as check-toolchain.R requires")
    never, unseen, other, unverified = [], [], [], {}
    for job, setup, bodies in candidates:
        if values is not None:
            visible = setup.splitlines()
            if job.inherits_default_before:
                visible += ci.default_before_text().splitlines()
            if not values:
                never.append(job.name)
                continue
            if not ("PANDOC_VERSION" in job.variables or "PANDOC_VERSION" in ci.global_vars
                    or any(line in assigning for line in visible)):
                unseen.append(job.name)
                continue
            if len(values) > 1:
                continue
            if values[0] != PANDOC_PIN:
                other.append(job.name)
                continue
        state = max([pandoc_install_state(script_entries(setup))] + [pandoc_install_state([body]) for body in bodies],
                    key=INSTALL_STATES.index)
        if state != "installed":
            unverified.setdefault(state, []).append(job.name)
    if unpinned:
        report.gap("ci", f"pandoc {PANDOC_PIN} is not installed from the pandoc release in the setup of "
                         f"{', '.join(unpinned)} (README.md is byte-stable only under the pinned pandoc)")
    if in_default:
        report.gap("ci", f"{', '.join(in_default)}: pandoc is pinned only in `default: before_script`, which every "
                         "job inherits, whatever its image; move the install into the before_script of the "
                         "template the R jobs extend")
    for tokens, names in unrecorded.items():
        report.gap("ci", f"{', '.join(names)}: downloads pandoc at {tokens}, not at $PANDOC_VERSION, the variable "
                         "check-toolchain.R compares the local pandoc with")
    if never:
        report.gap("ci", f"{', '.join(never)}: downloads pandoc at $PANDOC_VERSION, which .gitlab-ci.yml never assigns")
    if unseen:
        report.gap("ci", f"{', '.join(unseen)}: downloads pandoc at $PANDOC_VERSION, which neither its variables "
                         "nor its setup assign")
    if other:
        report.gap("ci", f"{', '.join(other)}: pins pandoc {values[0]}, not the fleet's {PANDOC_PIN}")
    reasons = {
        "noncanonical": f"does not install pandoc {PANDOC_PIN} in the standard's shape: `if <download to FILE, with a "
                        "time limit> && <sha256sum -c of FILE> && dpkg -i FILE; then ...; else <warn>; fi` in one "
                        "script item, or the download, the `sha256sum -c` and the `dpkg -i` as three script items in "
                        "that order, each one command or pipeline (design/fleet-standard.md)",
        "unbounded": f"downloads pandoc {PANDOC_PIN} with no time limit (curl --max-time, wget --timeout with "
                     "--tries of 5 or fewer, or timeout(1)), so a stalled download hangs the job instead of "
                     "reaching the warn fallback",
    }
    for state, names in unverified.items():
        report.gap("ci", f"{', '.join(names)}: {reasons[state]}")


def leg_roles(image: str, state: State, floor: str | None) -> set[str]:
    """Which deep-check legs an image covers: release, oldrel, devel, floor."""
    roles = set()
    name, _, tag = image.rpartition(":") if ":" in image.split("/")[-1] else (image, "", "")
    if "devel" in image.lower():
        roles.add("devel")
    if tag in ("latest", "release") or name.endswith("-release"):
        roles.add("release")
    if tag == "oldrel":
        roles.add("oldrel")
    if re.fullmatch(r"\d+\.\d+(?:\.\d+)?", tag):
        if state.r_release and minor(tag) == state.r_release:
            roles.add("release")
        if state.r_oldrel and minor(tag) == state.r_oldrel:
            roles.add("oldrel")
        if floor and minor(tag) == floor:
            roles.add("floor")
    return roles


# --- checks ------------------------------------------------------------------------


def fossa_locator(pkg: str) -> str:
    """The URL-encoded FOSSA project locator fossa-cli uploads `pkg` under."""
    return f"custom%2B{FOSSA_ORG_ID}%2Fgit%2Bgitlab.com%2F{OWNER}%2F{pkg}"


def fossa_image(pkg: str, issue: str) -> str:
    return f"https://app.fossa.com/api/projects/{fossa_locator(pkg)}.svg?type=shield&issueType={issue}"


def fossa_link(pkg: str, issue: str) -> str:
    return f"https://app.fossa.com/projects/{fossa_locator(pkg)}?ref=badge_shield&issueType={issue}"


@dataclass
class Slot:
    number: int
    name: str
    kind: re.Pattern
    image: str
    link: str


def badge_slots(pkg: str, concept_doi: str | None) -> list[Slot]:
    p = re.escape(pkg)
    o = re.escape(OWNER)
    stage = "(?P<stage>" + "|".join(LIFECYCLE) + ")"
    doi = re.escape(concept_doi) if concept_doi else r"10\.5281/zenodo\.\d+"

    def k(pattern: str) -> re.Pattern:
        return re.compile(pattern, re.I)

    return [
        Slot(1, "CRAN version", k(r"r-pkg\.org/badges/version"),
             rf"https://www\.r-pkg\.org/badges/version/{p}", rf"https://CRAN\.R-project\.org/package={p}"),
        Slot(2, "CRAN downloads", k(r"cranlogs|shields\.io/cran/d"),
             rf"https://cranlogs\.r-pkg\.org/badges/{p}", rf"https://CRAN\.R-project\.org/package={p}"),
        Slot(3, "CRAN checks", k(r"cranchecks|shields\.io/cran/checks"),
             rf"https://badges\.cranchecks\.info/worst/{p}\.svg",
             rf"https://cran\.r-project\.org/web/checks/check_results_{p}\.html"),
        Slot(4, "r-universe", k(r"r-universe\.dev"),
             rf"https://{o}\.r-universe\.dev/{p}/badges/version", rf"https://{o}\.r-universe\.dev/{p}"),
        Slot(5, "GitLab pipeline", k(r"/pipeline\.svg"),
             rf"https://gitlab\.com/{o}/{p}/badges/main/pipeline\.svg", rf"https://gitlab\.com/{o}/{p}/-/pipelines"),
        Slot(6, "GitLab coverage", k(r"/coverage\.svg|codecov"),
             rf"https://gitlab\.com/{o}/{p}/badges/main/coverage\.svg", rf"https://gitlab\.com/{o}/{p}/-/pipelines"),
        Slot(7, "docs", k(r"shields\.io/website|badge/docs|label=docs"),
             rf"https://img\.shields\.io/website\?url=https%3A%2F%2F{o}\.gitlab\.io%2F{p}%2F&label=docs"
             rf"&logo=gitlab&logoColor=white&up_message=pkgdown&up_color=1f75cb",
             rf"https://{o}\.gitlab\.io/{p}/"),
        Slot(8, "latest release", k(r"/v/release|badges/release\.svg"),
             rf"https://img\.shields\.io/gitlab/v/release/{o}%2F{p}", rf"https://gitlab\.com/{o}/{p}/-/releases"),
        Slot(9, "lifecycle", k(r"lifecycle"),
             rf"https://img\.shields\.io/badge/lifecycle-{stage}-(?P<color>\w+)\.svg",
             r"https://lifecycle\.r-lib\.org/articles/stages\.html#(?P<lstage>\w+)"),
        Slot(10, "repostatus", k(r"repostatus\.org"),
             r"https://www\.repostatus\.org/badges/latest/active\.svg", r"https://www\.repostatus\.org/#active"),
        Slot(11, "DOI", k(r"zenodo\.org/badge/(?:DOI|latestdoi)|doi\.org"),
             rf"https://zenodo\.org/badge/DOI/{doi}\.svg", rf"https://doi\.org/{doi}"),
        Slot(12, "Zenodo all software", k(r"badge/Zenodo"),
             r"https://img\.shields\.io/badge/Zenodo-all_software-1682D4\?logo=zenodo&logoColor=white",
             rf"https://zenodo\.org/search\?q=metadata\.creators\.person_or_org\.identifiers\.identifier:{ORCID}"),
        Slot(13, "OpenSSF Best Practices", k(r"bestpractices\.dev"),
             r"https://www\.bestpractices\.dev/projects/(?P<bp>\d+)/badge",
             r"https://www\.bestpractices\.dev/projects/(?P<bplink>\d+)"),
        Slot(14, "license", k(r"/license/|/l/|badge/license"),
             rf"https://img\.shields\.io/gitlab/license/{o}%2F{p}", rf"https://gitlab\.com/{o}/{p}/-/blob/main/LICENSE\.md"),
        Slot(15, "dependencies", k(r"tinyverse"),
             rf"https://tinyverse\.netlify\.app/badge/{p}", rf"https://CRAN\.R-project\.org/package={p}"),
        Slot(16, "last commit", k(r"last-commit"),
             rf"https://img\.shields\.io/gitlab/last-commit/{o}%2F{p}", rf"https://gitlab\.com/{o}/{p}/-/commits/main"),
        Slot(17, "FOSSA license", k(r"fossa\.com/api/projects/.*issueType=license|fossa\.com/api/projects/[^?]*$"),
             re.escape(fossa_image(pkg, "license")), re.escape(fossa_link(pkg, "license"))),
        Slot(18, "FOSSA security", k(r"fossa\.com/api/projects/.*issueType=security"),
             re.escape(fossa_image(pkg, "security")), re.escape(fossa_link(pkg, "security"))),
    ]


BADGE_RE = re.compile(r"\[!\[([^\]]*)\]\(([^)\s]+)\)\]\(([^)\s]+)\)")


def required_slots(pkg: str, state: State, concept_doi: str | None, report: Report) -> list[int] | None:
    """Slot numbers in the order the README must show them, or None if unknowable."""
    if state.on_cran is None:
        report.skip("badges", "CRAN status unknown, so the CRAN slots and the order are not judged")
        return None
    order = [1, 2, 3, 4] if state.on_cran else [4]
    order += [5, 6, 7]
    if state.has_release is None:
        report.skip("badges", "GitLab Release state unknown; slot 8 (latest release) not judged")
    elif state.has_release:
        order.append(8)
    order += [9, 10]
    if concept_doi:
        if state.doi_resolves is None:
            report.skip("badges", f"DOI {concept_doi} not resolved (offline or probe failed); slot 11 not judged")
        elif state.doi_resolves:
            order.append(11)
    order += [12, 13, 14]
    if state.on_cran:
        order.append(15)
    order.append(16)
    if pkg in FOSSA_PACKAGES:
        if state.fossa_project is None:
            report.skip("badges", "FOSSA project state unknown; slot 17 not judged")
        elif state.fossa_project:
            order += [17, 18]
    return order


def check_badges(pkg: str, source, state: State, report: Report) -> list[str]:
    """Badge row checks. Returns the image URLs found, for the image check."""
    readme = source.read("README.Rmd")
    if readme is None:
        report.gap("badges", "no README.Rmd, so no badge row")
        return []
    m = re.search(r"<!-- badges: start -->(.*?)<!-- badges: end -->", readme, re.S)
    if not m:
        report.gap("badges", "README.Rmd has no badges: start/end markers")
        return []
    block = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
    concept_doi = cff_doi(source.read("CITATION.cff"))
    badges = BADGE_RE.findall(block)
    if not concept_doi:
        for _, image, _ in badges:
            dm = re.search(r"zenodo\.org/badge/DOI/(10\.[^/]+/[^/]+?)\.svg", image)
            if dm:
                concept_doi = dm.group(1)
    if concept_doi and state.doi_is_concept is False:
        report.gap("badges", f"DOI {concept_doi} is a version DOI; the badge takes the concept DOI")
    slots = badge_slots(pkg, concept_doi)
    by_number = {s.number: s for s in slots}
    found: list[int] = []
    for alt, image, link in badges:
        slot = next((s for s in slots if s.kind.search(image)), None)
        if slot is None:
            report.gap("badges", f"badge not in the standard: [{alt}]({image})")
            continue
        if slot.number in (17, 18) and pkg not in FOSSA_PACKAGES:
            report.gap("badges", f"FOSSA badge on a package outside the allocation: {image}")
            continue
        im, lm = re.fullmatch(slot.image, image), re.fullmatch(slot.link, link)
        if not im:
            report.gap("badges", f"slot {slot.number} {slot.name}: image URL differs from the template: {image}")
        if not lm:
            report.gap("badges", f"slot {slot.number} {slot.name}: link differs from the template: {link}")
        if slot.number == 9 and im and lm:
            if LIFECYCLE[im.group("stage")] != im.group("color") or lm.group("lstage") != im.group("stage"):
                report.gap("badges", f"slot 9 lifecycle: stage, color and anchor disagree: {image} {link}")
        if slot.number == 13 and im and lm and im.group("bp") != lm.group("bplink"):
            report.gap("badges", "slot 13 OpenSSF: image and link name different projects")
        if slot.number in found:
            report.gap("badges", f"slot {slot.number} {slot.name}: shown twice")
            continue
        found.append(slot.number)
    order = required_slots(pkg, state, concept_doi, report)
    if order is None:
        return [image for _, image, _ in badges]
    for number in order:
        if number not in found:
            report.gap("badges", f"missing slot {number}: {by_number[number].name}")
    reasons = {1: "not on CRAN", 2: "not on CRAN", 3: "not on CRAN", 15: "not on CRAN",
               8: "no GitLab Release", 11: "no concept DOI that doi.org resolves",
               17: "no FOSSA project under the custom+<org>/git+gitlab.com locator yet",
               18: "no FOSSA project under the custom+<org>/git+gitlab.com locator yet"}
    unknown = set()
    if state.has_release is None:
        unknown.add(8)
    if concept_doi and state.doi_resolves is None:
        unknown.add(11)
    if state.fossa_project is None:
        unknown |= {17, 18}
    for number in found:
        if number not in order and number not in unknown and (number not in (17, 18) or pkg in FOSSA_PACKAGES):
            report.gap("badges", f"slot {number} {by_number[number].name} shown, but {reasons.get(number, 'not required')}")
    shown = [n for n in found if n in order]
    expected = [n for n in order if n in shown]
    if shown != expected:
        names = lambda seq: ", ".join(by_number[n].name for n in seq)  # noqa: E731
        report.gap("badges", f"order: shown {names(shown)}; the standard's order is {names(expected)}")
    if state.on_runiverse is False:
        report.gap("badges", "package is not on r-universe, so the r-universe badge cannot render")
    elif state.on_runiverse is None:
        report.skip("badges", "r-universe presence unknown")
    return [image for _, image, _ in badges]


def badge_text(body: bytes) -> str:
    text = body.decode("utf-8", errors="replace")
    parts = re.findall(r">([^<>]+)<", text)
    parts += re.findall(r"(?:aria-label|title)=\"([^\"]*)\"", text)
    return " ".join(parts).lower()


def check_images(images: list[str], fetch: Callable[[str], tuple[int, str, bytes]], report: Report) -> None:
    def one(url: str):
        try:
            return url, fetch(url), None
        except ProbeError as error:
            return url, None, str(error)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(one, images))
    for url, result, error in results:
        if error is not None:
            report.skip("badge images", f"network error fetching {url}: {error}")
            continue
        status, ctype, body = result
        if status != 200:
            report.gap("badge images", f"HTTP {status}: {url}")
            continue
        if "image" not in ctype and not body.lstrip().startswith((b"<svg", b"<?xml")):
            report.gap("badge images", f"not an image ({ctype or 'no content type'}): {url}")
            continue
        text = badge_text(body)
        bad = [word for word in BAD_BADGE_TEXT if word in text]
        if bad:
            report.gap("badge images", f"renders {bad[0]!r}: {url}")


def readme_headings(text: str) -> list[tuple[int, str, int]]:
    """(level, title, line index) for each ATX heading that renders: outside the YAML
    front matter, HTML comments, fenced code and chunks. Setext headings are not read."""
    fm = re.match(r"---\n.*?\n---[ \t]*\n", text, re.S)
    if fm:  # blank the front matter and comments out, keeping line numbers
        text = "\n" * fm.group(0).count("\n") + text[fm.end():]
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out, fence = [], None
    for i, line in enumerate(text.splitlines()):
        cm = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line)
        # A backtick fence's info string holds no backtick: ```x``` is inline code.
        if cm and not (cm.group(1)[0] == "`" and "`" in cm.group(2)):
            mark, rest = cm.groups()
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence) and not rest.strip():
                fence = None
            continue
        hm = re.match(r" {0,3}(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if fence is None and hm:
            out.append((len(hm.group(1)), hm.group(2), i))
    return out


def heading_key(title: str) -> str:
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title.replace("`", ""))
    return re.sub(r"\s+", " ", title).strip().rstrip(":.").lower()


# An install.packages() call whose arguments (one level of nested calls, such as
# repos = c(...)) name the fleet's r-universe.
RUNIVERSE_INSTALL_RE = re.compile(rf"install\.packages\((?:[^()]|\([^()]*\))*(?:\([^()]*)?{re.escape(OWNER)}\.r-universe\.dev")
# pkgdown's config locations, and the YAML 1.1 false values its yaml parser reads.
PKGDOWN_CONFIGS = ("_pkgdown.yml", "_pkgdown.yaml", "pkgdown/_pkgdown.yml", "pkgdown/_pkgdown.yaml", "inst/_pkgdown.yml")
LLM_DOCS_OFF_RE = re.compile(r"^llm-docs:\s*[\"']?(?:false|no|off|n)[\"']?\s*(?:#.*)?$", re.M | re.I)


def check_readme(pkg: str, source, state: State, report: Report) -> None:
    text = source.read("README.Rmd")
    if text is not None:
        headings = readme_headings(text)
        for level, title, _ in headings:
            if BANNED_HEADING_RE.fullmatch(heading_key(title)):
                report.gap("readme", f"heading {'#' * level} {title} is maintainer content")
        install = [(n, i) for n, (level, title, i) in enumerate(headings)
                   if level == 2 and heading_key(title) == "installation"]
        if not install:
            report.gap("readme", "no ## Installation section")
        else:
            n, start = install[0]
            end = next((i for level, _, i in headings[n + 1:] if level <= 2), None)
            section = "\n".join(text.splitlines()[start:end])
            if not RUNIVERSE_INSTALL_RE.search(section):
                report.gap("readme", "Installation has no r-universe install.packages() command")
            cran_command = re.search(rf"install\.packages\(\s*[\"']{pkg}[\"']\s*\)", section)
            if state.on_cran is None:
                report.skip("readme", "Installation: the CRAN command is not judged (CRAN status unknown)")
            elif state.on_cran and not cran_command:
                report.gap("readme", f'Installation has no install.packages("{pkg}") for CRAN')
            elif not state.on_cran and cran_command:
                report.gap("readme", f'Installation shows install.packages("{pkg}"), but not on CRAN')
    if source.read("llms.txt") is not None:
        report.gap("readme", "a hand-written root llms.txt; the pkgdown site builds it")
    for path in PKGDOWN_CONFIGS:
        config = source.read(path)
        if config and LLM_DOCS_OFF_RE.search(config):
            report.gap("readme", f"{path} sets llm-docs off")


# What r-universe and pkgdown look for, and the README header that shows it.
LOGO_FILES = ("man/figures/logo.svg", "man/figures/logo.png")


def tag_attrs(tag: str) -> dict[str, str | None]:
    """One HTML start tag's attributes as a browser reads them: names lower-cased,
    entities decoded, spaces around `=` allowed, and the first of a repeated
    attribute kept."""
    found: dict[str, str | None] = {}

    class Reader(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for name, value in attrs:
                found.setdefault(name, value)

    Reader(convert_charrefs=True).feed(tag)
    return found


def check_logo(pkg: str, source, report: Report) -> None:
    tree = source.tree()
    for path in LOGO_FILES:
        if path not in tree:
            report.gap("logo", f"missing {path}")
    text = source.read("README.Rmd")
    if text is None:
        return
    title = next((title for level, title, _ in readme_headings(text) if level == 1), None)
    # The bare <img> only: inside a link (usethis::use_logo()) an empty alt would
    # leave the link without a name. Its attributes are read as a browser reads
    # them (tag_attrs), not by pattern.
    m = title and re.fullmatch(rf"{re.escape(pkg)}\s+(<img\s[^>]*>)", title)
    attrs = tag_attrs(m.group(1)) if m else {}
    if attrs.get("src") != "man/figures/logo.png":
        report.gap("logo", f'README.Rmd: the first heading is not "# {pkg}" with the man/figures/logo.png <img>')
    elif "alt" not in attrs or attrs["alt"]:  # a bare `alt` is empty to a browser (None here)
        found = "no alt" if "alt" not in attrs else f"alt={attrs['alt']!r}"
        report.gap("logo", f'README.Rmd: the logo <img> lacks an empty alt="" ({found})')
    else:
        # Each of these names the image again, so it is no longer decorative (WCAG H67).
        naming = [name for name in ("title", "aria-label", "aria-labelledby") if name in attrs]
        if attrs.get("role") not in (None, "presentation", "none"):
            naming.append("role")
        if naming:
            report.gap("logo", f"README.Rmd: the logo <img> has an empty alt but is named by {', '.join(naming)}")


def check_files(source, report: Report) -> None:
    tree = source.tree()
    for path in REQUIRED_FILES:
        if path not in tree:
            report.gap("files", f"missing {path}")
    for directory in REQUIRED_DIRS:
        if not any(p.startswith(directory + "/") for p in tree):
            report.gap("files", f"missing {directory}/ (no template in it)")
    license_text = source.read("LICENSE")
    if license_text is not None and not re.search(r"COPYRIGHT HOLDER:\s*Bart Turczynski\s*$", license_text, re.M):
        report.gap("files", "LICENSE: copyright holder is not Bart Turczynski")
    license_md = source.read("LICENSE.md")
    if license_md is not None and "Permission is hereby granted" not in license_md:
        report.gap("files", "LICENSE.md is not the full MIT text")
    security = source.read("SECURITY.md")
    if security is not None:
        if CONTACT not in security:
            report.gap("files", f"SECURITY.md does not name {CONTACT}")
        if len([line for line in security.splitlines() if line.strip()]) < SECURITY_STUB_LINES:
            report.gap("files", "SECURITY.md is a stub (no real process)")
    conduct = source.read("CODE_OF_CONDUCT.md")
    if conduct is not None and CONTACT not in conduct:
        report.gap("files", f"CODE_OF_CONDUCT.md does not name {CONTACT} as the contact")


def person_calls(text: str) -> list[str]:
    out = []
    for m in re.finditer(r"\bperson\s*\(", text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            if depth == 0:
                out.append(text[m.start():i + 1])
                break
            i += 1
    return out


def check_description(pkg: str, source, state: State, report: Report) -> str | None:
    """DESCRIPTION checks. Returns the declared R floor as a minor version."""
    text = source.read("DESCRIPTION")
    if text is None:
        report.gap("description", "no DESCRIPTION")
        return None
    fields = read_dcf(text)
    bart = [p for p in person_calls(fields.get("Authors@R", "")) if "Turczynski" in p]
    if not bart:
        report.gap("description", "Authors@R has no Bart Turczynski person")
    else:
        person = bart[0]
        rm = re.search(r"role\s*=\s*(c\([^)]*\)|\"[^\"]*\")", person)
        roles = set(re.findall(r"\"(\w+)\"", rm.group(1))) if rm else set()
        missing = [r for r in ("aut", "cre", "cph") if r not in roles]
        if missing:
            report.gap("description", f"Bart Turczynski lacks role(s) {', '.join(missing)}")
        if not re.search(rf"ORCID\s*=\s*\"{ORCID}\"", person):
            report.gap("description", f"Bart Turczynski has no ORCID {ORCID} comment")
        if CONTACT not in person:
            report.gap("description", f"maintainer email is not {CONTACT}")
    expected = [f"https://{OWNER}.gitlab.io/{pkg}", f"https://gitlab.com/{OWNER}/{pkg}",
                f"https://{OWNER}.r-universe.dev/{pkg}"]
    if state.on_cran:
        expected.append(f"https://CRAN.R-project.org/package={pkg}")
    urls = [u.rstrip("/") for u in re.split(r"[,\s]+", fields.get("URL", "")) if u]
    if state.on_cran is None:
        report.skip("description", "URL: the CRAN entry is not judged (CRAN status unknown)")
        urls = [u for u in urls if "CRAN.R-project.org" not in u]
    if urls != expected:
        report.gap("description", f"URL is {', '.join(urls) or '(empty)'}; the standard's is {', '.join(expected)}")
    keywords = [k.strip() for k in fields.get("X-schema.org-keywords", "").split(",") if k.strip()]
    if not keywords:
        report.gap("description", "no X-schema.org-keywords (r-universe's only keyword source)")
    else:
        dropped = [k for k in keywords if k.lower() in DROPPED_KEYWORDS]
        if dropped:
            report.gap("description", f"X-schema.org-keywords lists {', '.join(dropped)}, which r-universe drops")
        usable = len({k.lower() for k in keywords} - DROPPED_KEYWORDS)
        if usable < MIN_KEYWORDS:
            report.gap("description", f"X-schema.org-keywords has {usable} distinct usable "
                                      f"token(s); the standard wants at least {MIN_KEYWORDS}")
    if fields.get("Language") != "en-US":
        report.gap("description", f"Language is {fields.get('Language')!r}, not en-US")
    fm = re.search(r"\bR\s*\(\s*>=\s*([\d.]+)\s*\)", fields.get("Depends", ""))
    if not fm:
        report.gap("description", "Depends declares no R floor")
        return None
    return minor(fm.group(1))


def check_ci(pkg: str, source, state: State, floor: str | None, report: Report) -> None:
    text = source.read(".gitlab-ci.yml")
    if text is None:
        report.gap("ci", "no .gitlab-ci.yml")
        return
    ci = CI(text, source)
    if not ci.admitted("push"):
        report.gap("ci", "workflow: rules admit no push to main")
    on_push = [j for j in ci.jobs.values() if j.runs["push"]]

    checks = [j for j in on_push if CHECK_RE.search(j.full_text())]
    if not checks:
        report.gap("ci", "no R CMD check runs on a push to main")
    else:
        if not any(AS_CRAN_RE.search(j.full_text()) for j in checks):
            report.gap("ci", f"R CMD check on push ({', '.join(j.name for j in checks)}) does not use --as-cran")
        if not any(ERROR_ON_RE.search(j.full_text()) for j in checks):
            report.gap("ci", "R CMD check on push is not rcmdcheck with error_on = \"warning\"")
    for job in ci.jobs.values():
        body = job.full_text()
        if pkg != "seor" and INCOMING_OFF_RE.search(body):
            report.gap("ci", f"{job.name}: turns CRAN incoming off (only seor may, ADR 0004)")
        if pkg not in ("seor", "pslr") and INCOMING_REMOTE_OFF_RE.search(body):
            report.gap("ci", f"{job.name}: turns remote CRAN incoming off (only pslr is grandfathered, ADR 0004)")

    coverage = [j for j in on_push if j.attrs.get("coverage", ("", []))[0]]
    if not coverage:
        report.gap("ci", "no coverage job with a coverage: regex runs on a push to main")
    for job in coverage:
        body = job.full_text()
        if not re.search(r"coverage_format:\s*cobertura", body):
            report.gap("ci", f"{job.name}: no cobertura coverage_report artifact")
        if job.attrs.get("allow_failure", ("", []))[0] == "true":
            report.gap("ci", f"{job.name}: allow_failure: true, so coverage cannot fail the pipeline")
        thresholds = coverage_thresholds(body)
        if not thresholds:
            report.gap("ci", f"{job.name}: no {COVERAGE_MIN:g}% coverage threshold")
        elif min(thresholds) < COVERAGE_MIN:
            report.gap("ci", f"{job.name}: coverage threshold {min(thresholds):g} is below {COVERAGE_MIN:g}")
    # The coverage badge reads the latest successful pipeline on main, schedules included.
    if coverage:
        for kind in SCHEDULE_KINDS:
            if not any(j.runs[kind] for j in coverage):
                report.gap("ci", f"coverage job does not run on the {kind} schedule")

    if not any(j.name == "pages" or j.attrs.get("pages", ("", []))[0] == "true" for j in on_push):
        report.gap("ci", "pages does not deploy on a push to main")

    check_pandoc_pin(on_push, ci, report)

    chunks = [chunk for j in on_push for chunk in j.chunks()]
    for gate, patterns in GATES.items():
        if not any(all(p.search(chunk) for p in patterns) for chunk in chunks):
            report.gap("ci", f"no {gate} gate runs on a push to main")

    legs = [j for j in ci.jobs.values()
            if j.runs["deep-check"] and not j.runs["push"] and not j.runs["dependency-audit"]]
    roles: set[str] = set()
    for job in legs:
        if CHECK_RE.search(job.full_text()):
            for image in ci.images(job):
                if not SANITIZER_IMAGE_RE.search(image):
                    roles |= leg_roles(image, state, floor)
    if state.r_release is None:
        report.skip("ci", "current R release/oldrel unknown; numeric deep-check legs judged for the floor only")
    for leg in ("release", "oldrel", "devel"):
        if leg not in roles:
            report.gap("ci", f"no deep-check leg for R {leg}")
    if floor and "floor" not in roles:
        report.gap("ci", f"no deep-check leg at the declared R floor ({floor})")
    if pkg in SANITIZER_PACKAGES:
        sanitized = [j for j in legs
                     if any(SANITIZER_IMAGE_RE.search(i) for i in ci.images(j))
                     or (re.search(r"fsanitize=address|\bASAN\b", j.full_text())
                         and re.search(r"fsanitize=[\w,]*undefined|\bUBSAN\b", j.full_text()))]
        if not sanitized:
            report.gap("ci", "no ASAN/UBSAN sanitizer leg on the deep-check schedule")

    for name in ("osv-audit", "security-audit"):
        job = ci.jobs.get(name)
        if job is None:
            report.gap("ci", f"no {name} job")
        elif not job.runs["dependency-audit"] or job.runs["push"] or job.runs["deep-check"]:
            report.gap("ci", f"{name} does not run only on the dependency-audit schedule")
    tree = source.tree()
    missing = [p for p in AUDIT_TEST_FILES if p not in tree]
    if missing:
        report.gap("ci", f"audit jobs lack seor's disposition-row shape: missing {', '.join(missing)}")

    if pkg in FOSSA_PACKAGES and not any(re.search(r"\bfossa analyze\b", j.full_text()) for j in ci.jobs.values()):
        report.gap("ci", "no fossa analyze job")


def check_local_gate(source, report: Report) -> None:
    text = source.read(".pre-commit-config.yaml")
    if text is None:
        report.gap("local gate", "no .pre-commit-config.yaml")
        return
    body = strip_comment_lines(text)
    # R and shell only: a Python script that merely names check_url_db (this
    # one, check-bugreports.py's docstring) runs no URL check.
    named = [(path, s) for path, s in inline_scripts(body, source, depth=3) if Path(path).suffix in ("", ".R", ".r", ".sh")]
    scripts = [s for _, s in named]
    if not any(URL_CHECK_RE.search(chunk) for chunk in [body] + scripts):
        report.gap("local gate", "no URL check in the pre-push gate")

    # One script both asks rmarkdown for its pandoc and reads the CI pin from
    # .gitlab-ci.yml: a pandoc_version() call alone may be an unrelated
    # minimum-version check, and PANDOC_VERSION is never set locally.
    def reads_ci_pin(path: str, chunk: str) -> bool:
        names_ci = PANDOC_CI_FILE_RE.search(chunk) or (
            Path(path).suffix not in (".R", ".r") and PANDOC_CI_FILE_WORD_RE.search(chunk))
        return bool(PANDOC_LOCAL_RE.search(chunk) and names_ci
                    and PANDOC_PIN_READ_RE.search(PANDOC_ENV_READ_RE.sub("", chunk)))

    if not any(reads_ci_pin(path, chunk) for path, chunk in [(".pre-commit-config.yaml", body)] + named):
        report.gap("local gate", "no check that compares the local rmarkdown::pandoc_version() with the CI pin "
                                 f"(PANDOC_VERSION, {PANDOC_PIN})")


def check_schedules(state: State, report: Report) -> None:
    if state.schedules is None:
        report.skip("schedules", "pipeline schedules not read")
        return
    kinds: dict[str, list[dict]] = {}
    for schedule in state.schedules:
        variables = {v.get("key"): v.get("value") for v in schedule.get("variables") or []}
        kind = variables.get("SCHEDULE_KIND")
        label = f"schedule {schedule.get('id')} ({schedule.get('description', '')})"
        if not kind:
            report.gap("schedules", f"{label} sets no SCHEDULE_KIND")
            continue
        if schedule.get("ref") not in ("main", "refs/heads/main"):
            report.gap("schedules", f"{label} targets {schedule.get('ref')}, not main")
        kinds.setdefault(kind, []).append(schedule)
    for kind in SCHEDULE_KINDS:
        found = kinds.get(kind, [])
        if not found:
            report.gap("schedules", f"no {kind} schedule")
        elif not any(s.get("active") for s in found):
            report.gap("schedules", f"the {kind} schedule is inactive")


def check_repo(pkg: str, source, state: State,
               fetch: Callable[[str], tuple[int, str, bytes]] | None = None) -> Report:
    report = Report(pkg)
    for area, error in state.errors:
        report.skip(area, f"probe failed: {error}")
    images = check_badges(pkg, source, state, report)
    if fetch is None:
        report.skip("badge images", "not fetched (--offline)")
    elif images:
        check_images(images, fetch, report)
    check_readme(pkg, source, state, report)
    check_logo(pkg, source, report)
    check_files(source, report)
    floor = check_description(pkg, source, state, report)
    check_ci(pkg, source, state, floor, report)
    check_local_gate(source, report)
    check_schedules(state, report)
    return report


def run_one(pkg: str, local: Path | None, offline: bool) -> Report:
    source = LocalSource(local) if local else GitLabSource(pkg)
    try:
        concept_doi = cff_doi(source.read("CITATION.cff"))
        state = State() if offline else probe_state(pkg, concept_doi)
        return check_repo(pkg, source, state, None if offline else http_get)
    except ProbeError as error:
        report = Report(pkg)
        report.skip("source", f"could not read the repository: {error}")
        return report


# --- self-test (offline) -------------------------------------------------------------


def fixture_badges(pkg: str, on_cran: bool, release: bool, doi: str | None) -> str:
    o = OWNER
    rows = {
        1: f"[![CRAN status](https://www.r-pkg.org/badges/version/{pkg})](https://CRAN.R-project.org/package={pkg})",
        2: f"[![CRAN downloads](https://cranlogs.r-pkg.org/badges/{pkg})](https://CRAN.R-project.org/package={pkg})",
        3: f"[![CRAN checks](https://badges.cranchecks.info/worst/{pkg}.svg)]"
           f"(https://cran.r-project.org/web/checks/check_results_{pkg}.html)",
        4: f"[![r-universe](https://{o}.r-universe.dev/{pkg}/badges/version)](https://{o}.r-universe.dev/{pkg})",
        5: f"[![Pipeline](https://gitlab.com/{o}/{pkg}/badges/main/pipeline.svg)](https://gitlab.com/{o}/{pkg}/-/pipelines)",
        6: f"[![Coverage](https://gitlab.com/{o}/{pkg}/badges/main/coverage.svg)](https://gitlab.com/{o}/{pkg}/-/pipelines)",
        7: f"[![Docs](https://img.shields.io/website?url=https%3A%2F%2F{o}.gitlab.io%2F{pkg}%2F&label=docs&logo=gitlab"
           f"&logoColor=white&up_message=pkgdown&up_color=1f75cb)](https://{o}.gitlab.io/{pkg}/)",
        8: f"[![Latest release](https://img.shields.io/gitlab/v/release/{o}%2F{pkg})](https://gitlab.com/{o}/{pkg}/-/releases)",
        9: "[![Lifecycle: stable](https://img.shields.io/badge/lifecycle-stable-brightgreen.svg)]"
           "(https://lifecycle.r-lib.org/articles/stages.html#stable)",
        10: "[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)",
        11: f"[![DOI](https://zenodo.org/badge/DOI/{doi}.svg)](https://doi.org/{doi})",
        12: "[![Zenodo](https://img.shields.io/badge/Zenodo-all_software-1682D4?logo=zenodo&logoColor=white)]"
            f"(https://zenodo.org/search?q=metadata.creators.person_or_org.identifiers.identifier:{ORCID})",
        13: "[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/12345/badge)]"
            "(https://www.bestpractices.dev/projects/12345)",
        14: f"[![License](https://img.shields.io/gitlab/license/{o}%2F{pkg})](https://gitlab.com/{o}/{pkg}/-/blob/main/LICENSE.md)",
        15: f"[![Dependencies](https://tinyverse.netlify.app/badge/{pkg})](https://CRAN.R-project.org/package={pkg})",
        16: f"[![Last commit](https://img.shields.io/gitlab/last-commit/{o}%2F{pkg})](https://gitlab.com/{o}/{pkg}/-/commits/main)",
    }
    order = ([1, 2, 3, 4] if on_cran else [4]) + [5, 6, 7] + ([8] if release else []) + [9, 10]
    order += ([11] if doi else []) + [12, 13, 14] + ([15] if on_cran else []) + [16]
    return "\n".join(rows[n] for n in order)


FIXTURE_CI = """\
stages: [check, deploy, audit]
default:
  image: rocker/r-ver:4.6.1
variables:
  P3M_SNAPSHOT: "2026-09-01"
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: never
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "web"
    - when: never
.r:
  before_script:
    - PANDOC_VERSION=3.10
    - curl -fsSL --retry 3 --max-time 300 -o /tmp/pandoc.deb "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-amd64.deb"
    - echo "d502599878eb29af3ae5f0cb5d559134df96534125d452c7a0674a5bad2c5ecf  /tmp/pandoc.deb" | sha256sum -c -
    - dpkg -i /tmp/pandoc.deb
.on-main:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "web"
.deep:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule" && $SCHEDULE_KIND == "deep-check"
    - if: $CI_PIPELINE_SOURCE == "schedule"
      when: never
    - if: $CI_PIPELINE_SOURCE == "web"
      when: manual
.audit:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule" && $SCHEDULE_KIND =~ /^dependency-audit$/'
    - when: never
.deps: &deps
  - Rscript -e 'pak::local_install_deps(dependencies = TRUE)'
gates:
  extends: [.r, .on-main]
  script:
    - *deps
    - Rscript tools/gates.R
check:
  extends: [.r, .on-main]
  script:
    - *deps
    - Rscript -e 'res <- rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning")'
coverage:
  extends: [.r, .on-main]
  script:
    - Rscript -e 'cov <- covr::package_coverage(); covr::to_cobertura(cov); pct <- covr::percent_coverage(cov); cat(sprintf("Coverage: %.2f%%\\n", pct)); if (pct < 95) quit(status = 1)'
  coverage: '/Coverage: (\\d+\\.\\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: cobertura.xml
"check:deep":
  extends: .deep
  image: rocker/r-ver:$R_VERSION
  parallel:
    matrix:
      - R_VERSION: ["4.6.1", "4.5.3", "devel", "4.1.3"]
  script:
    - Rscript -e 'rcmdcheck::rcmdcheck(args = "--as-cran", error_on = "warning")'
sanitizers:
  extends: .deep
  image: rocker/r-devel-san
  script:
    - RD CMD check --as-cran fixture.tar.gz
fossa:
  extends: .on-main
  script:
    - fossa analyze
pages:
  extends: [.r, .on-main]
  script:
    - Rscript -e 'pkgdown::build_site()'
osv-audit:
  extends: .audit
  script:
    - Rscript -e 'testthat::test_local(filter = "osv")'
security-audit:
  extends: .audit
  script:
    - Rscript -e 'testthat::test_local(filter = "security")'
"""

FIXTURE_GATES_R = """\
# Gates the CI runs.
stages = list(
  lint = list(default = TRUE, run = function() lintr::lint_package()),
  spelling = list(default = TRUE, run = function() spelling::spell_check_package()),
  readme = list(default = TRUE, run = function() devtools::build_readme()),
  news = list(default = TRUE, run = function() {
    h <- readLines("NEWS.md")[1]
    stopifnot(grepl("(development version)", h, fixed = TRUE))
  }),
  citation = list(default = TRUE, run = function() system("python3 scripts/check-citation.py")),
  coverage = list(default = FALSE, run = function() covr::package_coverage())
)
"""

def fixture_h1(pkg: str) -> str:
    return f'# {pkg} <img src="man/figures/logo.png" align="right" height="139" alt="" />'


def fixture_readme_body(pkg: str, on_cran: bool) -> str:
    cran = f'install.packages("{pkg}")\n\n' if on_cran else ""
    return (f"\n{pkg} does one thing well.\n\n## Installation\n\n```r\n{cran}"
            f'install.packages(\n  "{pkg}",\n  repos = c("https://{OWNER}.r-universe.dev", "https://cloud.r-project.org")\n)\n```\n\n'
            "Building from source needs a C++17 toolchain.\n\n## Usage\n\n"
            "```{r}\n# Development\nx <- 1\n```\n\n~~~\n## Setup\n~~~\n\n## Learn more\n\nSee the vignettes.\n")


FIXTURE_PRECOMMIT = """\
repos:
  - repo: local
    hooks:
      - id: check-toolchain
        entry: Rscript scripts/check-toolchain.R
        language: system
        stages: [pre-push]
      - id: verify
        entry: Rscript tools/verify.R
        language: system
        stages: [pre-push]
"""

FIXTURE_TOOLCHAIN_R = """\
# The pin is read from the CI file; a toolchain check compares the local pandoc to it.
ci <- readLines(file.path(root, ".gitlab-ci.yml"))
pin <- read_pin(ci, "PANDOC_VERSION")
if (!identical(as.character(rmarkdown::pandoc_version()), pin)) quit(status = 1)
"""


def fixture_repo(pkg: str, on_cran: bool = True, release: bool = True, doi: str | None = "10.5281/zenodo.111") -> dict:
    urls = [f"https://{OWNER}.gitlab.io/{pkg}/", f"https://gitlab.com/{OWNER}/{pkg}",
            f"https://{OWNER}.r-universe.dev/{pkg}"] + ([f"https://CRAN.R-project.org/package={pkg}"] if on_cran else [])
    files = {path: "x\n" for path in REQUIRED_FILES}
    files.update({
        "README.Rmd": fixture_h1(pkg) + "\n\n<!-- badges: start -->\n<!-- a comment is ignored -->\n"
                      + fixture_badges(pkg, on_cran, release, doi) + "\n<!-- badges: end -->\n"
                      + fixture_readme_body(pkg, on_cran),
        "DESCRIPTION": f"Package: {pkg}\nVersion: 1.0.0\n"
                       f"Authors@R:\n    person(\"Bart\", \"Turczynski\", , \"{CONTACT}\", role = c(\"aut\", \"cre\", \"cph\"),\n"
                       f"           comment = c(ORCID = \"{ORCID}\"))\n"
                       f"Depends: R (>= 4.1.0)\nURL: {', '.join(urls)}\nLanguage: en-US\n"
                       "X-schema.org-keywords: punycode, idna, idn, unicode,\n    domain-names\n",
        "_pkgdown.yml": "url: https://example.org/\ntemplate:\n  bootstrap: 5\n",
        "LICENSE": "YEAR: 2026\nCOPYRIGHT HOLDER: Bart Turczynski\n",
        "LICENSE.md": "MIT License\n\nPermission is hereby granted, free of charge\n",
        "SECURITY.md": "".join(f"line {i} {CONTACT}\n" for i in range(12)),
        "CODE_OF_CONDUCT.md": f"Contact {CONTACT}.\n",
        "CITATION.cff": f"cff-version: 1.2.0\ndoi: {doi}\n" if doi else "cff-version: 1.2.0\n",
        ".gitlab-ci.yml": FIXTURE_CI,
        "tools/gates.R": FIXTURE_GATES_R,
        ".pre-commit-config.yaml": FIXTURE_PRECOMMIT,
        "tools/verify.R": "db <- tools:::url_db_from_package_sources('.')\nbad <- tools:::check_url_db(db)\n",
        "scripts/check-toolchain.R": FIXTURE_TOOLCHAIN_R,
        "scripts/check-citation.py": "print('ok')\n",
        ".gitlab/issue_templates/Bug.md": "x\n",
        ".gitlab/merge_request_templates/Default.md": "x\n",
    })
    files.update({path: "x\n" for path in LOGO_FILES})
    files.update({path: "x\n" for path in AUDIT_TEST_FILES})
    return files


def fixture_state(on_cran: bool = True, release: bool = True, doi: bool = True, fossa: bool = True) -> State:
    return State(
        on_cran=on_cran, on_runiverse=True, doi_resolves=True if doi else None, doi_is_concept=True if doi else None,
        has_release=release, fossa_project=fossa, r_release="4.6", r_oldrel="4.5",
        schedules=[
            {"id": 1, "description": "deep", "ref": "refs/heads/main", "active": True,
             "variables": [{"key": "SCHEDULE_KIND", "value": "deep-check"}]},
            {"id": 2, "description": "audit", "ref": "main", "active": True,
             "variables": [{"key": "SCHEDULE_KIND", "value": "dependency-audit"}]},
        ],
    )


def self_test() -> list[str]:
    """The fixtures, run twice: the first pass only collects their
    .gitlab-ci.yml texts, so check-toolchain.R reads every pin in one Rscript
    run rather than one per fixture (SEOR-xhyrogfm); the second judges them."""
    texts: list[str] = []
    self_test_cases(texts)
    try:
        read_pandoc_assignments(texts)
    except ProbeError as error:
        return [f"the pandoc pin reader did not run: {error}"]
    return self_test_cases(None)


def self_test_cases(collect: list[str] | None) -> list[str]:
    failures: list[str] = []

    def run(pkg: str, files: dict, state: State, fetch=None) -> Report:
        if collect is not None:
            collect.append(files.get(".gitlab-ci.yml", ""))
            return Report(pkg)
        return check_repo(pkg, DictSource(files), state, fetch)

    def expect_clean(tag: str, pkg: str, files: dict, state: State, fetch=None) -> None:
        report = run(pkg, files, state, fetch)
        if report.gaps:
            failures.append(f"{tag}: expected no gaps, got {report.gaps}")

    def expect_gap(tag: str, needle: str, pkg: str, files: dict, state: State, fetch=None) -> Report:
        report = run(pkg, files, state, fetch)
        if not any(needle in text for _, text in report.gaps):
            failures.append(f"{tag}: expected a gap containing {needle!r}, got {report.gaps}")
        return report

    def edit(files: dict, path: str, old: str, new: str) -> dict:
        if old not in files[path]:
            raise SystemExit(f"self-test fixture edit not applicable: {old!r} in {path}")
        return dict(files, **{path: files[path].replace(old, new)})

    # Rules evaluator.
    env = {"CI_PIPELINE_SOURCE": "schedule", "SCHEDULE_KIND": "deep-check", "CI_COMMIT_BRANCH": "main",
           "CI_DEFAULT_BRANCH": "main"}
    for expr, want in (
        ('$CI_PIPELINE_SOURCE == "schedule" && $SCHEDULE_KIND == "deep-check"', True),
        ('$CI_PIPELINE_SOURCE == "schedule" && $SCHEDULE_KIND == "dependency-audit"', False),
        ("$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH", True),
        ("$CI_COMMIT_TAG", False),
        ("$CI_COMMIT_TAG == null", True),
        ('$CI_PIPELINE_SOURCE =~ /^(web|api|schedule)$/', True),
        ('$CI_PIPELINE_SOURCE !~ /^sched/', False),
        ('($CRAN_PREP == "1" || $SCHEDULE_KIND == "deep-check") && $CI_PIPELINE_SOURCE != "push"', True),
    ):
        if evaluate(expr, env) is not want:
            failures.append(f"evaluate({expr!r}) should be {want}")

    # Opt-in stages drop out; default ones stay.
    dropped = drop_opt_in_stages(FIXTURE_GATES_R)
    if "package_coverage" in dropped or "lint_package" not in dropped:
        failures.append("drop_opt_in_stages: kept an opt-in stage or dropped a default one")

    # POSITIVE: a conforming package on CRAN with a Release and a DOI.
    cran = fixture_repo("punycoder")
    expect_clean("conforming, on CRAN", "punycoder", cran, fixture_state())

    # POSITIVE: a conforming FOSSA package off CRAN, no Release, no DOI, no FOSSA project yet.
    seor = fixture_repo("seor", on_cran=False, release=False, doi=None)
    expect_clean("conforming, off CRAN", "seor", seor, fixture_state(on_cran=False, release=False, doi=False, fossa=False))

    # NEGATIVE: badges.
    expect_gap("badge dropped", "missing slot 5: GitLab pipeline", "punycoder",
               edit(cran, "README.Rmd", fixture_badges("punycoder", True, True, "10.5281/zenodo.111").splitlines()[4] + "\n", ""),
               fixture_state())
    rows = fixture_badges("punycoder", True, True, "10.5281/zenodo.111").splitlines()
    swapped = rows[:]
    swapped[4], swapped[5] = swapped[5], swapped[4]
    expect_gap("badge order", "order: shown", "punycoder",
               edit(cran, "README.Rmd", "\n".join(rows), "\n".join(swapped)), fixture_state())
    expect_gap("CRAN badge off CRAN", "slot 1 CRAN version shown, but not on CRAN", "seor",
               edit(seor, "README.Rmd", "<!-- badges: end -->",
                    "[![CRAN status](https://www.r-pkg.org/badges/version/seor)](https://CRAN.R-project.org/package=seor)\n"
                    "<!-- badges: end -->"),
               fixture_state(on_cran=False, release=False, doi=False, fossa=False))
    expect_gap("release badge required", "missing slot 8: latest release", "seor", seor,
               fixture_state(on_cran=False, release=True, doi=False, fossa=False))
    expect_gap("FOSSA badges once the project exists", "missing slot 17: FOSSA license", "seor", seor,
               fixture_state(on_cran=False, release=False, doi=False, fossa=True))
    # FOSSA locator, pinned as literals: rurl's first upload (job 16914055629, 2026-10-03) landed under
    # custom+62973/git+gitlab.com/...; its badge answered 200, the bare git+gitlab.com form 404.
    fossa_new = (
        "[![FOSSA license](https://app.fossa.com/api/projects/custom%2B62973%2Fgit%2Bgitlab.com%2Fbart-turczynski"
        "%2Fseor.svg?type=shield&issueType=license)](https://app.fossa.com/projects/custom%2B62973%2Fgit%2Bgitlab.com"
        "%2Fbart-turczynski%2Fseor?ref=badge_shield&issueType=license)\n"
        "[![FOSSA security](https://app.fossa.com/api/projects/custom%2B62973%2Fgit%2Bgitlab.com%2Fbart-turczynski"
        "%2Fseor.svg?type=shield&issueType=security)](https://app.fossa.com/projects/custom%2B62973%2Fgit%2Bgitlab.com"
        "%2Fbart-turczynski%2Fseor?ref=badge_shield&issueType=security)\n")
    fossa_old = fossa_new.replace("custom%2B62973%2F", "")
    expect_clean("FOSSA pair under the custom locator", "seor",
                 edit(seor, "README.Rmd", "<!-- badges: end -->", fossa_new + "<!-- badges: end -->"),
                 fixture_state(on_cran=False, release=False, doi=False, fossa=True))
    old_report = expect_gap("FOSSA pair under the bare git+gitlab.com locator", "slot 17 FOSSA license: image URL differs",
                            "seor", edit(seor, "README.Rmd", "<!-- badges: end -->", fossa_old + "<!-- badges: end -->"),
                            fixture_state(on_cran=False, release=False, doi=False, fossa=True))
    for needle in ("slot 17 FOSSA license: link differs", "slot 18 FOSSA security: image URL differs",
                   "slot 18 FOSSA security: link differs"):
        if not any(needle in text for _, text in old_report.gaps):
            failures.append(f"FOSSA bare locator: expected a gap containing {needle!r}, got {old_report.gaps}")
    if fossa_image("rurl", "license") != ("https://app.fossa.com/api/projects/custom%2B62973%2Fgit%2Bgitlab.com"
                                          "%2Fbart-turczynski%2Frurl.svg?type=shield&issueType=license"):
        failures.append(f"FOSSA probe URL is not the measured 200 form: {fossa_image('rurl', 'license')}")
    expect_gap("lifecycle stage outside the set", "slot 9 lifecycle: image URL differs", "punycoder",
               edit(cran, "README.Rmd", "lifecycle-stable-brightgreen", "lifecycle-maturing-blue"), fixture_state())
    expect_gap("static docs badge", "slot 7 docs: image URL differs", "punycoder",
               edit(cran, "README.Rmd", "https://img.shields.io/website?url=https%3A%2F%2Fbart-turczynski.gitlab.io%2Fpunycoder"
                    "%2F&label=docs&logo=gitlab&logoColor=white&up_message=pkgdown&up_color=1f75cb",
                    "https://img.shields.io/badge/docs-pkgdown-blue.svg"), fixture_state())
    expect_gap("FOSSA on a GitHub locator, outside the allocation", "FOSSA badge on a package outside", "punycoder",
               edit(cran, "README.Rmd", "<!-- badges: end -->",
                    "[![FOSSA](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fx%2Fpunycoder.svg?type=shield"
                    "&issueType=license)](https://app.fossa.com/projects/x)\n<!-- badges: end -->"), fixture_state())
    expect_gap("version DOI", "is a version DOI", "punycoder", cran, State(**{**fixture_state().__dict__, "doi_is_concept": False}))
    expect_gap("not on r-universe", "not on r-universe", "punycoder", cran,
               State(**{**fixture_state().__dict__, "on_runiverse": False}))

    # Badge images: a bad render is a gap; a network error is not.
    def fetch_bad(url: str):
        if "coverage" in url:
            return 200, "image/svg+xml", b'<svg aria-label="coverage: unknown"><text>coverage</text><text>unknown</text></svg>'
        if "cranchecks" in url:
            return 200, "text/html", b"<html>not a badge</html>"
        if "tinyverse" in url:
            raise ProbeError("timed out")
        if "r-pkg.org/badges/version" in url:
            return 500, "text/plain", b""
        return 200, "image/svg+xml", b"<svg><text>ok</text></svg>"

    report = expect_gap("image renders unknown", "renders 'unknown'", "punycoder", cran, fixture_state(), fetch_bad)
    if not any("HTTP 500" in t for _, t in report.gaps) or not any("not an image" in t for _, t in report.gaps):
        failures.append(f"image checks: expected HTTP 500 and not-an-image gaps, got {report.gaps}")
    if any("tinyverse" in t for _, t in report.gaps) or not any("tinyverse" in t for _, t in report.unjudged):
        failures.append("image checks: a network error must be not judged, never a gap")

    # NEGATIVE: files, DESCRIPTION.
    no_arch = dict(cran)
    del no_arch["ARCHITECTURE.md"]
    expect_gap("missing file", "missing ARCHITECTURE.md", "punycoder", no_arch, fixture_state())
    no_tpl = {k: v for k, v in cran.items() if not k.startswith(".gitlab/issue_templates/")}
    expect_gap("missing templates", "missing .gitlab/issue_templates/", "punycoder", no_tpl, fixture_state())
    expect_gap("LICENSE holder", "copyright holder is not Bart", "punycoder",
               edit(cran, "LICENSE", "Bart Turczynski", "punycoder authors"), fixture_state())
    expect_gap("SECURITY stub", "SECURITY.md is a stub", "punycoder", dict(cran, **{"SECURITY.md": f"{CONTACT}\n"}),
               fixture_state())
    expect_gap("cph role", "lacks role(s) cph", "punycoder",
               edit(cran, "DESCRIPTION", '"aut", "cre", "cph"', '"aut", "cre"'), fixture_state())
    expect_gap("URL order", "URL is", "punycoder",
               edit(cran, "DESCRIPTION", "URL: https://bart-turczynski.gitlab.io/punycoder/, https://gitlab.com/bart-turczynski/punycoder",
                    "URL: https://gitlab.com/bart-turczynski/punycoder, https://bart-turczynski.gitlab.io/punycoder/"),
               fixture_state())

    # NEGATIVE: README contents and keywords.
    expect_gap("no Installation", "no ## Installation section", "punycoder",
               edit(cran, "README.Rmd", "## Installation", "## Getting it"), fixture_state())
    expect_gap("Installation at level 3 only", "no ## Installation section", "punycoder",
               edit(cran, "README.Rmd", "## Installation", "### Installation"), fixture_state())
    expect_gap("Setup heading", "heading ## Setup (development) is maintainer content", "punycoder",
               edit(cran, "README.Rmd", "## Learn more", "## Setup (development)"), fixture_state())
    expect_gap("Project layout at level 3", "heading ### Project layout is maintainer content", "punycoder",
               edit(cran, "README.Rmd", "See the vignettes.\n", "See the vignettes.\n\n### Project layout\n"),
               fixture_state())
    expect_gap("function index", "heading ## Function Overview is maintainer content", "punycoder",
               edit(cran, "README.Rmd", "## Learn more", "## Function Overview"), fixture_state())
    report = run("punycoder", edit(cran, "README.Rmd", "## Learn more", "## Development version"), fixture_state())
    if report.gaps:
        failures.append(f"a heading that only starts with a banned word is not banned, got {report.gaps}")
    expect_gap("no r-universe command", "no r-universe install.packages()", "punycoder",
               edit(cran, "README.Rmd", f'repos = c("https://{OWNER}.r-universe.dev", ', "repos = c("), fixture_state())
    report = expect_gap("on CRAN, no CRAN command", 'no install.packages("punycoder") for CRAN', "punycoder",
                        edit(cran, "README.Rmd", 'install.packages("punycoder")\n\n', ""), fixture_state())
    if any("r-universe" in t for _, t in report.gaps):
        failures.append(f"on CRAN, no CRAN command: the r-universe command was there, got {report.gaps}")
    unknown_cran = run("punycoder", edit(cran, "README.Rmd", 'install.packages("punycoder")\n\n', ""),
                       State(**{**fixture_state().__dict__, "on_cran": None}))
    if any("for CRAN" in t for _, t in unknown_cran.gaps) or not any("CRAN command" in t for _, t in unknown_cran.unjudged):
        failures.append("Installation: unknown CRAN status must be not judged, never a gap")
    expect_gap("root llms.txt", "hand-written root llms.txt", "punycoder", dict(cran, **{"llms.txt": "# x\n"}),
               fixture_state())
    expect_gap("llm-docs off", "_pkgdown.yaml sets llm-docs off", "punycoder",
               dict(cran, **{"_pkgdown.yaml": "url: https://example.org/\nllm-docs: off\n"}), fixture_state())
    expect_gap("duplicate keywords", "has 3 distinct usable token(s)", "punycoder",
               edit(cran, "DESCRIPTION", "unicode,\n    domain-names\n", "IDNA, Punycode\n"), fixture_state())
    expect_gap("r-universe only in prose", "no r-universe install.packages()", "punycoder",
               edit(cran, "README.Rmd", f'repos = c("https://{OWNER}.r-universe.dev", ',
                    f'repos = NULL)\n# see https://{OWNER}.r-universe.dev\nc('), fixture_state())
    expect_gap("CRAN command off CRAN", 'shows install.packages("seor"), but not on CRAN', "seor",
               edit(seor, "README.Rmd", "```r\n", '```r\ninstall.packages("seor")\n'),
               fixture_state(on_cran=False, release=False, doi=False, fossa=False))
    expect_gap("indented heading after inline triple backticks", "heading ## Verification is maintainer content",
               "punycoder", edit(cran, "README.Rmd", "See the vignettes.\n",
                                 "See ```x``` inline.\n\n   ## Verification\n"), fixture_state())
    hidden = edit(cran, "README.Rmd", fixture_h1("punycoder") + "\n",
                  "---\noutput: github_document\n# Setup: knit it\n---\n\n" + fixture_h1("punycoder") + "\n")
    hidden = edit(hidden, "README.Rmd", "See the vignettes.\n", "See the vignettes.\n\n<!--\n## Development\n-->\n")
    expect_clean("headings in front matter and comments do not render", "punycoder", hidden, fixture_state())
    expect_gap("no keywords", "no X-schema.org-keywords", "punycoder",
               edit(cran, "DESCRIPTION", "X-schema.org-keywords:", "X-keywords:"), fixture_state())
    report = expect_gap("dropped keywords", "lists r, rstats, which r-universe drops", "punycoder",
                        edit(cran, "DESCRIPTION", "domain-names\n", "domain-names, r, rstats\n"), fixture_state())
    if any("usable" in t for _, t in report.gaps):
        failures.append(f"dropped keywords: five usable tokens remain, got {report.gaps}")
    expect_gap("too few keywords", "has 4 distinct usable token(s)", "punycoder",
               edit(cran, "DESCRIPTION", "unicode,\n    domain-names\n", "unicode, R-package\n"), fixture_state())

    # NEGATIVE: logo.
    no_png = dict(cran)
    del no_png["man/figures/logo.png"]
    expect_gap("no logo.png", "missing man/figures/logo.png", "punycoder", no_png, fixture_state())
    plain_h1 = edit(cran, "README.Rmd", fixture_h1("punycoder"), "# punycoder")
    expect_gap("heading without the logo", "the first heading is not", "punycoder", plain_h1, fixture_state())
    expect_gap("logo from another path", "the first heading is not", "punycoder",
               edit(cran, "README.Rmd", 'src="man/figures/logo.png"', 'src="logo.png"'), fixture_state())
    expect_gap("logo under another package's name", "the first heading is not", "punycoder",
               edit(cran, "README.Rmd", "# punycoder <img", "# fixture <img"), fixture_state())
    expect_gap("logo path only in data-src", "the first heading is not", "punycoder",
               edit(cran, "README.Rmd", 'src="man/figures/logo.png"', 'src="logo.png" data-src="man/figures/logo.png"'),
               fixture_state())
    no_svg = dict(cran)
    del no_svg["man/figures/logo.svg"]
    expect_gap("no logo.svg", "missing man/figures/logo.svg", "punycoder", no_svg, fixture_state())
    expect_gap("no level-1 heading", "the first heading is not", "punycoder",
               edit(cran, "README.Rmd", fixture_h1("punycoder") + "\n", ""), fixture_state())
    expect_clean("single-quoted logo src", "punycoder",
                 edit(cran, "README.Rmd", 'src="man/figures/logo.png"', "src='man/figures/logo.png'"), fixture_state())
    expect_gap("the use_logo() link-wrapped heading", "the first heading is not", "punycoder",
               edit(cran, "README.Rmd", fixture_h1("punycoder"),
                    '# punycoder <a href="https://bart-turczynski.gitlab.io/punycoder/"><img src="man/figures/logo.png" '
                    'align="right" height="138" alt="" /></a>'), fixture_state())
    alt = ' alt=""'
    expect_gap("logo without alt", 'lacks an empty alt=""', "punycoder",
               edit(cran, "README.Rmd", alt, ""), fixture_state())
    expect_gap("logo with descriptive alt text", "lacks an empty alt=", "punycoder",
               edit(cran, "README.Rmd", alt, ' alt="punycoder hex logo, white on black"'), fixture_state())
    expect_gap("empty alt only in data-alt", "lacks an empty alt=", "punycoder",
               edit(cran, "README.Rmd", alt, ' data-alt=""'), fixture_state())
    expect_gap("an empty alt only inside another attribute", "lacks an empty alt=", "punycoder",
               edit(cran, "README.Rmd", alt, " title='x" + alt + "'"), fixture_state())
    expect_gap("a whitespace alt, entity-encoded", "(alt=' ')", "punycoder",
               edit(cran, "README.Rmd", alt, ' alt="&#32;"'), fixture_state())
    for naming in (' title="punycoder logo"', ' aria-label="punycoder"', ' role="img"'):
        expect_gap(f"an empty alt with {naming.strip()}", "but is named by", "punycoder",
                   edit(cran, "README.Rmd", alt, alt + naming), fixture_state())
    expect_clean("an empty alt with role=presentation", "punycoder",
                 edit(cran, "README.Rmd", alt, alt + ' role="presentation"'), fixture_state())
    expect_gap("alt text ahead of an empty alt", "lacks an empty alt=", "punycoder",
               edit(cran, "README.Rmd", alt, ' alt="punycoder"' + alt), fixture_state())
    for spelling in (' alt = ""', ' ALT=""', " alt=''", " alt"):
        expect_clean(f"alt spelled {spelling.strip()!r}", "punycoder",
                     edit(cran, "README.Rmd", alt, spelling), fixture_state())
    expect_clean("single-quoted alt, ahead of src", "punycoder",
                 edit(cran, "README.Rmd", fixture_h1("punycoder"),
                      "# punycoder <img alt='' src=\"man/figures/logo.png\" />"),
                 fixture_state())

    ci = ".gitlab-ci.yml"
    # POSITIVE: coverage named on each schedule by its own rules, the other push jobs not.
    push_only = edit(cran, ci, "    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH\n    - if: $CI_PIPELINE_SOURCE == \"web\"\n.deep:",
                     "    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && $CI_PIPELINE_SOURCE != \"schedule\"\n"
                     "    - if: $CI_PIPELINE_SOURCE == \"web\"\n.deep:")
    expect_clean("coverage on both schedules by its own rules", "punycoder",
                 edit(push_only, ci, "coverage:\n  extends: [.r, .on-main]\n",
                      "coverage:\n  extends: .r\n  rules:\n    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH\n"),
                 fixture_state())

    # NEGATIVE: CI.
    report = expect_gap("coverage only on push", "coverage job does not run on the deep-check schedule", "punycoder",
                        push_only, fixture_state())
    if not any("coverage job does not run on the dependency-audit schedule" in t for _, t in report.gaps):
        failures.append(f"coverage only on push: expected a dependency-audit schedule gap too, got {report.gaps}")
    report = expect_gap("coverage off the audit schedule", "coverage job does not run on the dependency-audit schedule",
                        "punycoder",
                        edit(cran, ci, "coverage:\n  extends: [.r, .on-main]\n",
                             "coverage:\n  extends: .r\n  rules:\n    - if: $SCHEDULE_KIND == \"dependency-audit\"\n      when: never\n"
                             "    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH\n"),
                        fixture_state())
    if any("deep-check schedule" in t for _, t in report.gaps):
        failures.append(f"coverage off the audit schedule: unexpected deep-check gap, got {report.gaps}")
    expect_gap("coverage threshold below 95", "coverage threshold 90 is below 95", "punycoder",
               edit(cran, ci, "pct < 95", "pct < 90"), fixture_state())
    expect_gap("coverage threshold absent", "no 95% coverage threshold", "punycoder",
               edit(cran, ci, "; if (pct < 95) quit(status = 1)", ""), fixture_state())
    expect_gap("coverage regex absent", "no coverage job with a coverage: regex", "punycoder",
               edit(cran, ci, "  coverage: '/Coverage: (\\d+\\.\\d+)%/'\n", ""), fixture_state())
    expect_gap("coverage allow_failure", "allow_failure: true", "punycoder",
               edit(cran, ci, "coverage:\n  extends: [.r, .on-main]\n",
                    "coverage:\n  extends: [.r, .on-main]\n  allow_failure: true\n"),
               fixture_state())
    expect_gap("check not --as-cran", "does not use --as-cran", "punycoder",
               edit(cran, ci, 'rcmdcheck(args = "--as-cran", error_on = "warning")\'\ncoverage',
                    'rcmdcheck(args = "--no-manual", error_on = "warning")\'\ncoverage'), fixture_state())
    expect_gap("incoming off outside seor", "turns CRAN incoming off", "punycoder",
               edit(cran, ci, 'error_on = "warning")\'\ncoverage',
                    'error_on = "warning", env = c("_R_CHECK_CRAN_INCOMING_" = "false"))\'\ncoverage'), fixture_state())
    expect_gap("check only on tags", "no R CMD check runs on a push to main", "punycoder",
               edit(cran, ci, "check:\n  extends: [.r, .on-main]\n", "check:\n  extends: .r\n  rules:\n    - if: $CI_COMMIT_TAG\n"),
               fixture_state())
    expect_gap("workflow shuts out main", "workflow: rules admit no push to main", "punycoder",
               edit(cran, ci, "    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH\n    - if: $CI_PIPELINE_SOURCE == \"web\"\n    - when: never",
                    "    - if: $CI_PIPELINE_SOURCE == \"web\"\n    - when: never"), fixture_state())
    expect_gap("pages off main", "pages does not deploy", "punycoder",
               edit(cran, ci, "pages:\n  extends: [.r, .on-main]\n", "pages:\n  extends: .r\n  rules:\n    - if: $CI_COMMIT_TAG\n"),
               fixture_state())
    expect_gap("opt-in readme stage", "no README drift gate", "punycoder",
               edit(cran, "tools/gates.R", "readme = list(default = TRUE", "readme = list(default = FALSE"), fixture_state())
    expect_gap("floor leg missing", "no deep-check leg at the declared R floor (4.1)", "punycoder",
               edit(cran, ci, ', "4.1.3"]', "]"), fixture_state())
    expect_gap("devel leg missing", "no deep-check leg for R devel", "punycoder",
               edit(cran, ci, ', "devel"', ""), fixture_state())
    expect_gap("deep leg also on push is not a leg", "no deep-check leg for R oldrel", "punycoder",
               edit(cran, ci, '"check:deep":\n  extends: .deep', '"check:deep":\n  extends: .on-main'), fixture_state())
    expect_gap("sanitizers missing", "no ASAN/UBSAN sanitizer leg", "punycoder",
               edit(cran, ci, "  image: rocker/r-devel-san\n", "  image: rocker/r-ver:devel\n"), fixture_state())
    expect_gap("audit on push", "osv-audit does not run only on the dependency-audit schedule", "punycoder",
               edit(cran, ci, "osv-audit:\n  extends: .audit\n", "osv-audit:\n  extends: .on-main\n"), fixture_state())
    expect_gap("audit job missing", "no security-audit job", "punycoder",
               edit(cran, ci, "security-audit:\n  extends: .audit", "security-check:\n  extends: .audit"), fixture_state())
    expect_gap("audit shape", "disposition-row shape", "punycoder",
               {k: v for k, v in cran.items() if k != "tests/testthat/helper-security.R"}, fixture_state())
    expect_gap("fossa job missing", "no fossa analyze job", "seor",
               edit(seor, ci, "    - fossa analyze\n", "    - echo fossa\n"),
               fixture_state(on_cran=False, release=False, doi=False, fossa=False))

    # pandoc pin (SEOR-egfbijyi): every R job on push installs PANDOC_PIN from the
    # release with a sha256 check. The fixture pins it in the `.r` template the R jobs extend.
    pin_block = cran[ci].split(".r:\n", 1)[1].split(".on-main:\n", 1)[0]
    pin_lines = pin_block.split("  before_script:\n", 1)[1]
    no_pin = edit(cran, ci, ".r:\n" + pin_block, ".r:\n  image: rocker/r-ver:4.6.1\n")
    report = expect_gap("pandoc pin absent", "pandoc 3.10 is not installed from the pandoc release in the setup of",
                        "punycoder", no_pin, fixture_state())
    unpinned = next((t for _, t in report.gaps if "not installed from the pandoc release" in t), "")
    if not all(name in unpinned for name in ("gates", "check", "coverage", "pages")) or "fossa" in unpinned:
        failures.append(f"pandoc pin absent: expected the four R jobs and not fossa, got {unpinned!r}")
    noncanonical = "does not install pandoc 3.10 in the standard's shape"
    expect_gap("pandoc pin without sha256", noncanonical, "punycoder",
               edit(cran, ci, "    - echo \"d502599878eb29af3ae5f0cb5d559134df96534125d452c7a0674a5bad2c5ecf  "
                    "/tmp/pandoc.deb\" | sha256sum -c -\n", ""), fixture_state())
    # The sha256 check and the install are tied to the downloaded .deb.
    digest = "d502599878eb29af3ae5f0cb5d559134df96534125d452c7a0674a5bad2c5ecf"
    check_line = f"    - echo \"{digest}  /tmp/pandoc.deb\" | sha256sum -c -\n"
    install_line = "    - dpkg -i /tmp/pandoc.deb\n"
    expect_gap("sha256 check of another download", noncanonical,
               "punycoder", edit(cran, ci, check_line, "    - curl -fsSL -o /tmp/other.tgz https://example.org/o.tgz\n"
                                 f"    - echo \"{digest}  /tmp/other.tgz\" | sha256sum -c -\n"), fixture_state())
    expect_gap("checked .deb never installed", noncanonical,
               "punycoder", edit(cran, ci, install_line, ""), fixture_state())
    expect_gap("another .deb installed", noncanonical,
               "punycoder", edit(cran, ci, install_line, "    - dpkg -i /tmp/other.deb\n"), fixture_state())
    expect_gap("installed before the check", noncanonical,
               "punycoder", edit(cran, ci, check_line + install_line, install_line + check_line), fixture_state())
    expect_gap("release named but never downloaded", noncanonical, "punycoder",
               edit(cran, ci, "    - curl -fsSL --retry 3 --max-time 300 -o /tmp/pandoc.deb ", "    - echo -o /tmp/pandoc.deb "), fixture_state())
    seor_shape = (
        "    - PANDOC_VERSION=3.10\n"
        "    - |\n"
        "      ARCH=$(dpkg --print-architecture)\n"
        "      if curl -fsSL --retry 3 --retry-delay 5 --connect-timeout 20 --max-time 300 -o /tmp/pandoc.deb \"https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/"
        "pandoc-${PANDOC_VERSION}-1-${ARCH}.deb\" \\\n"
        "        && echo \"${PANDOC_SHA256}  /tmp/pandoc.deb\" | sha256sum -c - \\\n"
        "        && dpkg -i /tmp/pandoc.deb; then\n"
        "        echo \"pandoc ${PANDOC_VERSION} installed\"\n"
        "      else\n"
        "        echo \"WARNING: pandoc ${PANDOC_VERSION} not installed\"\n"
        "      fi\n")
    expect_clean("pandoc installed in seor's shape", "punycoder", edit(cran, ci, pin_lines, seor_shape), fixture_state())
    # Nothing installs the .deb outside the canonical shape, and the three items
    # are consecutive: a second download between them replaces the checked file.
    expect_gap("an unchecked install beside seor's shape", noncanonical, "punycoder",
               edit(cran, ci, pin_lines, seor_shape + "    - dpkg -i --force-all /tmp/pandoc.deb\n"), fixture_state())
    expect_gap("an unchecked install beside the three items", noncanonical, "punycoder",
               edit(cran, ci, install_line, install_line + install_line), fixture_state())
    expect_gap("a second download between the check and the install", noncanonical, "punycoder",
               edit(cran, ci, check_line, check_line + "    - curl -m 60 -o /tmp/pandoc.deb https://example.org/x.deb\n"),
               fixture_state())
    expect_clean("pandoc saved under its release name", "punycoder",
                 edit(edit(edit(cran, ci, "-o /tmp/pandoc.deb \"https", "-O \"https"), ci,
                           "  /tmp/pandoc.deb\" | sha256sum -c -",
                           "  pandoc-${PANDOC_VERSION}-1-amd64.deb\" | sha256sum --check"),
                      ci, install_line, "    - dpkg -i ./pandoc-${PANDOC_VERSION}-1-amd64.deb\n"), fixture_state())
    expect_clean("pandoc fetched with wget", "punycoder",
                 edit(cran, ci, "curl -fsSL --retry 3 --max-time 300 -o /tmp/pandoc.deb ",
                      "wget -q --timeout=60 --tries=3 -O /tmp/pandoc.deb "), fixture_state())
    expect_clean("pandoc URL in a variable", "punycoder",
                 edit(edit(cran, ci, "    - curl -fsSL --retry 3 --max-time 300 -o /tmp/pandoc.deb \"https:", "    - PANDOC_URL=\"https:"),
                      ci, "-1-amd64.deb\"\n", "-1-amd64.deb\"\n    - curl -m 300 -fsSL -o /tmp/pandoc.deb \"$PANDOC_URL\"\n"),
                 fixture_state())
    unbounded = "downloads pandoc 3.10 with no time limit"
    expect_gap("pandoc download with no time limit", unbounded, "punycoder",
               edit(cran, ci, "--retry 3 --max-time 300 ", "--retry 3 "), fixture_state())
    expect_gap("pandoc download with a zero time limit", unbounded, "punycoder",
               edit(cran, ci, "--retry 3 --max-time 300 ", "--retry 3 --max-time 0 "), fixture_state())
    expect_gap("wget with no time limit", unbounded, "punycoder",
               edit(cran, ci, "curl -fsSL --retry 3 --max-time 300 -o /tmp/pandoc.deb ", "wget -q -O /tmp/pandoc.deb "), fixture_state())
    expect_gap("pandoc pin at another version", "pins pandoc 3.9, not the fleet's 3.10", "punycoder",
               edit(cran, ci, "PANDOC_VERSION=3.10", "PANDOC_VERSION=3.9"), fixture_state())
    expect_gap("pandoc version never recorded", "downloads pandoc at $PANDOC_VERSION, which .gitlab-ci.yml never assigns",
               "punycoder", edit(cran, ci, "    - PANDOC_VERSION=3.10\n", ""), fixture_state())
    # Every spelling of the pin passes here, and check-toolchain.R's self-test
    # reads the same list: a repository this script passes is never one whose
    # local pandoc check silently finds no pin.
    for spelling in ('PANDOC_VERSION="3.10"', "export PANDOC_VERSION=3.10", "PANDOC_VERSION=3.10  # the fleet pin",
                     "export PANDOC_VERSION='3.10' # pinned"):
        expect_clean(f"pandoc pin spelled {spelling!r}", "punycoder",
                     edit(cran, ci, "    - PANDOC_VERSION=3.10\n", f"    - {spelling}\n"), fixture_state())
    for spelling in ('PANDOC_VERSION: "3.10"', "PANDOC_VERSION: '3.10'",
                     'PANDOC_VERSION: "3.10"  # the fleet pin', "PANDOC_VERSION: '3.10' # pinned"):
        expect_clean(f"pandoc pin spelled {spelling!r}", "punycoder",
                     edit(edit(cran, ci, "    - PANDOC_VERSION=3.10\n", ""), ci, "variables:\n",
                          f"variables:\n  {spelling}\n"), fixture_state())
    # Unquoted, YAML reads 3.10 as the float 3.1: CI would fetch pandoc 3.1.
    for spelling in ("PANDOC_VERSION: 3.10", "PANDOC_VERSION: 3.10 # pinned"):
        expect_gap(f"pandoc pin spelled {spelling!r}", "pins pandoc 3.1, not the fleet's 3.10", "punycoder",
                   edit(edit(cran, ci, "    - PANDOC_VERSION=3.10\n", ""), ci, "variables:\n",
                        f"variables:\n  {spelling}\n"), fixture_state())
    expect_gap("pandoc version written into the URL", "downloads pandoc at 3.10, not at $PANDOC_VERSION", "punycoder",
               edit(cran, ci, "download/${PANDOC_VERSION}/", "download/3.10/"), fixture_state())
    expect_gap("pandoc version in another variable", "downloads pandoc at ${PV}, not at $PANDOC_VERSION", "punycoder",
               edit(edit(cran, ci, "download/${PANDOC_VERSION}/", "download/${PV}/"), ci, "variables:\n",
                    "variables:\n  PV: \"3.10\"\n"), fixture_state())
    expect_gap("pandoc version assigned only in a script", "which .gitlab-ci.yml never assigns", "punycoder",
               dict(edit(cran, ci, "    - PANDOC_VERSION=3.10\n", "    - . tools/pin.sh\n"),
                    **{"tools/pin.sh": "PANDOC_VERSION=3.10\n"}), fixture_state())
    # seor before SEOR-egfbijyi: only `gates` pinned it.
    report = expect_gap("pandoc pin in one job only", "in the setup of check, coverage, pages", "punycoder",
                        edit(no_pin, ci, "gates:\n  extends: [.r, .on-main]\n  script:\n",
                             "gates:\n  extends: [.r, .on-main]\n  script:\n" + pin_lines), fixture_state())
    if "gates" in next((t for _, t in report.gaps if "not installed from the pandoc release" in t), ""):
        failures.append(f"pandoc pin in one job only: gates pins it, got {report.gaps}")
    # GitLab replaces arrays along `extends`: a job's own before_script drops the template's pin.
    report = expect_gap("job replaces the template's before_script", "in the setup of check (README.md", "punycoder",
                        edit(cran, ci, "check:\n  extends: [.r, .on-main]\n",
                             "check:\n  extends: [.r, .on-main]\n  before_script:\n    - echo own setup\n"),
                        fixture_state())
    # The pin in `default:` reaches every job, citation-version's python:alpine
    # included, so it does not count; the R jobs are told to move it.
    in_default = edit(no_pin, ci, "default:\n  image: rocker/r-ver:4.6.1\n",
                      "default:\n  image: rocker/r-ver:4.6.1\n  before_script:\n" + pin_lines)
    report = expect_gap("pandoc pin only in default:", "gates, check, coverage, pages: pandoc is pinned only in "
                        "`default: before_script`", "punycoder", in_default, fixture_state())
    if any("not installed from the pandoc release" in t for _, t in report.gaps):
        failures.append(f"pandoc pin only in default:: expected the move-it gap alone, got {report.gaps}")
    expect_gap("default: pin with the job opted out", "in the setup of check (README.md", "punycoder",
               edit(in_default, ci, "check:\n  extends: [.r, .on-main]\n",
                    "check:\n  extends: [.r, .on-main]\n  inherit:\n    default: false\n"), fixture_state())
    expect_clean("pandoc version as a CI variable", "punycoder",
                 edit(edit(cran, ci, "    - PANDOC_VERSION=3.10\n", ""), ci, "variables:\n",
                      "variables:\n  PANDOC_VERSION: \"3.10\"\n"), fixture_state())

    # SEOR-xhyrogfm. One pin, read by check-toolchain.R's own reader: a shell
    # assignment overrides `variables:` at run time, so two values are a gap
    # whichever one a job would see, and check-toolchain.R refuses them too.
    two_pins = ".gitlab-ci.yml assigns PANDOC_VERSION more than once, with different values"
    expect_gap("pin in variables, another in the setup", two_pins, "punycoder",
               edit(edit(cran, ci, "    - PANDOC_VERSION=3.10\n", "    - PANDOC_VERSION=3.9\n"), ci, "variables:\n",
                    "variables:\n  PANDOC_VERSION: \"3.10\"\n"), fixture_state())
    expect_gap("pin in the setup, another in variables", two_pins, "punycoder",
               edit(cran, ci, "variables:\n", "variables:\n  PANDOC_VERSION: \"3.9\"\n"), fixture_state())
    expect_clean("the same pin in variables and the setup", "punycoder",
                 edit(cran, ci, "variables:\n", "variables:\n  PANDOC_VERSION: \"3.10\"\n"), fixture_state())
    expect_gap("two shell pins in the setup", two_pins, "punycoder",
               edit(cran, ci, "    - PANDOC_VERSION=3.10\n", "    - PANDOC_VERSION=3.10\n    - PANDOC_VERSION=3.9\n"),
               fixture_state())
    expect_gap("a second pin in a job without R", two_pins, "punycoder",
               edit(cran, ci, "    - fossa analyze\n", "    - export PANDOC_VERSION=3.9\n    - fossa analyze\n"),
               fixture_state())
    expect_gap("a second pin as a matrix entry", two_pins, "punycoder",
               edit(cran, ci, "      - R_VERSION: [\"4.6.1\", \"4.5.3\", \"devel\", \"4.1.3\"]\n",
                    "      - R_VERSION: [\"4.6.1\", \"4.5.3\", \"devel\", \"4.1.3\"]\n      - PANDOC_VERSION: \"3.9\"\n"),
               fixture_state())
    expect_gap("pin only in a job that installs no pandoc", "which neither its variables nor its setup assign",
               "punycoder", edit(edit(cran, ci, "    - PANDOC_VERSION=3.10\n", ""), ci, "    - fossa analyze\n",
                                 "    - PANDOC_VERSION=3.10\n    - fossa analyze\n"), fixture_state())
    # Only an assignment sh would run is a pin: not text in a comment or an echo.
    expect_clean("pin named in a comment and in echo text", "punycoder",
                 edit(cran, ci, "    - PANDOC_VERSION=3.10\n", "    - PANDOC_VERSION=3.10  # was PANDOC_VERSION=3.9\n"
                      "    - echo \"PANDOC_VERSION=3.9 is gone\"\n"), fixture_state())
    # A matrix entry is a pin per leg: a gap even with the fleet's value.
    expect_gap("pin in a parallel: matrix", "check:deep: sets PANDOC_VERSION in `parallel: matrix`", "punycoder",
               edit(cran, ci, "      - R_VERSION: [\"4.6.1\", \"4.5.3\", \"devel\", \"4.1.3\"]\n",
                    "      - R_VERSION: [\"4.6.1\", \"4.5.3\", \"devel\", \"4.1.3\"]\n        PANDOC_VERSION: \"3.10\"\n"),
               fixture_state())

    # The standard's two install shapes, and nothing else (SEOR-xhyrogfm): one
    # item `if <download> && <check> && dpkg -i; then …; else …; fi`, or three
    # items in that order. Each step is one command or pipeline, judged by its
    # last command; control flow beyond that, `set -e` included, is not read.
    url = "\"https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-amd64.deb\""
    dl_cmd = f"curl -fsSL --retry 3 --max-time 300 -o /tmp/pandoc.deb {url}"
    check_cmd = f"echo \"{digest}  /tmp/pandoc.deb\" | sha256sum -c -"

    def setup(*entries: str) -> dict:
        return edit(cran, ci, pin_lines, "    - PANDOC_VERSION=3.10\n" + "".join(entries))

    def if_block(cond: str, orelse: str = "      else\n        echo \"WARNING: pandoc not installed\"\n") -> str:
        return f"    - |\n      if {cond}; then\n        echo installed\n{orelse}      fi\n"

    expect_clean("one-line if in a plain item", "punycoder",
                 setup(f"    - if {dl_cmd} && {check_cmd} && dpkg -i /tmp/pandoc.deb; then echo ok; else echo WARN; fi\n"),
                 fixture_state())
    expect_clean("if over lines joined at the &&", "punycoder",
                 setup(if_block(f"{dl_cmd} &&\n        {check_cmd} &&\n        dpkg -i /tmp/pandoc.deb")),
                 fixture_state())
    expect_clean("seor's shape with its arch case", "punycoder", setup(
        "    - |\n"
        "      ARCH=$(dpkg --print-architecture)\n"
        "      case \"$ARCH\" in\n"
        f"        amd64) PANDOC_SHA256={digest} ;;\n"
        "        *) PANDOC_SHA256=unknown ;;\n"
        "      esac\n"
        "      if curl -fsSL --retry 3 --retry-delay 5 --retry-max-time 300 --connect-timeout 20 --max-time 120 \\\n"
        "        -o /tmp/pandoc.deb \"https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/"
        "pandoc-${PANDOC_VERSION}-1-${ARCH}.deb\" \\\n"
        "        && echo \"${PANDOC_SHA256}  /tmp/pandoc.deb\" | sha256sum -c - \\\n"
        "        && dpkg -i /tmp/pandoc.deb; then\n"
        "        echo \"pandoc ${PANDOC_VERSION} installed\"\n"
        "      else\n"
        "        echo \"WARNING: pandoc ${PANDOC_VERSION} not installed\"\n"
        "      fi\n"
        "      pandoc --version | sed -n 1p\n"), fixture_state())
    expect_clean("the three items as a flow sequence", "punycoder",
                 edit(cran, ci, "  before_script:\n" + pin_lines,
                      f"  variables:\n    PANDOC_VERSION: \"3.10\"\n  before_script: ['{dl_cmd}', '{check_cmd}',\n"
                      "    'dpkg -i /tmp/pandoc.deb']\n"), fixture_state())
    for tag, entries in (
        ("sha256 failure ignored with || true", (f"    - {dl_cmd}\n", f"    - {check_cmd} || true\n", install_line)),
        ("install after ; on the check's line", (f"    - {dl_cmd}\n", f"    - {check_cmd}; dpkg -i /tmp/pandoc.deb\n")),
        ("sha256 failure exits", (f"    - {dl_cmd}\n", f"    - {check_cmd} || exit 1\n", install_line)),
        ("three steps in one block", (f"    - |\n      {dl_cmd}\n      {check_cmd}\n      dpkg -i /tmp/pandoc.deb\n",)),
        ("three steps chained with ;", (f"    - {dl_cmd}; {check_cmd}; dpkg -i /tmp/pandoc.deb\n",)),
        ("three steps after set -Eeuo pipefail",
         (f"    - |\n      set -Eeuo pipefail\n      {dl_cmd}\n      {check_cmd}\n      dpkg -i /tmp/pandoc.deb\n",)),
        ("install after the if that checks",
         (if_block(f"{dl_cmd} && {check_cmd}"), install_line)),
        ("if without an else", (if_block(f"{dl_cmd} && {check_cmd} && dpkg -i /tmp/pandoc.deb", ""),)),
        ("|| inside the if", (if_block(f"{dl_cmd} && {check_cmd} || true && dpkg -i /tmp/pandoc.deb"),)),
        ("negated check", (f"    - {dl_cmd}\n", f"    - ! {check_cmd}\n", install_line)),
        # A pipeline's status is its last command's: `| tee` hides the check.
        ("check piped into tee", (f"    - {dl_cmd}\n", f"    - {check_cmd} | tee /tmp/sha.log\n", install_line)),
        ("check piped into tee inside the if",
         (if_block(f"{dl_cmd} && {check_cmd} | tee /tmp/sha.log && dpkg -i /tmp/pandoc.deb"),)),
        # Paths compare as whole tokens; `-` is stdout, not a file.
        ("download to stdout, another file checked",
         (f"    - wget -q -T 60 -t 3 -O- {url} > /tmp/pandoc.deb\n",
          f"    - echo \"{digest}  /tmp/other.deb\" | sha256sum -c -\n", install_line)),
        ("output path inside an unrelated checksum file's name",
         (f"    - curl -fsSL --max-time 300 -o p {url}\n", "    - sha256sum -c /tmp/unrelated.sha256\n",
          "    - dpkg -i p\n")),
        ("installs a .deb whose name extends the download's",
         (f"    - {dl_cmd}\n", check_line, "    - dpkg -i /tmp/pandoc.deb.bak\n")),
        ("checked file named only in a comment",
         (f"    - {dl_cmd}\n", "    - sha256sum -c /tmp/x.sha256  # checks /tmp/pandoc.deb\n", install_line)),
    ):
        expect_gap(tag, noncanonical, "punycoder", setup(*entries), fixture_state())

    # The download's file: stdout's redirect, not stderr's, `>|` included.
    for redirect in ("> /tmp/pandoc.deb", "2>/dev/null > /tmp/pandoc.deb", "&>/dev/null >/tmp/pandoc.deb",
                     "2>&1 >/tmp/pandoc.deb", ">| /tmp/pandoc.deb"):
        expect_clean(f"download saved with {redirect!r}", "punycoder",
                     setup(f"    - curl -fsSL --max-time 300 {url} {redirect}\n", check_line, install_line), fixture_state())

    # Time limits: timeout(1) and a bundled -m bound the download; wget's
    # --timeout bounds one try, and it tries 20 times by default (0: forever).
    for bounded in (f"timeout 300 curl -fsSL --retry 3 -o /tmp/pandoc.deb {url}",
                    f"curl -fsSLm 300 -o /tmp/pandoc.deb {url}",
                    f"timeout -k 10 5m wget -q -O /tmp/pandoc.deb {url}",
                    f"wget -q -T 60 -t 3 -O /tmp/pandoc.deb {url}"):
        expect_clean(f"download bounded: {bounded[:30]!r}", "punycoder", setup(f"    - {bounded}\n", check_line, install_line),
                     fixture_state())
    for unbounded_dl in (f"timeout 0 curl -fsSL -o /tmp/pandoc.deb {url}",
                         f"wget -q --timeout=60 -O /tmp/pandoc.deb {url}",
                         f"wget -q --timeout=60 --tries=0 -O /tmp/pandoc.deb {url}",
                         f"wget -q --timeout=60 --tries=20 -O /tmp/pandoc.deb {url}"):
        expect_gap(f"download unbounded: {unbounded_dl[:40]!r}", unbounded, "punycoder",
                   setup(f"    - {unbounded_dl}\n", check_line, install_line), fixture_state())

    # NEGATIVE: local gate and schedules.
    expect_gap("URL check missing", "no URL check", "punycoder",
               dict(cran, **{"tools/verify.R": "# check_url_db is only mentioned in a comment\nx <- 1\n"}), fixture_state())
    no_local_pandoc = "no check that compares the local rmarkdown::pandoc_version() with the CI pin (PANDOC_VERSION, 3.10)"
    expect_gap("local pandoc check missing", no_local_pandoc, "punycoder",
               dict(cran, **{"scripts/check-toolchain.R": "# pandoc_version() is only mentioned here\nx <- 1\n"}),
               fixture_state())
    expect_gap("local pandoc check against a minimum only", no_local_pandoc, "punycoder",
               dict(cran, **{"scripts/check-toolchain.R":
                             "if (rmarkdown::pandoc_version() < \"2.11\") stop(\"pandoc too old\")\n"}),
               fixture_state())
    expect_gap("pin read and pandoc asked in different scripts", no_local_pandoc, "punycoder",
               dict(cran, **{"scripts/check-toolchain.R": "pin <- Sys.getenv(\"PANDOC_VERSION\")\n",
                             "tools/verify.R": cran["tools/verify.R"] + "v <- rmarkdown::pandoc_version()\n"}),
               fixture_state())
    # The pin is read from .gitlab-ci.yml: nothing sets PANDOC_VERSION locally,
    # so an environment read compares with its default, a minimum check.
    compare = "if (!identical(as.character(rmarkdown::pandoc_version()), pin)) quit(status = 1)\n"
    expect_gap("local pandoc check against an unset variable", no_local_pandoc, "punycoder",
               dict(cran, **{"scripts/check-toolchain.R": "pin <- Sys.getenv(\"PANDOC_VERSION\", \"2.11\")\n" + compare}),
               fixture_state())
    expect_gap("CI file read for something else, pin from the environment", no_local_pandoc, "punycoder",
               dict(cran, **{"scripts/check-toolchain.R": "ci <- readLines(\".gitlab-ci.yml\")\n"
                                                          "pin <- Sys.getenv(\"PANDOC_VERSION\")\n" + compare}),
               fixture_state())
    expect_gap("CI file named only in a trailing comment", no_local_pandoc, "punycoder",
               dict(cran, **{"scripts/check-toolchain.R": "pin <- PANDOC_VERSION  # see .gitlab-ci.yml\n" + compare}),
               fixture_state())
    no_deep = fixture_state()
    no_deep.schedules = no_deep.schedules[1:]
    expect_gap("deep-check schedule missing", "no deep-check schedule", "punycoder", cran, no_deep)
    stray = fixture_state()
    stray.schedules = stray.schedules + [{"id": 3, "description": "x", "ref": "dev", "active": True, "variables": []}]
    expect_gap("schedule without kind", "sets no SCHEDULE_KIND", "punycoder", cran, stray)

    # Unknown state is not judged, never a gap.
    unknown = run("punycoder", cran, State())
    if unknown.gaps and any(area in ("badges", "schedules") for area, _ in unknown.gaps):
        failures.append(f"unknown state produced badge/schedule gaps: {unknown.gaps}")
    return failures


# --- main ----------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", choices=FLEET, help="check one package (default: all nine)")
    parser.add_argument("--local", type=Path, help="read a local checkout instead of GitLab main (needs --repo)")
    parser.add_argument("--offline", action="store_true", help="no network at all (needs --local)")
    parser.add_argument("--self-test", action="store_true", help="run the offline fixtures")
    args = parser.parse_args(argv)

    if args.self_test:
        failures = self_test()
        if failures:
            print("check-fleet-standard self-test FAILED:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print("check-fleet-standard self-test: all checks passed.")
        return 0
    if args.local and not args.repo:
        parser.error("--local needs --repo")
    if args.offline and not args.local:
        parser.error("--offline needs --local")

    reports = [run_one(pkg, args.local.expanduser() if args.local else None, args.offline)
               for pkg in ([args.repo] if args.repo else FLEET)]
    for report in reports:
        print(report.render())
    total = sum(len(r.gaps) for r in reports)
    incomplete = sum(len(r.unjudged) for r in reports)
    print(f"{total} gap(s) in {sum(1 for r in reports if r.gaps)} of {len(reports)} package(s); "
          f"{incomplete} item(s) not judged.")
    if total:
        return 1
    return 2 if any("probe failed" in t or "could not read" in t or "network error" in t
                    for r in reports for _, t in r.unjudged) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
