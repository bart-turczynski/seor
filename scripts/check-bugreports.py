# check-bugreports v2 (seor adaptation of pslr's v2, PSLR-cvhksjst). v2 requires
# /-/work_items in DESCRIPTION too, the opposite of v1 and of the other
# packages' copies until SEOR-sptibjph reaches them: never re-port from those.
# seor's copy also carries the SEOR-jjblyiyd hardening (own tracker address,
# missing files, empty BugReports:, http:// and subgroup links, no seor-only
# paths, the package block's @seealso); the members' ports predate it.
"""BugReports / tracker-link gate.

WHY THIS EXISTS. CRAN runs two checks over a GitLab `BugReports:` URL and,
on gitlab.com, they contradict each other. `tools::check_url_db()` actually
fetches the address; GitLab moved issue reporting to work items, so the
classic `.../-/issues` path 404s for a client that does not send
`Accept: text/html` (the exact client CRAN's check uses) while
`.../-/work_items` serves 200. `tools:::.check_package_CRAN_incoming()`
never fetches anything -- it string-tests the path and flags anything but
`/issues`, `/-/work_items` included, with a "which should likely be"
NOTE proposing an `/issues` path (R 4.6.1 proposes
`.../-/work_items/issues`). No URL satisfies both.

The fleet used to keep `/-/issues` in DESCRIPTION
and `/-/work_items` everywhere else (SEOR-ocbtrrnl). pslr's 1.2.2
pretest then drew the 404 NOTE, and on 2026-10-23 Uwe Ligges (CRAN) called
the "should likely be" NOTE a bug in CRAN's check for GitLab and invited the
working form: "Please feel free to use the working form such as
https://gitlab.com/bart-turczynski/pslr/-/work_items and we will let it pass
and fix our checks." So every file, DESCRIPTION included, now names
`/-/work_items`, and none names `/-/issues` (SEOR-sptibjph, ADR 0011).

The package man page's "Report bugs at" link is not a separate decision.
`man/<pkg>-package.Rd` (`<pkg>` is `DESCRIPTION`'s `Package:`) is generated
from the R/ file holding roxygen2's `"_PACKAGE"` sentinel, which writes a
"Useful links" section verbatim from `DESCRIPTION`'s own `URL:`/`BugReports:`
fields. If that link is present it MUST agree with `DESCRIPTION`, or
`devtools::document()` was not re-run.

roxygen2 emits that generated section only when the package doc has no
`@seealso` of its own. seor's `R/seor-package.R` declares none, so
`man/seor-package.Rd` carries the line and it is compared. Its absence is
accepted only while an `@seealso` in the `"_PACKAGE"` block itself
suppresses it (pslr's shape).

WHAT IT CHECKS.

1. `DESCRIPTION`'s `BugReports:` is the `/-/work_items` address,
   optionally with a trailing slash, of the gitlab.com repository that
   `DESCRIPTION`'s `URL:` names, and `codemeta.json`'s `"issueTracker"`
   is the same address.
2. `man/<pkg>-package.Rd`'s "Report bugs at" link, when present, is
   IDENTICAL to `DESCRIPTION`'s `BugReports:` value; when absent, the
   `"_PACKAGE"` file declares the `@seealso` that suppresses it.
3. Every file that carries the tracker link exists, names this package's own
   `/-/work_items` address (the repository `BugReports:` and `URL:` agree
   on; another project's tracker may appear beside it, never instead), and
   none of them carries a `/-/issues` link (over `http://` or `https://`,
   in a subgroup or not):
     - codemeta.json (`"issueTracker"`)
     - .bestpractices.json
     - CONTRIBUTING.md (where to report a bug)
     - SECURITY.md (the confidential-issue channel)
4. No other human-facing surface carries a `/-/issues` link. These files
   name no tracker URL today, so the check forbids the old form without
   requiring the new one; requiring it would force a link nobody asked for
   into them:
     - README.Rmd, README.md, SECURITY-INSIGHTS.yml, _pkgdown.yml,
       vignettes/*.Rmd, .github/**

WHAT IT DOES NOT CHECK, ON PURPOSE.

* `NEWS.md` is a point-in-time record of what was announced. A historical
  bullet that quotes an old `/-/issues` form, including one arguing FOR that
  form, is not drift, so it is unchecked.
* `cran-comments.md` is unchecked too. seor's is the draft for its first
  submission, and it must quote the incoming check's NOTE, which proposes an
  `/issues` path, verbatim.
* Nothing here touches the network. Whether a URL currently resolves is a
  fact about the rest of the world; `R CMD check --as-cran` already fetches
  declared URLs, and a network call in a pre-push gate fails on a train.

Stdlib only, so it runs in any bare Python CI image, same shape as
`scripts/check-citation.py` (which this file does not import from or
modify -- that script is owned by a separate, fleet-wide dedup decision).

    python3 scripts/check-bugreports.py              # exit 1 on drift
    python3 scripts/check-bugreports.py --self-test  # positive/negative cases
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

# A gitlab.com project path: a namespace, any subgroups, then the project.
# A GitLab path segment cannot start with "-", so "/-/" ends the path.
_SEGMENT = r"[\w.][\w.-]*"
_PROJECT = rf"gitlab\.com/{_SEGMENT}(?:/{_SEGMENT})+"

# Over http:// too: it redirects to the same 404ing https:// address.
ISSUES_RE = re.compile(rf"https?://{_PROJECT}/-/issues(?![\w-])")
# Group 1 is the repository the tracker belongs to.
WORK_ITEMS_RE = re.compile(rf"(https://{_PROJECT})/-/work_items\b")

# DESCRIPTION's BugReports: value, in full, must match this.
BUGREPORTS_RE = re.compile(rf"^(https://{_PROJECT})/-/work_items/?$")
# A gitlab.com repository address in DESCRIPTION's URL: field.
REPO_URL_RE = re.compile(rf"(https://gitlab\.com/{_SEGMENT}(?:/{_SEGMENT})+?)/?(?=[\s,]|$)")
ISSUE_TRACKER_RE = re.compile(r'"issueTracker"\s*:\s*"([^"]*)"')

# Files beside DESCRIPTION that carry the tracker link; each must name
# /-/work_items.
HUMAN_FACING_FILES = (
    "codemeta.json",
    ".bestpractices.json",
    "CONTRIBUTING.md",
    "SECURITY.md",
)

# Human-facing surfaces that link no tracker today: /-/issues is forbidden,
# /-/work_items is not required. Globs, relative to the repository root.
NO_ISSUES_GLOBS = (
    "README.Rmd",
    "README.md",
    "SECURITY-INSIGHTS.yml",
    "_pkgdown.yml",
    "vignettes/*.Rmd",
    ".github/**/*",
    ".gitlab/**/*",
)

# The line roxygen2 documents as the package itself.
PACKAGE_SENTINEL_RE = re.compile(r"""^\s*["']_PACKAGE["']\s*$""", re.MULTILINE)


def read_dcf(path: Path) -> dict[str, str]:
    """Flat DCF fields, joining RFC-822 style continuation lines."""
    fields: dict[str, str] = {}
    key: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            key = None
            continue
        if line[0].isspace():
            if key is not None:
                fields[key] += " " + line.strip()
            continue
        name, sep, value = line.partition(":")
        if not sep:
            key = None
            continue
        key = name.strip()
        fields[key] = value.strip()
    return fields


def package_doc_source(root: Path) -> Path | None:
    """The R/ file holding the "_PACKAGE" sentinel (R/<pkg>-package.R by
    usethis's convention, but any file name works for roxygen2)."""
    for path in sorted((root / "R").glob("*.[Rr]")):
        if PACKAGE_SENTINEL_RE.search(path.read_text(encoding="utf-8", errors="replace")):
            return path
    return None


def package_block(text: str) -> str:
    """The roxygen block documenting "_PACKAGE": the run of #' lines right
    above the sentinel. Only an @seealso there suppresses the generated
    "Report bugs at" line; one on another object's block does not."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if PACKAGE_SENTINEL_RE.match(line):
            start = index
            while start > 0 and lines[start - 1].lstrip().startswith("#'"):
                start -= 1
            return "\n".join(line.lstrip() for line in lines[start:index])
    return ""


def check_repo(root: Path) -> list[str]:
    """Findings for one repository; empty when every tracker link agrees."""
    errors: list[str] = []

    description = root / "DESCRIPTION"
    if not description.exists():
        return ["DESCRIPTION is missing; nothing to check BugReports against"]
    desc = read_dcf(description)
    # No BugReports: field is a separate question, not drift here; the checks
    # that compare against it are skipped, the /-/issues ban still runs.
    bugreports = desc.get("BugReports", "")

    # The package's own repository: BugReports:'s, when URL: names it too;
    # otherwise whatever gitlab.com repository URL: names.
    url_repos = REPO_URL_RE.findall(desc.get("URL", ""))
    match = BUGREPORTS_RE.match(bugreports)
    if match is not None and match.group(1) in url_repos:
        own = {match.group(1)}
    else:
        own = set(url_repos)
    own_label = ", ".join(f"{repo}/-/work_items" for repo in sorted(own)) or "none in URL:"

    if bugreports and match is None:
        errors.append(
            f"DESCRIPTION BugReports: is '{bugreports}', which is not a "
            f"gitlab.com /-/work_items address. /-/issues 404s for CRAN's URL "
            f"check, and CRAN accepts /-/work_items (Uwe Ligges, 2026-10-23; "
            f"SEOR-sptibjph)."
        )
    elif match is not None and match.group(1) not in url_repos:
        errors.append(
            f"DESCRIPTION BugReports: is '{bugreports}', but URL: names no "
            f"repository '{match.group(1)}'. The tracker must be this "
            f"package's own."
        )

    codemeta = root / "codemeta.json"
    if bugreports and codemeta.exists():
        tracker = ISSUE_TRACKER_RE.search(codemeta.read_text(encoding="utf-8"))
        if tracker is None or tracker.group(1).rstrip("/") != bugreports.rstrip("/"):
            found = tracker.group(1) if tracker else "nothing"
            errors.append(
                f"codemeta.json issueTracker is '{found}', but DESCRIPTION's "
                f"BugReports: is '{bugreports}'. codemeta.json is hand-"
                f"maintained; make it name the same address."
            )

    package = desc.get("Package", "")
    man_rel = f"man/{package}-package.Rd"
    man_path = root / man_rel
    if package and man_path.exists():
        text = man_path.read_text(encoding="utf-8")
        match = re.search(r"Report bugs at \\url\{([^}]*)\}", text)
        pkg_r = package_doc_source(root)
        r_rel = pkg_r.relative_to(root).as_posix() if pkg_r else 'no R/ file with "_PACKAGE"'
        has_seealso = pkg_r is not None and re.search(
            r"^#'\s*@seealso\b", package_block(pkg_r.read_text(encoding="utf-8")), re.MULTILINE
        )
        # roxygen2 generates the line only from a BugReports: value.
        if match is None and bugreports and not has_seealso:
            errors.append(
                f"{man_rel} has no 'Report bugs at' link, and "
                f"{r_rel} declares no @seealso that "
                f"suppresses it -- the man page is stale. Re-run "
                f"devtools::document()."
            )
        elif match is not None and match.group(1) != bugreports:
            errors.append(
                f"{man_rel}'s 'Report bugs at' link is "
                f"'{match.group(1)}', but DESCRIPTION's BugReports: is "
                f"'{bugreports}'. This link is generated verbatim from "
                f"DESCRIPTION by roxygen2's \"_PACKAGE\" sentinel -- re-run "
                f"devtools::document(), do not hand-edit the .Rd."
            )

    for name in HUMAN_FACING_FILES:
        path = root / name
        if not path.is_file():
            errors.append(
                f"{name} is missing; it must exist and name this package's "
                f"own tracker ({own_label})."
            )
            continue
        text = path.read_text(encoding="utf-8")
        if ISSUES_RE.search(text):
            errors.append(
                f"{name} still links a /-/issues form, which 404s for a "
                f"non-browser client. Repoint it at /-/work_items."
            )
        # Another project's tracker may appear beside this package's own,
        # never instead of it.
        trackers = set(WORK_ITEMS_RE.findall(text))
        if not (trackers & own if own else trackers):
            errors.append(
                f"{name} does not name the project's /-/work_items tracker "
                f"link ({own_label}) anywhere -- expected this package's own "
                f"tracker URL."
            )

    # A file already checked above is not reported a second time by the
    # glob pass.
    seen: set[Path] = {root / name for name in HUMAN_FACING_FILES}
    for pattern in NO_ISSUES_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            if ISSUES_RE.search(text):
                errors.append(
                    f"{path.relative_to(root)} links a /-/issues form, which "
                    f"404s for a non-browser client. Use /-/work_items."
                )

    return errors


# --- self-test (positive + negative coverage, executable) --------------------
#
# The fixture is package-neutral: it names its own package ("fixture" unless a
# case says otherwise) and writes that package's own man/<pkg>-package.Rd and
# R/<pkg>-package.R, so a copy ported to another package tests the shape it
# runs on, not seor's.

# Cases that pin a known gap still open in check_repo(). A listed case must
# fail; one that passes fails the self-test, so a fix has to drop its tag.
XFAIL: frozenset[str] = frozenset()


def _fixture(
    directory: Path,
    bugreports: str,
    man_url: str | None,
    human: dict[str, str],
    seealso: str = "package",
    url: str = "https://gitlab.com/bart-turczynski/fixture",
    package: str = "fixture",
) -> Path:
    """A throwaway package; `seealso` is "package", "other" or "none".

    "package" puts an @seealso in the "_PACKAGE" block (it suppresses the
    generated "Report bugs at" line), "other" puts one only in another
    object's block (it suppresses nothing), "none" declares no @seealso.
    """
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "DESCRIPTION").write_text(
        f"Package: {package}\nVersion: 0.1.0\nURL: {url}\nBugReports: {bugreports}\n",
        encoding="utf-8",
    )
    # Spelled out here, not taken from check_repo()'s own path logic, so the
    # fixture states the roxygen2 file-name convention independently.
    man_dir = directory / "man"
    man_dir.mkdir(parents=True, exist_ok=True)
    if man_url is not None:
        rd = f"\\seealso{{\nReport bugs at \\url{{{man_url}}}\n}}\n"
    else:
        rd = "\\seealso{\nThe package website.\n}\n"
    (man_dir / f"{package}-package.Rd").write_text(rd, encoding="utf-8")
    r_dir = directory / "R"
    r_dir.mkdir(parents=True, exist_ok=True)
    package_block = {
        "package": "#' The package.\n#'\n#' @seealso The package website.\n\"_PACKAGE\"\n",
        "other": (
            "#' The package.\n\"_PACKAGE\"\n\n"
            "#' A helper.\n#' @seealso [base::print()]\nhelper <- function() NULL\n"
        ),
        "none": "#' The package.\n\"_PACKAGE\"\n",
    }[seealso]
    (r_dir / f"{package}-package.R").write_text(package_block, encoding="utf-8")
    for name, content in human.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return directory


def self_test() -> None:
    org = "https://gitlab.com/bart-turczynski/fixture"
    issues = f"{org}/-/issues"
    work_items = f"{org}/-/work_items"
    foreign = "https://gitlab.com/someone/else/-/work_items"

    failures: list[str] = []
    xpassed: list[str] = []
    counts = {"positive": 0, "negative": 0, "xfail": 0}

    def run(tag: str, **kwargs) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            return check_repo(_fixture(Path(tmp) / tag, **kwargs))

    def record(tag: str, ok: bool, detail: str) -> None:
        if tag in XFAIL:
            if ok:
                xpassed.append(tag)
            else:
                counts["xfail"] += 1
        elif not ok:
            failures.append(f"{tag}: {detail}")

    def expect_clean(tag: str, **kwargs) -> None:
        counts["positive"] += 1
        found = run(tag, **kwargs)
        record(tag, not found, f"expected clean, got {found}")

    def expect_flagged(tag: str, needle: str, **kwargs) -> None:
        counts["negative"] += 1
        found = run(tag, **kwargs)
        record(tag, any(needle in f for f in found), f"expected {needle!r}, got {found}")

    human_target = {
        "codemeta.json": f'{{"issueTracker": "{work_items}"}}',
        ".bestpractices.json": f'{{"report_url_justification": "Bug tracker: {work_items}"}}',
        "CONTRIBUTING.md": f"Report bugs at <{work_items}>.",
        "SECURITY.md": f"Or open a confidential issue at <{work_items}>.",
        "README.Rmd": "Install from CRAN.",
        "README.md": "Install from CRAN.",
    }

    def with_file(name: str, text: str | None) -> dict[str, str]:
        """human_target with one file replaced, or dropped when `text` is None."""
        human = dict(human_target)
        if text is None:
            del human[name]
        else:
            human[name] = text
        return human

    # POSITIVE: every tracker link names /-/work_items (the "Report bugs at"
    # line generated into the package's man page is present).
    expect_clean("all-work-items", bugreports=work_items, man_url=work_items, human=human_target)

    # POSITIVE: no "Report bugs at" line because the package doc's own
    # @seealso suppresses the generated section.
    expect_clean("man-suppressed-by-seealso", bugreports=work_items, man_url=None, human=human_target)

    # POSITIVE: a trailing slash is the same address.
    expect_clean("trailing-slash", bugreports=f"{work_items}/", man_url=None, human=human_target)

    # POSITIVE: so is a trailing slash on URL:'s repository address.
    expect_clean(
        "url-trailing-slash",
        bugreports=work_items,
        man_url=work_items,
        human=human_target,
        url=f"{org}/",
    )

    # POSITIVE: a file may name another project's tracker beside this
    # package's own (a metapackage pointing at a member's, say).
    expect_clean(
        "own-plus-foreign-work-items",
        bugreports=work_items,
        man_url=work_items,
        human=with_file("CONTRIBUTING.md", f"Report bugs at <{work_items}>; member bugs at <{foreign}>."),
    )

    # POSITIVE: a package whose repository sits in a GitLab subgroup.
    sub = "https://gitlab.com/some-group/sub.group/fixture"
    expect_clean(
        "subgroup-package",
        bugreports=f"{sub}/-/work_items",
        man_url=f"{sub}/-/work_items",
        human={name: text.replace(org, sub) for name, text in human_target.items()},
        url=sub,
    )

    # POSITIVE: no BugReports: at all is a separate question, not drift here;
    # the own address then comes from URL:.
    expect_clean("empty-bugreports-clean", bugreports="", man_url=None, human=human_target)

    # POSITIVE: the same checks hold for a package of any name.
    expect_clean(
        "other-package-name",
        bugreports=work_items,
        man_url=work_items,
        human=human_target,
        package="otherpkg",
    )

    # NEGATIVE: the line is absent and nothing suppresses it any more.
    expect_flagged(
        "man-missing-without-seealso",
        "declares no @seealso",
        bugreports=work_items,
        man_url=None,
        human=human_target,
        seealso="none",
    )

    # NEGATIVE: an @seealso in another object's block suppresses nothing in
    # the package's own man page.
    expect_flagged(
        "seealso-in-other-block",
        "declares no @seealso",
        bugreports=work_items,
        man_url=None,
        human=human_target,
        seealso="other",
    )

    # NEGATIVE: a tracker copied from another package.
    expect_flagged(
        "foreign-tracker",
        "URL: names no repository",
        bugreports=foreign,
        man_url=None,
        human=human_target,
    )

    # NEGATIVE: codemeta.json names another /-/work_items address than
    # DESCRIPTION's.
    expect_flagged(
        "codemeta-differs",
        "codemeta.json issueTracker is",
        bugreports=work_items,
        man_url=None,
        human=with_file("codemeta.json", f'{{"issueTracker": "{foreign}"}}'),
    )

    # NEGATIVE: DESCRIPTION back on /-/issues, the form that drew the 1.2.2
    # pretest's 404 NOTE.
    expect_flagged(
        "description-issues",
        "not a gitlab.com /-/work_items address",
        bugreports=issues,
        man_url=issues,
        human=human_target,
    )

    # NEGATIVE: DESCRIPTION on /-/issues/new, the other form CRAN's incoming
    # check string-tests for.
    expect_flagged(
        "description-issues-new",
        "not a gitlab.com /-/work_items address",
        bugreports=f"{issues}/new",
        man_url=None,
        human=human_target,
    )

    # NEGATIVE: man page not regenerated after a DESCRIPTION edit.
    expect_flagged(
        "man-stale",
        "generated verbatim from",
        bugreports=work_items,
        man_url=issues,
        human=human_target,
    )

    # NEGATIVE: the same, in a package not named "fixture": the man page
    # checked is that package's own.
    expect_flagged(
        "other-package-name-man-stale",
        "man/otherpkg-package.Rd's 'Report bugs at' link",
        bugreports=work_items,
        man_url=issues,
        human=human_target,
        package="otherpkg",
    )

    # NEGATIVE: a human-facing file reverted to /-/issues (the "prove it
    # bites" case this gate exists for).
    expect_flagged(
        "contributing-reverted",
        "still links a /-/issues form",
        bugreports=work_items,
        man_url=work_items,
        human=with_file("CONTRIBUTING.md", f"Report bugs at <{issues}/new>."),
    )

    # NEGATIVE: a human-facing file never names /-/work_items at all.
    expect_flagged(
        "codemeta-missing-work-items",
        "does not name the project's /-/work_items",
        bugreports=work_items,
        man_url=work_items,
        human=with_file("codemeta.json", '{"issueTracker": ""}'),
    )

    # NEGATIVE: a human-facing file names only another project's tracker.
    expect_flagged(
        "contributing-foreign-work-items",
        f"CONTRIBUTING.md does not name the project's /-/work_items tracker link ({work_items})",
        bugreports=work_items,
        man_url=work_items,
        human=with_file("CONTRIBUTING.md", f"Report bugs at <{foreign}>."),
    )

    # NEGATIVE: a required human-facing file is missing.
    expect_flagged(
        "contributing-missing",
        "CONTRIBUTING.md is missing",
        bugreports=work_items,
        man_url=work_items,
        human=with_file("CONTRIBUTING.md", None),
    )

    # NEGATIVE: SECURITY.md keeps its /-/work_items link but gains a
    # /-/issues one beside it.
    expect_flagged(
        "security-issues-link",
        "SECURITY.md still links a /-/issues form",
        bugreports=work_items,
        man_url=work_items,
        human=with_file("SECURITY.md", human_target["SECURITY.md"] + f" Or [a confidential issue]({issues}/new)."),
    )

    # NEGATIVE: with no BugReports:, the /-/issues ban still runs.
    expect_flagged(
        "empty-bugreports-issues-link",
        "README.md links a /-/issues form",
        bugreports="",
        man_url=None,
        human=with_file("README.md", f"Report problems at <{issues}>."),
    )

    # NEGATIVE: a surface with no tracker link today (a vignette) gains a
    # /-/issues link.
    expect_flagged(
        "vignette-issues-link",
        "vignettes/getting-started.Rmd links a /-/issues form",
        bugreports=work_items,
        man_url=work_items,
        human={**human_target, "vignettes/getting-started.Rmd": f"Report problems at <{issues}>."},
    )

    # NEGATIVE: the link in backticks, before a full stop, to one issue, over
    # plain http://, and in a GitLab subgroup; earlier patterns missed each.
    for tag, text in (
        ("backticks", f"See `{issues}`."),
        ("full-stop", f"Report problems at {issues}."),
        ("one-issue", f"Fixed in {issues}/42 already."),
        ("http", f"Report problems at <{issues.replace('https://', 'http://')}>."),
        ("subgroup", "Report problems at <https://gitlab.com/some-group/sub.group/fixture/-/issues>."),
    ):
        expect_flagged(
            f"issues-link-{tag}",
            "README.md links a /-/issues form",
            bugreports=work_items,
            man_url=work_items,
            human=with_file("README.md", text),
        )

    # NEGATIVE: a GitLab template under .gitlab/ gains a /-/issues link.
    expect_flagged(
        "gitlab-template-issues-link",
        ".gitlab/issue_templates/Bug.md links a /-/issues form",
        bugreports=work_items,
        man_url=work_items,
        human={**human_target, ".gitlab/issue_templates/Bug.md": f"Search {issues} first."},
    )

    if failures or xpassed:
        lines = [f"  - {failure}" for failure in failures]
        lines += [f"  - {tag}: passes but is listed in XFAIL; drop it" for tag in xpassed]
        raise SystemExit("check-bugreports self-test FAILED:\n" + "\n".join(lines))
    pending = f", {counts['xfail']} expected failures pending" if counts["xfail"] else ""
    print(
        f"check-bugreports self-test: PASS ({counts['positive']} positive + "
        f"{counts['negative']} negative cases{pending})"
    )


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        self_test()
        return 0

    root = Path(__file__).resolve().parent.parent
    errors = check_repo(root)
    if errors:
        print("check-bugreports failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("check-bugreports: every tracker link names /-/work_items.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
