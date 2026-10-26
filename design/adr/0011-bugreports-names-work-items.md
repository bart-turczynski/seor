---
status: accepted
date: 2026-10-26
tracking: SEOR-sptibjph, PSLR-cvhksjst
---

# ADR 0011: BugReports names /-/work_items in every fleet package

## Context

GitLab serves issues as work items. On gitlab.com, measured 2026-10-24,
`/-/issues` answers 404 to a client that does not send `Accept: text/html`
(curl, `tools::check_url_db()`), and 302 to `/-/work_items` for a browser.
`/-/work_items` answers 200 to both. The user agent does not matter.

CRAN runs two checks over `BugReports:`, and on gitlab.com no address
satisfies both. The URL check fetches it, so `/-/issues` draws a 404 NOTE.
`tools:::.check_package_CRAN_incoming()` string-tests the path and flags
anything but `/issues`, so `/-/work_items` draws a "which should likely be"
NOTE. R 4.6.1 words it as "which should likely be
`https://gitlab.com/<o>/<p>/-/work_items/issues`".

Until now the fleet kept `/-/issues` in `DESCRIPTION` and `man/`, and
`/-/work_items` in every file a person reads (SEOR-ocbtrrnl). Each gate
exempted that one 404. The split rested on pslr's first 1.2.1 upload, which
declared `/-/work_items` and was archived at the pretest.

On 2026-10-23, on the pslr 1.2.2 submission thread, Uwe Ligges (CRAN) called
the "should likely be" NOTE a bug in CRAN's check for GitLab: "Please feel
free to use the working form such as
https://gitlab.com/bart-turczynski/pslr/-/work_items and we will let it pass
and fix our checks." pslr 1.2.2 was resubmitted with `/-/work_items`, the
auto-check archived it for that NOTE, the owner replied that it was a false
positive, and CRAN published it on 2026-10-24.

## Decision

Every fleet package's `BugReports:` is the `/-/work_items` address of its own
gitlab.com repository, and no file names `/-/issues`:

- `DESCRIPTION`, the generated `man/<pkg>-package.Rd`, and `codemeta.json`'s
  `issueTracker` all name the same `/-/work_items` address.
- `scripts/check-bugreports.py` v2 enforces it. pslr's copy is the pilot;
  each package ports it to its own file set and does not re-derive it.
- The URL check has no exemption: a `/-/issues` 404 is red like any other.
- `cran-comments.md` explains the "should likely be" NOTE, quoting the local
  check's wording, until CRAN changes its check. Uwe's permission was given
  on pslr's thread, so each submission still explains it.

`NEWS.md` and the `cran-comments.md` of past submissions keep their old
wording: they record what was announced or submitted.

## Consequences

The split and its 404 exemptions are gone, and the link a reader clicks and
the link CRAN reads are the same address. Each submission carries one
expected NOTE in the incoming check, and an auto-check may archive the upload
for it, which a reply to CRAN explains as pslr's did.

Do not move `BugReports:` back to `/-/issues` to clear that NOTE: it trades
it for a 404. Revisit when CRAN's incoming check accepts `/-/work_items`
(the NOTE stops appearing), or if GitLab serves `/-/issues` with 200 again.
