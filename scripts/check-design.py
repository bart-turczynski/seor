# check-design v1
"""Design-doc hygiene checks.

Three hard checks (exit 1 on failure):

1. ADR immutability  - an accepted ADR may not be edited, only superseded.
2. ARCHITECTURE.md coverage - every top-level source directory is named there.
3. Frontmatter - parses, and `status` is in the enum for its kind.

Plus one non-blocking warning: drafts left untouched in `_scratch/`.

Stdlib only, so it runs in R, Python, TypeScript, and extension repos alike
without adding a CI dependency. Invoke as `python3 scripts/check-design.py`,
or `python3 scripts/check-design.py --self-test` for the offline self-test.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ADR_STATUSES = {"proposed", "accepted", "superseded", "deprecated"}
SPEC_STATUSES = {"draft", "accepted", "shipped", "abandoned"}
IMMUTABLE_STATUSES = {"accepted"}

# Source directories per ecosystem, detected from marker files. Only the ones
# that actually exist are required, so a project that ships no `src/` is fine.
ECOSYSTEMS = [
    ("DESCRIPTION", ["R", "src"]),
    ("wxt.config.ts", ["entrypoints", "utils"]),
    ("pyproject.toml", ["src"]),
    ("package.json", ["src"]),
]
FALLBACK_SOURCE_DIRS = ["src", "lib"]

SCRATCH_STALE_DAYS = 3


def git(*args: str) -> str | None:
    """Run a git command, returning None if it fails (no remote, no repo, ...)."""
    # flake8-bandit flags every subprocess call. `shell=False` (the default) is
    # S603's premise, not its answer: with no shell in the picture the risk that
    # remains is argument injection, because git reads any argv element starting
    # with `-` as an option. Not every argument here is a literal - `ref`,
    # `base` and `rel` are all parsed back out of git's own output - so the thing
    # that actually makes this safe is that none of them can lead with `-`: git
    # refuses to create a ref name that does (and for-each-ref prints full
    # `refs/...` names), `base` is a SHA from merge-base,
    # and `rel` only ever reaches git embedded as f"{base}:{rel}". Keep that true
    # when adding callers. S607: `git` is resolved from PATH on purpose, so the
    # script runs wherever the checkout does - CI images, Homebrew, Nix, Windows.
    try:
        result = subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip()


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Parse a flat `key: value` YAML frontmatter block. None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        fields[key.strip()] = value.strip()
    return None  # unterminated block


def check_frontmatter(root: Path, errors: list[str]) -> None:
    for kind, statuses in (("adr", ADR_STATUSES), ("specs", SPEC_STATUSES)):
        for path in sorted((root / "design" / kind).glob("*.md")):
            if path.name == "README.md":
                continue
            rel = path.relative_to(root)
            fields = parse_frontmatter(path.read_text(encoding="utf-8"))
            if fields is None:
                errors.append(f"{rel}: missing or unterminated YAML frontmatter")
                continue
            status = fields.get("status")
            if status is None:
                errors.append(f"{rel}: frontmatter has no `status`")
            elif status not in statuses:
                errors.append(f"{rel}: status {status!r} not in {sorted(statuses)}")
            elif status == "superseded" and not fields.get("superseded-by"):
                errors.append(
                    f"{rel}: status is superseded but `superseded-by` is unset"
                )


def adr_base() -> str | None:
    """The commit committed HEAD's ADRs are judged against, or None.

    The merge-base with the tracking branch; failing that (a new branch's
    first push has no upstream yet), with the remote's default branch:
    origin/HEAD, then origin/main or origin/master, then any remote's
    HEAD, main or master, then any remote-tracking ref. None only when no
    remote-tracking ref shares history with HEAD.
    """
    candidates: list[str] = []
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if upstream:
        candidates.append(upstream)
    candidates += [
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
        "refs/remotes/origin/master",
    ]
    listed = git("for-each-ref", "--format=%(refname)", "refs/remotes")
    remote_refs = listed.splitlines() if listed else []
    for suffix in ("/HEAD", "/main", "/master"):
        candidates += [ref for ref in remote_refs if ref.endswith(suffix)]
    candidates += remote_refs
    for ref in candidates:
        base = git("merge-base", "HEAD", ref)
        if base:
            return base
    return None


def check_adr_immutability(root: Path, errors: list[str]) -> None:
    """An accepted ADR may be superseded, never edited.

    Compares committed HEAD against adr_base(): the merge-base with the
    tracking branch, or with the remote's default branch when there is no
    upstream yet. A freshly generated project has no remote yet, so the
    check no-ops rather than failing - there is no history to be immutable
    against.
    """
    base = adr_base()
    if base is None:
        return

    changed = git("diff", "--name-status", base, "HEAD", "--", "design/adr")
    if not changed:
        return

    for line in changed.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0].startswith("M"):
            continue
        rel = parts[-1]
        if Path(rel).name.startswith("0000-"):
            continue  # the template itself
        before = git("show", f"{base}:{rel}")
        if before is None:
            continue
        old = parse_frontmatter(before) or {}
        path = root / rel
        new = (
            parse_frontmatter(path.read_text(encoding="utf-8")) if path.exists() else {}
        )
        old_status = old.get("status", "")
        new_status = (new or {}).get("status", "")
        if old_status in IMMUTABLE_STATUSES and new_status == old_status:
            errors.append(
                f"{rel}: accepted ADR was edited. Supersede it with a new ADR "
                f"instead, and set this one's status to `superseded`."
            )


def check_architecture_coverage(root: Path, errors: list[str]) -> None:
    architecture = root / "ARCHITECTURE.md"
    if not architecture.exists():
        errors.append("ARCHITECTURE.md is missing")
        return

    source_dirs = FALLBACK_SOURCE_DIRS
    for marker, dirs in ECOSYSTEMS:
        if (root / marker).exists():
            source_dirs = dirs
            break

    text = architecture.read_text(encoding="utf-8")
    for name in source_dirs:
        if not (root / name).is_dir():
            continue
        if name not in text:
            errors.append(f"ARCHITECTURE.md does not mention the `{name}/` directory")


def warn_stale_scratch(root: Path) -> list[str]:
    scratch = root / "_scratch"
    if not scratch.is_dir():
        return []
    cutoff = time.time() - SCRATCH_STALE_DAYS * 86400
    return sorted(
        path.relative_to(scratch).as_posix()
        for path in scratch.rglob("*")
        if path.is_file() and path.stat().st_mtime < cutoff
    )


# --- self-test (ADR immutability against throwaway repos, offline) -----------

ADR_ACCEPTED = "---\nstatus: accepted\n---\n\n# 0001 Decision\n\nWe decide A.\n"
ADR_EDITED = "---\nstatus: accepted\n---\n\n# 0001 Decision\n\nWe decide B.\n"
ADR_SUPERSEDED = (
    "---\nstatus: superseded\nsuperseded-by: 0002\n---\n\n# 0001 Decision\n\nWe decide A.\n"
)
ADR_REL = "design/adr/0001-decision.md"


def _run(cwd: Path, *args: str) -> None:
    subprocess.run(  # noqa: S603 - literal git argv on a throwaway repo
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],  # noqa: S607
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _commit_adr(repo: Path, text: str, message: str) -> None:
    (repo / ADR_REL).write_text(text, encoding="utf-8")
    _run(repo, "add", ADR_REL)
    _run(repo, "commit", "-q", "-m", message)


def _adr_errors(repo: Path) -> list[str]:
    errors: list[str] = []
    previous = Path.cwd()
    os.chdir(repo)
    try:
        check_adr_immutability(repo, errors)
    finally:
        os.chdir(previous)
    return errors


def _fixture(tmp: Path, name: str) -> tuple[Path, Path]:
    """An origin repo with an accepted ADR on main, and a clone of it."""
    origin = tmp / f"{name}-origin"
    origin.mkdir()
    _run(origin, "init", "-q", "-b", "main")
    (origin / "design" / "adr").mkdir(parents=True)
    _commit_adr(origin, ADR_ACCEPTED, "accept ADR 0001")
    clone = tmp / f"{name}-clone"
    _run(tmp, "clone", "-q", str(origin), str(clone))
    return origin, clone


def self_test() -> None:
    import tempfile

    # A hook runs us with GIT_DIR and friends set; the fixtures need their own.
    for var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        os.environ.pop(var, None)

    failures: list[str] = []

    def expect(name: str, errors: list[str], fails: bool) -> None:
        if bool(errors) != fails:
            want = "an error" if fails else "no error"
            failures.append(f"{name}: wanted {want}, got {errors!r}")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str).resolve()

        # Tracking branch set: the edit is caught (the behavior before the fix).
        _, repo = _fixture(tmp, "tracking")
        _run(repo, "checkout", "-q", "-b", "edit", "--track", "origin/main")
        _commit_adr(repo, ADR_EDITED, "edit ADR body")
        expect("tracking branch edits accepted ADR", _adr_errors(repo), True)

        # A new branch's first push: no upstream yet (SEOR-fnemeutq).
        _, repo = _fixture(tmp, "no-upstream")
        _run(repo, "checkout", "-q", "--no-track", "-b", "edit", "origin/main")
        _commit_adr(repo, ADR_EDITED, "edit ADR body")
        expect("no-upstream branch edits accepted ADR", _adr_errors(repo), True)

        # No upstream and no origin/HEAD: origin/main still anchors it.
        _, repo = _fixture(tmp, "no-origin-head")
        _run(repo, "remote", "set-head", "origin", "-d")
        _run(repo, "checkout", "-q", "--no-track", "-b", "edit", "origin/main")
        _commit_adr(repo, ADR_EDITED, "edit ADR body")
        expect("no-upstream, no origin/HEAD, edits ADR", _adr_errors(repo), True)

        # No upstream, but superseding (a status change) is allowed.
        _, repo = _fixture(tmp, "supersede")
        _run(repo, "checkout", "-q", "--no-track", "-b", "edit", "origin/main")
        _commit_adr(repo, ADR_SUPERSEDED, "supersede ADR 0001")
        expect("no-upstream branch supersedes ADR", _adr_errors(repo), False)

        # No upstream, ADR untouched.
        _, repo = _fixture(tmp, "untouched")
        _run(repo, "checkout", "-q", "--no-track", "-b", "edit", "origin/main")
        expect("no-upstream branch leaves ADR alone", _adr_errors(repo), False)

        # Fresh project: no remote-tracking ref at all, so nothing to compare.
        origin, _ = _fixture(tmp, "fresh")
        _commit_adr(origin, ADR_EDITED, "edit ADR body")
        expect("fresh project with no remote", _adr_errors(origin), False)

    if failures:
        print("check-design self-test failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        raise SystemExit(1)
    print("check-design self-test: ok")


def main() -> int:
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        return 0
    root_str = git("rev-parse", "--show-toplevel")
    root = Path(root_str) if root_str else Path.cwd()

    errors: list[str] = []
    check_frontmatter(root, errors)
    check_adr_immutability(root, errors)
    check_architecture_coverage(root, errors)

    stale = warn_stale_scratch(root)
    if stale:
        shown = ", ".join(stale[:5])
        more = f", +{len(stale) - 5} more" if len(stale) > 5 else ""
        print(
            f"warning: _scratch/: {len(stale)} file(s) untouched "
            f"{SCRATCH_STALE_DAYS}+ days ({shown}{more}). Graduate or delete.",
            file=sys.stderr,
        )

    if errors:
        print("check-design failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
