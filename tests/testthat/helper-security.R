# Disposition machinery for the OSS Index dependency audit in
# test-security.R. The allow-list lives here rather than in the test file
# because more than one test block reads it -- the offline well-formedness
# check and the network audit itself.
#
# The contract this file implements is "every reported advisory has a current,
# explicit disposition", replacing "the scan reports nothing" (SEOR-fkvlzltx,
# deciding SEOR-feqgnbwt route (a)). Measured 2026-09-11 with live OSS Index
# credentials, the hard dependency closure was 12 packages and reported zero
# advisories, so the list started empty.
#
# That clean result was an artifact of who is on CRAN, not of seor being
# unexposed. `oysteR::audit_description()` expands the dependency closure from
# CRAN metadata, so a member that is not on CRAN is reported as a single leaf
# component with its own subtree invisible. robotstxtr reached CRAN on
# 2026-10-24 (0.3.1), and the audit now expands `robotstxtr -> httr2 -> curl`:
# seor's T2 of 2026-10-30 reported six advisories against curl 8.1.0, the rows
# below (SEOR-dtsibbuo). In CRAN's dependency metadata httr2 is the only
# package in seor's hard tree that imports curl, and robotstxtr the only one
# that imports httr2, so robotstxtr is the caller each row argues from.
# sitemapr and ssrfr also drive curl (through httr2 and directly) but are still
# leaves here; the same six rows, argued for each, are in sitemapr's and
# ssrfr's own helper-security.R.
#
# Rows are added only once reported (SEOR-sxvcbuia): rule B below fails a row
# that is not currently reported, so an anticipatory row is stale on arrival.
#
# Three rules keep the list honest. test-security.R enforces them:
#
#   A  UNEXPECTED  an advisory reported and not allow-listed FAILS. This is
#                  the gate still doing its job.
#   B  STALE       an allow-listed advisory NO LONGER reported FAILS. An
#                  allow-list may not over-permit; a row that has outlived its
#                  justification is deleted, not left to widen the exemption
#                  silently.
#   C  DRIFT       past its review date, or audited at a package version later
#                  than `version_seen`, a row WARNS. Deliberately not a
#                  failure: a calendar date that turns every push red is how a
#                  gate teaches people to reach for --no-verify.
#
# Adding a row is a decision, not a formality. Rule B is what keeps it one.
#
# The reference implementation is `sitemapr/tests/testthat/helper-security.R`.
#
# Every row below names a libcurl range that covers CRAN's current curl 8.1.0
# (2026-10-14), so no available version clears it. libcurl itself fixes all
# six by 8.23.0 (curl.se/docs/CVE-<id>.json, read 2026-10-31: fixed in 8.19.0,
# 8.22.0 or 8.23.0), but the audit matches the R package's version, so a newer
# system libcurl would not clear them either; only a new CRAN curl can.
# robotstxtr facts are read from its CRAN release, v0.3.1, because the audit
# resolves CRAN metadata, not the `Remotes:` entry that points at its main.

oss_index_allowlist <- list(
  list(
    id = "CVE-2026-18924",
    package = "curl",
    version_seen = "8.1.0",
    review = as.Date("2026-12-01"),
    reason = paste(
      "CWE-416 use-after-free on HTTP/2 server push over a shared",
      "connection handle (CVSS 9.1). Unreachable from R: the flaw needs a",
      "push callback, and curl::curl_options() exposes no option matching",
      "`push` while curl::multi_set() takes only total_con, host_con,",
      "max_streams, multiplex and pool, so CURLMOPT_PUSHFUNCTION cannot be",
      "set and server push cannot be enabled by any package in seor's tree.",
      "Independently, ssrfr pins http_version to HTTP/1.1. Re-check those",
      "two curl calls before renewing this row."
    )
  ),
  list(
    id = "CVE-2026-3783",
    package = "curl",
    version_seen = "8.1.0",
    review = as.Date("2026-12-01"),
    reason = paste(
      "CWE-522: an OAuth2 bearer token is leaked to a redirect target when",
      ".netrc carries a matching entry (CVSS 6.9). The leak happens only in",
      "libcurl's own redirect following. robotstxtr 0.3.1's",
      "build_fetch_request() (R/fetch-policy.R) sets followlocation = FALSE",
      "and follows redirects manually, one fresh request per hop, and sends",
      "no bearer token. ssrfr and sitemapr also set followlocation = 0, and",
      "ssrfr and robotstxtr's main set netrc = 0 as well. Re-check those",
      "request builders before renewing this row."
    )
  ),
  list(
    id = "CVE-2026-86410",
    package = "curl",
    version_seen = "8.1.0",
    review = as.Date("2026-12-01"),
    reason = paste(
      "CWE-297: the curl command-line tool sets its SSH host verification",
      "options only for a direct SFTP or SCP transfer, not for one reached",
      "by a redirect (CVSS 5.1). curl.se: only the command line tool is",
      "affected, not libcurl. Every package in seor's tree drives libcurl",
      "through R curl or httr2 and none runs the curl tool. Re-check with a",
      "search for system2()/processx calls to curl before renewing this row."
    )
  ),
  list(
    id = "CVE-2026-86414",
    package = "curl",
    version_seen = "8.1.0",
    review = as.Date("2026-12-01"),
    reason = paste(
      "CWE-201: an HTTP proxy answering a CONNECT with 401 instead of 407",
      "makes libcurl send the origin's credentials set through libcurl",
      "(CURLOPT_USERPWD, Negotiate) to the proxy (CVSS 6.5). It needs",
      "libcurl-level origin credentials. robotstxtr 0.3.1 sets no auth",
      "option and its per-hop request carries no userinfo (robots_origin()",
      "drops it), but it leaves netrc at curl's default, which curl 8.1.0",
      "turns on when the caller sets options(netrc = <path>); it also honors",
      "environment proxies. So in 0.3.1 the path needs a caller who sets",
      "options(netrc) with a matching entry AND routes through a hostile",
      "proxy. robotstxtr main sets netrc = 0 (62a3a09), shipping in its next",
      "release. ssrfr sets netrc = 0 and disables proxies (proxy = \"\",",
      "noproxy = \"*\"); sitemapr's own auth is an httr2 Authorization",
      "header, which libcurl keeps off the CONNECT, unless a caller sets",
      "userpwd through its tls list or prepare hook. Re-check the request",
      "builders and hooks, and drop the netrc caveat once robotstxtr's next",
      "release is on CRAN, before renewing this row."
    )
  ),
  list(
    id = "CVE-2026-87864",
    package = "curl",
    version_seen = "8.1.0",
    review = as.Date("2026-12-01"),
    reason = paste(
      "CWE-130: with CURLOPT_CRLF set, curl advertises the raw byte count",
      "in an IMAP APPEND literal but sends the expanded data (CVSS 3.7). It",
      "needs both an IMAP upload and crlf. No package in seor's tree uploads",
      "or sets crlf itself; only a caller could, through sitemapr's tls list",
      "or prepare hook. Independently, robotstxtr 0.3.1 builds only http(s)",
      "robots URLs (robots_origin()) and refuses non-http(s) redirect",
      "targets, ssrfr limits protocols to http,https, and sitemapr's SSRF",
      "guard admits only http(s) unless the caller sets ssrf_guard = FALSE.",
      "Re-check for upload/crlf options and hooks before renewing this row."
    )
  ),
  list(
    id = "CVE-2026-87865",
    package = "curl",
    version_seen = "8.1.0",
    review = as.Date("2026-12-01"),
    reason = paste(
      "CWE-295: libcurl built on libssh2, with a hashed known_hosts file,",
      "can report a host-key mismatch as a missing key to a",
      "CURLOPT_SSH_KEYFUNCTION callback that then accepts it; SFTP and SCP",
      "only (CVSS 6.9). The callback the flaw needs cannot be installed from",
      "R: curl 8.1.0's handle_setopt() rejects ssh_keyfunction as an",
      "unsupported option type, so not even a caller's hook can set it.",
      "Independently, no package in seor's tree sets an SSH option, and each",
      "limits requests to http(s) by default. Re-check that rejection before",
      "renewing this row."
    )
  )
)

# The fields every allow-list row carries, in the order they are documented.
oss_index_allowlist_fields <- c(
  "id",
  "package",
  "version_seen",
  "review",
  "reason"
)

# Problems with a set of allow-list rows, as a character vector; empty when the
# set is well formed. Written as a function returning findings rather than as a
# block of expectations so that it can be exercised against fixtures -- with no
# live rows, a loop of expectations over `oss_index_allowlist` would assert
# nothing at all and still report as a passing test.
oss_index_allowlist_violations <- function(rows) {
  out <- character()

  parses_as_version <- function(x) {
    tryCatch(
      {
        package_version(x)
        TRUE
      },
      error = function(e) FALSE,
      warning = function(w) FALSE
    )
  }

  for (i in seq_along(rows)) {
    row <- rows[[i]]
    label <- sprintf("row %d", i)

    absent <- setdiff(oss_index_allowlist_fields, names(row))
    unknown <- setdiff(names(row), oss_index_allowlist_fields)
    if (length(absent) > 0) {
      out <- c(
        out,
        sprintf("%s: missing field(s): %s", label, toString(absent))
      )
    }
    if (length(unknown) > 0) {
      out <- c(
        out,
        sprintf("%s: unknown field(s): %s", label, toString(unknown))
      )
    }
    if (length(absent) > 0) {
      next
    }

    label <- sprintf("row %d (%s)", i, paste(row$id, collapse = " "))
    if (
      !is.character(row$id) ||
        length(row$id) != 1L ||
        !grepl("^CVE-[0-9]{4}-[0-9]+$", row$id)
    ) {
      out <- c(out, sprintf("%s: `id` is not a single CVE identifier", label))
    }
    if (
      !is.character(row$package) ||
        length(row$package) != 1L ||
        !nzchar(row$package)
    ) {
      out <- c(
        out,
        sprintf("%s: `package` is not a single package name", label)
      )
    }
    if (
      !is.character(row$version_seen) ||
        length(row$version_seen) != 1L ||
        !parses_as_version(row$version_seen)
    ) {
      out <- c(
        out,
        sprintf("%s: `version_seen` is not a parseable version", label)
      )
    }
    if (!inherits(row$review, "Date") || length(row$review) != 1L) {
      out <- c(out, sprintf("%s: `review` is not a single Date", label))
    }
    # A reason long enough to be an argument rather than a placeholder.
    if (
      !is.character(row$reason) ||
        length(row$reason) != 1L ||
        nchar(row$reason) <= 80
    ) {
      out <- c(
        out,
        sprintf("%s: `reason` is missing or too short to be an argument", label)
      )
    }
  }

  ids <- vapply(
    rows,
    function(row) {
      if (is.character(row$id) && length(row$id) == 1L) {
        row$id
      } else {
        NA_character_
      }
    },
    character(1)
  )
  duplicates <- unique(ids[duplicated(ids) & !is.na(ids)])
  if (length(duplicates) > 0) {
    out <- c(
      out,
      sprintf("duplicate allow-list id(s): %s", toString(duplicates))
    )
  }

  out
}

# Flatten an oysteR::audit_description() result to one row per reported
# advisory. The `vulnerabilities` column is a list of per-package lists, empty
# for a clean package, so the zero-advisory case has to survive unlist().
oss_index_reported <- function(audit) {
  ids <- lapply(audit$vulnerabilities, function(v) {
    if (length(v) == 0) {
      return(character())
    }
    vapply(v, function(x) as.character(x$id), character(1))
  })
  data.frame(
    package = rep(as.character(audit$package), lengths(ids)),
    version = rep(as.character(audit$version), lengths(ids)),
    id = as.character(unlist(ids, use.names = FALSE))
  )
}
