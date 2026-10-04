# Security Policy

## Supported versions

Security fixes are made against the latest released version of `seor` and the
development version on `main`. Please upgrade to the most recent release
before reporting.

| Version                        | Supported          |
| ------------------------------ | ------------------ |
| Latest release                 | :white_check_mark: |
| Development version (`main`)   | :white_check_mark: |
| Older releases                 | :x:                |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public issues.**

Preferred channel — **email the maintainer at bartek@turczynski.pl.**

Alternatively, open a **confidential issue** on the GitLab project:

1. Go to [Issues](https://gitlab.com/bart-turczynski/seor/-/work_items) and click
   **New issue**.
2. Tick **This issue is confidential** before submitting.

A confidential issue is visible only to you, its assignees and the project
members whose role lets them see confidential issues.

Email is listed first deliberately: it works whether or not you have a GitLab
account, and it is the channel the maintainer monitors.

Do not include secrets, credentials, tokens, or private customer data in a
report, an issue, a merge request or a log. A minimal reproduction is enough.

## What to expect

- We aim to acknowledge a report within **7 days**.
- We will investigate, work on a fix, and coordinate disclosure with you.
- We are happy to credit reporters in the release notes unless you prefer to
  remain anonymous.

## Scope

`seor` is a metapackage: `library(seor)` installs and attaches its member
packages, and it has no analysis functions of its own.

### What is in scope

- Code in `seor` itself: the attach logic, `seor_packages()` and
  `seor_conflicts()`, doing something other than attaching the declared
  members and reporting name conflicts.
- A `DESCRIPTION` dependency or `Remotes:` entry that makes installing `seor`
  fetch a package from a source other than the one it declares.

### What is out of scope

- A vulnerability in a member package (`rurl`, `punycoder`, `pslr`, `raddr`,
  `sitemapr`, `pagerankr`, `robotstxtr`). Report it to that package; each one
  carries its own `SECURITY.md`. If you are unsure which package is affected,
  report it here and it will be forwarded.
- A vulnerability in a third-party dependency of a member. The scheduled
  dependency audits (`osv-audit`, `security-audit`) track those.
