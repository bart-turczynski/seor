# OSS Index advisories against curl

The shared libcurl facts behind the fleet's OSS Index allow-list rows for the R
package `curl`, recorded once (SEOR-syhraigk). It is a living reference, not an
ADR or a spec: it changes when an advisory or R's curl changes.

Each fleet repository's `tests/testthat/helper-security.R` cites a section here
by its anchor (`libcurl facts: seor design/oss-index-advisories.md#cve-…`).
What stays in the row:

- its own `id`, `package`, `version_seen` and `review` fields, which the
  validator requires;
- the argument for its own package's callers: which route reaches curl in that
  repository's audited closure, and why that route cannot reach the flaw.

A repository adds a row only once its own audit reports the advisory (rule B
in each helper fails a row nobody reports; `fleet-standard.md`, "The audits,
in `deep-check`"). So row sets may differ between repositories, and a section
here may have no citing row in some of them.

The shared review date is 2026-12-01. The review re-reads this file once, then
each repository's rows only where its own callers changed.

## What every section shares

- OSS Index matches the R package's version number against libcurl's affected
  ranges. Every range below covers CRAN's current curl 8.1.0 (2026-10-14), so
  no available version clears it, and a newer system libcurl would not clear
  it either: only a new CRAN curl can.
- libcurl itself fixes all six by 8.23.0 (curl.se/docs/CVE-<id>.json, read
  2026-10-31: fixed in 8.19.0, 8.22.0 or 8.23.0). The per-CVE fixed-in version
  was not recorded.
- What actually runs is the libcurl the package links: the Windows and macOS
  CRAN binaries bundle one with CVE backports (curl 8.1.0's NEWS); on Linux it
  is the system's. So a row is OSS Index's attribution, and each row argues
  reachability.
- `version_seen` for every row is 8.1.0.

## CVE-2026-18924

- **Weakness:** CWE-416, use-after-free on HTTP/2 server push over a shared
  connection handle. CVSS 9.1. Published 2026-09-06.
- **Affected:** a libcurl range covering curl 8.1.0.
- **Prerequisites:** server push enabled, which needs a push callback
  (`CURLMOPT_PUSHFUNCTION`), over HTTP/2.
- **Why R's curl cannot reach it:** `curl::curl_options()` exposes no option
  matching `push`, and `curl::multi_set()` takes only `total_con`,
  `host_con`, `max_streams`, `multiplex` and `pool`. `CURLMOPT_PUSHFUNCTION`
  is not settable, so no R caller can enable server push.
- **Re-check:** those two calls against the installed curl.
- **Review:** 2026-12-01.

## CVE-2026-3783

- **Weakness:** CWE-522, an OAuth2 bearer token leaked to a redirect target
  when `.netrc` carries a matching (machine or default) entry. CVSS 6.9.
- **Affected:** a libcurl range covering curl 8.1.0.
- **Prerequisites:** libcurl's own redirect following
  (`followlocation`), a bearer token, and a `.netrc` entry that libcurl reads.
- **Why R's curl cannot reach it:** it can. The leak is inside libcurl's
  redirect following, so each row argues from its callers: whether they turn
  off `followlocation`, send a bearer token, or turn off `netrc`.
- **Re-check:** each caller's request builder.
- **Review:** 2026-12-01.

## CVE-2026-86410

- **Weakness:** CWE-297, a redirect to SFTP or SCP skips SSH host
  verification: the curl command-line tool sets its SSH host verification
  options only for a direct SFTP or SCP transfer, not for one reached by a
  redirect. CVSS 5.1. Published 2026-10-14.
- **Affected:** the range OSS Index attributes covers curl 8.1.0. curl.se:
  only the command-line tool is affected, not libcurl.
- **Prerequisites:** running the curl command-line tool.
- **Why R's curl cannot reach it:** R links only libcurl. A caller reaches
  the flaw only by shelling out to a curl binary.
- **Re-check:** that curl.se still places the flaw in the tool alone, and that
  no caller runs the curl tool (`system2()` or processx calls to curl).
- **Review:** 2026-12-01.

## CVE-2026-86414

- **Weakness:** CWE-201, an HTTP proxy answering a CONNECT with 401 instead
  of 407 makes libcurl send the origin's credentials set through libcurl (a
  Basic password through `CURLOPT_USERPWD`, or a Negotiate ticket) to the
  proxy. CVSS 6.5. Published 2026-10-14.
- **Affected:** a libcurl range covering curl 8.1.0.
- **Prerequisites:** libcurl-level origin credentials and a proxy that is
  itself hostile.
- **Why R's curl cannot reach it:** it can. An `Authorization` header set as a
  plain header (httr2's basic and bearer auth) is not libcurl's
  `CURLOPT_USERPWD`, and libcurl keeps custom headers off the CONNECT request;
  credentials set through libcurl options, or from `.netrc`, are exposed. Each
  row argues from its callers: auth options, `netrc`, URL userinfo and proxy
  settings.
- **Re-check:** that httr2 still applies basic auth as a header, and each
  caller's auth, `netrc` and proxy options.
- **Review:** 2026-12-01.

## CVE-2026-87864

- **Weakness:** CWE-130: in an (authenticated) IMAP APPEND with
  `CURLOPT_CRLF` set, curl advertises the raw byte count in the literal but
  sends the CRLF-expanded data, so the excess runs as pipelined IMAP
  commands. CVSS 3.7 (robotstxtr's copy: severity Low). Published 2026-10-14.
- **Affected:** a libcurl range covering curl 8.1.0.
- **Prerequisites:** an IMAP upload and `crlf` set.
- **Why R's curl cannot reach it:** it can, if a caller sets both. Each row
  argues from its callers: whether they upload, set `crlf`, or can reach an
  `imap://` URL at all.
- **Re-check:** each caller for upload and `crlf` options, hooks that let its
  own callers set them, and the schemes it admits.
- **Review:** 2026-12-01.

## CVE-2026-87865

- **Weakness:** CWE-295: libcurl built on libssh2, with a hashed
  `known_hosts` file, can report a host-key mismatch as a missing key to a
  `CURLOPT_SSH_KEYFUNCTION` callback, which then accepts it. SFTP and SCP
  only. CVSS 6.9. Published 2026-10-14.
- **Affected:** a libcurl range covering curl 8.1.0.
- **Prerequisites:** an SFTP or SCP transfer and an SSH key callback.
- **Why R's curl cannot reach it:** the callback cannot be installed from R:
  curl 8.1.0's `handle_setopt()` rejects `ssh_keyfunction` as an unsupported
  option type, so no caller, nor a hook a caller supplies, can set it.
- **Re-check:** that rejection, against the installed curl.
- **Review:** 2026-12-01.
