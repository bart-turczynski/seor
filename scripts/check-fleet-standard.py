# check-fleet-standard v5
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
but the run is incomplete: a probe failed (a network error, glab refusing),
a file could not be read, .gitlab-ci.yml did not load, or a pandoc pin
assignment sits where this cannot see. Each is reported under "not judged",
never as a gap. A judgment `--offline` leaves out, or one that hangs on a
state the run does not know, is listed there too but leaves the run complete
(Report.skip's `incomplete` flag).

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
  `src` is `man/figures/logo.png` and whose `alt` is "hex logo, white on black"
  (LOGO_ALT), without the package name the heading already says, and no
  aria-label, aria-labelledby, aria-hidden or role replaces or hides it. The
  link-wrapped form usethis::use_logo() writes is accepted. The artwork itself
  is not judged.
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
  count: nothing sets it locally. And the generated-docs drift check: some
  script in that chain runs roxygen2 (`roxygenise` or `roxygenize`) and some
  script runs `git archive`, the export it regenerates into, since a stale
  `.Rd` is still valid `.Rd` and nothing else in the gate sees it
  (SEOR-nwfmerhu). That the two belong together, and that it diffs, is a
  review item.
* Schedules. A `deep-check` and a `dependency-audit` schedule, each active,
  on `main`, with `SCHEDULE_KIND` set on the schedule itself; no schedule
  without a `SCHEDULE_KIND` or off `main`.

HOW IT READS CI, AND WHERE THAT STOPS. `.gitlab-ci.yml` is read with PyYAML
(`yaml.safe_load_all`, YAML 1.1 as GitLab reads it: an unquoted `3.10` is
3.1, `yes` is true), so quoting, trailing comments, flow and block lists,
anchors, aliases and `<<` merge keys come from YAML itself (ADR 0008,
SEOR-oznwzhem). The file is one config document, or a `spec:` header document
and then the config. A file that does not load (a YAML error, an unknown tag
such as `!reference`, a scalar its tag cannot hold such as `2026-02-30`, a
recursive alias, another document shape), whose `extends:` names a block it
does not define, or whose `rules:if` does not read (an empty one included),
leaves every CI rule of that package not judged and the run incomplete; the
other areas are still judged. `include:` is not followed. On top of the YAML sits only GitLab's own
semantics: `extends:` deep-merges mappings and replaces arrays, later parents
over earlier ones and the job over all; `default:` (or a deprecated top-level
`image:`, `before_script:`, ...) fills each key a job leaves unset, never
merging into one it sets, unless `inherit: default:` turns it off; global
`variables:` reach a job unless `inherit: variables:` turns them off, and a
job's own variables override them, in its commands and in its `rules:if`.
`before_script` and `script` are the items GitLab runs: a string is one item,
nested lists (an alias to a list of commands) flatten. `rules:if` and
`workflow:rules` are evaluated for real (a
small evaluator for `==`, `!=`, `=~`, `!~`, `&&`, `||`, presence and
parentheses) in four pipelines: a push to main, a `deep-check` schedule, a
`dependency-audit` schedule and a tag. A job "runs" in a pipeline when the
workflow admits it and its first matching rule is not `never` or `manual`.
A deep-check leg is an R CMD check job that runs in the deep-check schedule and
in neither a push to main nor the dependency-audit schedule (design/fleet.md:
every scheduled job requires its kind). Its R version comes from its image tag,
expanded through `parallel:matrix` and variables, and is compared by minor
version with the current release and oldrel (api.r-hub.io) and the DESCRIPTION
floor. Settings GitLab holds as keys are read as keys: `allow_failure`,
`coverage`, the cobertura report, `pages`, and variables such as
`_R_CHECK_CRAN_INCOMING_` as typed values. What a job's commands do is read
textually, from the `before_script` and `script` items it ends up with (a
parent's script it replaces does not count, nor an anchor it never uses),
with a `NAME=value` line for each variable those items or the scripts read
(so `--as-cran` in `$ARGS` counts, and a variable nothing reads does not),
and from every repository R, shell or YAML script that text
names, each a
separate text (two levels deep, comment lines dropped, and R stage tables'
`default = FALSE` entries dropped, since those stages are opt-in). Python
scripts are not followed: the citation scripts a job names quote
`R CMD check --as-cran` in their prose.
So a gate is "present" when its call appears in that text; a script that takes
the call but skips it at run time reads as present. Not checked: whether a tag
pipeline fails on "already on CRAN", whether the URL check fails on zero URLs
and exempts only the BugReports 404, how security-audit treats missing OSS
Index credentials, the GitLab project badges, and that no employer is named as
copyright holder or funder. Those stay review items.

Needs PyYAML (pinned at 6.0.3 in the pre-commit hook, which installs it); a run
without it exits 2 with an install hint. `glab` must be on PATH and
authenticated unless `--offline`, and `Rscript` for the pandoc pin (the
self-test included).
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
from functools import cached_property
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

try:
    import yaml
except ImportError:  # main() says how to install it
    yaml = None

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
    incomplete: bool = False

    def gap(self, area: str, text: str) -> None:
        self.gaps.append((area, text))

    def skip(self, area: str, text: str, *, incomplete: bool) -> None:
        """A judgment not made. Each caller says whether it leaves the run
        `incomplete` (exit_status): true when the run could not make it, a
        probe that failed, a file that did not load, a construct this script
        cannot see into. False when it is left out by choice (`--offline`),
        or hangs on a state that is unknown because the run was offline or
        because a probe failed, which that probe's own skip already marks."""
        self.unjudged.append((area, text))
        self.incomplete = self.incomplete or incomplete

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
    """(path, text) for each repository script `text` names, followed `depth` levels.

    ProbeError when a named script cannot be read: a view without it would
    judge the rules it holds as missing.
    """
    seen = set() if seen is None else seen
    out = []
    tree = source.tree()
    for token in PATH_TOKEN.findall(text):
        if token in seen or token not in tree or Path(token).suffix not in SCRIPT_SUFFIXES:
            continue
        if token == ".gitlab-ci.yml":
            continue
        seen.add(token)
        body = source.read(token) or ""
        if len(body) > 400_000:
            continue
        body = strip_comment_lines(body)
        if Path(token).suffix in (".R", ".r"):
            body = drop_opt_in_stages(body)
        out.append((token, body))
        if depth > 1:
            out += inline_scripts(body, source, depth - 1, seen)
    return out


# --- CI: the YAML, extends, default, rules -----------------------------------------

# Top-level keys that are not jobs.
RESERVED = {"stages", "default", "variables", "workflow", "include", "image", "services",
            "cache", "before_script", "after_script"}
# The deprecated top-level spellings of `default:` keys.
LEGACY_DEFAULTS = ("image", "services", "cache", "before_script", "after_script")
# GitLab refuses `extends` nested deeper than this.
EXTENDS_DEPTH = 11


class CIError(Exception):
    """A .gitlab-ci.yml GitLab itself would refuse: its CI rules are not judged."""


def load_ci(text: str) -> dict:
    """The config mapping of a .gitlab-ci.yml, or CIError when GitLab would refuse it.

    Every failure to load is a CIError: a YAML error, an unknown tag, and also
    a scalar its tag cannot hold (`2026-02-30`, `!!int 'abc'`), which PyYAML
    raises as a plain ValueError. The file is one document, or a header
    document holding only `spec:` (an include's inputs), `---`, then the
    config; an empty document (a trailing `---`) is no document. A node that contains itself (`a: &a [*a]`) is refused here, so
    nothing downstream recurses into it.
    """
    try:
        documents = [document for document in yaml.safe_load_all(text) if document is not None]
    except Exception as error:  # noqa: BLE001 - any failure to load is a load error
        detail = str(error) if isinstance(error, yaml.YAMLError) else f"{type(error).__name__}: {error}"
        raise CIError(" ".join(detail.split())[:300]) from error
    if len(documents) == 2 and isinstance(documents[0], dict) and set(documents[0]) == {"spec"}:
        documents = documents[1:]
    if len(documents) != 1:
        raise CIError(f"it holds {len(documents)} YAML documents, not one config after at most a `spec:` header")
    if not isinstance(documents[0], dict):
        raise CIError("its top level is not a mapping")
    acyclic(documents[0])
    return documents[0]


def acyclic(node: object, open_ids: set[int] | None = None, done: set[int] | None = None) -> None:
    """CIError when a mapping or list contains itself, through a recursive alias."""
    if not isinstance(node, (dict, list)):
        return
    open_ids = set() if open_ids is None else open_ids
    done = set() if done is None else done
    if id(node) in done:
        return
    if id(node) in open_ids:
        raise CIError("a recursive alias: a node contains itself")
    open_ids.add(id(node))
    for child in node.values() if isinstance(node, dict) else node:
        acyclic(child, open_ids, done)
    open_ids.discard(id(node))
    done.add(id(node))


def gitlab_str(value: object) -> str:
    """A YAML scalar as GitLab hands it to a job or a rule: `true`/`false`, 3.1 for an unquoted 3.10."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


def as_strings(variables: dict[str, object]) -> dict[str, str]:
    """Typed variables as the strings a job and its rules see."""
    return {name: gitlab_str(value) for name, value in variables.items()}


def variables_of(block: object) -> dict[str, object]:
    """A `variables:` mapping as typed values; the `{value: ..., description: ...}` form gives its value."""
    if not isinstance(block, dict):
        return {}
    return {str(name): value.get("value") if isinstance(value, dict) else value for name, value in block.items()}


def script_items(value: object) -> list[str]:
    """A `before_script`/`script` value as the items GitLab runs, in order.

    A string is one item. Nested lists flatten, as GitLab flattens them: an
    alias to an anchored list of commands is its commands. A mapping is no
    command (GitLab refuses it) and gives none.
    """
    if value is None or isinstance(value, dict):
        return []
    if isinstance(value, list):
        return [item for entry in value for item in script_items(entry)]
    return [gitlab_str(value)]


def deep_merge(base: object, over: object) -> object:
    """GitLab's `extends` merge: mappings merge key by key, anything else (arrays included) is replaced."""
    if not (isinstance(base, dict) and isinstance(over, dict)):
        return over
    merged = dict(base)
    for key, value in over.items():
        merged[key] = deep_merge(base[key], value) if key in base else value
    return merged


def inherited(setting: object, key: str) -> bool:
    """Whether an `inherit:` setting (true, false or a list of keys) lets `key` through."""
    if setting is False:
        return False
    if isinstance(setting, list):
        return key in setting
    return True


# A variable a command or script reads: `$NAME`, `${NAME…}`, or R's `Sys.getenv("NAME")`.
VAR_READ_RE = re.compile(r"\$\{?(\w+)|Sys\.getenv\(\s*[\"'](\w+)[\"']")
REGEX_LITERAL = re.compile(r"/((?:\\.|[^/])*)/([a-z]*)")
EXPR_TOKEN = re.compile(r"\s*(?:(\$\{?\w+\}?)|(\"[^\"]*\"|'[^']*')|(==|!=|=~|!~|&&|\|\||\(|\))|(null)\b)")


def evaluate(expr: str, env: dict[str, str]) -> bool:
    """Evaluate a GitLab `rules:if` expression against variables in `env`.

    The right of `=~`/`!~` is a `/regex/`, or a variable holding one.
    ValueError (or re.error, for a bad regex) when the expression does not
    read whole: empty, cut short, unbalanced, with words left over, or a
    pattern variable that is unset or holds no `/regex/`.
    """
    tokens: list[tuple[str, str]] = []
    i = 0
    while i < len(expr):
        if expr[i].isspace():
            i += 1
            continue
        if tokens and tokens[-1] == ("op", "=~") or tokens and tokens[-1] == ("op", "!~"):
            m = REGEX_LITERAL.match(expr, i)
            held = None if m else re.compile(r"\$\{?(\w+)\}?").match(expr, i)
            if held:
                # A variable on the right holds the pattern, slashes included.
                m = REGEX_LITERAL.fullmatch(env.get(held.group(1)) or "")
                if not m:
                    raise ValueError(f"${held.group(1)} holds no /regex/ for {expr!r}")
            elif not m:
                raise ValueError(f"bad regex in {expr!r}")
            tokens.append(("re", m.group(1) + ("\x00i" if "i" in m.group(2) else "")))
            i = (held or m).end()
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

    def take() -> tuple[str, str]:
        nonlocal pos
        if pos == len(tokens):
            raise ValueError(f"rule {expr!r} ends early")
        pos += 1
        return tokens[pos - 1]

    def atom() -> bool:
        token = take()
        if token == ("op", "("):
            result = disjunction()
            if take() != ("op", ")"):
                raise ValueError(f"unbalanced parentheses in {expr!r}")
            return result
        if token[0] not in ("var", "str", "null"):
            raise ValueError(f"cannot read rule {expr!r}")
        if pos < len(tokens) and tokens[pos][0] == "op" and tokens[pos][1] in ("==", "!=", "=~", "!~"):
            op = take()[1]
            right = take()
            left = value(token)
            if op in ("==", "!="):
                if right[0] not in ("var", "str", "null"):
                    raise ValueError(f"cannot read rule {expr!r}")
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

    result = disjunction()
    if pos != len(tokens):
        raise ValueError(f"cannot read rule {expr!r}")
    return result


def first_match(rules: list, env: dict[str, str]) -> str | None:
    """The `when` of the first rule that matches, or None when none matches.

    CIError for an `if:` this cannot evaluate, an empty one included
    (`- if:` with no expression): what GitLab makes of that is not settled
    here, so the file's CI is not judged rather than guessed.
    """
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if "if" in rule:
            expr = rule["if"]
            if not isinstance(expr, str) or not expr.strip():
                raise CIError(f"a rule's `if:` is {expr!r}, not an expression")
            try:
                matched = evaluate(expr, env)
            except (ValueError, re.error) as error:
                raise CIError(f"cannot evaluate `if: {expr}`: {error}") from error
            if not matched:
                continue
        return gitlab_str(rule.get("when", "on_success"))
    return None


PIPELINES = {
    "push": {"CI_PIPELINE_SOURCE": "push", "CI_COMMIT_BRANCH": "main", "CI_COMMIT_REF_NAME": "main"},
    "deep-check": {"CI_PIPELINE_SOURCE": "schedule", "CI_COMMIT_BRANCH": "main",
                   "CI_COMMIT_REF_NAME": "main", "SCHEDULE_KIND": "deep-check"},
    "dependency-audit": {"CI_PIPELINE_SOURCE": "schedule", "CI_COMMIT_BRANCH": "main",
                         "CI_COMMIT_REF_NAME": "main", "SCHEDULE_KIND": "dependency-audit"},
    "tag": {"CI_PIPELINE_SOURCE": "push", "CI_COMMIT_TAG": "v9.9.9", "CI_COMMIT_REF_NAME": "v9.9.9"},
}


@dataclass(eq=False)
class Job:
    """A job as GitLab runs it.

    `config` is its mapping with `extends` merged and `default:` filled in;
    `defaulted` names the keys `default:` supplied; `global_variables` are the
    global ones `inherit: variables:` lets through. `source` is the
    repository its scripts are read from.
    """

    name: str
    config: dict
    defaulted: frozenset[str]
    global_variables: dict[str, object]
    source: object = None
    runs: dict[str, bool] = field(default_factory=dict)

    @property
    def variables(self) -> dict[str, object]:
        """The job's own variables, typed, merged along `extends`."""
        return variables_of(self.config.get("variables"))

    def all_variables(self) -> dict[str, object]:
        """What the job sees: the global variables it inherits, then its own over them."""
        return {**self.global_variables, **self.variables}

    @cached_property
    def strings(self) -> dict[str, str]:
        """all_variables() as the strings the job, its rules and its image see."""
        return as_strings(self.all_variables())

    @property
    def inherits_default_before(self) -> bool:
        return "before_script" in self.defaulted

    def script(self, with_default: bool = True) -> list[str]:
        """The `before_script` then `script` items the job runs, decoded and flattened.

        `with_default=False` leaves out a `before_script` that `default:` supplied.
        """
        before = [] if self.inherits_default_before and not with_default else script_items(self.config.get("before_script"))
        return before + script_items(self.config.get("script"))

    def matrix(self) -> list[dict]:
        """The `parallel: matrix` entries."""
        parallel = self.config.get("parallel")
        entries = parallel.get("matrix") if isinstance(parallel, dict) else None
        return [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []

    def command_text(self) -> str:
        """The job's own script items as one text, comment lines dropped."""
        return "\n".join(strip_comment_lines(item) for item in self.script())

    @cached_property
    def view(self) -> tuple[str, ...]:
        """The one view every text rule searches, as separate texts: the
        job's script items with a `NAME=value` line for each variable they
        read, then each repository script that text names, followed two
        levels. A variable counts when the items, a script or another
        counted variable's value reads it (VAR_READ_RE): `R CMD check $ARGS`
        holds ARGS's flags and `Rscript $GATES` runs GATES's script, while a
        variable nothing reads is no command. ProbeError when a named script
        cannot be read."""
        commands, strings, used = self.command_text(), self.strings, set()
        while True:
            own = "\n".join([commands] + [f"{name}={value}" for name, value in strings.items() if name in used])
            scripts = [body for _, body in inline_scripts(own, self.source)] if self.source is not None else []
            reads = {a or b for text in [own] + scripts for a, b in VAR_READ_RE.findall(text)}
            if not (reads & set(strings)) - used:
                return (own, *scripts)
            used |= reads & set(strings)

    @cached_property
    def full_text(self) -> str:
        """view as one text."""
        return "\n".join(self.view)


class CI:
    """A .gitlab-ci.yml, loaded with yaml.safe_load_all and resolved as GitLab resolves it.

    `error` is set, and `jobs` left empty, when GitLab would refuse the file
    or this reader cannot follow it: it does not load (load_ci()), an
    `extends` names no block, loops or nests too deep, or a `rules:if` does
    not read.
    """

    def __init__(self, text: str, source):
        self.text = text
        self.source = source
        self.error: str | None = None
        self.data: dict = {}
        self.global_vars: dict[str, object] = {}
        self.default: dict = {}
        self.workflow_rules: list | None = None
        self.admits: dict[str, bool] = {}
        self.jobs: dict[str, Job] = {}
        try:
            data = load_ci(text)
            self.data = data
            self.global_vars = variables_of(data.get("variables"))
            default = data.get("default")
            self.default = dict(default) if isinstance(default, dict) else {}
            for key in LEGACY_DEFAULTS:
                if key in data and key not in self.default:
                    self.default[key] = data[key]
            workflow = data.get("workflow")
            rules = workflow.get("rules") if isinstance(workflow, dict) else None
            self.workflow_rules = rules if isinstance(rules, list) else None
            self.admits = {pipeline: self.workflow_rules is None
                           or first_match(self.workflow_rules, self.env(pipeline)) not in (None, "never")
                           for pipeline in PIPELINES}
            self.jobs = {name: self.job(name) for name, block in data.items()
                         if isinstance(name, str) and name not in RESERVED and not name.startswith(".")
                         and isinstance(block, dict)}
        except (CIError, RecursionError) as error:
            self.error = str(error) if isinstance(error, CIError) else "it nests too deep to resolve"
            self.jobs = {}

    def env(self, pipeline: str, variables: dict[str, str] | None = None) -> dict[str, str]:
        """What `rules:if` sees in `pipeline`: `variables` (the global ones
        when None, which is what `workflow:rules` sees), then the pipeline's own."""
        env = dict(as_strings(self.global_vars) if variables is None else variables)
        env.update({"CI_DEFAULT_BRANCH": "main"})
        env.update(PIPELINES[pipeline])
        return env

    def admitted(self, pipeline: str) -> bool:
        return self.admits.get(pipeline, False)

    def resolve(self, name: str, chain: tuple[str, ...] = ()) -> dict:
        """A block with its `extends` merged in: parents in order, later over earlier, the block over all."""
        if name in chain:
            raise CIError(f"extends loops: {' -> '.join(chain + (name,))}")
        if len(chain) > EXTENDS_DEPTH:
            raise CIError(f"{chain[0]}: extends nests deeper than {EXTENDS_DEPTH} levels")
        block = self.data.get(name)
        if not isinstance(block, dict):
            raise CIError(f"{chain[-1]} extends {name}, which .gitlab-ci.yml does not define")
        parents = block.get("extends", [])
        parents = [parents] if isinstance(parents, str) else parents
        if not isinstance(parents, list) or not all(isinstance(parent, str) for parent in parents):
            raise CIError(f"{name}: extends is neither a name nor a list of names")
        merged: object = {}
        for parent in parents:
            merged = deep_merge(merged, self.resolve(parent, chain + (name,)))
        return deep_merge(merged, {key: value for key, value in block.items() if key != "extends"})

    def job(self, name: str) -> Job:
        config = self.resolve(name)
        inherit = config.get("inherit") if isinstance(config.get("inherit"), dict) else {}
        defaulted = set()
        for key, value in self.default.items():
            if key not in config and inherited(inherit.get("default", True), key):
                config[key] = value
                defaulted.add(key)
        global_variables = {key: value for key, value in self.global_vars.items()
                            if inherited(inherit.get("variables", True), key)}
        job = Job(name, config, frozenset(defaulted), global_variables, self.source)
        rules = config.get("rules")
        job_when = gitlab_str(config.get("when") or "on_success")
        for pipeline in PIPELINES:
            if not self.admitted(pipeline):
                job.runs[pipeline] = False
                continue
            # A job's rules see its own variables over the global ones it inherits.
            when = first_match(rules, self.env(pipeline, job.strings)) if isinstance(rules, list) else job_when
            job.runs[pipeline] = when in ("on_success", "always", "delayed")
        return job

    def default_before(self) -> list[str]:
        """The items of `default: before_script` (or the top-level one)."""
        return script_items(self.default.get("before_script"))

    def images(self, job: Job) -> list[str]:
        """The job's image(s), expanded through parallel:matrix and variables."""
        image = job.config.get("image")
        if isinstance(image, dict):
            image = image.get("name")
        image = "" if isinstance(image, (dict, list)) else gitlab_str(image)
        matrix: dict[str, list[str]] = {}
        for entry in job.matrix():
            for var, values in entry.items():
                values = values if isinstance(values, list) else [values]
                matrix.setdefault(str(var), []).extend(gitlab_str(value) for value in values)
        variables = job.strings
        out = [image]
        for _ in range(3):
            expanded = []
            for img in out:
                m = re.search(r"\$\{?(\w+)\}?", img)
                if not m:
                    expanded.append(img)
                    continue
                values = matrix.get(m.group(1)) or [variables.get(m.group(1), "")]
                expanded += [img[:m.start()] + v + img[m.end():] for v in values]
            out = expanded
        return [img for img in out if img]


CHECK_RE = re.compile(r"rcmdcheck::rcmdcheck\s*\(|\bR CMD check\b|\"CMD\",\s*\"check\"")
AS_CRAN_RE = re.compile(r"--as-cran")
ERROR_ON_RE = re.compile(r"error_on\s*=\s*\\?[\"']warning\\?[\"']")
# R reads a check setting with tools:::config_val_to_logical(): lower-cased,
# "false", "no" and "0" are off.
R_FALSE = ("false", "no", "0")
INCOMING_OFF_RE = re.compile(rf"_R_CHECK_CRAN_INCOMING_[\"']?\s*[=:]\s*[\"']?(?i:{'|'.join(R_FALSE)})\b")
INCOMING_REMOTE_OFF_RE = re.compile(rf"_R_CHECK_CRAN_INCOMING_REMOTE_[\"']?\s*[=:]\s*[\"']?(?i:{'|'.join(R_FALSE)})\b")
# The generated-docs drift check regenerates man/ with roxygen2, in either
# spelling, on a `git archive` export of the pushed commit (SEOR-nwfmerhu):
# the shell command, or R's system2("git", c("archive", ...)).
DOCS_DRIFT_RE = re.compile(r"\broxygeni[sz]e\b")
DOCS_EXPORT_RE = re.compile(r"\bgit\s+archive\b|[\"']git[\"']\s*,\s*c\(\s*[\"']archive[\"']")
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


# A PANDOC_VERSION assignment command, read on the Shell mask. It starts a
# command: a line's start, or after `;`, `&&`, `||`, a lone `&` (the command
# before it is backgrounded, not this one), a `{` group, a case pattern's `)`,
# `then`, `do` or `else`. Not after `(` or `|`: a subshell or a pipeline stage. The command is
# assignments only (`A=1 PANDOC_VERSION=3.10`) or the `export`, `readonly`,
# `declare` or `typeset` builtin, and it ends there: with a command word after
# it (`PANDOC_VERSION=3.10 curl …/$PANDOC_VERSION/…`), the assignment reaches
# that one command's environment, after its words are expanded, and with `|`
# or `&` after it, a subshell. Whether the compound command around it runs in
# the current shell is shell_frames()' to say.
PIN_HEAD = r"(?:^|;|&&|\|\||(?<![&|>])&(?![&>])|(?<!\$)\{|\))[ \t]*(?:(?:then|do|else)[ \t]+)?"
PIN_WORD = r"[^\s;&|<>()]*"
PIN_TAIL = r"(?=[ \t]*(?:$|;|&&|\|\|))"
PIN_ASSIGN_RE = re.compile(
    rf"{PIN_HEAD}(?:(?:\w+={PIN_WORD}[ \t]+)*PANDOC_VERSION={PIN_WORD}(?:[ \t]+\w+={PIN_WORD})*"
    rf"|(?:export|readonly|declare|typeset)(?:[ \t]+[-+]\w+)*(?:[ \t]+\w+(?:={PIN_WORD})?)*?"
    rf"[ \t]+PANDOC_VERSION={PIN_WORD}(?:[ \t]+\w+(?:={PIN_WORD})?)*){PIN_TAIL}", re.M)
# `local` is valid only in a function, where the pin reaches what the function
# runs, and only if it is called: not judged.
PIN_LOCAL_RE = re.compile(rf"{PIN_HEAD}local(?:[ \t]+[-+]\w+)*(?:[ \t]+\w+(?:={PIN_WORD})?)*?[ \t]+PANDOC_VERSION=",
                          re.M)
# Where an assignment would run out of this reader's sight.
OPAQUE_SHELL_RE = re.compile(r"\$\(|`|\beval\b|\b(?:ba|da|k|z)?sh\s+(?:-\w+\s+)*-\w*c\b")
# A here-document's operator; `<<<` is a here-string, one word.
HEREDOC_RE = re.compile(r"(?<!<)<<(-?)(?!<)[ \t]*")
# Its delimiter: one shell word, quoted in part or whole (`'END-PIN'`, `EOF.x`, `\\EOF`).
HEREDOC_WORD_RE = re.compile(r"(?:'[^']*'|\"(?:[^\"\\]|\\.)*\"|\\.|[^\s;&|<>()'\"\\])+")
# `(( … ))` arithmetic, where `<<` is a shift (the mask already blanks `$(( … ))`).
ARITHMETIC_RE = re.compile(r"\(\((?:[^()]|\([^()]*\))*\)\)")
# The mask's tokens: operators, parentheses, redirections and words.
SHELL_TOKEN_RE = re.compile(r"\n|;;&|;;|;&|;|&&|\|\||\|&|\||&|\(|\)|[<>]+&?|[^\s;&|()<>]+")
SHELL_SEPARATORS = {"\n", ";", "&&", "||", "|", "|&", "&", ";;", ";&", ";;&"}
# Reserved words that open a compound command, and the word that closes it.
SHELL_CLOSERS = {"if": "fi", "while": "done", "until": "done", "for": "done", "select": "done",
                 "case": "esac", "{": "}"}
# Words after which the next word still starts a command.
SHELL_PREFIXES = {"then", "do", "else", "elif", "!", "time"}


@dataclass(eq=False)
class Frame:
    """A compound command in a Shell mask: `(…)`, `{…}`, `if…fi`, a loop or
    `case…esac`, spanning [start, end). `piped` when it is a pipeline stage
    or backgrounded, so a subshell; `function` when it is a function's body."""

    kind: str
    start: int
    end: int = -1
    piped: bool = False
    function: bool = False
    case_state: str = ""


def shell_frames(mask: str) -> list[Frame]:
    """Each compound command in a Shell mask (here-documents blanked), read
    as sh reads it: reserved words count only at a command's start, a case
    pattern's `)` closes nothing, `(( … ))` and `[[ … ]]` open nothing, and
    `name ()` or `function name` makes the next compound command a function
    body. A frame left open runs to the end."""
    frames: list[Frame] = []
    stack: list[Frame] = []
    ended: list[Frame] = []
    tokens = list(SHELL_TOKEN_RE.finditer(mask))
    start, function_next, last = True, False, "\n"
    k = 0

    def open_frame(kind: str, at: int) -> None:
        nonlocal function_next
        frame = Frame(kind, at, piped=last in ("|", "|&"), function=function_next,
                      case_state="subject" if kind == "case" else "")
        function_next = False
        frames.append(frame)
        stack.append(frame)

    def close_frame(at: int) -> None:
        nonlocal ended
        frame = stack.pop()
        frame.end = at
        ended = [frame]

    while k < len(tokens):
        m = tokens[k]
        tok = m.group(0)
        k += 1
        top = stack[-1] if stack else None
        if top is not None and top.case_state in ("subject", "pattern"):
            if top.case_state == "subject" and tok == "in":
                top.case_state = "pattern"
            elif top.case_state == "pattern" and tok == ")":
                top.case_state, start = "body", True
            elif top.case_state == "pattern" and tok == "esac":
                close_frame(m.end())
                start = False
            last = tok
            continue
        if tok in SHELL_SEPARATORS:
            if tok in ("|", "|&", "&"):
                for frame in ended:
                    frame.piped = True
            ended = []
            if top is not None and top.kind == "case" and tok in (";;", ";&", ";;&"):
                top.case_state = "pattern"
            start, last = True, tok
            continue
        if tok == "(":
            nxt = tokens[k] if k < len(tokens) else None
            if mask.startswith("((", m.start()) and (start or last == "for"):
                arithmetic = ARITHMETIC_RE.match(mask, m.start())
                stop = arithmetic.end() if arithmetic else len(mask)
                while k < len(tokens) and tokens[k].start() < stop:
                    k += 1
                start, last = False, "))"
                continue
            if not start and nxt is not None and nxt.group(0) == ")":
                k += 1
                function_next, start, last = True, True, ")"
                continue
            open_frame("(", m.start())
            start, last = True, tok
            continue
        if tok == ")":
            if top is not None and top.kind == "(":
                close_frame(m.end())
            start, last = False, tok
            continue
        if start and tok in SHELL_CLOSERS:
            open_frame(tok, m.start())
            start = tok == "{"
        elif start and top is not None and tok == SHELL_CLOSERS.get(top.kind):
            close_frame(m.end())
            start = False
        elif start and tok == "function":
            k += 1
            function_next, start = True, True
        elif start and tok == "[[":
            while k < len(tokens) and tokens[k].group(0) != "]]":
                k += 1
            k += 1
            start = False
        else:
            start = start and (tok in SHELL_PREFIXES or tok in ("if", "while", "until"))
        last = tok
    for frame in stack:
        frame.end = len(mask)
    return frames


def without_heredocs(shell: Shell) -> str:
    """The mask with each here-document's body blanked, its delimiter line
    included: its lines are data. The bodies follow the line that opens
    them, in order; `<<-` lets the delimiter line lead with tabs. The
    delimiter is a shell word with its quotes removed; a `<<` inside
    `(( … ))` is a shift, no here-document."""
    mask, pending, pos = list(shell.mask), [], 0
    for line in shell.text.split("\n"):
        end = pos + len(line)
        if pending:
            delimiter, dash = pending[0]
            mask[pos:end] = " " * len(line)
            if (line.lstrip("\t") if dash else line) == delimiter:
                pending.pop(0)
        else:
            for m in HEREDOC_RE.finditer(shell.mask, pos, end):
                if any(a.start() <= m.start() < a.end() for a in ARITHMETIC_RE.finditer(shell.mask, pos, end)):
                    continue
                word = HEREDOC_WORD_RE.match(shell.text, m.end(), end)
                if word:
                    pending.append((re.sub(r"\\(.)|['\"]", r"\1", word.group(0)), bool(m.group(1))))
        pos = end + 1
    return "".join(mask)


def pin_assignment(item: str) -> str | None:
    """How a script item supplies PANDOC_VERSION: "assigns" when sh runs an
    assignment of it that the commands after it see (PIN_ASSIGN_RE, outside
    any subshell, pipeline stage or function), "opaque" when one may run
    where this reader cannot see (in a function's body, which runs only if
    called, under `local`, eval, sh -c, `$(...)` or backticks), else None:
    the name in a comment, an echoed string, a word or a here-document
    assigns nothing, and neither does an assignment in a subshell, in a
    compound command that is a pipeline stage or backgrounded, or in a
    command's prefix."""
    shell = Shell(item)
    mask = without_heredocs(shell)
    frames = shell_frames(mask)
    opaque = False
    for m in PIN_ASSIGN_RE.finditer(mask):
        around = [frame for frame in frames if frame.start <= m.end() - 1 < frame.end]
        if any(frame.function for frame in around):
            opaque = True
        elif not any(frame.kind == "(" or frame.piped for frame in around):
            return "assigns"
    if opaque or PIN_LOCAL_RE.search(mask) or ("PANDOC_VERSION=" in shell.text and OPAQUE_SHELL_RE.search(shell.text)):
        return "opaque"
    return None


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
    must also see the pin: a variable it gets (its own or a global one), or an
    assignment in an item of its setup that the commands after it see
    (pin_assignment()): not the name in a comment, an echoed string or a
    here-document, nor an assignment in a subshell, a pipeline stage or a
    command's prefix. An assignment where this reader cannot see (in a
    function's body, or under `eval`, `sh -c` or `$(...)`) is not judged,
    and leaves the run incomplete. A `parallel: matrix` entry is a gap of its
    own: a pin per leg is not one pin.
    """
    matrix = [job.name for job in ci.jobs.values() if any("PANDOC_VERSION" in entry for entry in job.matrix())]
    if matrix:
        report.gap("ci", f"{', '.join(matrix)}: sets PANDOC_VERSION in `parallel: matrix`; record the pin once, in "
                         "`variables:` or the shared setup, so every leg installs the same pandoc")
    unpinned, in_default, unrecorded, candidates = [], [], {}, []
    for job in on_push:
        if not R_JOB_RE.search(job.full_text):
            continue
        setup = job.script(with_default=False)
        commands = "\n".join(strip_comment_lines(item) for item in setup)
        bodies = [body for _, body in inline_scripts(commands, ci.source)]
        tokens = {t for chunk in [commands] + bodies for t in PANDOC_URL_RE.findall(chunk)}
        if not tokens:
            if job.inherits_default_before and any(PANDOC_URL_RE.search(item) for item in ci.default_before()):
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
    if candidates:
        try:
            values = list(dict.fromkeys(value for _, value in pandoc_assignments(ci.text)))
        except ProbeError as error:
            report.skip("ci", f"the pandoc pin was not read, only the install steps (probe failed: {error})", incomplete=True)
    if values and len(values) > 1:
        report.gap("ci", f".gitlab-ci.yml assigns PANDOC_VERSION more than once, with different values "
                         f"({', '.join(values)}); keep one pin, as check-toolchain.R requires")
    never, unseen, opaque, other, unverified = [], [], [], [], {}
    for job, setup, bodies in candidates:
        if values is not None:
            visible = setup + (ci.default_before() if job.inherits_default_before else [])
            if not values:
                never.append(job.name)
                continue
            supplied = {pin_assignment(item) for item in visible}
            if "PANDOC_VERSION" not in job.all_variables() and "assigns" not in supplied:
                if "opaque" not in supplied:
                    unseen.append(job.name)
                    continue
                opaque.append(job.name)
            if len(values) > 1:
                continue
            if values[0] != PANDOC_PIN:
                other.append(job.name)
                continue
        state = max([pandoc_install_state(setup)] + [pandoc_install_state([body]) for body in bodies],
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
    if opaque:
        report.skip("ci", f"{', '.join(opaque)}: whether the setup assigns PANDOC_VERSION is not judged (an "
                          "assignment in a function's body, or under eval, sh -c, `$(...)` or backticks)",
                    incomplete=True)
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
        report.skip("badges", "CRAN status unknown, so the CRAN slots and the order are not judged", incomplete=False)
        return None
    order = [1, 2, 3, 4] if state.on_cran else [4]
    order += [5, 6, 7]
    if state.has_release is None:
        report.skip("badges", "GitLab Release state unknown; slot 8 (latest release) not judged", incomplete=False)
    elif state.has_release:
        order.append(8)
    order += [9, 10]
    if concept_doi:
        if state.doi_resolves is None:
            report.skip("badges", f"DOI {concept_doi} not resolved (offline or probe failed); slot 11 not judged", incomplete=False)
        elif state.doi_resolves:
            order.append(11)
    order += [12, 13, 14]
    if state.on_cran:
        order.append(15)
    order.append(16)
    if pkg in FOSSA_PACKAGES:
        if state.fossa_project is None:
            report.skip("badges", "FOSSA project state unknown; slot 17 not judged", incomplete=False)
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
        report.skip("badges", "r-universe presence unknown", incomplete=False)
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
            report.skip("badge images", f"network error fetching {url}: {error}", incomplete=True)
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
                report.skip("readme", "Installation: the CRAN command is not judged (CRAN status unknown)", incomplete=False)
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
LOGO_ALT = "hex logo, white on black"


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
    # The bare <img>, or the link-wrapped one usethis::use_logo() writes, which
    # the alt names. Its attributes are read as a browser reads them
    # (tag_attrs), not by pattern, and the alt with its whitespace collapsed.
    img = r"<img\s[^>]*>"
    m = title and re.fullmatch(rf"{re.escape(pkg)}\s+(?:({img})|<a\s[^>]*>\s*({img})\s*</a>)", title)
    attrs = tag_attrs(m.group(1) or m.group(2)) if m else {}
    alt = " ".join((attrs.get("alt") or "").split())
    # Each of these replaces or hides the alt as the image's name.
    overriding = [name for name in ("aria-label", "aria-labelledby", "aria-hidden", "role") if name in attrs]
    if attrs.get("src") != "man/figures/logo.png":
        report.gap("logo", f'README.Rmd: the first heading is not "# {pkg}" with the man/figures/logo.png <img>')
    elif alt != LOGO_ALT:
        found = "no alt" if "alt" not in attrs else f"alt={alt!r}"
        report.gap("logo", f'README.Rmd: the logo <img> lacks alt="{LOGO_ALT}" ({found})')
    elif overriding:
        report.gap("logo", f"README.Rmd: the logo <img>'s {', '.join(overriding)} replaces or hides its alt")


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
        report.skip("description", "URL: the CRAN entry is not judged (CRAN status unknown)", incomplete=False)
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


def switched_off(variables: dict[str, object], name: str) -> bool:
    """Whether a variable the job gets turns an R check setting off, as R reads it (R_FALSE)."""
    return name in variables and gitlab_str(variables[name]).lower() in R_FALSE


def coverage_format(job: Job) -> object:
    """`artifacts: reports: coverage_report: coverage_format`, or None."""
    node: object = job.config
    for key in ("artifacts", "reports", "coverage_report", "coverage_format"):
        node = node.get(key) if isinstance(node, dict) else None
    return node


def sanitizer_flags(job: Job) -> bool:
    """ASAN and UBSAN switched on in the job's commands, the scripts they run or its variables."""
    text = job.full_text
    return bool(re.search(r"fsanitize=address|\bASAN\b", text)
                and re.search(r"fsanitize=[\w,]*undefined|\bUBSAN\b", text))


def check_audit_files(source, report: Report) -> None:
    tree = source.tree()
    missing = [p for p in AUDIT_TEST_FILES if p not in tree]
    if missing:
        report.gap("ci", f"audit jobs lack seor's disposition-row shape: missing {', '.join(missing)}")


def check_ci(pkg: str, source, state: State, floor: str | None, report: Report) -> None:
    text = source.read(".gitlab-ci.yml")
    if text is None:
        report.gap("ci", "no .gitlab-ci.yml")
        return
    ci = CI(text, source)
    if ci.error:
        report.skip("ci", f"could not read .gitlab-ci.yml ({ci.error}), so none of its CI rules is judged: R CMD "
                          "check, CRAN incoming, coverage, pages, the pandoc pin, the gates, the deep-check and "
                          "sanitizer legs, the audit jobs and FOSSA", incomplete=True)
        check_audit_files(source, report)
        return
    try:
        for job in ci.jobs.values():
            job.view  # noqa: B018 - read every job's scripts now, where a failed read can be reported
    except ProbeError as error:
        report.skip("ci", f"could not read a script the CI jobs run ({error}), so none of the CI rules is judged",
                    incomplete=True)
        check_audit_files(source, report)
        return
    if not ci.admitted("push"):
        report.gap("ci", "workflow: rules admit no push to main")
    on_push = [j for j in ci.jobs.values() if j.runs["push"]]

    checks = [j for j in on_push if CHECK_RE.search(j.full_text)]
    if not checks:
        report.gap("ci", "no R CMD check runs on a push to main")
    else:
        if not any(AS_CRAN_RE.search(j.full_text) for j in checks):
            report.gap("ci", f"R CMD check on push ({', '.join(j.name for j in checks)}) does not use --as-cran")
        if not any(ERROR_ON_RE.search(j.full_text) for j in checks):
            report.gap("ci", "R CMD check on push is not rcmdcheck with error_on = \"warning\"")
    for job in ci.jobs.values():
        body = job.full_text
        variables = job.all_variables()
        if pkg != "seor" and (INCOMING_OFF_RE.search(body) or switched_off(variables, "_R_CHECK_CRAN_INCOMING_")):
            report.gap("ci", f"{job.name}: turns CRAN incoming off (only seor may, ADR 0004)")
        if pkg not in ("seor", "pslr") and (INCOMING_REMOTE_OFF_RE.search(body)
                                            or switched_off(variables, "_R_CHECK_CRAN_INCOMING_REMOTE_")):
            report.gap("ci", f"{job.name}: turns remote CRAN incoming off (only pslr is grandfathered, ADR 0004)")

    coverage = [j for j in on_push if j.config.get("coverage")]
    if not coverage:
        report.gap("ci", "no coverage job with a coverage: regex runs on a push to main")
    for job in coverage:
        if coverage_format(job) != "cobertura":
            report.gap("ci", f"{job.name}: no cobertura coverage_report artifact")
        if job.config.get("allow_failure") is True:
            report.gap("ci", f"{job.name}: allow_failure: true, so coverage cannot fail the pipeline")
        thresholds = coverage_thresholds(job.full_text)
        if not thresholds:
            report.gap("ci", f"{job.name}: no {COVERAGE_MIN:g}% coverage threshold")
        elif min(thresholds) < COVERAGE_MIN:
            report.gap("ci", f"{job.name}: coverage threshold {min(thresholds):g} is below {COVERAGE_MIN:g}")
    # The coverage badge reads the latest successful pipeline on main, schedules included.
    if coverage:
        for kind in SCHEDULE_KINDS:
            if not any(j.runs[kind] for j in coverage):
                report.gap("ci", f"coverage job does not run on the {kind} schedule")

    if not any(j.name == "pages" or j.config.get("pages") is True or isinstance(j.config.get("pages"), dict)
               for j in on_push):
        report.gap("ci", "pages does not deploy on a push to main")

    check_pandoc_pin(on_push, ci, report)

    chunks = [chunk for j in on_push for chunk in j.view]
    for gate, patterns in GATES.items():
        if not any(all(p.search(chunk) for p in patterns) for chunk in chunks):
            report.gap("ci", f"no {gate} gate runs on a push to main")

    legs = [j for j in ci.jobs.values()
            if j.runs["deep-check"] and not j.runs["push"] and not j.runs["dependency-audit"]]
    roles: set[str] = set()
    for job in legs:
        if CHECK_RE.search(job.full_text):
            for image in ci.images(job):
                if not SANITIZER_IMAGE_RE.search(image):
                    roles |= leg_roles(image, state, floor)
    if state.r_release is None:
        report.skip("ci", "current R release/oldrel unknown; numeric deep-check legs judged for the floor only", incomplete=False)
    for leg in ("release", "oldrel", "devel"):
        if leg not in roles:
            report.gap("ci", f"no deep-check leg for R {leg}")
    if floor and "floor" not in roles:
        report.gap("ci", f"no deep-check leg at the declared R floor ({floor})")
    if pkg in SANITIZER_PACKAGES:
        sanitized = [j for j in legs if any(SANITIZER_IMAGE_RE.search(i) for i in ci.images(j)) or sanitizer_flags(j)]
        if not sanitized:
            report.gap("ci", "no ASAN/UBSAN sanitizer leg on the deep-check schedule")

    for name in ("osv-audit", "security-audit"):
        job = ci.jobs.get(name)
        if job is None:
            report.gap("ci", f"no {name} job")
        elif not job.runs["dependency-audit"] or job.runs["push"] or job.runs["deep-check"]:
            report.gap("ci", f"{name} does not run only on the dependency-audit schedule")
    check_audit_files(source, report)

    if pkg in FOSSA_PACKAGES and not any(re.search(r"\bfossa analyze\b", j.full_text) for j in ci.jobs.values()):
        report.gap("ci", "no fossa analyze job")


def check_local_gate(source, report: Report) -> None:
    text = source.read(".pre-commit-config.yaml")
    if text is None:
        report.gap("local gate", "no .pre-commit-config.yaml")
        return
    body = strip_comment_lines(text)
    # R and shell only: a Python script that merely names check_url_db (this
    # one, check-bugreports.py's docstring) runs no URL check.
    try:
        named = [(path, s) for path, s in inline_scripts(body, source, depth=3)
                 if Path(path).suffix in ("", ".R", ".r", ".sh")]
    except ProbeError as error:
        report.skip("local gate", f"could not read a script the pre-push gate runs ({error})", incomplete=True)
        return
    scripts = [s for _, s in named]
    if not any(URL_CHECK_RE.search(chunk) for chunk in [body] + scripts):
        report.gap("local gate", "no URL check in the pre-push gate")
    chunks = [body] + scripts
    if not (any(DOCS_DRIFT_RE.search(chunk) for chunk in chunks)
            and any(DOCS_EXPORT_RE.search(chunk) for chunk in chunks)):
        report.gap("local gate", "no generated-docs drift check in the pre-push gate: roxygen2 run on a `git archive` "
                                 "export of the pushed commit, failing when man/, NAMESPACE or DESCRIPTION differ")

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
        report.skip("schedules", "pipeline schedules not read", incomplete=False)
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
        report.skip(area, f"probe failed: {error}", incomplete=True)
    images = check_badges(pkg, source, state, report)
    if fetch is None:
        report.skip("badge images", "not fetched (--offline)", incomplete=False)
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
        report.skip("source", f"could not read the repository: {error}", incomplete=True)
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
    - |
      Rscript -e 'cov <- covr::package_coverage(); covr::to_cobertura(cov); pct <- covr::percent_coverage(cov); cat(sprintf("Coverage: %.2f%%\\n", pct)); if (pct < 95) quit(status = 1)'
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
    return f'# {pkg} <img src="man/figures/logo.png" align="right" height="139" alt="{LOGO_ALT}" />'


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
        "tools/verify.R": "db <- tools:::url_db_from_package_sources('.')\nbad <- tools:::check_url_db(db)\n"
                          "system2(\"git\", c(\"archive\", \"-o\", tarball, ref))\nroxygen2::roxygenise(export)\n",
        "scripts/check-toolchain.R": FIXTURE_TOOLCHAIN_R,
        "scripts/check-citation.py": "print('ok')\n",
        ".gitlab/issue_templates/Bug.md": "x\n",
        ".gitlab/merge_request_templates/Default.md": "x\n",
    })
    files.update({path: "x\n" for path in LOGO_FILES})
    # The keywords logo-metadata.py writes from the DESCRIPTION above, spelled
    # out rather than built here, in its two bags (the RDF block's and the XMP
    # packet's).
    subject = ("<dc:subject><rdf:Bag><rdf:li>R</rdf:li><rdf:li>rstats</rdf:li><rdf:li>R package</rdf:li>"
               "<rdf:li>punycode</rdf:li><rdf:li>idna</rdf:li><rdf:li>idn</rdf:li><rdf:li>unicode</rdf:li>"
               "<rdf:li>domain-names</rdf:li></rdf:Bag></dc:subject>")
    files["man/figures/logo.svg"] = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">\n<metadata>\n'
        f"<rdf:RDF><cc:Work>\n{subject}\n</cc:Work></rdf:RDF>\n"
        f'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF><rdf:Description>\n{subject}\n'
        "</rdf:Description></rdf:RDF></x:xmpmeta>\n</metadata>\n<rect width=\"10\" height=\"10\"/>\n</svg>\n"
    )
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

    def loads(tag: str, report: Report) -> None:
        # A fixture GitLab would refuse leaves CI not judged, and a clean
        # report would then prove nothing: only the load-error rows want that.
        if any("could not read .gitlab-ci.yml" in text for _, text in report.unjudged):
            failures.append(f"{tag}: the fixture's .gitlab-ci.yml did not load: {report.unjudged}")

    def expect_clean(tag: str, pkg: str, files: dict, state: State, fetch=None) -> None:
        report = run(pkg, files, state, fetch)
        loads(tag, report)
        if report.gaps:
            failures.append(f"{tag}: expected no gaps, got {report.gaps}")

    def expect_gap(tag: str, needle: str, pkg: str, files: dict, state: State, fetch=None) -> Report:
        report = run(pkg, files, state, fetch)
        loads(tag, report)
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
    # Logo keywords (SEOR-uwpnkqnb): logo.svg's dc:subject bags against the
    # list logo-metadata.py builds from DESCRIPTION's X-schema.org-keywords.
    expect_clean("logo keywords match DESCRIPTION", "punycoder", cran, fixture_state())
    expect_clean("a case-only duplicate tag in DESCRIPTION is not drift", "punycoder",
                 edit(cran, "DESCRIPTION", "domain-names\n", "domain-names, IDNA\n"), fixture_state())
    expect_gap("no level-1 heading", "the first heading is not", "punycoder",
               edit(cran, "README.Rmd", fixture_h1("punycoder") + "\n", ""), fixture_state())
    expect_clean("single-quoted logo src", "punycoder",
                 edit(cran, "README.Rmd", 'src="man/figures/logo.png"', "src='man/figures/logo.png'"), fixture_state())
    expect_clean("the use_logo() link-wrapped heading", "punycoder",
                 edit(cran, "README.Rmd", fixture_h1("punycoder"),
                      '# punycoder <a href="https://bart-turczynski.gitlab.io/punycoder/"><img src="man/figures/logo.png" '
                      f'align="right" height="138" alt="{LOGO_ALT}" /></a>'), fixture_state())
    alt = f' alt="{LOGO_ALT}"'
    expect_gap("logo without alt", f'lacks alt="{LOGO_ALT}" (no alt)', "punycoder",
               edit(cran, "README.Rmd", alt, ""), fixture_state())
    for empty in (' alt=""', " alt"):
        expect_gap(f"logo with {empty.strip()!r}", "(alt='')", "punycoder",
                   edit(cran, "README.Rmd", alt, empty), fixture_state())
    expect_gap("logo alt repeating the package name", "lacks alt=", "punycoder",
               edit(cran, "README.Rmd", alt, f' alt="punycoder {LOGO_ALT}"'), fixture_state())
    expect_gap("logo alt only in data-alt", "lacks alt=", "punycoder",
               edit(cran, "README.Rmd", alt, f' data-alt="{LOGO_ALT}"'), fixture_state())
    expect_gap("alt text only inside another attribute", "lacks alt=", "punycoder",
               edit(cran, "README.Rmd", alt, " title='x" + alt + "'"), fixture_state())
    expect_gap("an empty alt ahead of the right one", "lacks alt=", "punycoder",
               edit(cran, "README.Rmd", alt, ' alt=""' + alt), fixture_state())
    for extra in (' aria-label="punycoder"', ' aria-hidden="true"', ' role="presentation"'):
        expect_gap(f"the right alt with {extra.strip()}", "replaces or hides its alt", "punycoder",
                   edit(cran, "README.Rmd", alt, alt + extra), fixture_state())
    for spelling in (f' alt = "{LOGO_ALT}"', f' ALT="{LOGO_ALT}"', ' alt="hex logo&#44; white on black"',
                     f" alt='{LOGO_ALT}'", ' alt=" hex logo,  white on black "'):
        expect_clean(f"alt spelled {spelling.strip()!r}", "punycoder",
                     edit(cran, "README.Rmd", alt, spelling), fixture_state())
    expect_clean("a title beside the alt", "punycoder",
                 edit(cran, "README.Rmd", alt, alt + ' title="punycoder"'), fixture_state())
    expect_clean("alt ahead of src", "punycoder",
                 edit(cran, "README.Rmd", fixture_h1("punycoder"),
                      f"# punycoder <img alt='{LOGO_ALT}' src=\"man/figures/logo.png\" />"),
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
        # Quoted: unquoted, `- ! cmd` is YAML's non-specific tag and the item is `cmd`.
        ("negated check", (f"    - {dl_cmd}\n", f"    - '! {check_cmd}'\n", install_line)),
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

    # The CI reader's case table (SEOR-oznwzhem). Every expected value is what
    # GitLab makes of the YAML, written down from the YAML 1.1 spec and GitLab's
    # documented semantics (`extends` deep-merges mappings and replaces arrays,
    # `default:` fills only the keys a job leaves unset, script lists flatten),
    # never what an earlier reader printed. First the reader itself, then the
    # same cases end to end.
    def ci_of(text: str) -> CI:
        return CI(text, DictSource({ci: text}))

    def config_of(c: CI, name: str) -> dict:
        return c.jobs[name].config

    deep_merge_ci = (
        ".base:\n  image:\n    name: rocker/r-ver:4.5.3\n  variables: {A: \"1\", B: \"1\"}\n"
        "  artifacts:\n    reports:\n      coverage_report:\n        coverage_format: cobertura\n"
        "  script: [echo base]\n  rules:\n    - if: $CI_COMMIT_TAG\n"
        ".mid:\n  extends: .base\n  variables: {B: \"2\"}\n"
        "  artifacts:\n    reports:\n      coverage_report:\n        path: cobertura.xml\n"
        "job:\n  extends: .mid\n  image:\n    entrypoint: [\"\"]\n  variables:\n    C: \"3\"\n"
        "  rules:\n    - when: manual\n")
    default_ci = (
        "default:\n  image: rocker/r-ver:4.6.1\n  before_script: [echo default]\n  artifacts:\n    paths: [a]\n"
        "bare:\n  script: [echo x]\n"
        "own:\n  before_script: [echo own]\n  artifacts:\n    expire_in: 1 week\n  script: [echo y]\n"
        "picky:\n  inherit:\n    default: [image]\n  script: [echo z]\n"
        "none:\n  inherit:\n    default: false\n  script: [echo w]\n")
    reader_cases: tuple[tuple[str, str, Callable[[CI], object], object], ...] = (
        ("extends with a trailing comment keeps its template",
         ".r:\n  image: rocker/r-ver:4.6.1\n  script:\n    - Rscript -e 'rcmdcheck::rcmdcheck()'\n"
         "check:\n  extends: .r  # template\n",
         lambda c: (config_of(c, "check").get("image"), c.jobs["check"].script()),
         ("rocker/r-ver:4.6.1", ["Rscript -e 'rcmdcheck::rcmdcheck()'"])),
        ("when with a trailing comment runs on push", "job:\n  script: [x]\n  when: on_success # explicit\n",
         lambda c: c.jobs["job"].runs["push"], True),
        ("a quoted image with a trailing comment", "job:\n  image: \"rocker/r-ver:4.5\" # newer\n  script: [x]\n",
         lambda c: c.images(c.jobs["job"]), ["rocker/r-ver:4.5"]),
        ("allow_failure with a trailing comment is the boolean",
         "job:\n  script: [x]\n  allow_failure: true # soft for now\n",
         lambda c: config_of(c, "job").get("allow_failure"), True),
        ("YAML 1.1: an unquoted 3.10 is the float 3.1",
         "variables:\n  A: 3.10\n  B: \"3.10\"\njob:\n  script: [x]\n  variables:\n    C: 4.10\n",
         lambda c: (c.global_vars, c.jobs["job"].variables, c.env("push")["A"]),
         ({"A": 3.1, "B": "3.10"}, {"C": 4.1}, "3.1")),
        ("YAML 1.1 booleans, and the string GitLab hands the job",
         "variables:\n  A: true\n  B: \"true\"\n  C: yes\n  D: off\n  E: False\njob:\n  script: [x]\n",
         lambda c: (c.global_vars, [c.env("push")[k] for k in "ABCDE"]),
         ({"A": True, "B": "true", "C": True, "D": False, "E": False}, ["true", "true", "true", "false", "false"])),
        ("flow and block lists, `- |` and `- >`",
         "job:\n  before_script: [echo a, \"echo b\", 'echo ''c''']\n  script:\n    - |\n      line one\n      line two\n"
         "    - >\n      folded one\n      folded two\n    - plain\n      continued\n    - \"quoted # not a comment\"\n",
         lambda c: c.jobs["job"].script(),
         ["echo a", "echo b", "echo 'c'", "line one\nline two\n", "folded one folded two\n", "plain continued",
          "quoted # not a comment"]),
        ("a script given as one string", "job:\n  script: Rscript -e 'x'  # one item\n",
         lambda c: c.jobs["job"].script(), ["Rscript -e 'x'"]),
        ("`- ! cmd` is YAML's non-specific tag, not a negation", "job:\n  script:\n    - ! sha256sum -c x\n    - '! true'\n",
         lambda c: c.jobs["job"].script(), ["sha256sum -c x", "! true"]),
        ("an anchored `- &name |` item reused in a job's own list",
         ".r:\n  before_script:\n    - &pandoc |\n      echo install\n    - echo other\n"
         "check:\n  extends: .r\n  before_script:\n    - echo own\n    - *pandoc\n  script: [echo run]\n",
         lambda c: c.jobs["check"].script(), ["echo own", "echo install\n", "echo run"]),
        ("nested script lists flatten, aliases included",
         ".deps: &deps\n  - echo one\n  - echo two\njob:\n  script:\n    - *deps\n    - echo three\n"
         "    - [echo four, [echo five]]\n",
         lambda c: c.jobs["job"].script(), ["echo one", "echo two", "echo three", "echo four", "echo five"]),
        ("YAML merge keys come from YAML",
         ".tpl: &tpl\n  image: rocker/r-ver:4.5.3\n  script: [echo tpl]\njob:\n  <<: *tpl\n  script: [echo own]\n",
         lambda c: (config_of(c, "job").get("image"), c.jobs["job"].script()), ("rocker/r-ver:4.5.3", ["echo own"])),
        ("nested extends deep-merges mappings and replaces arrays", deep_merge_ci,
         lambda c: (config_of(c, "job").get("image"), c.jobs["job"].variables, config_of(c, "job").get("artifacts"),
                    c.jobs["job"].script(), config_of(c, "job").get("rules")),
         ({"name": "rocker/r-ver:4.5.3", "entrypoint": [""]}, {"A": "1", "B": "2", "C": "3"},
          {"reports": {"coverage_report": {"coverage_format": "cobertura", "path": "cobertura.xml"}}},
          ["echo base"], [{"when": "manual"}])),
        ("several parents: the later one wins, mappings still merge",
         ".a:\n  script: [a]\n  variables: {X: a, Y: a}\n.b:\n  script: [b]\n  variables: {Y: b}\njob:\n  extends: [.a, .b]\n",
         lambda c: (c.jobs["job"].script(), c.jobs["job"].variables), (["b"], {"X": "a", "Y": "b"})),
        ("a job overrides its parent's script",
         ".tpl:\n  script:\n    - R CMD check --as-cran x.tar.gz\njob:\n  extends: .tpl\n  script:\n    - echo skipped\n",
         lambda c: (c.jobs["job"].script(), [chunk for chunk in c.jobs["job"].view if "R CMD check" in chunk]),
         (["echo skipped"], [])),
        ("default: fills only the keys a job leaves unset", default_ci,
         lambda c: [(config_of(c, n).get("image"), config_of(c, n).get("artifacts"), c.jobs[n].script())
                    for n in ("bare", "own", "picky", "none")],
         [("rocker/r-ver:4.6.1", {"paths": ["a"]}, ["echo default", "echo x"]),
          ("rocker/r-ver:4.6.1", {"expire_in": "1 week"}, ["echo own", "echo y"]),
          ("rocker/r-ver:4.6.1", None, ["echo z"]),
          (None, None, ["echo w"])]),
        ("an unknown tag is a load error", "job:\n  script:\n    - !reference [.r, script]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("a syntax error is a load error", "job:\n  script: [x\n", lambda c: (bool(c.error), c.jobs), (True, {})),
        ("extends naming no block is a load error", "job:\n  extends: .missing\n  script: [x]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        # Every failure to load fails closed: PyYAML raises a plain ValueError
        # for a scalar its tag cannot hold, and a recursive alias would
        # recurse without end in the resolver.
        ("an impossible date is a load error", "variables: {D: 2026-02-30}\njob:\n  script: [x]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("a scalar its tag cannot hold is a load error", "x: !!int 'abc'\njob:\n  script: [x]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("a recursive alias in a script is a load error", "a: &a [*a]\njob:\n  script: *a\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("a recursive alias along extends is a load error", ".t: &t {v: *t}\njob: {extends: .t, v: *t, script: [x]}\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        # A `rules:if` that does not read is a load error, an empty one included.
        ("an empty rules:if is a load error", "job:\n  script: [x]\n  rules:\n    - if:\n      when: always\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("an empty workflow rules:if is a load error", "workflow:\n  rules:\n    - if: ''\njob:\n  script: [x]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("a rules:if cut short is a load error", "job:\n  script: [x]\n  rules:\n    - if: $A ==\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("words left over in a rules:if are a load error", "job:\n  script: [x]\n  rules:\n    - if: $A $B\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        # A job's rules see its own variables over the global ones `inherit:` lets through.
        ("a job's rules see its own variables and the global ones it inherits",
         "variables: {G: \"on\", H: \"on\"}\n"
         "own:\n  variables: {RUN: \"yes\"}\n  rules:\n    - if: $RUN == \"yes\"\n  script: [x]\n"
         "over:\n  variables: {G: \"off\"}\n  rules:\n    - if: $G == \"on\"\n  script: [x]\n"
         "barred:\n  inherit: {variables: false}\n  rules:\n    - if: $G == \"on\"\n  script: [x]\n"
         "picky:\n  inherit: {variables: [G]}\n  rules:\n    - if: $G == \"on\"\n  script: [x]\n"
         "left:\n  inherit: {variables: [G]}\n  rules:\n    - if: $H == \"on\"\n  script: [x]\n",
         lambda c: [c.jobs[n].runs["push"] for n in ("own", "over", "barred", "picky", "left")],
         [True, False, False, True, False]),
        # One config document, after at most a `spec:` header (an include's inputs).
        ("a trailing `---` adds no document", "job:\n  script: [x]\n---\n",
         lambda c: (c.error, c.jobs["job"].script()), (None, ["x"])),
        # A pattern held in a variable, slashes included, is a pattern; one that
        # holds no /regex/ does not read.
        ("`=~ $VAR` matches the /regex/ the variable holds",
         "variables: {MAIN_RE: /^ma.n$/, CASE_RE: /^MAIN$/i}\n"
         "a:\n  script: [x]\n  rules: [{if: $CI_COMMIT_BRANCH =~ $MAIN_RE}]\n"
         "b:\n  script: [x]\n  rules:\n    - if: $CI_COMMIT_BRANCH !~ ${MAIN_RE}\n"
         "c:\n  script: [x]\n  rules: [{if: $CI_COMMIT_BRANCH =~ $CASE_RE}]\n",
         lambda c: (c.error, [c.jobs[n].runs["push"] for n in "abc"]), (None, [True, False, True])),
        ("`=~ $VAR` with no /regex/ in it does not read",
         "variables: {PLAIN: main}\njob:\n  script: [x]\n  rules: [{if: $CI_COMMIT_BRANCH =~ $PLAIN}]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("a `spec:` header document, then the config",
         "spec:\n  inputs:\n    stage:\n      default: check\n---\njob:\n  script: [x]\n",
         lambda c: (c.error, c.jobs["job"].script()), (None, ["x"])),
        ("two config documents are a load error", "a:\n  script: [x]\n---\njob:\n  script: [x]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("a header holding more than `spec:` is a load error", "spec: {inputs: {}}\nstages: [x]\n---\njob:\n  script: [x]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        ("two documents after a `spec:` header are a load error", "spec: {}\n---\na: 1\n---\njob:\n  script: [x]\n",
         lambda c: (bool(c.error), c.jobs), (True, {})),
        # The text rules' view holds the variables a job's commands read, once,
        # beside its items: not one nothing reads, and one another one's value reads.
        ("the text view holds the job's script items, then the variables they read",
         "variables: {G: \"1\"}\njob:\n  variables: {ARGS: --as-cran}\n  script: [R CMD check $ARGS x.tar.gz]\n",
         lambda c: list(c.jobs["job"].view), ["R CMD check $ARGS x.tar.gz\nARGS=--as-cran"]),
        ("a variable read through another one's value is in the text view",
         "variables: {B: --as-cran, C: x}\njob:\n  variables: {A: \"${B} -v\"}\n  script: [R CMD check $A x.tar.gz]\n",
         lambda c: list(c.jobs["job"].view), ["R CMD check $A x.tar.gz\nB=--as-cran\nA=${B} -v"]),
    )
    if collect is None:
        for tag, text, probe, want in reader_cases:
            try:
                got = probe(ci_of(text))
            except Exception as error:  # noqa: BLE001 - a reader that raises fails the row
                got = f"raised {type(error).__name__}: {error}"
            if got != want:
                failures.append(f"reader: {tag}: expected {want!r}, got {got!r}")

    check_tpl = edit(cran, ci, "check:\n  extends: [.r, .on-main]\n  script:\n",
                     ".check-tpl:\n  extends: [.r, .on-main]\n  script:\n")
    expect_clean("reader e2e: extends with a trailing comment", "punycoder",
                 edit(check_tpl, ci, "coverage:\n  extends", "check:\n  extends: .check-tpl  # template\ncoverage:\n  extends"),
                 fixture_state())
    expect_gap("reader e2e: a job overrides its parent's script", "no R CMD check runs on a push to main", "punycoder",
               edit(check_tpl, ci, "coverage:\n  extends",
                    "check:\n  extends: .check-tpl\n  script:\n    - echo skipped\ncoverage:\n  extends"), fixture_state())
    expect_clean("reader e2e: when with a trailing comment", "punycoder",
                 edit(cran, ci, "pages:\n  extends: [.r, .on-main]\n",
                      "pages:\n  extends: .r\n  rules:\n    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH\n"
                      "      when: on_success # explicit\n"), fixture_state())
    rcmdcheck_item = "  script:\n    - Rscript -e 'rcmdcheck::rcmdcheck(args = \"--as-cran\", error_on = \"warning\")'\n"
    no_oldrel = edit(cran, ci, '"4.6.1", "4.5.3", "devel"', '"4.6.1", "devel"')
    expect_clean("reader e2e: a quoted image with a trailing comment", "punycoder",
                 edit(no_oldrel, ci, "sanitizers:\n", "\"check:oldrel\":\n  extends: .deep\n"
                      "  image: \"rocker/r-ver:4.5.3\" # oldrel\n" + rcmdcheck_item + "sanitizers:\n"), fixture_state())
    expect_clean("reader e2e: an image mapping deep-merged along extends", "punycoder",
                 edit(no_oldrel, ci, "sanitizers:\n", ".oldrel-image:\n  image:\n    name: \"rocker/r-ver:4.5.3\"\n"
                      "\"check:oldrel\":\n  extends: [.deep, .oldrel-image]\n  image:\n    entrypoint: [\"\"]\n"
                      + rcmdcheck_item + "sanitizers:\n"), fixture_state())
    expect_gap("reader e2e: allow_failure with a trailing comment", "coverage: allow_failure: true", "punycoder",
               edit(cran, ci, "coverage:\n  extends: [.r, .on-main]\n",
                    "coverage:\n  extends: [.r, .on-main]\n  allow_failure: true # soft for now\n"), fixture_state())
    no_floor = edit(cran, ci, ', "4.1.3"]', "]")
    floor_job = "floor:\n  extends: .deep\n  image: rocker/r-ver:$R_FLOOR\n  variables:\n    R_FLOOR: {}\n" + rcmdcheck_item
    expect_clean("reader e2e: an unquoted 4.10 is R 4.1", "punycoder",
                 edit(no_floor, ci, "sanitizers:\n", floor_job.format("4.10") + "sanitizers:\n"), fixture_state())
    expect_gap("reader e2e: a quoted \"4.10\" is not R 4.1", "no deep-check leg at the declared R floor (4.1)", "punycoder",
               edit(no_floor, ci, "sanitizers:\n", floor_job.format('"4.10"') + "sanitizers:\n"), fixture_state())
    expect_gap("reader e2e: incoming off as a boolean job variable", "check: turns CRAN incoming off", "punycoder",
               edit(cran, ci, "check:\n  extends: [.r, .on-main]\n",
                    "check:\n  extends: [.r, .on-main]\n  variables:\n    _R_CHECK_CRAN_INCOMING_: false\n"), fixture_state())
    expect_gap("reader e2e: incoming off as a global variable", "check: turns CRAN incoming off", "punycoder",
               edit(cran, ci, "variables:\n", "variables:\n  _R_CHECK_CRAN_INCOMING_: \"FALSE\"\n"), fixture_state())
    # R lower-cases a check setting: "false", "no" and "0" are off, in any case.
    for value in ('"no"', '"False"', "'NO'"):
        expect_gap(f"reader e2e: incoming off as {value}", "check: turns CRAN incoming off", "punycoder",
                   edit(cran, ci, "check:\n  extends: [.r, .on-main]\n",
                        f"check:\n  extends: [.r, .on-main]\n  variables:\n    _R_CHECK_CRAN_INCOMING_: {value}\n"),
                   fixture_state())
    expect_gap("reader e2e: remote incoming off as \"No\"", "check: turns remote CRAN incoming off", "punycoder",
               edit(cran, ci, "check:\n  extends: [.r, .on-main]\n",
                    "check:\n  extends: [.r, .on-main]\n  variables:\n    _R_CHECK_CRAN_INCOMING_REMOTE_: \"No\"\n"),
               fixture_state())
    expect_gap("incoming off as \"No\" in the commands", "turns CRAN incoming off", "punycoder",
               edit(cran, ci, 'error_on = "warning")\'\ncoverage',
                    'error_on = "warning", env = c("_R_CHECK_CRAN_INCOMING_" = "No"))\'\ncoverage'), fixture_state())
    # The text rules see the variables a job gets: a flag or a script path its
    # commands take from one counts, and a script a variable names is followed.
    expect_clean("reader e2e: --as-cran from a job variable", "punycoder",
                 edit(edit(cran, ci, 'rcmdcheck(args = "--as-cran", error_on = "warning")\'\ncoverage',
                           'rcmdcheck(args = Sys.getenv("CHECK_ARGS"), error_on = "warning")\'\ncoverage'),
                      ci, "check:\n  extends: [.r, .on-main]\n",
                      "check:\n  extends: [.r, .on-main]\n  variables:\n    CHECK_ARGS: --as-cran\n"), fixture_state())
    expect_clean("reader e2e: error_on from a global variable", "punycoder",
                 edit(edit(cran, ci, "    - Rscript -e 'res <- rcmdcheck::rcmdcheck(args = \"--as-cran\", error_on = \"warning\")'\n",
                           "    - Rscript -e \"res <- rcmdcheck::rcmdcheck(args = '--as-cran', $ERROR_ON)\"\n"),
                      ci, "variables:\n", "variables:\n  ERROR_ON: error_on = \"warning\"\n"), fixture_state())
    expect_clean("reader e2e: the gates script named by a variable", "punycoder",
                 edit(edit(cran, ci, "    - *deps\n    - Rscript tools/gates.R\n", "    - *deps\n    - Rscript $GATES\n"),
                      ci, "gates:\n  extends: [.r, .on-main]\n",
                      "gates:\n  extends: [.r, .on-main]\n  variables:\n    GATES: tools/gates.R\n"), fixture_state())
    # A variable nothing reads is no command: it neither supplies a flag nor
    # makes a job an R job.
    expect_gap("reader e2e: --as-cran only in a variable nothing reads", "does not use --as-cran", "punycoder",
               edit(edit(cran, ci, 'rcmdcheck(args = "--as-cran", error_on = "warning")\'\ncoverage',
                         'rcmdcheck(error_on = "warning")\'\ncoverage'),
                    ci, "variables:\n", "variables:\n  ARGS: --as-cran\n"), fixture_state())
    expect_clean("reader e2e: an R command in a variable nothing reads", "punycoder",
                 edit(cran, ci, "variables:\n", "variables:\n  RUNNER_CMD: Rscript tools/gates.R\n"), fixture_state())
    # A script a job runs that cannot be read leaves CI not judged, never a gap.
    class Unreadable(DictSource):
        def read(self, path: str) -> str | None:
            if path == "tools/gates.R":
                raise ProbeError("reading tools/gates.R: 503")
            return super().read(path)

    if collect is None:
        report = check_repo("punycoder", Unreadable(cran), fixture_state(), None)
        if (any(area == "ci" for area, _ in report.gaps)
                or not any(area == "ci" and "could not read a script" in t for area, t in report.unjudged)
                or exit_status([report]) != 2):
            failures.append(f"reader e2e: an unreadable script a job runs: expected CI not judged and exit 2, got "
                            f"{report.gaps} / {report.unjudged}")
    # A `spec:` header document before the config is valid GitLab.
    expect_clean("reader e2e: a `spec:` header, then the config", "punycoder",
                 dict(cran, **{ci: "spec:\n  inputs:\n    image:\n      default: rocker/r-ver:4.6.1\n---\n" + cran[ci]}),
                 fixture_state())
    cov_artifacts = ("  artifacts:\n    reports:\n      coverage_report:\n        coverage_format: cobertura\n"
                     "        path: cobertura.xml\n")
    in_default_artifacts = edit(edit(cran, ci, cov_artifacts, ""), ci, "default:\n  image: rocker/r-ver:4.6.1\n",
                                "default:\n  image: rocker/r-ver:4.6.1\n" + cov_artifacts)
    expect_clean("reader e2e: default: artifacts reach a job that sets none", "punycoder", in_default_artifacts,
                 fixture_state())
    expect_gap("reader e2e: default: does not merge into a job's own artifacts", "coverage: no cobertura", "punycoder",
               edit(in_default_artifacts, ci, "  coverage: '/Coverage",
                    "  artifacts:\n    paths: [cobertura.xml]\n  coverage: '/Coverage"), fixture_state())
    anchored = edit(cran, ci, pin_lines, seor_shape.replace("    - |\n", "    - &pandoc |\n", 1))
    expect_clean("reader e2e: an anchored install item reused in a job's own before_script", "punycoder",
                 edit(anchored, ci, "check:\n  extends: [.r, .on-main]\n",
                      "check:\n  extends: [.r, .on-main]\n  before_script:\n    - PANDOC_VERSION=3.10\n    - *pandoc\n"),
                 fixture_state())
    # The pin reaches a job through a variable or an assignment sh runs, not a
    # mention; an assignment this reader cannot see into is not judged.
    pin_elsewhere = edit(cran, ci, "    - fossa analyze\n", "    - PANDOC_VERSION=3.10\n    - fossa analyze\n")
    for echoed in ('echo "PANDOC_VERSION=3.10 is set in fossa"', 'echo "set in fossa; PANDOC_VERSION=3.10"',
                   "echo done  # PANDOC_VERSION=3.10"):
        expect_gap(f"reader e2e: the pin only in {echoed!r}", "which neither its variables nor its setup assign",
                   "punycoder", edit(pin_elsewhere, ci, "    - PANDOC_VERSION=3.10\n    - curl",
                                     f"    - {echoed}\n    - curl"), fixture_state())
    # Nor an assignment that ends before the commands after it: in a subshell,
    # a pipeline stage or a here-document's body, or as a command's prefix,
    # which reaches that one command after its words are expanded.
    for form, item in (("a subshell", "    - (PANDOC_VERSION=3.10)\n"),
                       ("a pipeline stage", "    - echo a | PANDOC_VERSION=3.10 true\n"),
                       ("a here-document", "    - |\n      cat <<EOF > /tmp/pin.env\n      PANDOC_VERSION=3.10\n      EOF\n"),
                       ("a command's prefix", "    - PANDOC_VERSION=3.10 curl -fsSL -o /tmp/v https://example.org/$PANDOC_VERSION/v\n"),
                       ("a subshell, after a command", "    - (cd /tmp; PANDOC_VERSION=3.10; true)\n"),
                       ("a subshell's && chain", "    - ( true && PANDOC_VERSION=3.10 && true )\n"),
                       ("a subshell over lines", "    - |\n      (\n      PANDOC_VERSION=3.10\n      )\n"),
                       ("a group that is a pipeline stage", "    - echo a | { PANDOC_VERSION=3.10; }\n"),
                       ("a group piped on", "    - '{ PANDOC_VERSION=3.10; } | cat'\n"),
                       ("a loop that is a pipeline stage", "    - echo a | while read -r x; do PANDOC_VERSION=3.10; done\n"),
                       ("a backgrounded loop", "    - while true; do PANDOC_VERSION=3.10; break; done &\n")):
        expect_gap(f"reader e2e: the pin only in {form}", "which neither its variables nor its setup assign",
                   "punycoder", edit(pin_elsewhere, ci, "    - PANDOC_VERSION=3.10\n    - curl", f"{item}    - curl"),
                   fixture_state())
    # A compound command in the current shell keeps the assignment: a group,
    # a branch, a case clause. A finished subshell, `(( … ))` and a closed
    # here-document leave the commands after them to be read.
    for form, item in (("a group", "    - '{ PANDOC_VERSION=3.10; }'\n"),
                       ("an if branch", "    - if true; then PANDOC_VERSION=3.10; fi\n"),
                       ("a case clause", "    - case x in a|b) PANDOC_VERSION=3.10;; esac\n"),
                       ("a line after a subshell", "    - (cd /tmp; true); PANDOC_VERSION=3.10\n"),
                       ("a line after a shift", "    - |\n      (( n = 1 << 2 ))\n      PANDOC_VERSION=3.10\n"),
                       ("a line after a here-document ended by END-PIN",
                        "    - |\n      cat <<END-PIN > /tmp/x\n      hi\n      END-PIN\n      PANDOC_VERSION=3.10\n"),
                       ("a line after a here-document ended by 'EOF.x'",
                        "    - |\n      cat <<'EOF.x' > /tmp/x\n      hi\n      EOF.x\n      PANDOC_VERSION=3.10\n")):
        expect_clean(f"reader e2e: the pin assigned in {form}", "punycoder",
                     edit(pin_elsewhere, ci, "    - PANDOC_VERSION=3.10\n    - curl", f"{item}    - curl"),
                     fixture_state())
    # The builtins that assign in the current shell count as assignments.
    for spelling in ("readonly PANDOC_VERSION=3.10", "declare -x PANDOC_VERSION=3.10", "typeset -x PANDOC_VERSION=3.10"):
        expect_clean(f"reader e2e: the pin assigned with {spelling.split()[0]}", "punycoder",
                     edit(pin_elsewhere, ci, "    - PANDOC_VERSION=3.10\n    - curl", f"    - {spelling}\n    - curl"),
                     fixture_state())
    # An assignment this reader cannot see into is not judged, and the run is incomplete.
    # A function's body runs only if the function is called: not judged, `local` or not.
    for form, item in (("eval", "eval \"PANDOC_VERSION=3.10\""), ("local", "local PANDOC_VERSION=3.10"),
                       ("a function's body", "f() { PANDOC_VERSION=3.10; }"),
                       ("a `function` body", "function f { PANDOC_VERSION=3.10; }")):
        report = run("punycoder", edit(pin_elsewhere, ci, "    - PANDOC_VERSION=3.10\n    - curl", f"    - {item}\n    - curl"),
                     fixture_state())
        if collect is None and (report.gaps
                                or not any("PANDOC_VERSION" in t and "not judged" in t for _, t in report.unjudged)
                                or exit_status([report]) != 2):
            failures.append(f"reader e2e: an assignment under {form}: expected not judged and exit 2, got "
                            f"{report.gaps} / {report.unjudged}")
    # A judgment left out by choice (--offline) does not make the run incomplete.
    report = run("punycoder", cran, fixture_state())
    if collect is None and (not report.unjudged or exit_status([report]) != 0):
        failures.append(f"an --offline skip alone: expected exit 0, got {exit_status([report])} for {report.unjudged}")
    # A load error: CI is not judged, the run is incomplete, the other areas are still judged.
    for tag, old, new in (("an unknown tag", "    - *deps\n    - Rscript tools/gates.R\n",
                           "    - !reference [.deps]\n    - Rscript tools/gates.R\n"),
                          ("a syntax error", "stages: [check, deploy, audit]\n", "stages: [check, deploy, audit\n"),
                          ("an impossible date", "stages: [check, deploy, audit]\n",
                           "stages: [check, deploy, audit]\nreleased: 2026-02-30\n"),
                          ("a recursive alias", "    - *deps\n    - Rscript tools/gates.R\n",
                           "    - &loop [*loop]\n    - Rscript tools/gates.R\n"),
                          ("an empty rules:if", ".on-main:\n  rules:\n",
                           ".on-main:\n  rules:\n    - if:\n      when: always\n")):
        broken = edit(no_arch, ci, old, new)
        report = run("punycoder", broken, fixture_state())
        if collect is None and (any(area == "ci" for area, _ in report.gaps)
                                or not any("missing ARCHITECTURE.md" in t for _, t in report.gaps)
                                or not any(area == "ci" and "could not read .gitlab-ci.yml" in t
                                           for area, t in report.unjudged)
                                or exit_status([Report("x", unjudged=report.unjudged, incomplete=report.incomplete)]) != 2):
            failures.append(f"reader e2e: {tag}: expected CI not judged and exit 2, got {report.gaps} / {report.unjudged}")

    # NEGATIVE: local gate and schedules.
    expect_gap("URL check missing", "no URL check", "punycoder",
               dict(cran, **{"tools/verify.R": "# check_url_db is only mentioned in a comment\nx <- 1\n"}), fixture_state())
    expect_gap("docs-drift check missing", "no generated-docs drift check", "punycoder",
               edit(cran, "tools/verify.R", "roxygen2::roxygenise(export)\n", "# roxygen2::roxygenise() only in a comment\n"),
               fixture_state())
    # Regenerating in the working tree, with no export, is not the check.
    expect_gap("docs-drift check run in place", "no generated-docs drift check", "punycoder",
               edit(cran, "tools/verify.R", "system2(\"git\", c(\"archive\", \"-o\", tarball, ref))\n", ""),
               fixture_state())
    # The shape the members use: a hook runs a shell wrapper that exports the
    # commit and runs the R check on it.
    expect_clean("docs-drift check through a shell wrapper", "punycoder",
                 dict(edit(edit(cran, "tools/verify.R", "roxygen2::roxygenise(export)\n", ""),
                           "tools/verify.R", "system2(\"git\", c(\"archive\", \"-o\", tarball, ref))\n", ""),
                      **{".pre-commit-config.yaml": cran[".pre-commit-config.yaml"]
                         + "      - id: docs-drift\n        entry: sh scripts/docs-drift.sh\n        language: system\n",
                         "scripts/docs-drift.sh": "git archive -o \"$d/e.tar\" \"$ref\"\nRscript scripts/check-docs-drift.R \"$d\"\n",
                         "scripts/check-docs-drift.R": "roxygen2::roxygenize(pkg)\n"}),
                 fixture_state())
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

    if yaml is None:
        print("check-fleet-standard: PyYAML is not installed, and .gitlab-ci.yml is read with it. Install it with "
              "`python3 -m pip install pyyaml==6.0.3`, or run the pre-commit hook, which installs it.", file=sys.stderr)
        return 2
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
    return exit_status(reports)


def exit_status(reports: list[Report]) -> int:
    """1 on any gap; else 2 when a report is incomplete (Report.skip), so the run is; else 0."""
    if any(r.gaps for r in reports):
        return 1
    return 2 if any(r.incomplete for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
