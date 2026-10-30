# check-fleet-standard v6
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
a file could not be read, .gitlab-ci.yml did not load, or fleet-ci could not
be read at the pinned SHA. Each is reported under "not judged",
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
  link-wrapped form usethis::use_logo() writes is accepted. logo.svg and
  logo.png pass scripts/logo-metadata.py's own `--check`: each is byte for
  byte what it writes from DESCRIPTION's X-schema.org-keywords and its table
  (check_logos(), on the files read as exact bytes), so a logo.png left
  behind, or a field edited by hand, is a gap; when the keywords are what
  differs (the dc:subject bags, PNG Keywords or EXIF XPKeywords), the gap
  names the tags. The artwork itself is not judged.
* Files. The list in "Files every package carries", plus: LICENSE names Bart
  Turczynski as holder, LICENSE.md is the full MIT text, SECURITY.md and
  CODE_OF_CONDUCT.md name the public contact, and SECURITY.md is more than a
  stub (fewer than 10 non-blank lines is a stub). An agent file (AGENTS.md,
  AGENTS_LANG.md or CLAUDE.md) carries the NEWS rule: it names NEWS and says
  "one terse line" (check_news_rule(), SEOR-mjrpwnqz), a loose test.
* DESCRIPTION. Bart Turczynski with roles aut, cre and cph, the ORCID comment
  and the public email; `URL:` in the standard's order (trailing slashes
  ignored); `Language: en-US`; a declared R floor; `X-schema.org-keywords`
  with at least five tokens besides `r`, `rstats`, `r-stats` and `r-package`,
  which r-universe drops, and none of those four.
* .gitlab-ci.yml. It includes fleet-ci's template (ADR 0012, ADR 0015): a
  file without that include is one gap, and its CI and local gate are not
  judged further; a file that does not load leaves both not judged and the
  run incomplete. The rest is under CI AND THE LOCAL GATE, below.
* Local gate. fleet-ci's, as below. scripts/check-docs-drift.R is there and
  matches seor's copy, line endings aside: one canonical copy, vendored byte
  for byte (check_docs_drift_copy(), SEOR-lyciowif). And the NEWS
  terseness check: a `.fleet-ci.yml` gate, or a hook that runs at pre-push
  (its `stages`, else `default_stages`, else every stage, as pre-commit
  decides) whose `entry` and `args` run scripts/check-news.py on NEWS.md,
  or call an R or shell script that does; its `--self-test` alone does not
  count (check_news_hook(), the `news-terse` hook, SEOR-mjrpwnqz). The port
  is not compared with seor's copy. scripts/check-toolchain.R is not
  compared with seor's copy, pending SEOR-bkwtrvhh.
* Schedules. A `deep-check` schedule, and pagerankr's `rurl-devel`, each
  active, on `main`, with `SCHEDULE_KIND` set on the schedule itself; no
  schedule without a `SCHEDULE_KIND` or off `main`. A `dependency-audit`
  schedule is neither required nor a gap.

HOW IT READS CI. `.gitlab-ci.yml` is read with PyYAML (YAML 1.1 as GitLab
reads it: an unquoted `3.10` is 3.1, `yes` is true), `!reference` kept
unresolved (ReferenceLoader), so quoting, comments, anchors, aliases and
`<<` merge keys come from YAML itself (ADR 0008). The file is one config
document, or a `spec:` header document and then the config. A file that
does not load (a YAML error, another unknown tag, a scalar its tag cannot
hold such as `2026-02-30`, a recursive alias, another document shape)
leaves every CI rule of that package not judged and the run incomplete;
the other areas are still judged. `include:` is followed for fleet-ci's
alone (ADR 0015). Not checked: whether a tag pipeline fails on "already on
CRAN", whether the URL check fails on zero URLs and has no exemption (ADR
0011), how security-audit treats missing OSS Index credentials, the GitLab
project badges, and that no employer is named as copyright holder or
funder. Those stay review items.

CI AND THE LOCAL GATE (ADR 0012, ADR 0015). The include is one entry,
`templates/r-package.yml` at a 40-hex SHA the fleet-ci clone (FLEET_CI_DIR,
`--fleet-ci`) holds (else a gap, an unknown fleet-ci commit), and a v* tag
of the clone points at that SHA (a gap when the clone holds v* tags, none
at the SHA; not judged when it holds none at all: it may lack the tags).
The package's own file sets no template-owned image variable
(FLEET_IMAGE_*, FLEET_RELEASE_IMAGE, FLEET_FLOOR_IMAGE) in its top-level
`variables`, writes no `workflow`, `rules`, job-level `when`, template job
or hidden key, and adds only x-* jobs, each extending exactly one of
`.t2-job`, `.t3-job`, `.schedule-job`, a schedule job on deep-check or, in
pagerankr alone, rurl-devel. On the merged configuration (the template at
the SHA, the package's file merged over it as GitLab merges an include):
ADR 0012's 13 job names, no fewer, no other; the switches and the incoming
settings "true" or "false", FLEET_SANITIZERS off only without `src/`,
FLEET_FLOOR or FLEET_MANUAL off only with a Markdown file naming it (a
loose test of "a reason recorded"), FLEET_MANUAL never off on CRAN,
FLEET_INCOMING off in seor alone and FLEET_INCOMING_REMOTE in pslr alone;
FLEET_LOCALE or FLEET_DEVEL off is listed as not judged, a review item;
with FLEET_FLOOR "true", FLEET_FLOOR_R's minor is DESCRIPTION's R floor.
`image/fleet-r/Dockerfile` at the SHA pins pandoc PANDOC_PIN (`ARG
PANDOC_VERSION=`), the image's copy of the pin. `.fleet-ci/` is byte for
byte what fleet-ci's bin/vendor writes at the SHA, and nothing else.
bin/rules-sim at the SHA accepts the file, its invariants hold, and its
contexts give ADR 0012's event table: no pipeline on a push to main or any
schedule but deep-check and rurl-devel, T2 on deep-check, T2 and t3-manual
on a RELEASE=1 run on main, all 13 on a v* tag, a switch's job aside when
it is off, and coverage in rurl-devel's pipeline. FOSSA packages run
`fossa analyze` in an x-* job, and every package carries seor's
disposition-row audit test files. Each SHA is checked out from a shared
clone in a temporary directory, never in the clone itself; that needs git,
and rules-sim needs Ruby. A SHA the clone lacks, or a step that cannot
run, leaves the rest not judged and the run incomplete, as does a package
file that cannot be read. The merged configuration is the local
expansion; GitLab's CI lint is not asked. The local gate is fleet-ci's
(check_local_gate_migrated()): `.fleet-ci.yml` loading as fleet-ci's own
classifier at the pinned SHA reads it (`bin/classify --config-json`, in a
subprocess), with scripts/check-docs-drift.R in `cheap_gates`, a URL
check in a gate list, and T1's README drift, NEWS version, lint and
spelling gates, each a gate-list command naming "readme", "news" (not
the terseness check), "lint" or "spell" (T1_GATES); the NEWS check a
pre-push hook or a gate; a pre-push hook running
scripts/check-toolchain.R, the host's pandoc against .fleet-ci/toolchain
and its roxygen2 against Config/roxygen2/version; no `verify` hook and no
hook running `.fleet-ci/gate` in .pre-commit-config.yaml; `^\\.fleet-ci$`
and `^\\.fleet-ci\\.yml$` in .Rbuildignore. R CMD check is the gate's
own, in the image.

Needs PyYAML (pinned at 6.0.3 in the pre-commit hook, which installs it); a run
without it exits 2 with an install hint. `glab` must be on PATH and
authenticated unless `--offline`. Every package needs git, Ruby and a
fleet-ci clone. So do the self-test's CI and local-gate rows, which build
a fixture fleet-ci from the clone's FLEET_CI_FIXTURE_BASE commit; without
the clone, that commit or Ruby the self-test fails, naming the fix;
SEOR_SKIP_FLEET_CI_SELFTEST=1 instead reports those rows SKIPPED, loudly,
and passes. The content rows (badges, README, logo, files, DESCRIPTION,
seor's own logos) need no clone and run either way (ADR 0015).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
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
ORCID = "0000-0002-8788-7980"
CONTACT = "bartek@turczynski.pl"
# The fleet's pandoc (design/fleet-standard.md, "Verification tiers";
# SEOR-egfbijyi). fleet-ci's fleet-r image installs it (`ARG PANDOC_VERSION=`
# in image/fleet-r/Dockerfile at the pinned SHA); this is the standard's
# value, so an image on another one is a gap. A bump moves it together with
# that Dockerfile, a new fleet-ci tag and each package's re-pinned include.
PANDOC_PIN = "3.10"
SECURITY_STUB_LINES = 10
BAD_BADGE_TEXT = ("unknown", "not found", "invalid", "not set up", "inaccessible", "no releases found")
LIFECYCLE = {"experimental": "orange", "stable": "brightgreen", "superseded": "blue", "deprecated": "orange"}
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
    """Files held in memory: the self-test's fixtures, text as str and
    binary files (logo.png) as bytes."""

    def __init__(self, files: dict[str, str | bytes]):
        self.files = dict(files)

    def tree(self) -> set[str]:
        return set(self.files)

    def read(self, path: str) -> str | None:
        found = self.files.get(path)
        return found.decode("utf-8", errors="replace") if isinstance(found, bytes) else found

    def read_bytes(self, path: str) -> bytes | None:
        found = self.files.get(path)
        return found.encode("utf-8") if isinstance(found, str) else found


class LocalSource:
    """A checkout on disk, read-only. Skips VCS and build directories, and
    the agents' worktrees in `.claude/worktrees`: other checkouts of the
    repository, never its files."""

    SKIP_DIRS = {".git", "node_modules", "renv", ".Rproj.user", "_scratch", "tmp", ".fp", ".r-lib"}

    def __init__(self, root: Path):
        self.root = root
        self._tree: set[str] | None = None

    def tree(self) -> set[str]:
        if self._tree is None:
            found = set()
            for dirpath, dirnames, filenames in os.walk(self.root):
                rel = Path(dirpath).relative_to(self.root)
                dirnames[:] = [d for d in dirnames if d not in self.SKIP_DIRS and not d.endswith(".Rcheck")
                               and (rel / d).as_posix() != ".claude/worktrees"]
                found.update((rel / name).as_posix() for name in filenames)
            self._tree = {p[2:] if p.startswith("./") else p for p in found}
        return self._tree

    def read(self, path: str) -> str | None:
        target = self.root / path
        if not target.is_file():
            return None
        return target.read_text(encoding="utf-8", errors="replace")

    def read_bytes(self, path: str) -> bytes | None:
        """The file's exact bytes: no decoding, no newline translation."""
        target = self.root / path
        return target.read_bytes() if target.is_file() else None


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
        self._cache: dict[str, bytes] = {}

    def tree(self) -> set[str]:
        if self._tree is None:
            entries = glab_api(
                f"projects/{self.project}/repository/tree?ref={self.ref}&recursive=true&per_page=100",
                paginate=True,
            )
            self._tree = {e["path"] for e in entries if e.get("type") == "blob"}
        return self._tree

    def read(self, path: str) -> str | None:
        raw = self.read_bytes(path)
        return None if raw is None else raw.decode("utf-8", errors="replace")

    def read_bytes(self, path: str) -> bytes | None:
        """The blob's exact bytes, as the raw endpoint serves them (glab api
        copies a non-JSON body through unchanged); read() decodes them."""
        if path not in self.tree():
            return None
        if path not in self._cache:
            quoted = urllib.parse.quote(path, safe="")
            command = ["glab", "api", f"projects/{self.project}/repository/files/{quoted}/raw?ref={self.ref}"]
            for _ in range(3):  # GitLab answers the odd TLS handshake timeout
                try:
                    result = subprocess.run(command, capture_output=True, timeout=120)  # noqa: S603
                except subprocess.TimeoutExpired as error:
                    raise ProbeError(f"reading {path}: {error}") from error
                if not result.returncode:
                    break
            if result.returncode:
                raise ProbeError(f"reading {path}: {result.stderr.decode(errors='replace').strip()[:200]}")
            self._cache[path] = result.stdout
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
# Python is not followed: seor's Python checks (check-citation,
# check-bugreports, check-news) name other scripts and commands in their
# prose, which would read as commands they run.
SCRIPT_SUFFIXES = {"", ".R", ".r", ".sh", ".yml", ".yaml"}


def inline_scripts(text: str, source, depth: int = 2, seen: set[str] | None = None) -> list[tuple[str, str]]:
    """(path, text) for each repository script `text` names, followed `depth` levels.

    `text` is a .fleet-ci.yml gate command or a pre-commit hook's command;
    the local-gate rules read what they run (the docs-drift, URL, NEWS and
    toolchain checks). Comment lines are dropped, and so are the opt-in
    stages of an R stage table (drop_opt_in_stages()), a `name = list(...,
    default = FALSE)` entry, since a stage that runs only on request is no
    gate.

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


# --- CI: the YAML ------------------------------------------------------------------

# Top-level keys that are not jobs.
RESERVED = {"stages", "default", "variables", "workflow", "include", "image", "services",
            "cache", "before_script", "after_script"}


class CIError(Exception):
    """A .gitlab-ci.yml GitLab itself would refuse: its CI rules are not judged."""


class Reference(list):
    """A `!reference [block, key, ...]`, kept unresolved: the fleet-ci template
    and a migrated package's file may hold them (fleet_ci_include())."""


if yaml is not None:
    class ReferenceLoader(yaml.SafeLoader):
        """SafeLoader that reads GitLab's `!reference` tag as a Reference;
        every other unknown tag is still an error."""

    ReferenceLoader.add_constructor(
        "!reference", lambda loader, node: Reference(loader.construct_sequence(node, deep=True)))


def load_ci(text: str, references: bool = False) -> dict:
    """The config mapping of a .gitlab-ci.yml, or CIError when GitLab would refuse it.

    Every failure to load is a CIError: a YAML error, an unknown tag, and also
    a scalar its tag cannot hold (`2026-02-30`, `!!int 'abc'`), which PyYAML
    raises as a plain ValueError. The file is one document, or a header
    document holding only `spec:` (an include's inputs), `---`, then the
    config; an empty document (a trailing `---`) is no document. A node that contains itself (`a: &a [*a]`) is refused here, so
    nothing downstream recurses into it. `references` reads `!reference`
    as a Reference instead of refusing it, as fleet-ci's template and a
    package's file that includes it may hold them.
    """
    try:
        loaded = yaml.load_all(text, Loader=ReferenceLoader) if references else yaml.safe_load_all(text)
        documents = [document for document in loaded if document is not None]
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


# A URL check in a gate a migrated package's .fleet-ci.yml lists.
URL_CHECK_RE = re.compile(r"check_url_db|url_db_from_package_sources|urlchecker::url_check|\burl_check\s*\(")


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


@cache
def logo_metadata():
    """scripts/logo-metadata.py as a module (its name has a hyphen), loaded
    once: its --check (check_logos), its keyword rule and its keyword readers
    are the only copies."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("logo_metadata", Path(__file__).with_name("logo-metadata.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# logo-metadata.py writes the keywords twice in logo.svg: the RDF block's bag
# and the XMP packet's.
LOGO_SUBJECT_BAGS = 2


def keyword_drift(want: list[str], found_lists: list[list[str]]) -> list[str]:
    """How each list of tags read back from a logo differs from `want`, once per
    distinct difference: missing and extra tags, or the order."""
    drift: list[str] = []
    for found in found_lists:
        if found == want:
            continue
        missing = [k for k in want if k not in found]
        extra = [k for k in found if k not in want]
        parts = ([f"missing {', '.join(missing)}"] if missing else []) + ([f"extra {', '.join(extra)}"] if extra else [])
        text = "; ".join(parts) or "the same tags in another order or repeated"
        if text not in drift:
            drift.append(text)
    return drift


def logo_keyword_gap(path: str, raw: bytes, want: list[str]) -> str | None:
    """The part of a drifted logo file's gap that names its keywords: None
    when they are what logo-metadata.py writes, so something else drifted."""
    lm = logo_metadata()
    if path.endswith(".svg"):
        bags = lm.read_svg_subjects(raw.decode("utf-8", errors="replace"))
        if not bags:
            return f"{path} has no keywords (no dc:subject bag as logo-metadata.py writes it)"
        drift = keyword_drift(want, bags)
        if len(bags) != LOGO_SUBJECT_BAGS:
            drift.insert(0, f"{len(bags)} dc:subject bag(s) as logo-metadata.py writes them, not {LOGO_SUBJECT_BAGS}")
    else:
        try:
            text, xp = lm.read_png_keywords(raw)
        except (SystemExit, ValueError, LookupError, StopIteration, OverflowError, lm.struct.error):
            return f"{path} has no keywords (no tEXt Keywords and EXIF XPKeywords as logo-metadata.py writes them)"
        drift = keyword_drift(want, [text.split(", "), xp.split("; ")])
    if not drift:
        return None
    return f"{path} keywords differ from DESCRIPTION's X-schema.org-keywords ({' | '.join(drift)})"


def check_logo_metadata(pkg: str, source, report: Report) -> None:
    """logo.svg and logo.png are byte for byte what logo-metadata.py writes
    from DESCRIPTION: its own --check (check_logos(): finalize, then compare),
    so a logo.png left behind or a field edited by hand is a gap
    (SEOR-seobtecv). A drifted file's gap names its keywords when they differ
    from DESCRIPTION's X-schema.org-keywords (SEOR-uwpnkqnb). A missing
    logo.svg or DESCRIPTION, or a DESCRIPTION with no keywords, is reported
    elsewhere; either logo file missing leaves the other judged alone, as --check
    does."""
    try:
        description = source.read("DESCRIPTION")
        raw_description = source.read_bytes("DESCRIPTION")
        logos = {path: source.read_bytes(path) for path in LOGO_FILES}
    except ProbeError as error:
        report.skip("logo", f"could not read {' or '.join(LOGO_FILES)} or DESCRIPTION ({error}), "
                            "so the logo metadata is not judged", incomplete=True)
        return
    logos = {path: raw for path, raw in logos.items() if raw is not None}
    if not logos or description is None or raw_description is None:
        return
    # logo-metadata.py reads DESCRIPTION as utf-8-sig.
    description = description.removeprefix("\ufeff")
    if not read_dcf(description).get("X-schema.org-keywords", "").strip(" ,\n"):
        return
    lm = logo_metadata()
    regenerate = (f"regenerate with seor's `python3 scripts/logo-metadata.py {pkg} <the {pkg} checkout>/man/figures`, "
                  "then commit both logo files")
    try:
        verdicts, broken = lm.check_logos(pkg, raw_description, {Path(path).name: raw for path, raw in logos.items()})
    except SystemExit as refusal:  # logo-metadata.py refuses this DESCRIPTION
        report.gap("logo", f"logo-metadata.py --check cannot judge the logo files ({refusal.code})")
        return
    want = None
    for path, raw in logos.items():
        name = Path(path).name
        if name in broken:  # a file it refuses or cannot parse, such as a logo.png that is no PNG
            report.gap("logo", f"{path} cannot be judged by logo-metadata.py --check ({broken[name]}); {regenerate}")
            continue
        if verdicts[name] is None:
            continue
        if want is None:
            want = lm.logo_keywords(pkg, description, "DESCRIPTION")
        keywords = logo_keyword_gap(path, raw, want)
        what = keywords or f"{path} differs from what logo-metadata.py writes (its --check reports drift)"
        report.gap("logo", f"{what}; {regenerate}")


def check_logo(pkg: str, source, report: Report) -> None:
    tree = source.tree()
    for path in LOGO_FILES:
        if path not in tree:
            report.gap("logo", f"missing {path}")
    check_logo_metadata(pkg, source, report)
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


def check_audit_files(source, report: Report) -> None:
    tree = source.tree()
    missing = [p for p in AUDIT_TEST_FILES if p not in tree]
    if missing:
        report.gap("ci", f"audit jobs lack seor's disposition-row shape: missing {', '.join(missing)}")


class CIShape(Enum):
    """What check_ci() found, which check_local_gate() reads: .gitlab-ci.yml
    loaded with fleet-ci's include, loaded (or is missing) without it, or
    did not load."""
    FLEET_CI = "fleet-ci"
    NO_INCLUDE = "no-include"
    UNLOADED = "unloaded"


def check_ci(pkg: str, source, state: State, floor: str | None, report: Report,
             fleet: FleetCI | None = None) -> CIShape:
    """The CI rules: every package includes fleet-ci's template (ADR 0012,
    ADR 0015) and is judged on the merged configuration (check_ci_migrated()).
    A file without the include is one gap, and the rest of its CI is not
    judged; a file that does not load leaves its CI not judged and the run
    incomplete."""
    text = source.read(".gitlab-ci.yml")
    if text is None:
        report.gap("ci", "no .gitlab-ci.yml")
        return CIShape.NO_INCLUDE
    try:
        load_ci(text, references=True)
    except (CIError, RecursionError) as error:
        report.skip("ci", f"could not read .gitlab-ci.yml ({error}), so none of its CI rules is judged",
                    incomplete=True)
        check_audit_files(source, report)
        return CIShape.UNLOADED
    migrated = fleet_ci_include(text)
    if migrated is None:
        report.gap("ci", f".gitlab-ci.yml does not include fleet-ci's {FLEET_CI_TEMPLATE} (project "
                         f"{FLEET_CI_PROJECT}); every package does (ADR 0015), so its CI and local gate are not "
                         "judged further")
        check_audit_files(source, report)
        return CIShape.NO_INCLUDE
    check_ci_migrated(pkg, source, state, floor, text, *migrated, fleet or FLEET_CI, report)
    return CIShape.FLEET_CI


# --- CI, migrated: a package that includes fleet-ci's template (ADR 0012) ----------

FLEET_CI_PROJECT = f"{OWNER}/fleet-ci"
FLEET_CI_TEMPLATE = "templates/r-package.yml"
# The local fleet-ci clone the pinned SHA is read from: tags, the template,
# bin/rules-sim, bin/vendor and the image Dockerfile, all at that SHA.
FLEET_CI_DIR = Path(os.environ.get("FLEET_CI_DIR") or "~/Projects/fleet-ci").expanduser()
FLEET_CI_DOCKERFILE = "image/fleet-r/Dockerfile"
SHA_RE = re.compile(r"[0-9a-f]{40}")


class FleetCIError(Exception):
    """fleet-ci could not be read at a SHA: not judged, never a gap."""


def git_env() -> dict[str, str]:
    """The environment without GIT_*: a pre-push hook runs this with GIT_DIR
    and friends pointing at seor, and a git command here must read only the
    repository it names."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


class FleetCI:
    """A fleet-ci clone, read-only, and what it holds at a commit.

    Nothing here changes the clone: a SHA is checked out into a shared
    clone of it in a temporary directory, where bin/vendor and bin/rules-sim
    run (bin/vendor needs a git checkout, clean, to write VERSION). Each SHA
    is checked out and vendored once per run; cleanup() removes them."""

    def __init__(self, clone: Path):
        self.clone = clone
        self._root: Path | None = None
        self._checkouts: dict[str, Path] = {}
        self._vendored: dict[str, dict[str, bytes]] = {}
        self._configs: dict[tuple[str, str], tuple[dict | None, str]] = {}
        self._runs = 0

    def run_git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        """git in the clone (or `cwd`), output decoded with bad bytes replaced;
        FleetCIError when git cannot run at all."""
        command = ["git", "-C", str(cwd or self.clone), *args]
        try:
            return subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace",  # noqa: S603
                                  env=git_env(), timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as error:
            raise FleetCIError(f"git {' '.join(args)}: {error}") from error

    def git(self, *args: str, cwd: Path | None = None) -> str:
        run = self.run_git(*args, cwd=cwd)
        if run.returncode:
            raise FleetCIError(f"git {' '.join(args)}: {run.stderr.strip()[:200]}")
        return run.stdout

    def root(self) -> Path:
        if self._root is None:
            try:
                self._root = Path(tempfile.mkdtemp(prefix="fleet-ci-"))
            except OSError as error:
                raise FleetCIError(f"a scratch directory: {error}") from error
        return self._root

    def has_commit(self, sha: str) -> bool:
        """Whether the clone holds commit `sha`: False only when git says it
        is absent; FleetCIError when there is no clone or git fails (a
        timeout, a lock, a broken repository), which is not judged."""
        if not (self.clone / ".git").exists() and not (self.clone / "HEAD").is_file():
            raise FleetCIError(f"no fleet-ci clone at {self.clone} (clone the private {FLEET_CI_PROJECT} there, "
                               "or point FLEET_CI_DIR or --fleet-ci at one)")
        run = self.run_git("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
        if run.returncode == 0:
            return True
        if run.returncode == 1 and not run.stderr.strip():
            return False
        raise FleetCIError(f"git rev-parse --verify {sha[:12]} exited {run.returncode}: {run.stderr.strip()[:200]}")

    def v_tags(self, sha: str) -> list[str]:
        """The v* tags that point at `sha`, lightweight or annotated."""
        return self.git("tag", "--list", "v*", "--points-at", sha).split()

    def any_v_tags(self) -> bool:
        """Whether the clone holds any v* tag at all."""
        return bool(self.git("tag", "--list", "v*").split())

    def scratch(self, prefix: str) -> Path:
        """A fresh, empty directory under root(), one per attempt: a step
        that failed part-way never leaves a path the next attempt trips on."""
        try:
            return Path(tempfile.mkdtemp(prefix=prefix, dir=self.root()))
        except OSError as error:
            raise FleetCIError(f"a scratch directory: {error}") from error

    def checkout(self, sha: str) -> Path:
        if sha not in self._checkouts:
            dest = self.scratch(f"checkout-{sha[:12]}-")
            self.git("clone", "--quiet", "--shared", "--no-checkout", str(self.clone), str(dest), cwd=self.root())
            self.git("checkout", "--quiet", "--detach", sha, cwd=dest)
            self._checkouts[sha] = dest
        return self._checkouts[sha]

    def read(self, sha: str, path: str) -> str | None:
        target = self.checkout(sha) / path
        try:
            return target.read_text(encoding="utf-8", errors="replace") if target.is_file() else None
        except OSError as error:
            raise FleetCIError(f"reading {path}: {error}") from error

    def vendored(self, sha: str) -> dict[str, bytes]:
        """What fleet-ci's bin/vendor writes into a package's .fleet-ci/ at
        `sha`, by file name: it runs on a scratch package, a fresh one per
        attempt. Every failure is a FleetCIError, so one bad SHA leaves that
        package not judged and never stops the run."""
        if sha not in self._vendored:
            checkout = self.checkout(sha)
            package = self.scratch(f"package-{sha[:12]}-")
            try:
                (package / "DESCRIPTION").write_text("Package: fixture\n", encoding="utf-8")
                (package / ".Rbuildignore").write_text("^\\.fleet-ci$\n^\\.fleet-ci\\.yml$\n", encoding="utf-8")
                run = subprocess.run([str(checkout / "bin" / "vendor"), str(package)], capture_output=True, text=True,  # noqa: S603
                                     env=git_env(), timeout=120, check=False)
                if run.returncode:
                    raise FleetCIError(f"bin/vendor exited {run.returncode}: {run.stderr.strip()[:200]}")
                written = package / ".fleet-ci"
                self._vendored[sha] = {path.relative_to(written).as_posix(): path.read_bytes()
                                       for path in sorted(written.rglob("*")) if path.is_file()}
            except (OSError, subprocess.SubprocessError, ValueError) as error:
                raise FleetCIError(f"bin/vendor: {error}") from error
        return self._vendored[sha]

    def rules_sim(self, sha: str, text: str) -> tuple[int, str, str]:
        """bin/rules-sim at `sha` on a package's .gitlab-ci.yml text, every
        context: (exit status, stdout, stderr). It reads YAML with Ruby."""
        if shutil.which("ruby") is None:
            raise FleetCIError("bin/rules-sim reads YAML with Ruby (bin/yaml2json), and ruby is not on PATH")
        checkout = self.checkout(sha)
        self._runs += 1
        consumer = self.root() / f"consumer-{self._runs}.yml"
        try:
            consumer.write_text(text, encoding="utf-8")
            run = subprocess.run([sys.executable, str(checkout / "bin" / "rules-sim"), "--fleet-ci", str(checkout),  # noqa: S603
                                  str(consumer)], capture_output=True, encoding="utf-8", errors="replace",
                                 env=git_env(), timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as error:
            raise FleetCIError(f"bin/rules-sim: {error}") from error
        return run.returncode, run.stdout, run.stderr

    def config(self, sha: str, text: str) -> tuple[dict | None, str]:
        """A package's .fleet-ci.yml `text` as fleet-ci's own classifier at
        `sha` reads it (`bin/classify --config-json`, run in a subprocess on
        the checkout; it reads YAML with Ruby): (the validated configuration,
        "") or (None, its complaint) when it refuses the file. FleetCIError
        when the classifier cannot run."""
        key = (sha, text)
        if key not in self._configs:
            if shutil.which("ruby") is None:
                raise FleetCIError("bin/classify reads YAML with Ruby (bin/yaml2json), and ruby is not on PATH")
            classify = self.checkout(sha) / "bin" / "classify"
            if not classify.is_file():
                raise FleetCIError(f"fleet-ci {sha[:12]} has no bin/classify")
            self._runs += 1
            config = self.root() / f"fleet-ci-{self._runs}.yml"
            try:
                config.write_text(text, encoding="utf-8")
                run = subprocess.run([sys.executable, str(classify), "--config-json", str(config)],  # noqa: S603
                                     capture_output=True, encoding="utf-8", errors="replace", env=git_env(),
                                     timeout=120, check=False)
            except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as error:
                raise FleetCIError(f"bin/classify --config-json: {error}") from error
            complaint = " ".join(line.strip().removeprefix("classify: ") for line in run.stderr.splitlines()
                                 if line.strip())
            if run.returncode == 2:
                self._configs[key] = (None, complaint.replace(str(config), FLEET_CI_CONFIG)[:300])
            elif run.returncode:
                raise FleetCIError(f"bin/classify --config-json exited {run.returncode}: {complaint[:200]}")
            else:
                try:
                    data = json.loads(run.stdout)
                except ValueError as error:
                    raise FleetCIError(f"bin/classify --config-json printed no JSON: {error}") from error
                if not isinstance(data, dict):
                    raise FleetCIError("bin/classify --config-json printed no mapping")
                self._configs[key] = (data, "")
        return self._configs[key]

    def cleanup(self) -> None:
        if self._root is not None:
            shutil.rmtree(self._root, ignore_errors=True)
        self._root, self._checkouts, self._vendored, self._configs = None, {}, {}, {}


# The clone a live run reads; main() points it at --fleet-ci.
FLEET_CI = FleetCI(FLEET_CI_DIR)

# ADR 0012's job names, its hidden bases for x-* jobs, and the jobs each
# switch turns off.
FIXED_JOBS = ("t2-check-release", "t2-check-oldrel", "t2-check-devel", "t2-floor", "t2-sanitizers", "t2-locale",
              "t2-ascran", "coverage", "osv-audit", "security-audit", "t3-manual", "pages", "citation-version")
T2_JOBS = tuple(job for job in FIXED_JOBS if job not in ("t3-manual", "pages"))
X_BASES = (".t2-job", ".t3-job", ".schedule-job")
SWITCH_JOBS = {"FLEET_SANITIZERS": "t2-sanitizers", "FLEET_FLOOR": "t2-floor", "FLEET_LOCALE": "t2-locale",
               "FLEET_DEVEL": "t2-check-devel", "FLEET_MANUAL": "t3-manual"}
# The two settings and the one package each may turn off (ADR 0004, carried
# forward by ADR 0012).
INCOMING_SETTINGS = {"FLEET_INCOMING": "seor", "FLEET_INCOMING_REMOTE": "pslr"}
# The schedules a consumer job may tie itself to, and who may use the one
# exception.
SCHEDULE_EXCEPTION = ("rurl-devel", "pagerankr")
# The image variables the template owns, beside its FLEET_IMAGE_* block: a
# package's top-level variables never set one.
TEMPLATE_IMAGE_VARIABLES = ("FLEET_RELEASE_IMAGE", "FLEET_FLOOR_IMAGE")
# What bin/rules-sim's contexts must give (ADR 0012's event table): the
# jobs each pipeline carries at least, None for no pipeline.
RULES_SIM_WANT: dict[str, tuple[str, ...] | None] = {
    "push-main": None,
    "schedule-deep-check": T2_JOBS,
    "schedule-dependency-audit": None,
    "schedule-other": None,
    "schedule-none": None,
    "web-release-main": T2_JOBS + ("t3-manual",),
    "tag-v1.2.3": FIXED_JOBS,
    "web-pages-tag": ("pages",),
    "tag-other": None,
    "web-nothing": None,
    "merge-request": None,
    "branch-push": None,
    "api-main": None,
}
DOCKER_PANDOC_RE = re.compile(r"^ARG[ \t]+PANDOC_VERSION=(\S+)[ \t]*$", re.M)


def fleet_ci_include(text: str) -> tuple[dict, list] | None:
    """(config, include entries) when .gitlab-ci.yml includes fleet-ci's
    project, which may hold `!reference`. None for anything else, a file
    that does not load included (check_ci() reports which)."""
    try:
        data = load_ci(text, references=True)
    except (CIError, RecursionError):
        return None
    include = data.get("include")
    entries = include if isinstance(include, list) else [include]
    if any(isinstance(entry, dict) and entry.get("project") == FLEET_CI_PROJECT for entry in entries):
        return data, entries
    return None


def key_paths(node: object, key: str, path: str = "") -> list[str]:
    """Where `key` sits as a mapping key in `node`, as `a/b[0]/c` paths."""
    hits: list[str] = []
    if isinstance(node, dict):
        for name, value in node.items():
            here = f"{path}/{name}" if path else str(name)
            if name == key:
                hits.append(here)
            hits += key_paths(value, key, here)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            hits += key_paths(value, key, f"{path}[{i}]")
    return hits


def pinned_sha(entries: list, report: Report) -> str | None:
    """The fleet-ci commit the include pins, or None after a gap: one
    include, of the template, at a 40-hex SHA."""
    if len(entries) != 1:
        report.gap("ci", f".gitlab-ci.yml has {len(entries)} includes; a migrated package includes fleet-ci's "
                         f"{FLEET_CI_TEMPLATE} and nothing else")
        return None
    entry = entries[0]
    if entry.get("file") not in (FLEET_CI_TEMPLATE, f"/{FLEET_CI_TEMPLATE}"):
        report.gap("ci", f"the fleet-ci include names file {entry.get('file')!r}, not {FLEET_CI_TEMPLATE}")
        return None
    ref = gitlab_str(entry.get("ref"))
    if not SHA_RE.fullmatch(ref):
        report.gap("ci", f"the fleet-ci include's ref {ref!r} is not a 40-hex commit SHA; pin fleet-ci by the "
                         "commit a v* tag points at, never a branch or a tag name (ADR 0012)")
        return None
    return ref


def check_consumer(pkg: str, consumer: dict, report: Report) -> None:
    """What the package's own .gitlab-ci.yml writes: variables and x-* jobs,
    each extending exactly one hidden base, and never `workflow`, `rules`,
    a job-level `when`, a template job or a hidden key, so the event table
    is the template's (ADR 0012, "What a package may vary")."""
    if "workflow" in consumer:
        report.gap("ci", ".gitlab-ci.yml overrides `workflow`, the template's event table; a package sets "
                         "variables and adds x-* jobs only (ADR 0012)")
    for name in variables_of(consumer.get("variables")):
        if str(name).startswith("FLEET_IMAGE_") or name in TEMPLATE_IMAGE_VARIABLES:
            report.gap("ci", f".gitlab-ci.yml sets `{name}` in its variables, a template-owned image variable; a "
                             "package picks its image with FLEET_RELEASE_VARIANT and never names one (fleet-ci "
                             "README, \"What a package sets\")")
    for path in key_paths({k: v for k, v in consumer.items() if k != "workflow"}, "rules"):
        report.gap("ci", f".gitlab-ci.yml writes `rules` at {path}; the template's rules decide what runs, and a "
                         "package never writes rules (ADR 0012)")
    for name, body in consumer.items():
        if name in ("include", "variables", "workflow"):
            continue
        if isinstance(body, dict) and "when" in body:
            report.gap("ci", f"{name}: a job-level `when`; a package never writes when (ADR 0012)")
        if name in FIXED_JOBS:
            report.gap("ci", f".gitlab-ci.yml redefines template job `{name}`; a package sets the template's "
                             "variables instead (ADR 0012)")
        elif str(name).startswith("."):
            report.gap("ci", f".gitlab-ci.yml overrides the template's hidden key `{name}`, which can change its "
                             "rules; a package defines no hidden key (ADR 0012)")
        elif name in RESERVED:
            report.gap("ci", f".gitlab-ci.yml sets top-level `{name}`; a package sets variables and x-* jobs only")
        elif not str(name).startswith("x-"):
            report.gap("ci", f"job `{name}` is outside ADR 0012's 13 names and the x-* prefix")
        else:
            extends = body.get("extends") if isinstance(body, dict) else None
            if not (isinstance(extends, str) and extends in X_BASES):
                report.gap("ci", f"{name}: extends {extends!r}, not exactly one of {', '.join(X_BASES)} (ADR 0012)")
            elif extends == ".schedule-job":
                kind = gitlab_str(variables_of(body.get("variables")).get("FLEET_JOB_SCHEDULE"))
                exception, owner = SCHEDULE_EXCEPTION
                if kind != "deep-check" and not (kind == exception and pkg == owner):
                    report.gap("ci", f"{name}: runs on the {kind!r} schedule; a schedule job runs on deep-check, and "
                                     f"the only schedule exception is {owner}'s {exception} (ADR 0012)")


def check_switches(pkg: str, source, state: State, variables: dict[str, str], report: Report) -> None:
    """The switches and the incoming settings, as the merged configuration
    sets them: "true" or "false", and "false" only where ADR 0012 allows it."""
    for name in (*SWITCH_JOBS, *INCOMING_SETTINGS):
        value = variables.get(name)
        if value not in ("true", "false"):
            report.gap("ci", f"{name} is {value!r}, not \"true\" or \"false\"")
    tree = source.tree()
    off = [name for name in SWITCH_JOBS if variables.get(name) == "false"]
    if "FLEET_SANITIZERS" in off and any(path.startswith("src/") for path in tree):
        report.gap("ci", "FLEET_SANITIZERS is \"false\", but the package has compiled code (src/), which the "
                         "sanitizer leg exists for")
    reasoned = [name for name in ("FLEET_FLOOR", "FLEET_MANUAL") if name in off]
    if reasoned:
        docs = [path for path in sorted(tree) if path.endswith(".md") and not path.startswith((".fleet-ci/", "docs/"))]
        texts = [source.read(path) or "" for path in docs]
        for name in reasoned:
            if not any(re.search(rf"\b{name}\b", text) for text in texts):
                report.gap("ci", f"{name} is \"false\" with no reason recorded: no Markdown file in the package "
                                 f"names {name} (ADR 0012)")
    if "FLEET_MANUAL" in off:
        if state.on_cran:
            report.gap("ci", "FLEET_MANUAL is \"false\" for a package on CRAN, which has a PDF manual (ADR 0012)")
        elif state.on_cran is None:
            report.skip("ci", "FLEET_MANUAL is \"false\"; whether the package is on CRAN is unknown", incomplete=False)
    for name in ("FLEET_LOCALE", "FLEET_DEVEL"):
        if name in off:
            report.skip("ci", f"{name} is \"false\"; whether the package lacks what {SWITCH_JOBS[name]} checks is "
                              "a review item", incomplete=False)
    for name, owner in INCOMING_SETTINGS.items():
        if variables.get(name) == "false" and pkg != owner:
            report.gap("ci", f"{name} is \"false\"; only {owner} may turn it off (ADR 0004, carried forward by "
                             "ADR 0012)")


def rules_sim_pipelines(stdout: str) -> dict[str, list[str] | None]:
    """bin/rules-sim's report as {context: the jobs it runs, or None for no pipeline}."""
    pipelines: dict[str, list[str] | None] = {}
    context = None
    for line in stdout.splitlines():
        if line.startswith("== "):
            context = line[3:].split(":", 1)[0]
            pipelines[context] = None
        elif context is None or not line.strip():
            continue
        elif line.startswith("   no pipeline"):
            pipelines[context] = None
        elif line.startswith("   pipeline"):
            pipelines[context] = []
        elif line.startswith("   (no jobs"):
            pipelines[context] = None
        elif pipelines[context] is not None:
            pipelines[context].append(line.split()[0])
    return pipelines


def check_rules_sim(pkg: str, sha: str, text: str, variables: dict[str, str], fleet: FleetCI, report: Report) -> None:
    """bin/rules-sim at the pinned SHA on the package's file: it accepts the
    file, its invariants hold, and each context's pipeline is the event
    table's, the switches the package turned off aside."""
    status, stdout, stderr = fleet.rules_sim(sha, text)
    short = sha[:12]
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    invariants = [line.removeprefix("rules-sim: invariant: ") for line in lines
                  if line.startswith("rules-sim: invariant: ")]
    if status and not invariants:
        report.gap("ci", f"fleet-ci's bin/rules-sim at {short} refuses .gitlab-ci.yml: "
                         f"{' '.join(lines).removeprefix('rules-sim: ')[:400]}")
        return
    for invariant in invariants:
        report.gap("ci", f"fleet-ci's bin/rules-sim at {short}: {invariant}")
    pipelines = rules_sim_pipelines(stdout)
    off = {SWITCH_JOBS[name] for name in SWITCH_JOBS if variables.get(name) == "false"}
    for context, want in RULES_SIM_WANT.items():
        if context not in pipelines:
            report.gap("ci", f"fleet-ci's bin/rules-sim at {short} reports no {context} context")
            continue
        jobs = pipelines[context]
        if want is None:
            if jobs:
                report.gap("ci", f"the {context} event creates a pipeline ({', '.join(jobs)}); ADR 0012's event "
                                 "table gives it none")
            continue
        missing = [job for job in want if job not in off and job not in (jobs or [])]
        if missing:
            label = context.removeprefix("schedule-")
            report.gap("ci", f"the {label} pipeline lacks {', '.join(missing)} (ADR 0012's event table)")
    rurl_devel = pipelines.get("schedule-rurl-devel")
    if rurl_devel and "coverage" not in rurl_devel:
        report.gap("ci", "the rurl-devel schedule's pipeline does not run coverage; every pipeline on main carries "
                         "it (ADR 0012)")
    if rurl_devel and pkg != SCHEDULE_EXCEPTION[1] and set(rurl_devel) - {"coverage"}:
        report.gap("ci", f"the rurl-devel schedule runs {', '.join(j for j in rurl_devel if j != 'coverage')}; the "
                         f"only schedule exception is {SCHEDULE_EXCEPTION[1]}'s rurl-devel (ADR 0012)")


def check_vendored_gate(source, sha: str, fleet: FleetCI, report: Report) -> None:
    """.fleet-ci/ is what fleet-ci's bin/vendor writes at the pinned SHA,
    byte for byte, and nothing else."""
    want = fleet.vendored(sha)
    have = sorted(path.removeprefix(".fleet-ci/") for path in source.tree() if path.startswith(".fleet-ci/"))
    rerun = f"re-run bin/vendor from a clean fleet-ci checkout at {sha[:12]}"
    for name in sorted(want):
        if name not in have:
            report.gap("ci", f".fleet-ci/{name} is missing; {rerun}")
        elif source.read_bytes(f".fleet-ci/{name}") != want[name]:
            report.gap("ci", f".fleet-ci/{name} differs from what fleet-ci's bin/vendor writes at {sha[:12]}; {rerun}")
    for name in have:
        if name not in want:
            report.gap("ci", f".fleet-ci/{name} is not written by fleet-ci's bin/vendor at {sha[:12]}; remove it")


def check_ci_migrated(pkg: str, source, state: State, floor: str | None, text: str, consumer: dict, entries: list,
                      fleet: FleetCI, report: Report) -> None:
    """A package that includes fleet-ci's template (ADR 0012), judged on its
    own file, the merged configuration and bin/rules-sim and bin/vendor, all
    at the fleet-ci commit it pins, read from `fleet`. A package file that
    cannot be read (a GitLab read that timed out) leaves the rest not judged
    and the run incomplete."""
    try:
        judge_ci_migrated(pkg, source, state, floor, text, consumer, entries, fleet, report)
    except ProbeError as error:
        report.skip("ci", f"could not read a file of the package ({error}), so the rest of its migrated CI rules "
                          "is not judged", incomplete=True)


def check_floor_leg(floor: str | None, variables: dict[str, str], report: Report) -> None:
    """The floor invariant (ADR 0007, carried by ADR 0012): with FLEET_FLOOR
    "true", t2-floor runs on R FLEET_FLOOR_R, whose minor is DESCRIPTION's
    `Depends: R (>= x.y)`. FLEET_FLOOR "false" is check_switches()'s."""
    if floor is None or variables.get("FLEET_FLOOR") != "true":
        return
    floor_r = variables.get("FLEET_FLOOR_R", "")
    if not re.fullmatch(r"\d+\.\d+(\.\d+)?", floor_r) or minor(floor_r) != floor:
        report.gap("ci", f"no deep-check leg at the declared R floor ({floor}): FLEET_FLOOR_R is {floor_r!r}, and "
                         f"t2-floor runs on that R; set it to an R {floor}.x release")


def judge_ci_migrated(pkg: str, source, state: State, floor: str | None, text: str, consumer: dict, entries: list,
                      fleet: FleetCI, report: Report) -> None:
    """check_ci_migrated()'s judgments; a failed package read propagates."""
    check_consumer(pkg, consumer, report)
    check_audit_files(source, report)
    if pkg in FOSSA_PACKAGES and not any(
            str(name).startswith("x-") and isinstance(body, dict)
            and any(re.search(r"\bfossa analyze\b", item) for item in script_items(body.get("script")))
            for name, body in consumer.items()):
        report.gap("ci", "no x-* job runs `fossa analyze` (x-fossa, on .t2-job, ADR 0012)")
    sha = pinned_sha(entries, report)
    if sha is None:
        return
    short = sha[:12]
    try:
        if not fleet.has_commit(sha):
            report.gap("ci", f"the fleet-ci include pins {sha}, an unknown fleet-ci commit: the clone at "
                             f"{fleet.clone} does not hold it (fetch the clone if it is new: git -C {fleet.clone} "
                             "fetch --tags)")
            report.skip("ci", f"fleet-ci {short} is unknown, so the pinned template, its rules and the vendored gate "
                              "are not judged", incomplete=True)
            return
        if not fleet.v_tags(sha):
            if fleet.any_v_tags():
                report.gap("ci", f"the fleet-ci include pins {sha}, which no v* tag points at; pin the commit a "
                                 "released v* tag points at (ADR 0012)")
            else:
                # A clone fetched without tags cannot tell; the SHA is real,
                # so this is not a gap.
                report.skip("ci", f"no v* tag in the clone at {fleet.clone} points at the pinned {sha}, so whether "
                                  f"the pin is a released fleet-ci is not judged; fetch fleet-ci tags: git -C "
                                  f"{fleet.clone} fetch --tags", incomplete=True)
        template_text = fleet.read(sha, FLEET_CI_TEMPLATE)
        if template_text is None:
            report.gap("ci", f"fleet-ci {short} has no {FLEET_CI_TEMPLATE}")
            return
        try:
            template = load_ci(template_text, references=True)
        except (CIError, RecursionError) as error:
            report.skip("ci", f"fleet-ci {short}'s {FLEET_CI_TEMPLATE} did not load ({error})", incomplete=True)
            return
        # GitLab merges the package's file over the included one: deep for
        # mappings, arrays replaced, as `extends` does.
        merged = deep_merge(template, {key: value for key, value in consumer.items() if key != "include"})
        jobs = {str(name) for name, block in merged.items()
                if isinstance(block, dict) and name not in RESERVED and not str(name).startswith(".")}
        missing = [job for job in FIXED_JOBS if job not in jobs]
        if missing:
            report.gap("ci", f"fleet-ci {short}'s template lacks {', '.join(missing)}, of ADR 0012's 13 jobs")
        extra = sorted(job for job in jobs - set(FIXED_JOBS) if not job.startswith("x-") and job not in consumer)
        if extra:
            report.gap("ci", f"fleet-ci {short}'s template adds {', '.join(extra)}, outside ADR 0012's 13 jobs")
        variables = as_strings(variables_of(merged.get("variables")))
        check_switches(pkg, source, state, variables, report)
        check_floor_leg(floor, variables, report)
        dockerfile = fleet.read(sha, FLEET_CI_DOCKERFILE)
        pins = DOCKER_PANDOC_RE.findall(dockerfile or "")
        if not pins:
            report.gap("ci", f"fleet-ci {short}'s {FLEET_CI_DOCKERFILE} does not pin pandoc (`ARG PANDOC_VERSION=`), "
                             f"so the image's pandoc is not the fleet's {PANDOC_PIN}")
        elif set(pins) != {PANDOC_PIN}:
            report.gap("ci", f"fleet-ci {short}'s {FLEET_CI_DOCKERFILE} pins pandoc {', '.join(pins)}, not the "
                             f"fleet's {PANDOC_PIN}")
        check_vendored_gate(source, sha, fleet, report)
        check_rules_sim(pkg, sha, text, variables, fleet, report)
    except FleetCIError as error:
        report.skip("ci", f"fleet-ci {short} could not be read ({error}), so the pinned template, its rules and "
                          "the vendored gate are not judged", incomplete=True)


@cache
def seor_docs_drift() -> str:
    """seor's scripts/check-docs-drift.R, the copy beside this script, read once."""
    return Path(__file__).resolve().with_name("check-docs-drift.R").read_text(encoding="utf-8", errors="replace")


def check_docs_drift_copy(source, report: Report) -> None:
    """A package's scripts/check-docs-drift.R is seor's: one canonical copy,
    vendored byte for byte (SEOR-lyciowif). It takes the package directory
    as its one argument and nothing repository-specific. A missing copy is a
    gap of its own, whatever else in the local gate runs roxygen2 on an
    export."""
    check_vendored_copy(source, report, "scripts/check-docs-drift.R", seor_docs_drift, "the canonical copy")


def check_vendored_copy(source, report: Report, path: str, seor_copy: Callable[[], str], role: str) -> None:
    """A package's `path` is seor's copy of it (`seor_copy()`), vendored byte
    for byte; `role` says what seor's copy is, in the gap. Compared as text
    with line endings made LF, so a local and a GitLab read agree. A missing
    copy is a gap of its own."""
    try:
        member = source.read(path)
    except ProbeError as error:
        report.skip("local gate", f"could not read {path} ({error})", incomplete=True)
        return
    if member is None:
        report.gap("local gate", f"no {path}; copy seor's, which every package vendors byte for byte")
        return
    try:
        seor = seor_copy()
    except OSError as error:
        report.skip("local gate", f"{path} not compared with seor's copy ({error})", incomplete=True)
        return
    if member.replace("\r\n", "\n") != seor.replace("\r\n", "\n"):
        report.gap("local gate", f"{path} differs from seor's, {role} (it is vendored byte for byte); "
                                 f"copy seor's {path} over it")


FLEET_CI_CONFIG = ".fleet-ci.yml"
FLEET_CI_GATE_KEYS = ("docs_gates", "cheap_gates", "host_gates")
FLEET_CI_HOOK = ".fleet-ci/pre-push"
FLEET_CI_GATE_RE = re.compile(r"\.fleet-ci/gate\b")
DOCS_DRIFT_SCRIPT_RE = re.compile(r"\bscripts/check-docs-drift\.R\b")
# T1's other cheap gates (design/fleet-standard.md, "Verification tiers"),
# each found by a stable token, case aside, in a command a .fleet-ci.yml gate
# list holds: the command itself, not the scripts it runs. The NEWS version
# gate is a command naming "news" that is not the terseness check
# (runs_news_check()), which is judged on its own.
T1_GATES = (
    ("readme", "README drift (README.md matches a fresh knit of README.Rmd)", "sh scripts/check-readme-drift.sh"),
    ("news", "NEWS version (NEWS.md's top heading names DESCRIPTION's Version)", "sh scripts/check-news-version.sh"),
    ("lint", "lint", "Rscript -e 'lintr::lint_package()'"),
    ("spell", "spelling", "Rscript -e 'spelling::spell_check_package()'"),
)
TOOLCHAIN_SCRIPT_RE = re.compile(r"\bscripts/check-toolchain\.R\b")
# fleet-ci README, "Adopting the template", step 1.
FLEET_CI_RBUILDIGNORE = (r"^\.fleet-ci$", r"^\.fleet-ci\.yml$")


def migrated_pin(source) -> str | None:
    """The fleet-ci commit a migrated package's include pins, or None when it
    pins none (check_ci_migrated() reports why, under ci)."""
    included = fleet_ci_include(source.read(".gitlab-ci.yml") or "")
    return None if included is None else pinned_sha(included[1], Report(""))


def check_old_gate_hooks(precommit: str | None, report: Report) -> None:
    """fleet-ci README, "Adopting the template", step 5: the old `verify`
    hook is dropped, and no pre-commit hook runs .fleet-ci/gate; the
    .fleet-ci/pre-push shim runs the gate, pre-commit must not."""
    if precommit is None:
        return
    try:
        document = yaml.safe_load(precommit)
        hooks = [hook for repo in (document or {}).get("repos") or [] for hook in repo.get("hooks") or []]
        if not all(isinstance(hook, dict) for hook in hooks):
            raise ValueError("a `hooks` entry is not a mapping")
    except (yaml.YAMLError, ValueError, AttributeError, TypeError) as error:
        report.skip("local gate", f"could not read the hooks of .pre-commit-config.yaml ({error}), so whether it "
                                  "still runs the old gate is not judged", incomplete=True)
        return
    for hook in hooks:
        args = hook.get("args") or []
        command = " ".join(str(part) for part in [hook.get("entry") or "", *(args if isinstance(args, list) else [args])])
        if hook.get("id") == "verify":
            report.gap("local gate", ".pre-commit-config.yaml still has the old `verify` hook; drop it, the "
                                     f"{FLEET_CI_HOOK} shim runs the gate (fleet-ci README, \"Adopting the "
                                     "template\", step 5)")
        elif FLEET_CI_GATE_RE.search(command):
            report.gap("local gate", f".pre-commit-config.yaml hook `{hook.get('id')}` runs .fleet-ci/gate; the "
                                     f"{FLEET_CI_HOOK} shim runs the gate, pre-commit must not (fleet-ci README, "
                                     "\"Adopting the template\", step 5)")


def check_local_gate_migrated(source, report: Report, fleet: FleetCI | None = None) -> None:
    """The local gate of a package that includes fleet-ci's template, by
    fleet-ci's contract (README at FLEET_CI_FIXTURE_BASE, "The local gate"
    and "Adopting the template"). The vendored gate runs R CMD check
    --as-cran on an export of the pushed commit, in the image whose pandoc
    is the pin (judged under ci), so of the old verify hook's requirements
    what is left lives in .fleet-ci.yml, validated by fleet-ci's own
    classifier at the pinned SHA (FleetCI.config()): the generated-docs
    drift check, scripts/check-docs-drift.R, in `cheap_gates` (it needs the
    dependencies), a URL check in a gate list (the gate turns remote
    incoming, which checks URLs, off), and T1's README drift, NEWS version,
    lint and spelling gates in a gate list (T1_GATES). The NEWS check stays
    a pre-commit pre-push hook, which the fleet-ci hook runs, or is a
    .fleet-ci.yml gate. A pre-push hook runs scripts/check-toolchain.R on
    the host (check_toolchain_hook()). .Rbuildignore keeps .fleet-ci and
    .fleet-ci.yml out of the build, and pre-commit no longer runs the old
    gate. The hook, .fleet-ci/pre-push, is judged with the rest of
    .fleet-ci/, under ci."""
    fleet = fleet or FLEET_CI
    try:
        config_text = source.read(FLEET_CI_CONFIG)
        precommit = source.read(".pre-commit-config.yaml")
        buildignore = source.read(".Rbuildignore")
        sha = migrated_pin(source)
    except ProbeError as error:
        report.skip("local gate", f"could not read a file the local gate is judged on ({error})", incomplete=True)
        return
    ignored = {line.strip() for line in (buildignore or "").splitlines()}
    for pattern in FLEET_CI_RBUILDIGNORE:
        if pattern not in ignored:
            report.gap("local gate", f".Rbuildignore lacks `{pattern}` (fleet-ci README, \"Adopting the template\", "
                                     "step 1)")
    check_old_gate_hooks(precommit, report)
    check_toolchain_hook(precommit, source, report)
    config: dict | None = None
    if config_text is None:
        report.gap("local gate", f"no {FLEET_CI_CONFIG}, which the fleet-ci gate reads its gates from")
        config = {}
    elif sha is None:
        report.skip("local gate", f"{FLEET_CI_CONFIG} not validated: the include pins no fleet-ci commit (under ci), "
                                  "so fleet-ci's classifier has no version to read it with; its gates are not judged",
                    incomplete=True)
        return
    else:
        try:
            config, complaint = fleet.config(sha, config_text)
        except FleetCIError as error:
            report.skip("local gate", f"{FLEET_CI_CONFIG} not validated: fleet-ci {sha[:12]} could not be read "
                                      f"({error}); its gates are not judged", incomplete=True)
            return
        if config is None:
            report.gap("local gate", f"{FLEET_CI_CONFIG} does not load as fleet-ci's schema reads it ({complaint}), "
                                     "so the gate refuses every push")
            config = {}

    def runs(commands: list[str]) -> list[tuple[str, str]]:
        """Each command, then the R and shell scripts it runs, three levels deep."""
        out = []
        for command in commands:
            out.append(("", command))
            out += [(path, s) for path, s in inline_scripts(command, source, depth=3)
                    if Path(path).suffix in ("", ".R", ".r", ".sh")]
        return out

    def gate_list(key: str) -> list[str]:
        value = config.get(key)
        return [str(command) for command in value] if isinstance(value, list) else []

    try:
        cheap = runs(gate_list("cheap_gates"))
        gates = runs([command for key in FLEET_CI_GATE_KEYS for command in gate_list(key)])
    except ProbeError as error:
        report.skip("local gate", f"could not read a script a {FLEET_CI_CONFIG} gate runs ({error})", incomplete=True)
        return
    if not any(DOCS_DRIFT_SCRIPT_RE.search(chunk) for _, chunk in cheap):
        report.gap("local gate", f"no generated-docs drift check in {FLEET_CI_CONFIG}'s cheap_gates: `Rscript "
                                 "scripts/check-docs-drift.R .`, the fleet's drift check, which runs roxygen2 on the "
                                 "gate's export")
    if not any(URL_CHECK_RE.search(chunk) for _, chunk in gates):
        report.gap("local gate", f"no URL check in {FLEET_CI_CONFIG}'s gates ({', '.join(FLEET_CI_GATE_KEYS)}); the "
                                 "fleet-ci gate's R CMD check runs with remote incoming, and so its URL check, off")
    commands = [command for key in FLEET_CI_GATE_KEYS for command in gate_list(key)]
    for token, gate, example in T1_GATES:
        if not any(token in command.lower() and not (token == "news" and runs_news_check(command))
                   for command in commands):
            report.gap("local gate", f"no {gate} gate in {FLEET_CI_CONFIG}'s gates ({', '.join(FLEET_CI_GATE_KEYS)}): "
                                     f"no command naming {token!r}, such as `{example}`; T1 runs it (design/"
                                     "fleet-standard.md, \"Verification tiers\")")
    if any(runs_news_check(chunk) for _, chunk in gates):
        return
    if precommit is None:
        report.gap("local gate", "no NEWS terseness check in the pre-push gate: no .pre-commit-config.yaml, whose "
                                 f"pre-push stage {FLEET_CI_HOOK} runs, and no {FLEET_CI_CONFIG} gate runs "
                                 "scripts/check-news.py NEWS.md")
        return
    check_news_hook(precommit, source, report)


def check_local_gate(source, report: Report, shape: CIShape, fleet: FleetCI | None = None) -> None:
    """The local gate, fleet-ci's (check_local_gate_migrated()), as
    check_ci() found .gitlab-ci.yml (`shape`). Not judged without the
    include, whose gap check_ci() reports; not judged, and the run
    incomplete, when the file did not load, since whether it includes
    fleet-ci is then unknown."""
    if shape is CIShape.UNLOADED:
        report.skip("local gate", "not judged: .gitlab-ci.yml did not load, so whether it includes fleet-ci's "
                                  "template is unknown (under ci)", incomplete=True)
    elif shape is CIShape.NO_INCLUDE:
        report.skip("local gate", "not judged: .gitlab-ci.yml does not include fleet-ci's template (under ci)",
                    incomplete=False)
    else:
        check_local_gate_migrated(source, report, fleet)


AGENT_FILES = ("AGENTS.md", "AGENTS_LANG.md", "CLAUDE.md")
NEWS_RULE_RE = re.compile(r"\bone\s+terse\s+line\b", re.I)
NEWS_CHECK_RE = re.compile(r"\bcheck-news\.py\b")
NEWS_FILE_RE = re.compile(r"\bNEWS\.md\b")
# pre-commit's stage names for the pre-push hook; `push` is the legacy one.
PRE_PUSH_STAGES = {"pre-push", "push"}


def check_news_rule(source, report: Report) -> None:
    """The NEWS rule (design/fleet-standard.md, "NEWS.md bullets",
    SEOR-mjrpwnqz): an agent file says a NEWS.md bullet is "one terse line".
    The test is loose: some agent file names NEWS anywhere and says "one
    terse line" anywhere, not necessarily of NEWS. An agent file that cannot
    be read is skipped; when none of the others carries the rule, the run is
    then incomplete rather than a gap. The pre-push hook half is
    check_news_hook(), run from check_local_gate()."""
    texts, unread = [], False
    for path in AGENT_FILES:
        try:
            text = source.read(path)
        except ProbeError as error:
            report.skip("files", f"could not read {path} ({error})", incomplete=True)
            unread = True
            continue
        if text is not None:
            texts.append(text)
    if not unread and not any("NEWS" in text and NEWS_RULE_RE.search(text) for text in texts):
        report.gap("files", f"no agent file ({', '.join(AGENT_FILES)}) carries the NEWS rule: a NEWS.md bullet is "
                            "one terse line, user-facing changes only, no housekeeping")


def runs_news_check(text: str) -> bool:
    """A line of `text`, outside comment lines, runs check-news.py on NEWS.md:
    it names both, and not `--self-test`."""
    return any(NEWS_CHECK_RE.search(line) and NEWS_FILE_RE.search(line) and "--self-test" not in line
               for line in strip_comment_lines(text).splitlines())


def pre_push_hooks(config: str) -> list[dict]:
    """The hooks of a .pre-commit-config.yaml that pre-commit runs at pre-push,
    as it decides: a hook's own `stages`, else the config's `default_stages`,
    else every stage. ValueError when the config is not that shape; a YAML
    error propagates."""
    document = yaml.safe_load(config)
    if not isinstance(document, dict):
        raise ValueError("not a mapping")
    default = document.get("default_stages")
    hooks = []
    for repo in document.get("repos") or []:
        if not isinstance(repo, dict):
            raise ValueError("a `repos` entry is not a mapping")
        for hook in repo.get("hooks") or []:
            if not isinstance(hook, dict):
                raise ValueError("a `hooks` entry is not a mapping")
            stages = hook.get("stages", default)
            if isinstance(stages, str):
                stages = [stages]
            if stages is None or PRE_PUSH_STAGES & {str(stage) for stage in stages}:
                hooks.append(hook)
    return hooks


def pre_push_runs(config: str, source, runs_it: Callable[[str], bool], report: Report) -> bool | None:
    """Whether a hook that runs at pre-push (pre_push_hooks()) runs a check:
    `runs_it` holds for its `entry` and `args`, or for an R or shell script
    they call, followed three levels deep. None when that is not judged (the
    hooks or a script could not be read), which this reports. A remote
    repository's hook carries no `entry` here, so it never counts."""
    try:
        hooks = pre_push_hooks(config)
    except (yaml.YAMLError, ValueError) as error:
        report.skip("local gate", f"could not read the hooks of .pre-commit-config.yaml ({error})", incomplete=True)
        return None
    for hook in hooks:
        args = hook.get("args") or []
        command = " ".join(str(part) for part in [hook.get("entry") or "", *(args if isinstance(args, list) else [args])])
        if runs_it(command):
            return True
        try:
            scripts = [s for path, s in inline_scripts(command, source, depth=3)
                       if Path(path).suffix in ("", ".R", ".r", ".sh")]
        except ProbeError as error:
            report.skip("local gate", f"could not read a script the pre-push gate runs ({error})", incomplete=True)
            return None
        if any(runs_it(script) for script in scripts):
            return True
    return False


def check_news_hook(config: str, source, report: Report) -> None:
    """The NEWS check in the pre-push gate (SEOR-mjrpwnqz): a pre-push hook
    that runs check-news.py on NEWS.md (pre_push_runs()). Its self-test
    alone, a hook on another stage, or check-news.py named only in a `name:`
    or a comment is no check."""
    if pre_push_runs(config, source, runs_news_check, report) is False:
        report.gap("local gate", "no NEWS terseness check in the pre-push gate: a `news-terse` hook running "
                                 "scripts/check-news.py NEWS.md at pre-push, ported from seor's")


def runs_toolchain_check(text: str) -> bool:
    """A line of `text`, outside comment lines, runs scripts/check-toolchain.R,
    and not its `--self-test`."""
    return any(TOOLCHAIN_SCRIPT_RE.search(line) and "--self-test" not in line
               for line in strip_comment_lines(text).splitlines())


def check_toolchain_hook(config: str | None, source, report: Report) -> None:
    """The host-side toolchain check: a pre-push hook (pre_push_runs()) runs
    scripts/check-toolchain.R, which compares this machine's pandoc with
    .fleet-ci/toolchain and its roxygen2 with Config/roxygen2/version. The
    gate runs in the fleet image, so nothing else compares the host's
    pandoc and roxygen2, which a local build_readme() or document() uses.
    Its self-test alone, or a hook on another stage, is no check."""
    want = ("no host toolchain check in the pre-push gate: a `check-toolchain` hook running "
            "`Rscript scripts/check-toolchain.R` at pre-push, which compares the local pandoc with "
            ".fleet-ci/toolchain and roxygen2 with Config/roxygen2/version")
    if config is None:
        report.gap("local gate", f"{want}; there is no .pre-commit-config.yaml")
    elif pre_push_runs(config, source, runs_toolchain_check, report) is False:
        report.gap("local gate", want)


TOOLCHAIN_PENDING = ("scripts/check-toolchain.R not compared with seor's copy: pending SEOR-bkwtrvhh "
                     "(check-toolchain reads the pin from fleet-ci)")


def check_toolchain_copy(report: Report) -> None:
    """A package's scripts/check-toolchain.R is not compared with seor's
    copy until check-toolchain.R reads the pin from fleet-ci
    (SEOR-bkwtrvhh): listed as not judged, leaving the run complete."""
    report.skip("local gate", TOOLCHAIN_PENDING, incomplete=False)


def check_schedules(state: State, report: Report, pkg: str = "") -> None:
    """The pipeline schedules: each sets SCHEDULE_KIND and targets main, and
    each required kind is there and active: deep-check (and pagerankr its
    rurl-devel). A dependency-audit schedule is neither required nor a gap
    (ADR 0012: the audits run in T2)."""
    required: tuple[str, ...] = ("deep-check",)
    exception, owner = SCHEDULE_EXCEPTION
    if pkg == owner:
        required += (exception,)
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
    for kind in required:
        found = kinds.get(kind, [])
        if not found:
            report.gap("schedules", f"no {kind} schedule")
        elif not any(s.get("active") for s in found):
            report.gap("schedules", f"the {kind} schedule is inactive")


def check_repo(pkg: str, source, state: State,
               fetch: Callable[[str], tuple[int, str, bytes]] | None = None,
               fleet: FleetCI | None = None) -> Report:
    """One package's report: its content (check_content()), then its CI and
    local gate. `fleet` is the fleet-ci clone the pinned template is read
    from (FLEET_CI when None)."""
    report = Report(pkg)
    floor = check_content(pkg, source, state, fetch, report)
    shape = check_ci(pkg, source, state, floor, report, fleet)
    check_local_gate(source, report, shape, fleet)
    check_toolchain_copy(report)
    return report


def check_content(pkg: str, source, state: State, fetch: Callable[[str], tuple[int, str, bytes]] | None,
                  report: Report) -> str | None:
    """The judgments that need no fleet-ci clone: badges and their images,
    README, logo, files, DESCRIPTION, the NEWS rule, the docs-drift copy and
    the schedules. Returns DESCRIPTION's R floor, which the CI rules read.
    The self-test judges its content rows with this alone when the clone is
    missing."""
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
    check_news_rule(source, report)
    check_docs_drift_copy(source, report)
    check_schedules(state, report, pkg)
    return floor


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


# An R stage table, as a gate command or hook may run one, whose opt-in
# stages drop_opt_in_stages() drops from a script inline_scripts() follows.
FIXTURE_GATES_R = """\
# Gates a wrapper script runs.
stages = list(
  lint = list(default = TRUE, run = function() lintr::lint_package()),
  spelling = list(default = TRUE, run = function() spelling::spell_check_package()),
  readme = list(default = TRUE, run = function() devtools::build_readme()),
  news = list(default = TRUE, run = function() {
    h <- readLines("NEWS.md")[1]
    stopifnot(grepl("(development version)", h, fixed = TRUE))
  }),
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


# A package's pre-push hooks: check-toolchain, the host-side pandoc and
# roxygen2 check (check_toolchain_hook()), and the NEWS check
# (check_news_hook()). The gate itself is .fleet-ci/pre-push's, never a hook.
FIXTURE_PRECOMMIT = """\
repos:
  - repo: local
    hooks:
      - id: check-toolchain
        entry: Rscript scripts/check-toolchain.R
        language: system
        stages: [pre-push]
      - id: news-terse
        entry: python3 scripts/check-news.py NEWS.md
        language: system
        stages: [pre-push]
"""

FIXTURE_NEWS_RULE = ("### NEWS\n\nA `NEWS.md` bullet goes only to a change a package user notices. One terse\n"
                     "line, no rationale prose, one issue reference.\n")


def fixture_files(pkg: str, ref: str, vendored: dict[str, bytes], on_cran: bool = True, release: bool = True,
                  doi: str | None = "10.5281/zenodo.111", variables: str = "", jobs: str = "") -> dict:
    """A conforming package that includes fleet-ci's template at `ref`, with
    .fleet-ci/ as `vendored` (what bin/vendor writes there), .fleet-ci.yml
    carrying the docs-drift, URL and T1 gates, the toolchain and NEWS checks
    pre-push hooks, .Rbuildignore keeping .fleet-ci and .fleet-ci.yml out of
    the build; `variables` and `jobs` go into its .gitlab-ci.yml
    (fixture_consumer()). The content rows build it without a fleet-ci
    clone, on a placeholder `ref` and no `vendored` files, which only the CI
    and local-gate rules read."""
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
        ".gitlab-ci.yml": fixture_consumer(ref, variables, jobs),
        ".pre-commit-config.yaml": FIXTURE_PRECOMMIT,
        "AGENTS_LANG.md": FIXTURE_NEWS_RULE,
        FLEET_CI_CONFIG: FIXTURE_FLEET_CI_YML,
        "scripts/check-urls.R": "db <- tools:::url_db_from_package_sources('.')\nbad <- tools:::check_url_db(db)\n",
        ".Rbuildignore": "^.*\\.Rproj$\n^\\.fleet-ci$\n^\\.fleet-ci\\.yml$\n",
        ".gitlab/issue_templates/Bug.md": "x\n",
        ".gitlab/merge_request_templates/Default.md": "x\n",
        # The docs-drift check every member vendors: seor's, byte for byte.
        "scripts/check-docs-drift.R": seor_docs_drift(),
    })
    # logo.svg and logo.png as logo-metadata.py writes them from the
    # DESCRIPTION above. A package it does not know gets placeholders.
    if pkg in logo_metadata().PACKAGES:
        files["man/figures/logo.svg"], files["man/figures/logo.png"] = fixture_logos(pkg, files["DESCRIPTION"])
    else:
        files.update({path: "x\n" for path in LOGO_FILES})
    files.update({path: "x\n" for path in AUDIT_TEST_FILES})
    files.update({f".fleet-ci/{name}": body for name, body in vendored.items()})
    return files


@cache
def fixture_logos(pkg: str, description: str) -> tuple[str, bytes]:
    """logo.svg (as text) and logo.png as logo-metadata.py writes them from
    `description`, on its own self-test artwork (TEST_SVG and test_png())."""
    lm = logo_metadata()
    new, _ = lm.check_logos(pkg, description, {"logo.svg": lm.TEST_SVG.encode("utf-8"), "logo.png": lm.test_png()})
    return new["logo.svg"].decode("utf-8"), new["logo.png"]


# The keywords logo-metadata.py writes for fixture_files("punycoder"), spelled
# out rather than built, so the generated fixture is checked against an
# independent list.
FIXTURE_LOGO_KEYWORDS = ["R", "rstats", "R package", "punycode", "idna", "idn", "unicode", "domain-names"]


def fixture_state(on_cran: bool = True, release: bool = True, doi: bool = True, fossa: bool = True) -> State:
    return State(
        on_cran=on_cran, on_runiverse=True, doi_resolves=True if doi else None, doi_is_concept=True if doi else None,
        has_release=release, fossa_project=fossa, r_release="4.6", r_oldrel="4.5",
        schedules=[
            {"id": 1, "description": "deep", "ref": "refs/heads/main", "active": True,
             "variables": [{"key": "SCHEDULE_KIND", "value": "deep-check"}]},
        ],
    )


# The fixture fleet-ci (fixture_fleet_ci()) is this commit's tree from the
# local clone (FLEET_CI_DIR), committed afresh in a scratch repository and
# tagged there, so the real template, bin/rules-sim and bin/vendor run on it.
FLEET_CI_FIXTURE_BASE = "a326159eca0a776e13f817ad82fbf24c0f3d9925"

# A migrated package's whole .gitlab-ci.yml: the include, the floor leg's
# settings, two x-* jobs (one through !reference), then `variables` and
# `jobs` a row adds.
FIXTURE_CONSUMER_CI = """\
include:
  - project: bart-turczynski/fleet-ci
    ref: {ref}
    file: templates/r-package.yml

variables:
  FLEET_FLOOR_R: "4.1.3"
  FLEET_FLOOR_SNAPSHOT: "https://packagemanager.posit.co/cran/2025-04-10"
{variables}
x-check-idn2:
  extends: .t2-job
  image: $FLEET_RELEASE_IMAGE
  variables:
    FLEET_RELEASE_VARIANT: fleet-r-idn2
  before_script:
    - !reference [.fleet-r, before_script]
  script:
    - !reference [.fleet-scripts, check]

x-renovate:
  extends: .schedule-job
  image: alpine:3
  variables:
    FLEET_JOB_SCHEDULE: deep-check
  script:
    - echo renovate
{jobs}"""

FIXTURE_RURL_DEVEL_JOB = """
x-rurl-devel:
  extends: .schedule-job
  image: alpine:3
  variables:
    FLEET_JOB_SCHEDULE: rurl-devel
  script:
    - echo rurl devel
"""

FIXTURE_FOSSA_JOB = """
x-fossa:
  extends: .t2-job
  image: alpine:3
  script:
    - fossa analyze
"""


# A package's .fleet-ci.yml: spelling as a docs gate; the docs-drift, lint,
# README drift, NEWS version and URL gates as cheap gates.
FIXTURE_SPELL_GATE = "  - Rscript -e 'spelling::spell_check_package()'\n"
FIXTURE_T1_GATES = {
    "readme": "  - sh scripts/check-readme-drift.sh\n",
    "news": "  - sh scripts/check-news-version.sh\n",
    "lint": "  - Rscript -e 'lintr::lint_package()'\n",
    "spell": FIXTURE_SPELL_GATE,
}
FIXTURE_FLEET_CI_YML = f"""\
version: 1
variant: fleet-r
docs_gates:
{FIXTURE_SPELL_GATE}cheap_gates:
  - Rscript scripts/check-docs-drift.R .
{FIXTURE_T1_GATES["lint"]}{FIXTURE_T1_GATES["readme"]}{FIXTURE_T1_GATES["news"]}  - Rscript scripts/check-urls.R
"""


def fixture_consumer(ref: str, variables: str = "", jobs: str = "") -> str:
    return FIXTURE_CONSUMER_CI.format(ref=ref, variables=variables, jobs=jobs)


def fixture_fleet_ci(clone: Path, dest: Path) -> dict[str, str]:
    """A fixture fleet-ci repository at `dest`, built from the fleet-ci
    `clone`'s tree at FLEET_CI_FIXTURE_BASE; its commits by name, each on a
    branch of that name. `v1` is that tree, tagged v1.0.0; `untagged` an
    empty commit on it with no tag; and, each on `v1` and tagged,
    `no-locale` (v1.0.1) the template without t2-locale, `pandoc` (v1.0.2)
    fleet-r's Dockerfile on pandoc 3.9, `no-rurl-coverage` (v1.0.3) coverage
    without the rurl-devel events, `bad-vendor` (v1.0.4) a bin/vendor that
    refuses. FleetCIError when the clone or the commit is missing, or the
    build fails."""
    if not FleetCI(clone).has_commit(FLEET_CI_FIXTURE_BASE):
        raise FleetCIError(f"the fleet-ci clone at {clone} lacks {FLEET_CI_FIXTURE_BASE} (git -C {clone} fetch)")
    try:
        archive = subprocess.run(["git", "-C", str(clone), "archive", "--format=tar", FLEET_CI_FIXTURE_BASE],  # noqa: S607
                                 capture_output=True, env=git_env(), timeout=120, check=True)
        dest.mkdir(parents=True)
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(dest, filter="data")
    except (OSError, subprocess.SubprocessError, tarfile.TarError, TypeError) as error:
        raise FleetCIError(f"git archive {FLEET_CI_FIXTURE_BASE} into {dest}: {error}") from error
    repo = FleetCI(dest)
    config = ("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
              "-c", "tag.gpgsign=false", "-c", "core.hooksPath=/dev/null", "-c", "init.defaultBranch=main")
    shas: dict[str, str] = {}

    def commit(name: str, tag: str | None) -> None:
        repo.git(*config, "add", "-A")
        repo.git(*config, "commit", "--quiet", "--allow-empty", "-m", name)
        shas[name] = repo.git("rev-parse", "HEAD").strip()
        repo.git(*config, "branch", "--force", name, shas[name])
        if tag:
            repo.git(*config, "tag", tag, shas[name])

    def variant(name: str, tag: str | None, path: str, edit: Callable[[str], str]) -> None:
        repo.git(*config, "checkout", "--quiet", "--detach", shas["v1"])
        target = dest / path
        old = target.read_text(encoding="utf-8")
        new = edit(old)
        if new == old:
            raise FleetCIError(f"fixture edit of {path} for {name} changed nothing")
        target.write_text(new, encoding="utf-8")
        commit(name, tag)

    repo.git(*config, "init", "--quiet")
    commit("v1", "v1.0.0")
    variant("untagged", None, "README.md", lambda text: text + "\nAn untagged commit.\n")
    variant("no-locale", "v1.0.1", FLEET_CI_TEMPLATE,
            lambda text: re.sub(r"(?ms)^t2-locale:\n.*?(?=^# Coverage through)", "", text))
    variant("pandoc", "v1.0.2", FLEET_CI_DOCKERFILE,
            lambda text: text.replace("ARG PANDOC_VERSION=3.10\n", "ARG PANDOC_VERSION=3.9\n"))
    variant("no-rurl-coverage", "v1.0.3", FLEET_CI_TEMPLATE,
            lambda text: text.replace("    - !reference [.fleet-events, rurl-devel-idn2]\n"
                                      "    - !reference [.fleet-events, rurl-devel]\n", ""))
    variant("bad-vendor", "v1.0.4", "bin/vendor",
            lambda text: text.replace("set -euo pipefail\n", "set -euo pipefail\necho 'vendor: broken' >&2\nexit 1\n", 1))
    repo.git(*config, "checkout", "--quiet", "--detach", shas["v1"])
    return shas


Judge = Callable[[Report], None]


# The include ref of the content rows' fixture when there is no fleet-ci
# clone: a well-formed SHA no rule reads, since those rows are then judged
# by check_content() alone.
CONTENT_FIXTURE_REF = "f" * 40


def self_test_rows(base: FleetCI | None, shas: dict[str, str] | None, fixture_dir: Path, fleets: list[FleetCI],
                   tally: dict[str, int]) -> list[str]:
    """The repository rows, each a package that includes fleet-ci's template
    from the fixture fleet-ci `base` (its commits by name, `shas`), pinned at
    `v1` unless the row says otherwise. Each row is queued with its judge
    (run()); once all are built, each is checked and judged. Clones a row
    builds go under `fixture_dir` and into `fleets`, which self_test()
    cleans up. Every row judged counts in tally["rows"].

    With `base` None (no fleet-ci clone), only the content rows run: badges,
    README, logo, files, DESCRIPTION, the NEWS rule, the docs-drift copy,
    schedules and seor's own logos, each judged by check_content() on a
    fixture at CONTENT_FIXTURE_REF with no .fleet-ci/. The CI and local-gate
    rows need the clone and are left out; self_test() reports them."""
    failures: list[str] = []
    queued: list[tuple[str, DictSource, State, object, Judge, FleetCI | None, bool]] = []
    v1 = shas["v1"] if shas else CONTENT_FIXTURE_REF
    known = set(shas.values()) if shas else set()

    def run(pkg: str, files: dict | DictSource, state: State, fetch=None, judge: Judge | None = None,
            fleet: FleetCI | None = None, full: bool = False) -> None:
        """Queue a row. Without a fleet-ci clone it is judged by
        check_content() alone, unless `full`: a row whose CI rules stop
        before fleet-ci is read (a file that does not load, no fleet-ci
        include) runs check_repo() either way."""
        source = files if isinstance(files, DictSource) else DictSource(files)
        queued.append((pkg, source, state, fetch, judge or (lambda report: None), fleet or base, full))

    def fixture_repo(pkg: str, on_cran: bool = True, release: bool = True,
                     doi: str | None = "10.5281/zenodo.111") -> dict:
        """A conforming package at `v1`; a FOSSA package carries x-fossa."""
        return fixture_files(pkg, v1, base.vendored(v1) if base else {}, on_cran, release, doi,
                             jobs=FIXTURE_FOSSA_JOB if pkg in FOSSA_PACKAGES else "")

    def loads(tag: str, report: Report) -> None:
        # A fixture GitLab would refuse leaves CI not judged, and a clean
        # report would then prove nothing: only the load-error rows want that.
        if any("could not read .gitlab-ci.yml" in text for _, text in report.unjudged):
            failures.append(f"{tag}: the fixture's .gitlab-ci.yml did not load: {report.unjudged}")

    def expect_clean(tag: str, pkg: str, files: dict, state: State, fetch=None) -> None:
        def judge(report: Report) -> None:
            loads(tag, report)
            if report.gaps:
                failures.append(f"{tag}: expected no gaps, got {report.gaps}")
        run(pkg, files, state, fetch, judge)

    def expect_gap(tag: str, needle: str, pkg: str, files: dict, state: State, fetch=None,
                   then: Judge | None = None, full: bool = False) -> None:
        """A row whose report holds a gap with `needle`; `then` judges the
        report further; `full` as run() reads it."""
        def judge(report: Report) -> None:
            loads(tag, report)
            if not any(needle in text for _, text in report.gaps):
                failures.append(f"{tag}: expected a gap containing {needle!r}, got {report.gaps}")
            if then is not None:
                then(report)
        run(pkg, files, state, fetch, judge, full=full)

    def edit(files: dict, path: str, old: str, new: str) -> dict:
        if old not in files[path]:
            raise SystemExit(f"self-test fixture edit not applicable: {old!r} in {path}")
        return dict(files, **{path: files[path].replace(old, new)})

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
    def fossa_old_gaps(old_report: Report) -> None:
        for needle in ("slot 17 FOSSA license: link differs", "slot 18 FOSSA security: image URL differs",
                       "slot 18 FOSSA security: link differs"):
            if not any(needle in text for _, text in old_report.gaps):
                failures.append(f"FOSSA bare locator: expected a gap containing {needle!r}, got {old_report.gaps}")

    expect_gap("FOSSA pair under the bare git+gitlab.com locator", "slot 17 FOSSA license: image URL differs",
               "seor", edit(seor, "README.Rmd", "<!-- badges: end -->", fossa_old + "<!-- badges: end -->"),
               fixture_state(on_cran=False, release=False, doi=False, fossa=True), then=fossa_old_gaps)
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

    def image_gaps(report: Report) -> None:
        if not any("HTTP 500" in t for _, t in report.gaps) or not any("not an image" in t for _, t in report.gaps):
            failures.append(f"image checks: expected HTTP 500 and not-an-image gaps, got {report.gaps}")
        if any("tinyverse" in t for _, t in report.gaps) or not any("tinyverse" in t for _, t in report.unjudged):
            failures.append("image checks: a network error must be not judged, never a gap")

    expect_gap("image renders unknown", "renders 'unknown'", "punycoder", cran, fixture_state(), fetch_bad,
               then=image_gaps)

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
    def no_banned(report: Report) -> None:
        if report.gaps:
            failures.append(f"a heading that only starts with a banned word is not banned, got {report.gaps}")

    run("punycoder", edit(cran, "README.Rmd", "## Learn more", "## Development version"), fixture_state(), judge=no_banned)
    expect_gap("no r-universe command", "no r-universe install.packages()", "punycoder",
               edit(cran, "README.Rmd", f'repos = c("https://{OWNER}.r-universe.dev", ', "repos = c("), fixture_state())
    def runiverse_kept(report: Report) -> None:
        if any("r-universe" in t for _, t in report.gaps):
            failures.append(f"on CRAN, no CRAN command: the r-universe command was there, got {report.gaps}")

    expect_gap("on CRAN, no CRAN command", 'no install.packages("punycoder") for CRAN', "punycoder",
               edit(cran, "README.Rmd", 'install.packages("punycoder")\n\n', ""), fixture_state(), then=runiverse_kept)

    def cran_unjudged(unknown_cran: Report) -> None:
        if any("for CRAN" in t for _, t in unknown_cran.gaps) or not any("CRAN command" in t for _, t in unknown_cran.unjudged):
            failures.append("Installation: unknown CRAN status must be not judged, never a gap")

    run("punycoder", edit(cran, "README.Rmd", 'install.packages("punycoder")\n\n', ""),
        State(**{**fixture_state().__dict__, "on_cran": None}), judge=cran_unjudged)
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
    def five_usable(report: Report) -> None:
        if any("usable" in t for _, t in report.gaps):
            failures.append(f"dropped keywords: five usable tokens remain, got {report.gaps}")

    expect_gap("dropped keywords", "lists r, rstats, which r-universe drops", "punycoder",
               edit(cran, "DESCRIPTION", "domain-names\n", "domain-names, r, rstats\n"), fixture_state(),
               then=five_usable)
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
    # The generated fixture against an independent list: both bags in logo.svg,
    # and logo.png's Keywords and XPKeywords.
    lm = logo_metadata()
    if lm.read_svg_subjects(cran["man/figures/logo.svg"]) != [FIXTURE_LOGO_KEYWORDS] * 2:
        failures.append(f"fixture logo.svg: keywords are not {FIXTURE_LOGO_KEYWORDS}")
    if lm.read_png_keywords(cran["man/figures/logo.png"]) != (", ".join(FIXTURE_LOGO_KEYWORDS),
                                                              "; ".join(FIXTURE_LOGO_KEYWORDS)):
        failures.append(f"fixture logo.png: keywords are not {FIXTURE_LOGO_KEYWORDS}")
    # The full logo-metadata.py --check (SEOR-seobtecv), on logo.svg and logo.png.
    png = "man/figures/logo.png"
    drifted_description = edit(cran, "DESCRIPTION", "domain-names\n", "domains\n")["DESCRIPTION"]
    old_svg, old_png = fixture_logos("punycoder", drifted_description)
    expect_clean("logo.svg and logo.png as logo-metadata.py writes them", "punycoder", cran, fixture_state())
    # The fixtures above come from check_logos() itself, so they cannot catch
    # a fault in it; seor's own committed logos, which logo-metadata.py
    # --check passes, are the independent anchor.
    seor_root = Path(__file__).resolve().parent.parent
    own = Report("seor")
    check_logo_metadata("seor", LocalSource(seor_root), own)
    if own.gaps or own.unjudged:
        failures.append(f"seor's own man/figures logos: expected no logo verdict, got {own.gaps} / {own.unjudged} "
                        "(does `python3 scripts/logo-metadata.py --check seor man/figures` pass?)")

    def only_logo_gap(path: str) -> Judge:
        def judge(report: Report) -> None:
            logo = [t for area, t in report.gaps if area == "logo"]
            if len(logo) != 1 or not logo[0].startswith(path):
                failures.append(f"expected one logo gap, on {path}, got {logo}")
        return judge

    expect_gap("a logo.png whose Keywords drifted from DESCRIPTION",
               "logo.png keywords differ from DESCRIPTION's X-schema.org-keywords (missing domain-names; extra domains)",
               "punycoder", dict(cran, **{png: old_png}), fixture_state(), then=only_logo_gap(png))
    expect_gap("a logo.png that matches, beside a logo.svg whose keywords drifted",
               "logo.svg keywords differ from DESCRIPTION's X-schema.org-keywords (missing domain-names; extra domains)",
               "punycoder", dict(cran, **{"man/figures/logo.svg": old_svg}), fixture_state(),
               then=only_logo_gap("man/figures/logo.svg"))
    # Metadata besides the keywords.
    expect_gap("a logo.svg whose dc:title drifted", "logo.svg differs from what logo-metadata.py writes", "punycoder",
               edit(cran, "man/figures/logo.svg", "<dc:title>punycoder</dc:title>", "<dc:title>punycode</dc:title>"),
               fixture_state(), then=only_logo_gap("man/figures/logo.svg"))
    expect_gap("a logo.png whose tEXt Author was edited", "logo.png differs from what logo-metadata.py writes",
               "punycoder", edit(cran, png, b"Author\0Bart Turczynski", b"Author\0Bart Turczynsky"), fixture_state(),
               then=only_logo_gap(png))
    expect_gap("a logo.png that is not a PNG", "logo.png cannot be judged by logo-metadata.py --check "
               "(logo-metadata: man/figures/logo.png is not a PNG)", "punycoder", dict(cran, **{png: "x\n"}),
               fixture_state(), then=only_logo_gap(png))
    expect_gap("a truncated logo.png", "man/figures/logo.png cannot be parsed", "punycoder",
               dict(cran, **{png: cran[png][:10]}), fixture_state())

    def logo_gaps(*paths: str) -> Judge:
        def judge(report: Report) -> None:
            logo = sorted(t.split(" ", 1)[0] for area, t in report.gaps if area == "logo")
            if logo != sorted(paths):
                failures.append(f"expected logo gaps on {sorted(paths)}, got {report.gaps}")
        return judge

    # A broken logo.png hides nothing: logo.svg's drift is still reported.
    expect_gap("a logo.svg that drifted beside a logo.png that is not a PNG",
               "logo.svg keywords differ from DESCRIPTION's X-schema.org-keywords", "punycoder",
               dict(cran, **{"man/figures/logo.svg": old_svg, png: "x\n"}), fixture_state(),
               then=logo_gaps("man/figures/logo.svg", png))
    # Without logo.svg's verdict, logo.png (which names it) is not judged.
    expect_gap("a logo.png beside a logo.svg that is not UTF-8", "logo.png cannot be judged by logo-metadata.py "
               "--check (not judged without logo.svg's verdict)", "punycoder",
               dict(cran, **{"man/figures/logo.svg": cran["man/figures/logo.svg"].encode() + b"\xff"}),
               fixture_state())
    expect_gap("a logo.svg that is not UTF-8", "logo.svg cannot be parsed (UnicodeDecodeError", "punycoder",
               dict(cran, **{"man/figures/logo.svg": cran["man/figures/logo.svg"].encode() + b"\xff"}),
               fixture_state(), then=logo_gaps("man/figures/logo.svg", png))

    def short_logo_gaps(report: Report) -> None:
        if any(len(t) > 600 for area, t in report.gaps if area == "logo"):
            failures.append("a logo gap carries the file it could not parse")

    expect_gap("a logo.svg that is not UTF-8, named in short", "UnicodeDecodeError", "punycoder",
               dict(cran, **{"man/figures/logo.svg": cran["man/figures/logo.svg"].encode() + b"\xff"}),
               fixture_state(), then=short_logo_gaps)
    # With logo.svg missing, logo.png is judged alone, as --check judges it.
    lone_png = dict(cran, **{png: old_png})
    del lone_png["man/figures/logo.svg"]
    expect_gap("a drifted logo.png with no logo.svg", "logo.png keywords differ", "punycoder", lone_png,
               fixture_state())
    # DESCRIPTION is judged as read: one that is not UTF-8 is refused, as --check refuses it.
    expect_gap("a DESCRIPTION that is not UTF-8", "logo-metadata.py --check cannot judge the logo files", "punycoder",
               dict(cran, DESCRIPTION=cran["DESCRIPTION"].encode() + b"Note: caf\xe9\n"), fixture_state())

    class UnreadablePng(DictSource):
        def read_bytes(self, path: str) -> bytes | None:
            if path == png:
                raise ProbeError(f"reading {png}: 503")
            return super().read_bytes(path)

    def png_unjudged(report: Report) -> None:
        if (report.gaps or exit_status([report]) != 2
                or not any(area == "logo" and "not judged" in t for area, t in report.unjudged)):
            failures.append(f"an unreadable logo.png: expected the logo metadata not judged and exit 2, got "
                            f"{report.gaps} / {report.unjudged}")

    run("punycoder", UnreadablePng(cran), fixture_state(), judge=png_unjudged)
    expect_clean("a case-only duplicate tag in DESCRIPTION is not drift", "punycoder",
                 edit(cran, "DESCRIPTION", "domain-names\n", "domain-names, IDNA\n"), fixture_state())
    svg = "man/figures/logo.svg"
    expect_gap("a DESCRIPTION keyword edited without regenerating the logo",
               "logo.svg keywords differ from DESCRIPTION's X-schema.org-keywords (missing domains; extra domain-names)",
               "punycoder", edit(cran, "DESCRIPTION", "domain-names\n", "domains\n"), fixture_state())
    expect_gap("a logo tag edited by hand", "(missing unicode; extra Unicode)", "punycoder",
               edit(cran, svg, "<rdf:li>unicode</rdf:li>", "<rdf:li>Unicode</rdf:li>"), fixture_state())
    expect_gap("logo tags reordered", "(the same tags in another order", "punycoder",
               edit(cran, svg, "<rdf:li>idna</rdf:li><rdf:li>idn</rdf:li>", "<rdf:li>idn</rdf:li><rdf:li>idna</rdf:li>"),
               fixture_state())
    no_subject = dict(cran, **{svg: re.sub(r"<dc:subject>.*?</dc:subject>\n", "", cran[svg])})
    expect_gap("a logo.svg without keywords", "logo.svg has no keywords", "punycoder", no_subject, fixture_state())
    expect_gap("a DESCRIPTION logo-metadata.py refuses", "logo-metadata.py --check cannot judge the logo files "
               "(logo-metadata: DESCRIPTION: the tag '東京' is not Latin-1", "punycoder",
               edit(cran, "DESCRIPTION", "idn,", "idn, 東京,"), fixture_state())
    one_bag = dict(cran, **{svg: re.sub(r"<dc:subject>.*?</dc:subject>\n", "", cran[svg], count=1)})
    expect_gap("a logo.svg with one dc:subject bag", "(1 dc:subject bag(s) as logo-metadata.py writes them, not 2)",
               "punycoder", one_bag, fixture_state())
    expect_clean("a DESCRIPTION with a byte-order mark", "punycoder",
                 dict(cran, DESCRIPTION="﻿" + cran["DESCRIPTION"]), fixture_state())
    def no_logo_gap(report: Report) -> None:
        if any(area == "logo" for area, _ in report.gaps):
            failures.append(f"DESCRIPTION without keywords: expected no logo gap beside the description one, got {report.gaps}")

    run("punycoder", edit(cran, "DESCRIPTION", "X-schema.org-keywords: punycode, idna, idn, unicode,\n"
                          "    domain-names\n", ""), fixture_state(), judge=no_logo_gap)

    def one_svg_gap(report: Report) -> None:
        if sum("logo.svg" in t for _, t in report.gaps) != 1:
            failures.append(f"no logo.svg: expected the one missing-file gap, got {report.gaps}")

    run("punycoder", no_svg, fixture_state(), judge=one_svg_gap)
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

    # A judgment left out by choice (--offline) does not make the run incomplete.
    def complete(report: Report) -> None:
        if not report.unjudged or exit_status([report]) != 0:
            failures.append(f"an --offline skip alone: expected exit 0, got {exit_status([report])} for {report.unjudged}")

    run("punycoder", cran, fixture_state(), judge=complete)
    # A file that does not load, `!reference` allowed: CI is not judged, the
    # run is incomplete, the other areas are still judged.
    ci = ".gitlab-ci.yml"
    for tag, old, new in (("an unknown tag", "    - echo renovate\n", "    - !secret [renovate]\n"),
                          ("a syntax error", "include:\n", "include: [\n"),
                          ("an impossible date", "variables:\n", "released: 2026-02-30\nvariables:\n"),
                          ("a recursive alias", "    - echo renovate\n", "    - &loop [*loop]\n")):
        # The local gate is not judged either: whether the file includes
        # fleet-ci is unknown, so the run is incomplete (CIShape.UNLOADED).
        def load_error(report: Report, tag: str = tag) -> None:
            if (any(area == "ci" for area, _ in report.gaps)
                    or not any("missing ARCHITECTURE.md" in t for _, t in report.gaps)
                    or not any(area == "ci" and "could not read .gitlab-ci.yml" in t for area, t in report.unjudged)
                    or not any(area == "local gate" and ".gitlab-ci.yml did not load" in t
                               for area, t in report.unjudged)
                    or exit_status([Report("x", unjudged=report.unjudged, incomplete=report.incomplete)]) != 2):
                failures.append(f"load error: {tag}: expected CI and the local gate not judged and exit 2, got "
                                f"{report.gaps} / {report.unjudged}")

        run("punycoder", edit(no_arch, ci, old, new), fixture_state(), judge=load_error, full=True)

    # A file that loads but does not include fleet-ci's template: one CI gap,
    # and the local gate, fleet-ci's, not judged, the run still complete.
    no_include = "does not include fleet-ci's templates/r-package.yml"

    def not_migrated(report: Report) -> None:
        if ([area for area, _ in report.gaps] != ["ci"]
                or not any(area == "local gate" and "does not include fleet-ci's template" in t
                           for area, t in report.unjudged)
                or report.incomplete):
            failures.append(f"no fleet-ci include: expected the one CI gap, the local gate not judged and the run "
                            f"complete, got {report.gaps} / {report.unjudged}")

    expect_gap("no include at all", no_include, "punycoder",
               dict(cran, **{ci: "stages: [check]\ncheck:\n  script:\n    - R CMD check --as-cran x.tar.gz\n"}),
               fixture_state(), then=not_migrated, full=True)
    expect_gap("another project's include", no_include, "punycoder",
               edit(cran, ci, "project: bart-turczynski/fleet-ci", "project: bart-turczynski/other-ci"),
               fixture_state(), then=not_migrated, full=True)

    # NEGATIVE: local gate and schedules.
    # check-docs-drift.R is vendored (SEOR-lyciowif): every member carries
    # seor's copy, byte for byte. The fixture carries it.
    docs_drift = "scripts/check-docs-drift.R"
    expect_clean("a member's check-docs-drift.R identical to seor's", "punycoder", cran, fixture_state())
    docs_drift_drifted = "scripts/check-docs-drift.R differs from seor's, the canonical copy"
    docs_drift_missing = "no scripts/check-docs-drift.R; copy seor's, which every package vendors byte for byte"

    def one_gap(needle: str) -> Judge:
        def judge(report: Report) -> None:
            if len(report.gaps) != 1:
                failures.append(f"{needle}: expected its one gap, got {report.gaps}")
        return judge

    expect_gap("a member's check-docs-drift.R drifted from seor's", docs_drift_drifted, "punycoder",
               dict(cran, **{docs_drift: cran[docs_drift] + "# a local edit\n"}), fixture_state(),
               then=one_gap(docs_drift_drifted))
    expect_clean("a member's check-docs-drift.R identical to seor's but for CRLF line endings", "punycoder",
                 dict(cran, **{docs_drift: cran[docs_drift].replace("\n", "\r\n")}), fixture_state())
    # Missing: the other docs-drift rule still passes (.fleet-ci.yml's cheap
    # gate names the script), so the missing copy is the one gap.
    expect_gap("no scripts/check-docs-drift.R", docs_drift_missing, "punycoder",
               {k: v for k, v in cran.items() if k != docs_drift}, fixture_state(),
               then=one_gap(docs_drift_missing))
    # The NEWS rule (SEOR-mjrpwnqz): an agent file carries it, and the
    # pre-push gate runs check-news.py. Each missing half is its one gap.
    no_news_rule = "carries the NEWS rule"
    no_news_hook = "no NEWS terseness check in the pre-push gate"
    expect_gap("no agent file carries the NEWS rule", no_news_rule, "punycoder",
               {k: v for k, v in cran.items() if k != "AGENTS_LANG.md"}, fixture_state(), then=one_gap(no_news_rule))
    expect_gap("an agent file without the NEWS rule", no_news_rule, "punycoder",
               dict(cran, **{"AGENTS_LANG.md": "### NEWS\n\nAdd a NEWS.md bullet per change.\n"}), fixture_state(),
               then=one_gap(no_news_rule))
    expect_clean("the NEWS rule in AGENTS.md instead", "punycoder",
                 dict({k: v for k, v in cran.items() if k != "AGENTS_LANG.md"}, **{"AGENTS.md": FIXTURE_NEWS_RULE}),
                 fixture_state())
    # The NEWS hook half, and the toolchain hook beside it, are judged in the
    # local gate, so these rows need the fleet-ci clone.
    if base is not None:
        expect_gap("no news-terse hook", no_news_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", "python3 scripts/check-news.py NEWS.md", "true"), fixture_state(),
                   then=one_gap(no_news_hook))
        expect_gap("check-news.py named only in a comment", no_news_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", "      - id: news-terse\n        entry: python3 scripts/check-news.py NEWS.md\n",
                        "      # scripts/check-news.py is not wired yet\n      - id: news-terse\n        entry: true\n"),
                   fixture_state(), then=one_gap(no_news_hook))
        # A pre-push hook that calls a shell script running the check counts.
        news_wrapped = edit(cran, ".pre-commit-config.yaml", "python3 scripts/check-news.py NEWS.md", "sh tools/news.sh")
        expect_clean("check-news.py run from a script a hook calls", "punycoder",
                     dict(news_wrapped, **{"tools/news.sh": "python3 scripts/check-news.py NEWS.md\n"}), fixture_state())
        # The hook runs the check on NEWS.md, at pre-push.
        news_hook = "        entry: python3 scripts/check-news.py NEWS.md\n        language: system\n        stages: [pre-push]\n"
        expect_gap("only check-news.py's self-test ported", no_news_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", news_hook, news_hook.replace("NEWS.md", "--self-test")),
                   fixture_state(), then=one_gap(no_news_hook))
        expect_gap("the news-terse hook on the pre-commit stage", no_news_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", news_hook, news_hook.replace("pre-push", "pre-commit")),
                   fixture_state(), then=one_gap(no_news_hook))
        expect_gap("check-news.py named only in the hook's name", no_news_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", news_hook,
                        "        name: python3 scripts/check-news.py NEWS.md\n        entry: 'true'\n"
                        "        language: system\n        stages: [pre-push]\n"),
                   fixture_state(), then=one_gap(no_news_hook))
        expect_gap("a script a hook calls that runs only check-news.py's self-test", no_news_hook, "punycoder",
                   dict(news_wrapped, **{"tools/news.sh": "python3 scripts/check-news.py --self-test  # NEWS.md\n"}),
                   fixture_state(), then=one_gap(no_news_hook))
        expect_clean("the news-terse hook inherits pre-push from default_stages", "punycoder",
                     dict(cran, **{".pre-commit-config.yaml": "default_stages: [pre-push]\n" + cran[".pre-commit-config.yaml"]
                                   .replace(news_hook, news_hook.replace("        stages: [pre-push]\n", ""))}),
                     fixture_state())
        expect_gap("the news-terse hook inherits pre-commit from default_stages", no_news_hook, "punycoder",
                   dict(cran, **{".pre-commit-config.yaml": "default_stages: [pre-commit]\n" + cran[".pre-commit-config.yaml"]
                                 .replace(news_hook, news_hook.replace("        stages: [pre-push]\n", ""))}),
                   fixture_state(), then=one_gap(no_news_hook))
        expect_clean("the news-terse hook with NEWS.md in args", "punycoder",
                     edit(cran, ".pre-commit-config.yaml", news_hook,
                          news_hook.replace(" NEWS.md\n", "\n        args: [NEWS.md]\n")), fixture_state())
        # The host toolchain check: a pre-push hook runs check-toolchain.R,
        # the local pandoc against .fleet-ci/toolchain (check_toolchain_hook()).
        no_toolchain_hook = "no host toolchain check in the pre-push gate"
        toolchain_hook = "        entry: Rscript scripts/check-toolchain.R\n        language: system\n        stages: [pre-push]\n"
        expect_gap("no check-toolchain hook", no_toolchain_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", "      - id: check-toolchain\n" + toolchain_hook, ""),
                   fixture_state(), then=one_gap(no_toolchain_hook))
        expect_gap("the check-toolchain hook on the pre-commit stage", no_toolchain_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", toolchain_hook, toolchain_hook.replace("pre-push", "pre-commit")),
                   fixture_state(), then=one_gap(no_toolchain_hook))
        expect_gap("only check-toolchain.R's self-test", no_toolchain_hook, "punycoder",
                   edit(cran, ".pre-commit-config.yaml", "Rscript scripts/check-toolchain.R\n",
                        "Rscript scripts/check-toolchain.R --self-test\n"),
                   fixture_state(), then=one_gap(no_toolchain_hook))
        expect_gap("no .pre-commit-config.yaml, so no check-toolchain hook", no_toolchain_hook, "punycoder",
                   {k: v for k, v in cran.items() if k != ".pre-commit-config.yaml"}, fixture_state())
        toolchain_wrapped = edit(cran, ".pre-commit-config.yaml", "Rscript scripts/check-toolchain.R\n",
                                 "sh tools/toolchain.sh\n")
        expect_clean("check-toolchain.R run from a script a hook calls", "punycoder",
                     dict(toolchain_wrapped, **{"tools/toolchain.sh": "Rscript scripts/check-toolchain.R\n"}),
                     fixture_state())
        expect_clean("the check-toolchain hook with its script in args", "punycoder",
                     edit(cran, ".pre-commit-config.yaml", "entry: Rscript scripts/check-toolchain.R\n",
                          "entry: Rscript\n        args: [scripts/check-toolchain.R]\n"), fixture_state())

        # An agent file that cannot be read is skipped: the hook half is still judged.
        class UnreadableAgents(DictSource):
            def read(self, path: str) -> str | None:
                if path == "AGENTS.md":
                    raise ProbeError("reading AGENTS.md: 503")
                return super().read(path)

        def hook_judged(report: Report) -> None:
            if (not any(no_news_hook in t for _, t in report.gaps)
                    or not any("could not read AGENTS.md" in t for _, t in report.unjudged)):
                failures.append(f"an unreadable agent file: expected the hook gap and the skip, got "
                                f"{report.gaps} / {report.unjudged}")

        run("punycoder", UnreadableAgents(edit(cran, ".pre-commit-config.yaml", "python3 scripts/check-news.py NEWS.md",
                                               "true")), fixture_state(), judge=hook_judged)
    no_deep = fixture_state()
    no_deep.schedules = no_deep.schedules[1:]
    expect_gap("deep-check schedule missing", "no deep-check schedule", "punycoder", cran, no_deep)
    stray = fixture_state()
    stray.schedules = stray.schedules + [{"id": 3, "description": "x", "ref": "dev", "active": True, "variables": []}]
    expect_gap("schedule without kind", "sets no SCHEDULE_KIND", "punycoder", cran, stray)

    # Unknown state is not judged, never a gap.
    def no_state_gaps(unknown: Report) -> None:
        if unknown.gaps and any(area in ("badges", "schedules") for area, _ in unknown.gaps):
            failures.append(f"unknown state produced badge/schedule gaps: {unknown.gaps}")

    run("punycoder", cran, State(), judge=no_state_gaps)

    # The CI and local gate rows: the merged configuration, bin/rules-sim and
    # bin/vendor at the pinned SHA, and fleet-ci's local gate.
    def queue_migrated(fleet: FleetCI) -> None:
        def migrated_repo(pkg: str, ref: str = v1, variables: str = "", jobs: str = "") -> dict:
            """A conforming package, the include at `ref`, .fleet-ci/ as
            bin/vendor writes it there (at v1 for a ref the fixture does not
            hold, or whose bin/vendor refuses), no x-* job but `jobs`."""
            vendored = fleet.vendored(ref if ref in known - {shas["bad-vendor"]} else v1)
            return fixture_files(pkg, ref, vendored, variables=variables, jobs=jobs)

        def migrated_state(pkg: str, kinds: tuple[str, ...] | None = None) -> State:
            """fixture_state() with ADR 0012's schedules only: deep-check, and
            pagerankr's rurl-devel; or `kinds`."""
            if kinds is None:
                kinds = ("deep-check", SCHEDULE_EXCEPTION[0]) if pkg == SCHEDULE_EXCEPTION[1] else ("deep-check",)
            state = fixture_state()
            state.schedules = [{"id": i, "description": kind, "ref": "main", "active": True,
                                "variables": [{"key": "SCHEDULE_KIND", "value": kind}]} for i, kind in enumerate(kinds)]
            return state

        def migrated(tag: str, pkg: str, files: dict | DictSource, needles: tuple[str, ...] = (),
                     absent: str | None = None, state: State | None = None, skips: tuple[str, ...] = (),
                     via: FleetCI | None = None, then: Judge | None = None) -> None:
            """A migrated row: no gap at all when `needles` and `absent` are
            both unset; else a gap holding each needle, and none holding
            `absent`. Nothing is left not judged but what `skips` names, each
            of which must be there, with the run incomplete, and the
            check-toolchain.R copy (TOOLCHAIN_PENDING). `via` is the fleet-ci
            clone the row reads, `fleet` when None; `then` judges further."""
            def judge(report: Report) -> None:
                loads(tag, report)
                unjudged = [text for area, text in report.unjudged if area in ("ci", "local gate", "schedules")
                            and text != TOOLCHAIN_PENDING and not any(skip in text for skip in skips)]
                if unjudged:
                    failures.append(f"{tag}: left not judged: {unjudged}")
                for skip in skips:
                    if not any(skip in text for _, text in report.unjudged) or not report.incomplete:
                        failures.append(f"{tag}: expected {skip!r} not judged and the run incomplete, got "
                                        f"{report.unjudged}")
                if not needles and absent is None and report.gaps:
                    failures.append(f"{tag}: expected no gaps, got {report.gaps}")
                for needle in needles:
                    if not any(needle in text for _, text in report.gaps):
                        failures.append(f"{tag}: expected a gap containing {needle!r}, got {report.gaps}")
                if absent is not None and any(absent in text for _, text in report.gaps):
                    failures.append(f"{tag}: expected no gap containing {absent!r}, got {report.gaps}")
                if then is not None:
                    then(report)
            run(pkg, files, state or migrated_state(pkg), judge=judge, fleet=via or fleet)

        migrated("migrated, pinned to the commit v1.0.0 points at", "punycoder", migrated_repo("punycoder"))
        migrated("migrated pagerankr with its rurl-devel suite", "pagerankr",
                 migrated_repo("pagerankr", jobs=FIXTURE_RURL_DEVEL_JOB))
        migrated("migrated, FOSSA package with x-fossa", "seor", migrated_repo("seor", jobs=FIXTURE_FOSSA_JOB),
                 absent="fossa analyze")
        migrated("migrated, FOSSA package without x-fossa", "seor", migrated_repo("seor"),
                 needles=("no x-* job runs `fossa analyze`",))
        # The pin: a SHA that a v* tag points at. A clone holding v* tags,
        # none of them at the SHA: a gap. A clone with no v* tag at all may
        # lack the tags only: not judged, never a gap. A SHA the clone does
        # not hold at all is an unknown fleet-ci commit: a gap.
        untagged = shas["untagged"]
        migrated("pinned to a commit no v* tag points at", "punycoder", migrated_repo("punycoder", ref=untagged),
                 needles=(f"pins {untagged}, which no v* tag points at",))
        notags = FleetCI(fixture_dir / "fleet-ci-notags")
        fleets.append(notags)
        fleet.git("clone", "--quiet", "--shared", "--no-tags", str(fleet.clone), str(notags.clone), cwd=fixture_dir)
        if notags.any_v_tags():
            raise FleetCIError(f"the fixture clone without tags at {notags.clone} holds a v* tag")
        migrated("pinned to an untagged commit, the clone holding no v* tag", "punycoder",
                 migrated_repo("punycoder", ref=untagged), via=notags,
                 skips=(f"no v* tag in the clone at {notags.clone} points at the pinned {untagged}",
                        f"fetch fleet-ci tags: git -C {notags.clone} fetch --tags"))
        unknown = "0123456789abcdef" * 2 + "01234567"
        migrated("pinned to a commit the clone does not hold", "punycoder", migrated_repo("punycoder", ref=unknown),
                 needles=(f"pins {unknown}, an unknown fleet-ci commit", f"git -C {fleet.clone} fetch"),
                 skips=(f"fleet-ci {unknown[:12]} is unknown", f"fleet-ci {unknown[:12]} could not be read"))
        # git failing in the clone (a lock, a timeout, a broken repository)
        # is not judged, never an unknown commit.
        broken = FleetCI(fixture_dir / "fleet-ci-broken")
        fleets.append(broken)
        broken.clone.mkdir()
        (broken.clone / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        migrated("git fails in the fleet-ci clone", "punycoder", migrated_repo("punycoder"), via=broken,
                 absent="unknown fleet-ci commit", skips=(f"fleet-ci {v1[:12]} could not be read",))
        for ref in ("main", "v1.0.0"):
            migrated(f"include ref {ref}, not a SHA", "punycoder", migrated_repo("punycoder", ref=ref),
                     needles=(f"ref {ref!r} is not a 40-hex commit SHA",),
                     skips=(f"{FLEET_CI_CONFIG} not validated: the include pins no fleet-ci commit",))
        # .fleet-ci/ is what bin/vendor writes at the pinned SHA, byte for byte.
        files = migrated_repo("punycoder")
        files[".fleet-ci/gate"] = files[".fleet-ci/gate"] + b"# a local edit\n"
        migrated("a vendored .fleet-ci file edited", "punycoder", files,
                 needles=(".fleet-ci/gate differs from what fleet-ci's bin/vendor writes",))
        files = migrated_repo("punycoder")
        files[".fleet-ci/notes.txt"] = "x\n"
        del files[".fleet-ci/VERSION"]
        migrated("a .fleet-ci file vendor does not write, and one missing", "punycoder", files,
                 needles=(".fleet-ci/notes.txt is not written by fleet-ci's bin/vendor",
                          ".fleet-ci/VERSION is missing"))
        # The event table is the template's: no rules, when or workflow.
        migrated("a template job's rules overridden", "punycoder",
                 migrated_repo("punycoder", jobs="\ncoverage:\n  rules:\n    - when: always\n"),
                 needles=("writes `rules` at coverage", ".gitlab-ci.yml redefines template job `coverage`",
                          "refuses .gitlab-ci.yml: consumer file breaks the standard"))
        migrated("the template's events overridden", "punycoder",
                 migrated_repo("punycoder", jobs="\n.fleet-events:\n  t2:\n    - when: always\n"),
                 needles=("overrides the template's hidden key `.fleet-events`",))
        migrated("workflow overridden", "punycoder",
                 migrated_repo("punycoder", jobs="\nworkflow:\n  rules:\n    - when: always\n"),
                 needles=("overrides `workflow`",))
        migrated("a job-level when", "punycoder",
                 migrated_repo("punycoder", jobs="\nx-notes:\n  extends: .t3-job\n  image: alpine:3\n  when: manual\n"
                                                 "  script:\n    - echo notes\n"),
                 needles=("x-notes: a job-level `when`",))
        migrated("an x-* job extending a list", "punycoder",
                 migrated_repo("punycoder", jobs="\nx-two:\n  extends: [.t2-job]\n  image: alpine:3\n"
                                                 "  script:\n    - echo two\n"),
                 needles=("x-two: extends ['.t2-job'], not exactly one of",))
        migrated("a job outside the fixed set and x-*", "punycoder",
                 migrated_repo("punycoder", jobs="\nlint:\n  extends: .t2-job\n  image: alpine:3\n"
                                                 "  script:\n    - echo lint\n"),
                 needles=("job `lint` is outside ADR 0012's 13 names and the x-* prefix",))
        # The job set: ADR 0012's 13, in the template at the pinned SHA.
        migrated("a template missing a T2 job", "punycoder", migrated_repo("punycoder", ref=shas["no-locale"]),
                 needles=("lacks t2-locale, of ADR 0012's 13 jobs", "the deep-check pipeline lacks t2-locale"))
        # Switches off only where the package lacks the capability.
        off = '  FLEET_SANITIZERS: "false"\n'
        files = migrated_repo("punycoder", variables=off)
        files["src/punycode.c"] = "int punycode;\n"
        migrated("sanitizers off in a package with src/", "punycoder", files,
                 needles=('FLEET_SANITIZERS is "false", but the package has compiled code',))
        migrated("sanitizers off in a package without src/", "punycoder", migrated_repo("punycoder", variables=off))
        floor_off = '  FLEET_FLOOR: "false"\n'
        migrated("the floor off with no reason recorded", "punycoder", migrated_repo("punycoder", variables=floor_off),
                 needles=('FLEET_FLOOR is "false" with no reason recorded',))
        files = migrated_repo("punycoder", variables=floor_off)
        files["ARCHITECTURE.md"] = "The floor leg is off (FLEET_FLOOR): the package has no R floor below 4.6.\n"
        migrated("the floor off, its reason recorded", "punycoder", files)
        files = migrated_repo("punycoder", variables='  FLEET_MANUAL: "false"\n')
        files["ARCHITECTURE.md"] = "FLEET_MANUAL is off: no reason good enough.\n"
        migrated("the manual off for a package on CRAN", "punycoder", files,
                 needles=('FLEET_MANUAL is "false" for a package on CRAN',))
        # The incoming settings: FLEET_INCOMING off in seor alone, the remote
        # half in pslr alone (ADR 0004, carried forward).
        incoming_off = '  FLEET_INCOMING: "false"\n'
        migrated("incoming off outside seor", "punycoder", migrated_repo("punycoder", variables=incoming_off),
                 needles=('FLEET_INCOMING is "false"',))
        migrated("incoming off in seor", "seor", migrated_repo("seor", variables=incoming_off, jobs=FIXTURE_FOSSA_JOB),
                 absent="FLEET_INCOMING")
        remote_off = '  FLEET_INCOMING_REMOTE: "false"\n'
        migrated("remote incoming off outside pslr", "punycoder", migrated_repo("punycoder", variables=remote_off),
                 needles=('FLEET_INCOMING_REMOTE is "false"',))
        migrated("remote incoming off in pslr", "pslr", migrated_repo("pslr", variables=remote_off),
                 absent="FLEET_INCOMING_REMOTE")
        # The pandoc pin lives in the image: fleet-r's Dockerfile at the SHA.
        migrated("an image on another pandoc", "punycoder", migrated_repo("punycoder", ref=shas["pandoc"]),
                 needles=(f"pins pandoc 3.9, not the fleet's {PANDOC_PIN}",))
        # pagerankr's rurl-devel is the one schedule exception, and carries coverage.
        migrated("a rurl-devel pipeline without coverage", "pagerankr",
                 migrated_repo("pagerankr", ref=shas["no-rurl-coverage"], jobs=FIXTURE_RURL_DEVEL_JOB),
                 needles=("the rurl-devel schedule's pipeline does not run coverage",))
        migrated("a rurl-devel suite outside pagerankr", "punycoder",
                 migrated_repo("punycoder", jobs=FIXTURE_RURL_DEVEL_JOB),
                 needles=("x-rurl-devel: runs on the 'rurl-devel' schedule",
                          "the rurl-devel schedule runs x-rurl-devel; the only schedule exception"))
        # The local gate, by fleet-ci's contract: .fleet-ci.yml loading as
        # fleet-ci's classifier reads it and carrying the docs-drift cheap
        # gate and a URL check; the old verify hook gone and no hook running
        # .fleet-ci/gate; .Rbuildignore keeping .fleet-ci and .fleet-ci.yml
        # out of the build.
        files = migrated_repo("punycoder")
        files[FLEET_CI_CONFIG] = FIXTURE_FLEET_CI_YML.replace("  - Rscript scripts/check-docs-drift.R .\n", "")
        migrated("migrated, no docs-drift cheap gate", "punycoder", files,
                 needles=(f"no generated-docs drift check in {FLEET_CI_CONFIG}'s cheap_gates",))
        files = migrated_repo("punycoder")
        files[FLEET_CI_CONFIG] = FIXTURE_FLEET_CI_YML.replace("  - Rscript scripts/check-docs-drift.R .\n",
                                                              "  - Rscript -e 'roxygen2::roxygenise()'\n")
        migrated("migrated, a bare roxygenise cheap gate, not the fleet's drift check", "punycoder", files,
                 needles=(f"no generated-docs drift check in {FLEET_CI_CONFIG}'s cheap_gates",))
        files = migrated_repo("punycoder")
        files[".pre-commit-config.yaml"] = FIXTURE_PRECOMMIT + ("      - id: verify\n        entry: Rscript tools/verify.R\n"
                                                                "        language: system\n        stages: [pre-push]\n")
        migrated("migrated, the old verify hook kept", "punycoder", files,
                 needles=(".pre-commit-config.yaml still has the old `verify` hook",))
        files = migrated_repo("punycoder")
        files[".pre-commit-config.yaml"] += ("      - id: fleet-gate\n        entry: .fleet-ci/gate\n"
                                             "        language: system\n        stages: [pre-push]\n")
        migrated("migrated, a pre-commit hook running .fleet-ci/gate", "punycoder", files,
                 needles=(".pre-commit-config.yaml hook `fleet-gate` runs .fleet-ci/gate",))
        for pattern in FLEET_CI_RBUILDIGNORE:
            files = migrated_repo("punycoder")
            files[".Rbuildignore"] = files[".Rbuildignore"].replace(pattern + "\n", "")
            migrated(f"migrated, .Rbuildignore without {pattern}", "punycoder", files,
                     needles=(f".Rbuildignore lacks `{pattern}`",))
        # The hook's wiring need not be named in Markdown.
        files = migrated_repo("punycoder")
        files["CONTRIBUTING.md"] = "x\n"
        migrated("migrated, the hook's wiring not named in Markdown", "punycoder", files)
        # A missing .fleet-ci/pre-push is one gap, under ci.
        files = migrated_repo("punycoder")
        del files[".fleet-ci/pre-push"]

        def pre_push_once(report: Report) -> None:
            found = [text for _, text in report.gaps if FLEET_CI_HOOK in text]
            if len(found) != 1:
                failures.append(f"a missing {FLEET_CI_HOOK}: expected one gap naming it, got {found}")

        migrated("migrated, .fleet-ci/pre-push missing", "punycoder", files,
                 needles=(f"{FLEET_CI_HOOK} is missing",), then=pre_push_once)
        # A migrated package's check-toolchain.R is not judged until it
        # reads the pin from fleet-ci (SEOR-bkwtrvhh).
        files = migrated_repo("punycoder")
        files["scripts/check-toolchain.R"] = "# a package's own pin reader\n"

        def toolchain_pending(report: Report) -> None:
            if not any(text == TOOLCHAIN_PENDING for _, text in report.unjudged):
                failures.append(f"a migrated check-toolchain.R: expected {TOOLCHAIN_PENDING!r} not judged, got "
                                f"{report.unjudged}")

        migrated("migrated, check-toolchain.R not seor's copy", "punycoder", files, then=toolchain_pending)
        files = migrated_repo("punycoder")
        files[FLEET_CI_CONFIG] = FIXTURE_FLEET_CI_YML.replace("  - Rscript scripts/check-urls.R\n", "")
        migrated("migrated, no URL check gate", "punycoder", files,
                 needles=(f"no URL check in {FLEET_CI_CONFIG}'s gates",))
        # T1's README drift, NEWS version, lint and spelling gates, each found
        # by its token in a gate list's command. Missing: a gap. Moved to
        # host_gates, in another spelling: still found.
        others = ("readme", "news", "lint", "spell")
        respelled = {"readme": "  - Rscript tools/README-check.R\n", "news": "  - Rscript tools/NEWS_version.R\n",
                     "lint": "  - Rscript -e 'lintr::lint_dir(\"R\")'\n", "spell": "  - Rscript tools/Spelling.R\n"}
        for token, gate, _ in T1_GATES:
            line = FIXTURE_T1_GATES[token]
            without = FIXTURE_FLEET_CI_YML.replace("docs_gates:\n" + line if token == "spell" else line, "")
            files = migrated_repo("punycoder")
            files[FLEET_CI_CONFIG] = without
            needle = f"no {gate} gate in {FLEET_CI_CONFIG}'s gates"
            migrated(f"migrated, no {token} gate", "punycoder", files, needles=(needle,),
                     then=one_gap(needle))
            files = migrated_repo("punycoder")
            files[FLEET_CI_CONFIG] = without + "host_gates:\n" + respelled[token]
            migrated(f"migrated, the {token} gate a host gate, spelled otherwise", "punycoder", files)
            if any(other != token and other in respelled[token].lower() for other in others):
                raise SystemExit(f"self-test fixture: the respelled {token} gate names another token")
        # The terseness check is not the NEWS version gate, though it names NEWS.
        files = migrated_repo("punycoder")
        files[FLEET_CI_CONFIG] = (FIXTURE_FLEET_CI_YML.replace(FIXTURE_T1_GATES["news"], "")
                                  + "host_gates:\n  - python3 scripts/check-news.py NEWS.md\n")
        news_version = f"no {T1_GATES[1][1]} gate in {FLEET_CI_CONFIG}'s gates"
        migrated("migrated, only the NEWS terseness gate, no NEWS version gate", "punycoder", files,
                 needles=(news_version,), then=one_gap(news_version))
        # seor's disposition-row audit test files (osv-audit, security-audit).
        files = migrated_repo("punycoder")
        del files["tests/testthat/helper-security.R"]
        audit_shape = "audit jobs lack seor's disposition-row shape: missing tests/testthat/helper-security.R"
        migrated("audit shape", "punycoder", files, needles=(audit_shape,), then=one_gap(audit_shape))
        files = migrated_repo("punycoder")
        del files[FLEET_CI_CONFIG]
        migrated("migrated, no .fleet-ci.yml", "punycoder", files,
                 needles=(f"no {FLEET_CI_CONFIG}, which the fleet-ci gate reads",
                          f"no generated-docs drift check in {FLEET_CI_CONFIG}'s cheap_gates"))
        files = migrated_repo("punycoder")
        files[FLEET_CI_CONFIG] = FIXTURE_FLEET_CI_YML + "cheap_gate:\n  - true\n"
        migrated("migrated, .fleet-ci.yml with an unknown key", "punycoder", files,
                 needles=(f"{FLEET_CI_CONFIG} does not load as fleet-ci's schema reads it "
                          f"({FLEET_CI_CONFIG}: unknown key 'cheap_gate')",))
        # fleet-ci's own classifier at the pin is the schema: it also
        # checks an exclude_tests path lies under tests/.
        files = migrated_repo("punycoder")
        files[FLEET_CI_CONFIG] = FIXTURE_FLEET_CI_YML + "exclude_tests:\n  - path: R/net.R\n    why: network\n"
        migrated("migrated, .fleet-ci.yml excluding a test outside tests/", "punycoder", files,
                 needles=("exclude_tests path 'R/net.R' must be a file under tests/",))
        files = migrated_repo("punycoder")
        files[".pre-commit-config.yaml"] = FIXTURE_PRECOMMIT.split("      - id: news-terse\n")[0]
        migrated("migrated, no NEWS check", "punycoder", files,
                 needles=("no NEWS terseness check in the pre-push gate",))
        files[FLEET_CI_CONFIG] = FIXTURE_FLEET_CI_YML + "host_gates:\n  - python3 scripts/check-news.py NEWS.md\n"
        migrated("migrated, the NEWS check a host gate", "punycoder", files)
        # Schedules: deep-check alone (pagerankr adds rurl-devel); a
        # dependency-audit schedule is neither required nor a gap.
        migrated("migrated, with the old dependency-audit schedule too", "punycoder", migrated_repo("punycoder"),
                 state=migrated_state("punycoder", ("deep-check", "dependency-audit")))
        migrated("migrated, no deep-check schedule", "punycoder", migrated_repo("punycoder"),
                 state=migrated_state("punycoder", ("dependency-audit",)), needles=("no deep-check schedule",))
        migrated("migrated pagerankr, no rurl-devel schedule", "pagerankr",
                 migrated_repo("pagerankr", jobs=FIXTURE_RURL_DEVEL_JOB), state=migrated_state("pagerankr", ("deep-check",)),
                 needles=("no rurl-devel schedule",))
        # The floor invariant: FLEET_FLOOR_R's minor is DESCRIPTION's floor.
        files = migrated_repo("punycoder")
        files["DESCRIPTION"] = files["DESCRIPTION"].replace("Depends: R (>= 4.1.0)", "Depends: R (>= 4.2.0)")
        migrated("migrated, FLEET_FLOOR_R off the declared floor", "punycoder", files,
                 needles=("no deep-check leg at the declared R floor (4.2): FLEET_FLOOR_R is '4.1.3'",))
        files = migrated_repo("punycoder", variables=floor_off)
        files["DESCRIPTION"] = files["DESCRIPTION"].replace("Depends: R (>= 4.1.0)", "Depends: R (>= 4.2.0)")
        files["ARCHITECTURE.md"] = "The floor leg is off (FLEET_FLOOR): the package has no R floor below 4.6.\n"
        migrated("migrated, the floor off, FLEET_FLOOR_R not judged", "punycoder", files)
        # Template-owned image variables: never set by the package.
        for name in ("FLEET_RELEASE_IMAGE", "FLEET_FLOOR_IMAGE", "FLEET_IMAGE_R_RELEASE"):
            migrated(f"migrated, {name} set", "punycoder",
                     migrated_repo("punycoder", variables=f'  {name}: "rocker/r-ver:4.6.1"\n'),
                     needles=(f".gitlab-ci.yml sets `{name}` in its variables, a template-owned image variable",))
        # One bad SHA (its bin/vendor refuses), met by two packages: each is
        # not judged, and the run goes on.
        for pkg in ("punycoder", "raddr"):
            migrated(f"bin/vendor refuses at the pinned SHA ({pkg})", pkg, migrated_repo(pkg, ref=shas["bad-vendor"]),
                     skips=("bin/vendor exited 1: vendor: broken",))

        # A package file that cannot be read leaves CI not judged, never a
        # lost report.
        class UnreadableGate(DictSource):
            def read_bytes(self, path: str) -> bytes | None:
                if path == ".fleet-ci/gate":
                    raise ProbeError("reading .fleet-ci/gate: 503")
                return super().read_bytes(path)

        migrated("migrated, a .fleet-ci file unreadable", "punycoder", UnreadableGate(migrated_repo("punycoder")),
                 skips=("could not read a file of the package (reading .fleet-ci/gate: 503)",))

    if base is not None:
        queue_migrated(base)
    for pkg, source, state, fetch, judge, fleet, full in queued:
        if fleet is None and not full:
            report = Report(pkg)
            check_content(pkg, source, state, fetch, report)
        else:
            report = check_repo(pkg, source, state, fetch, fleet)
        judge(report)
        tally["rows"] += 1
    return failures


def self_test(skipped: list[str] | None = None, tally: dict[str, int] | None = None) -> list[str]:
    """The fixtures, in one pass: the case tables, then the repository rows
    (self_test_rows()) on a fixture fleet-ci built from the local clone
    (fixture_fleet_ci()). The CI and local-gate rows need the private
    fleet-ci clone (FLEET_CI: --fleet-ci, else FLEET_CI_DIR) holding
    FLEET_CI_FIXTURE_BASE, and Ruby; without any of them the content rows
    still run, judged by check_content(), and the self-test FAILS, naming
    the fix, unless SEOR_SKIP_FLEET_CI_SELFTEST=1, which appends the CI and
    local-gate rows to `skipped`, never to the failures. Everything from the
    fixture's temporary directory on runs inside one try/finally, which
    removes it. `tally` gets the number of repository rows judged ("rows")
    and of case-table entries checked ("cases"), which main() prints."""
    skipped = [] if skipped is None else skipped
    tally = {} if tally is None else tally
    tally.update(rows=0, cases=0)
    failures: list[str] = []

    # The YAML reader (load_ci(), `!reference` allowed): what loads, and the
    # refusals GitLab would make too, each a load error that leaves CI not
    # judged. Every expected value is what GitLab makes of the YAML, from the
    # YAML 1.1 spec and GitLab's documented semantics.
    load_cases: tuple[tuple[str, str, bool], ...] = (
        ("`!reference` loads", "job:\n  script:\n    - !reference [.r, script]\n", True),
        ("an unknown tag is a load error", "job:\n  script:\n    - !secret [.r, script]\n", False),
        ("a syntax error is a load error", "job:\n  script: [x\n", False),
        ("an impossible date is a load error", "variables: {D: 2026-02-30}\njob:\n  script: [x]\n", False),
        ("a scalar its tag cannot hold is a load error", "x: !!int 'abc'\njob:\n  script: [x]\n", False),
        ("a recursive alias in a script is a load error", "a: &a [*a]\njob:\n  script: *a\n", False),
        ("a recursive alias in a mapping is a load error", ".t: &t {v: *t}\njob: {extends: .t, script: [x]}\n",
         False),
        ("a top level that is no mapping is a load error", "- job\n", False),
        ("a trailing `---` adds no document", "job:\n  script: [x]\n---\n", True),
        ("a `spec:` header document, then the config",
         "spec:\n  inputs:\n    stage:\n      default: check\n---\njob:\n  script: [x]\n", True),
        ("two config documents are a load error", "a:\n  script: [x]\n---\njob:\n  script: [x]\n", False),
        ("a header holding more than `spec:` is a load error",
         "spec: {inputs: {}}\nstages: [x]\n---\njob:\n  script: [x]\n", False),
        ("two documents after a `spec:` header are a load error", "spec: {}\n---\na: 1\n---\njob:\n  script: [x]\n",
         False),
    )
    for tag, case, loads_ok in load_cases:
        tally["cases"] += 1
        try:
            load_ci(case, references=True)
            got = True
        except CIError:
            got = False
        except Exception as error:  # noqa: BLE001 - a reader that raises anything else fails the row
            got = f"raised {type(error).__name__}: {error}"
        if got != loads_ok:
            failures.append(f"load_ci: {tag}: expected {'a load' if loads_ok else 'a load error'}, got {got!r}")

    # Opt-in stages drop out; default ones stay.
    tally["cases"] += 1
    dropped = drop_opt_in_stages(FIXTURE_GATES_R)
    if "package_coverage" in dropped or "lint_package" not in dropped:
        failures.append("drop_opt_in_stages: kept an opt-in stage or dropped a default one")

    fixture_dir = Path(tempfile.mkdtemp(prefix="fleet-ci-fixture-"))
    fixture_fleet = FleetCI(fixture_dir / "fleet-ci")
    fleets = [fixture_fleet]
    try:
        clone = FLEET_CI.clone
        try:
            missing = None if FLEET_CI.has_commit(FLEET_CI_FIXTURE_BASE) else (
                f"the fleet-ci clone at {clone} lacks {FLEET_CI_FIXTURE_BASE}; fetch it: git -C {clone} fetch")
        except FleetCIError as error:
            missing = str(error)
        if missing is None and shutil.which("ruby") is None:
            missing = "ruby is not on PATH, and fleet-ci's bin/rules-sim and bin/classify read YAML with it"
        if missing is None:
            try:
                shas = fixture_fleet_ci(clone, fixture_fleet.clone)
                failures += self_test_rows(fixture_fleet, shas, fixture_dir, fleets, tally)
            except FleetCIError as error:
                failures.append(f"the fixture fleet-ci was not built, or a row not queued ({error})")
        else:
            # The content rows need no clone: they run either way.
            failures += self_test_rows(None, None, fixture_dir, fleets, tally)
            if os.environ.get("SEOR_SKIP_FLEET_CI_SELFTEST") == "1":
                skipped.append(f"the CI and local-gate rows, which need the fixture fleet-ci: {missing} "
                               "(SEOR_SKIP_FLEET_CI_SELFTEST=1)")
            else:
                failures.append(f"the CI and local-gate rows cannot run: {missing}. Fix that, or set "
                                "SEOR_SKIP_FLEET_CI_SELFTEST=1 to skip them on this machine")
    except Exception as error:  # noqa: BLE001 - a crash is a failure line, and the finally still cleans up
        failures.append(f"the self-test crashed: {type(error).__name__}: {error}")
    finally:
        for fleet in fleets:
            fleet.cleanup()
        shutil.rmtree(fixture_dir, ignore_errors=True)
    return failures


# --- main ----------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", choices=FLEET, help="check one package (default: all nine)")
    parser.add_argument("--local", type=Path, help="read a local checkout instead of GitLab main (needs --repo)")
    parser.add_argument("--offline", action="store_true", help="no network at all (needs --local)")
    parser.add_argument("--self-test", action="store_true", help="run the offline fixtures")
    parser.add_argument("--fleet-ci", type=Path, help=f"the fleet-ci clone a migrated package's pin is read from "
                                                      f"(default: $FLEET_CI_DIR, else {FLEET_CI_DIR})")
    args = parser.parse_args(argv)
    global FLEET_CI
    if args.fleet_ci:
        FLEET_CI = FleetCI(args.fleet_ci.expanduser())

    if yaml is None:
        print("check-fleet-standard: PyYAML is not installed, and .gitlab-ci.yml is read with it. Install it with "
              "`python3 -m pip install pyyaml==6.0.3`, or run the pre-commit hook, which installs it.", file=sys.stderr)
        return 2
    if args.self_test:
        skipped: list[str] = []
        tally: dict[str, int] = {}
        failures = self_test(skipped, tally)
        print(f"check-fleet-standard self-test: {tally['rows']} repository row(s) judged, {tally['cases']} "
              "case-table entr(ies) checked.")
        if skipped:
            banner = "!" * 78
            print(banner, file=sys.stderr)
            for skip in skipped:
                print(f"check-fleet-standard self-test: SKIPPED {skip}", file=sys.stderr)
            print("These rows did not run, so this pass does not cover them.", file=sys.stderr)
            print(banner, file=sys.stderr)
        if failures:
            print("check-fleet-standard self-test FAILED:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        if skipped:
            print(f"check-fleet-standard self-test: every check that ran passed; {len(skipped)} group(s) SKIPPED "
                  "(above).")
        else:
            print("check-fleet-standard self-test: all checks passed.")
        return 0
    if args.local and not args.repo:
        parser.error("--local needs --repo")
    if args.offline and not args.local:
        parser.error("--offline needs --local")

    try:
        reports = [run_one(pkg, args.local.expanduser() if args.local else None, args.offline)
                   for pkg in ([args.repo] if args.repo else FLEET)]
    finally:
        FLEET_CI.cleanup()
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
