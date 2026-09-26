# Badges & supply-chain security

This project ships a README badge suite that surfaces CI, security, and coverage
status at a glance. The badges render on a **public** GitLab project; most need a
one-time connection step. R packages use the OpenSSF Best Practices program.
This file is the single source of truth — point an agent at it and it can wire
everything up.

## First, always: replace `OWNER`

Every README badge URL contains a literal `OWNER`. Replace it with your GitLab
user or group. For a project inside a subgroup, `OWNER` is the **full path**
(`group/subgroup`), not just the top-level group — GitLab badge and API URLs use
the whole namespace. In an R package, replace it in `DESCRIPTION` and
`_pkgdown.yml` too; the repo name is already rendered everywhere. Find every
remaining occurrence before publishing:

```sh
rg -n OWNER
```

For the README-only replacement:

```sh
sed -i '' "s#/OWNER/#/<your-user-or-group>/#g" README.md   # macOS
sed -i    "s#/OWNER/#/<your-user-or-group>/#g" README.md   # Linux
```

## Free-tier limits (verified June 2026)

| Service | Public projects | Private projects | The limit that bites |
| --- | --- | --- | --- |
| **GitLab pipeline/coverage badges** | Free, unlimited | Free, but the badge image is only served to users who can see the project | Coverage reads a regex you must configure (see below) |
| **OpenSSF Best Practices** | Free | Public FLOSS projects only | Requires registration and a self-assessment |
| **Codecov** | **Free forever, unlimited, any number of users** | Free for the first **5 users**, unlimited private repos | Public is unconstrained |
| **FOSSA** (Free) | **5 projects** total, 10 contributing devs | Same 5-project cap | ⚠️ **5 projects across your whole account** — does not scale to many repos |

**Read the FOSSA row twice.** The free plan caps you at **5 projects total**,
not 5 per org. If you scaffold more than five repos, the sixth FOSSA badge will
not work without a paid/OSS-sponsored plan. Either reserve FOSSA for your top
repos or drop its badge from the others.

## Dropped in the move to GitLab

Two badges the GitHub-era scaffold shipped have no GitLab equivalent and were
removed rather than left to render broken:

- **OpenSSF Scorecard.** The Scorecard project and the `scorecard.dev` viewer
  ingest GitHub repositories only — the checks themselves are written against
  the GitHub API (branch protection, required reviews, Dependabot, GitHub
  Actions pinning). There is no GitLab-hosted equivalent to point the badge at.
  Its closest substitute here is the OpenSSF **Best Practices** self-assessment,
  which is forge-neutral and which the `r` template already wires up.
- **Snyk's repo-form badge.** `snyk.io/test/github/OWNER/REPO/badge.svg`
  renders on demand for a public GitHub repo with no account or token. Snyk
  supports GitLab as an *import source*, but exposes no equivalent
  unauthenticated `snyk.io/test/gitlab/...` badge — you would have to run
  `snyk monitor` in CI with a `SNYK_TOKEN`, at which point the value over
  Renovate plus GitLab's own dependency scanning is small. If you do want it,
  see "Optional: Snyk in CI" below.

## Per-tool setup

### Pipeline (GitLab CI)

No setup — the badge tracks the pipeline for `main`, and the scaffold already
ships `.gitlab-ci.yml`. It goes green on the first push to `main`.

The badge URL takes a branch (`.../badges/main/pipeline.svg`); if your default
branch is not `main`, change it in both the image and the link. Two optional
query parameters are worth knowing: `?ignore_skipped=true` hides pipelines that
were skipped entirely, and `?key_text=CI&key_width=30` relabels the left half.

### Coverage — two options, pick one

**GitLab native (no account, no token).** GitLab reads a coverage percentage out
of the job log using a regex you set on the job, then serves it as
`.../badges/main/coverage.svg`. Add the emitter to the verify chain and the
regex to `.gitlab-ci.yml`:

```yaml
verify:
  # ...
  coverage: '/^TOTAL.*\s+(\d+%)$/'          # py: `pytest --cov --cov-report=term`
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura           # ts/ce: vitest `--coverage.reporter=cobertura`
        path: coverage/cobertura-coverage.xml
```

The `coverage:` regex drives the badge and the MR widget; the
`artifacts:reports:coverage_report` upload drives the per-line diff annotations
in the MR. They are independent — wire both.

Then add the badge:

```markdown
[![Coverage](https://gitlab.com/OWNER/REPO/badges/main/coverage.svg)](https://gitlab.com/OWNER/REPO/-/pipelines)
```

**Codecov (cross-project history, trend graphs, its own MR comments).** The
scaffold ships this badge because it survives a move between forges.

1. Sign in at <https://app.codecov.io> with GitLab and add the project. Codecov
   namespaces GitLab under `/gl/` — `codecov.io/gl/OWNER/REPO` — where the
   GitHub URLs used `/gh/`. Getting this wrong is the usual reason a Codecov
   badge stays grey.
2. Copy the repo upload token and store it as a **masked** CI/CD variable named
   `CODECOV_TOKEN` (Settings > CI/CD > Variables). Public projects can upload
   tokenless, but a token avoids flaky rate-limited uploads.
3. Make CI upload the report. There is no `codecov-action` on GitLab; use the
   uploader binary directly:

   ```yaml
   - curl -Os https://cli.codecov.io/latest/linux/codecov && chmod +x codecov
   - ./codecov --file ./coverage/lcov.info   # ts/ce: lcov; py: coverage.xml; r: cobertura.xml
   ```

   For `ts`/`ce` emit `lcov` from Vitest (`coverage.reporter: ['lcovonly']`);
   for `py` run `pytest --cov --cov-report=xml`; the `r` template wires
   covr → cobertura.

### OpenSSF Best Practices (R)

The R scaffold includes `.bestpractices.json` with proposed answers for facts
the fresh package already satisfies. The Best Practices service treats these as
automation suggestions: review every answer rather than accepting it blindly.

1. Replace `OWNER` throughout the repository and publish it publicly.
2. Register the project at <https://www.bestpractices.dev/projects/new>. The
   form takes any repository URL, GitLab included.
3. Copy the numeric project ID, replace `PROJECT_ID` in `README.md`, and
   uncomment the Best Practices badge.
4. Complete the self-assessment and keep `.bestpractices.json` aligned with the
   package as its security posture changes.

**The site does not import the file from GitLab.** bestpractices.dev reads
`.bestpractices.json` only when the project's repository URL is on github.com,
and a file answer never replaces one already stored. A project first
registered through its GitHub mirror keeps the mirror's answers. Push the file
through automation-proposal links instead:

```sh
python3 scripts/bestpractices-url.py --open    # links for what differs
python3 scripts/bestpractices-url.py --check   # after saving: exit 0 = in sync
```

Each link pre-fills the edit form with the file's answers, marks every change
for review, and saves nothing until you click Save. Answers are split across
several links because the site rejects a link over about 8 KB. The script
refuses to print links for a file the site would not count: a "URL required"
criterion marked Met without a link, or N/A where N/A is not allowed. Use
`--section silver` for the next level, and `--field description=...` to
propose the project description. seor went from 30% to passing this way on
2026-09-26 (SEOR-oaqnafzs).

The file and the badge are deliberately R-only. The R template targets public,
CRAN-shaped libraries; the other templates may describe private applications,
where the public-project self-assessment is not an appropriate default.

### FOSSA

1. Read the limits table — **5 projects total on the free plan.**
2. Sign in at <https://app.fossa.com> and import the project (quick import), or
   run the CLI in CI with a `FOSSA_API_KEY` masked CI/CD variable:

   ```yaml
   fossa:
     stage: maintenance
     image: alpine:3
     script:
       - apk add --no-cache curl bash
       - curl -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/fossas/fossa-cli/master/install-latest.sh | bash
       - fossa analyze
   ```

3. The badge uses the git locator (`git+gitlab.com/OWNER/REPO`), already
   URL-encoded in the README, so it resolves once the project is imported.
   Note the locator carries the **host**: a project imported from GitLab is
   `git+gitlab.com/...`, and reusing a `git+github.com/...` locator silently
   points at nothing.
- **Ecosystem note:** FOSSA's analysis of CRAN/R dependencies is limited; the
  `r` template omits it.

## Optional: GitLab's own security scanning

GitLab Free ships Dependency Scanning, SAST, and Secret Detection as CI
templates — no account or token, since they run as jobs in your own pipeline:

```yaml
include:
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/SAST.gitlab-ci.yml
  - template: Jobs/Secret-Detection.gitlab-ci.yml
```

On Free the findings land in the job artifacts and the pipeline's Security tab
is limited — the MR security widget and the vulnerability report are Ultimate
features. Secret Detection is the one that earns its keep regardless of tier:
it fails the pipeline on a committed credential, which no badge here covers.

## Optional: Snyk in CI

Snyk has no GitLab badge, but it still runs as a job if you want its database
rather than OSV/GitLab's:

```yaml
snyk:
  stage: maintenance
  image: snyk/snyk:node          # or snyk/snyk:python, snyk/snyk:golang, ...
  variables:
    SNYK_TOKEN: $SNYK_TOKEN      # masked CI/CD variable
  script:
    - snyk monitor
```

- **Ecosystem note:** Snyk Open Source covers npm/PyPI/Maven/Go/etc. but **not
  CRAN**, which is why the `r` template omits Snyk entirely.

## Optional: Socket.dev

Not shipped by default, but a strong complement for npm packages — supply-chain
risk scoring with a per-package badge
(`https://socket.dev/api/badge/npm/package/<pkg>`). It keys on the published
package, not the repository, so it is forge-independent. Add it once published.
