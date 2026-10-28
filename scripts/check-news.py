# check-news v1
"""NEWS.md terseness gate.

WHY THIS EXISTS. A NEWS file is read by a package user deciding whether an
upgrade touches them, and the fleet's had grown into design notes: rurl's
NEWS.md reached 311 KiB, bullets running to paragraphs of rationale. The rule
(design/fleet-standard.md, "NEWS.md bullets") was written down, and agents kept
breaking it, so this refuses a bloated bullet at push time (SEOR-mjrpwnqz).

WHAT IT REFUSES, per top-level bullet (`*`, `-` or `+`):

1. [wrap] The bullet's markdown source spans more than one line: a
   continuation line, a nested bullet, or an indented paragraph after a blank
   line. A bullet is one source line, whatever its rendered width.
2. [length] More than WORD_LIMIT words, not counting a trailing parenthesized
   reference such as `(SEOR-abcdefgh)`, `(!53)` or `(owner/repo#12, ADR 0004)`.
   A trailing parenthesis that holds anything else is counted.
3. [housekeeping] The bullet's subject is housekeeping (CI, gates, lint,
   spelling, logos, badges, codemeta/CITATION, agent files and the like) and
   it names no function. The test is deliberately conservative: it reads only
   the bullet's opening words (HOUSEKEEPING_RE), so it misses housekeeping
   phrased some other way rather than refuse a user-facing change.

And anywhere in the file:

4. [internal] An `## Internal` or `### Internal` heading (any level from two
   to six): housekeeping gets no bullet, so it gets no section either.

Fenced code blocks are skipped. Version headings and prose paragraphs are not
judged here; the top heading is the `news-version` gate's.

This is the reference copy every fleet package ports: it takes the NEWS.md
path as its one argument and knows nothing about any one repository. Stdlib
only.

    python3 scripts/check-news.py NEWS.md      # exit 1 on a refused bullet
    python3 scripts/check-news.py --self-test  # positive/negative cases

Exit status: 0 when every bullet passes, 1 on any refusal (or a failed
self-test), 2 when the file cannot be read or the arguments are wrong.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Calibrated on ssrfr's and sitemapr's NEWS.md (2026-10-28), the two already
# written one terse line per bullet: of their 82 bullets the longest run to 32
# words, the median to 18 or 19. 32 keeps both green; a bullet past it is
# carrying its rationale.
WORD_LIMIT = 32

FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")
HEADING_RE = re.compile(r"^#{1,6}\s")
INTERNAL_RE = re.compile(r"^#{2,6}\s+internal\b", re.I)
BULLET_RE = re.compile(r"^ ?[*+-]\s+(.*)$")  # top level; deeper is nested
INDENTED_RE = re.compile(r"^(?: {2,}|\t)\S")
WORD_RE = re.compile(r"\S*\w\S*")

# One reference: an fp or tracker key (SEOR-abcdefgh), an MR or issue number
# (!53, #12, owner/repo#12, robotstxtr !53), or an ADR (ADR 0004, ADR-008,
# ADR 0020 D3). Backticks around it are allowed.
REF_RE = re.compile(
    r"`?(?:[A-Z][A-Z0-9]*-[a-z0-9]+"
    r"|(?:[\w.-]+/)?[\w.-]*[#!]\d+"
    r"|[\w.-]+\s+[#!]\d+"
    r"|ADR[- ]?\d+(?:\s+D\d+)*)`?"
)
TRAILING_PAREN_RE = re.compile(r"\s*\(([^()]*)\)\s*[.;]?\s*$")
REF_SPLIT_RE = re.compile(r"\s*(?:,|;|\band\b)\s*")

# The bullet's opening words, after an optional bold marker and article.
HOUSEKEEPING_RE = re.compile(
    r"""^(?:\*\*)?(?:(?:the|a|an|its|this\s+package's)\s+)?(?:new\s+)?
    (?:CI\b|continuous\s+integration|CI\s+pipelines?|`?\.gitlab-ci\.ya?ml`?
      |`?pre-(?:push|commit)`?|(?:verify|pre-push|local|cheap)\s+gates?\b|gates?\b
      |lint(?:s|ing|r|\s+set)?\b|`?\.lintr`?|spelling\b|spell-?check|codespell
      |`?inst/WORDLIST`?|word\s*list\b|(?:hex\s+)?logos?\b|(?:README\s+)?badges?\b
      |badge\s+row|alt\s+text|`?codemeta\.json`?|`?CITATION\.cff`?|`?\.zenodo\.json`?
      |`?\.bestpractices\.json`?|`?(?:AGENTS(?:_LANG)?|CLAUDE)\.md`?
      |agent\s+(?:files?|instructions?))""",
    re.I | re.X,
)
FUNCTION_RE = re.compile(r"\b[\w.]+\(\)")


@dataclass
class Bullet:
    line: int  # 1-based source line of the bullet marker
    lines: list[str]  # its source lines, the first one included

    @property
    def text(self) -> str:
        first = BULLET_RE.match(self.lines[0])
        rest = [line.strip() for line in self.lines[1:] if line.strip()]
        return " ".join([first.group(1).strip() if first else self.lines[0].strip()] + rest)


def trailing_reference(text: str) -> str:
    """`text` without a trailing parenthesized reference, when it ends in one."""
    m = TRAILING_PAREN_RE.search(text)
    if not m:
        return text
    parts = [p for p in REF_SPLIT_RE.split(m.group(1).strip()) if p]
    if parts and all(REF_RE.fullmatch(p) for p in parts):
        return text[: m.start()]
    return text


def words(text: str) -> int:
    return len(WORD_RE.findall(trailing_reference(text)))


def is_housekeeping(text: str) -> bool:
    return bool(HOUSEKEEPING_RE.match(text)) and not FUNCTION_RE.search(text)


def parse(text: str) -> tuple[list[Bullet], list[tuple[int, str]]]:
    """The file's top-level bullets, and its headings as (line, text)."""
    bullets: list[Bullet] = []
    headings: list[tuple[int, str]] = []
    current: Bullet | None = None
    after_blank = False
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        m = FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(1) == fence:
                fence = None
            continue
        if m:
            fence, current = m.group(1), None
            continue
        if not line.strip():
            after_blank = True
            continue
        if HEADING_RE.match(line):
            headings.append((number, line.strip()))
            current = None
        elif BULLET_RE.match(line):
            current = Bullet(number, [line])
            bullets.append(current)
        elif current is not None and (not after_blank or INDENTED_RE.match(line)):
            current.lines.append(line)
        else:
            current = None
        after_blank = False
    return bullets, headings


def check_text(text: str) -> list[tuple[int, str, str]]:
    """Each refusal as (line, key, message); key is wrap, length, housekeeping or internal."""
    bullets, headings = parse(text)
    found: list[tuple[int, str, str]] = []
    for number, heading in headings:
        if INTERNAL_RE.match(heading):
            found.append((number, "internal", f"{heading!r}: housekeeping gets no bullet and no section"))
    for bullet in bullets:
        body = bullet.text
        if len(bullet.lines) > 1:
            found.append((bullet.line, "wrap", f"the bullet spans {len(bullet.lines)} source lines; make it one"))
        count = words(body)
        if count > WORD_LIMIT:
            found.append((bullet.line, "length", f"{count} words, over {WORD_LIMIT} (the trailing reference not "
                                                  "counted); the reasoning belongs in the issue or ADR"))
        if is_housekeeping(body):
            found.append((bullet.line, "housekeeping", f"housekeeping gets no NEWS bullet: {body[:60]!r}"))
    return sorted(found)


# --- self-test (positive + negative coverage, executable) --------------------


def self_test() -> None:
    limit_words = " ".join(["word"] * WORD_LIMIT)
    cases: list[tuple[str, str, set[str]]] = [
        # POSITIVE.
        ("terse", "# pkg 1.0.0\n\n* `f()` now accepts `NA` (PKG-abcdefgh).\n* `g()` is faster.\n", set()),
        ("dash and plus bullets", "- `f()` now accepts `NA` (!12).\n+ `g()` is faster.\n", set()),
        ("exactly the limit", f"* {limit_words}.\n", set()),
        ("long trailing reference not counted", f"* {limit_words} (PKG-abcdefgh, PKG-ijklmnop, owner/repo#12, !53, "
                                                "ADR 0004, ADR-008, robotstxtr !53).\n", set()),
        ("standard clause cited", "* `parse()` rejects a bare `%` in the path (RFC 3986 §2.1) (PKG-abcdefgh).\n", set()),
        ("blank line ends the bullet", "* `f()` is faster.\n\nA prose paragraph after it.\n", set()),
        ("feature subheadings", "# pkg 1.0.0\n\n## Reading\n\n* `read()` reads.\n\n### Policy\n\n* `p()` builds.\n",
         set()),
        ("fenced code skipped", "* `f()` is faster.\n\n```\n## Internal\n* CI\n  wraps\n```\n", set()),
        ("housekeeping word later in the bullet", "* `f()` no longer fails when CI is set.\n", set()),
        ("housekeeping subject naming a function", "* Badges: `badge_url()` builds a badge URL.\n", set()),
        ("user-facing subject that starts like one", "* Gateway timeouts now retry once.\n", set()),
        # NEGATIVE.
        ("continuation line", "* `f()` now accepts `NA`\n  and `NULL` (PKG-abcdefgh).\n", {"wrap"}),
        ("lazy continuation", "* `f()` now accepts `NA`\nand `NULL`.\n", {"wrap"}),
        ("nested bullet", "* `f()` changes:\n  - it accepts `NA`.\n", {"wrap"}),
        ("indented paragraph after a blank line", "* `f()` changes.\n\n  Here is why.\n", {"wrap"}),
        ("one word over the limit", f"* {limit_words} more.\n", {"length"}),
        # Fixed lengths, so the limit cannot drift far without this failing.
        ("a 25-word bullet", f"* {' '.join(['word'] * 25)}.\n", set()),
        ("a 45-word bullet", f"* {' '.join(['word'] * 45)}.\n", {"length"}),
        ("prose in the trailing parenthesis is counted",
         f"* {' '.join(['word'] * (WORD_LIMIT - 2))} (because the old one was slow).\n", {"length"}),
        ("## Internal", "# pkg 1.0.0\n\n## Internal\n", {"internal"}),
        ("### Internal changes", "# pkg 1.0.0\n\n### Internal changes\n", {"internal"}),
        ("CI", "* CI now caches the package library (PKG-abcdefgh).\n", {"housekeeping"}),
        ("the gate", "* The pre-push gate runs `check-urls`.\n", {"housekeeping"}),
        ("lint set", "* Lint set aligned with goodpractice.\n", {"housekeeping"}),
        ("spelling", "* Spelling fixed throughout the vignettes.\n", {"housekeeping"}),
        ("logo", "* The hex logo carries metadata.\n", {"housekeeping"}),
        ("badges", "* README badges follow the fleet standard.\n", {"housekeeping"}),
        ("codemeta", "* `codemeta.json` lists the keywords.\n", {"housekeeping"}),
        ("CITATION.cff", "* `CITATION.cff` names the release.\n", {"housekeeping"}),
        ("agent files", "* Agent instructions point at the house skills.\n", {"housekeeping"}),
        ("bold lead-in", "* **CI:** the coverage job fails below 95%.\n", {"housekeeping"}),
        ("every rule at once", f"## Internal\n\n* CI {limit_words}\n  wraps.\n", {"internal", "wrap", "length",
                                                                                 "housekeeping"}),
    ]
    for tag, text, want in cases:
        got = {key for _, key, _ in check_text(text)}
        if got != want:
            raise SystemExit(f"self-test FAILED ({tag}): expected {sorted(want)}, got {sorted(got)}")
    # The line a refusal names is the bullet's first line.
    lines = [line for line, _, _ in check_text("# pkg\n\n* ok.\n* wraps\n  here.\n")]
    if lines != [4]:
        raise SystemExit(f"self-test FAILED (line number): expected [4], got {lines}")
    positive = sum(1 for _, _, want in cases if not want)
    print(f"check-news self-test: PASS ({positive} positive + {len(cases) - positive} negative cases)")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if len(argv) != 1 or argv[0].startswith("-"):
        print("usage: check-news.py NEWS.md | --self-test", file=sys.stderr)
        return 2
    path = Path(argv[0])
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"check-news: cannot read {path}: {error}", file=sys.stderr)
        return 2
    found = check_text(text)
    if found:
        print(f"check-news failed: {len(found)} refusal(s) in {path} (design/fleet-standard.md, "
              "\"NEWS.md bullets\"):", file=sys.stderr)
        for line, key, message in found:
            print(f"  - {path}:{line}: [{key}] {message}", file=sys.stderr)
        return 1
    print(f"check-news: every bullet in {path} is one terse line.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
