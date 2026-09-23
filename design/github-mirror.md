# Mirroring a repo to GitHub

Playbook for turning a `bart-turczynski` GitHub repo into a locked-down,
read-only push mirror of its GitLab original, as actually executed across the
eight-repo R fleet rollout (SEOR-wscogmzh / SEOR-zfpaxrxk / SEOR-ggkpweeg,
2026-09-19 to 2026-09-23). Every step below was run for real, on a real repo,
with the trap that made it necessary named next to it. Nothing here is a
first draft.

**Why mirror at all:** some tooling only works against a `github.com` URL —
R-hub v2 (GitHub Actions only), Zenodo's automatic-versioning integration,
FOSSA and bestpractices.dev's project keys, `npm`/`pypi` trusted-publisher
flows that expect GitHub OIDC, some GitHub-App-only integrations. GitLab
stays the source of truth for code, issues, MRs, CI and Pages; GitHub exists
solely to satisfy those integrations, at zero Actions-runner cost.

**Reading guide.** §1–4 are ecosystem-agnostic — read these for a Python, JS,
or C++ repo and stop there. §5 (Zenodo) is also universal: any repo wanting a
DOI works the same way. §6 is currently a stub — it is blocked and there is
nothing to read yet. §7 is R-only (R-hub, r-universe, CRAN); skip it entirely
for a non-R repo.

## 1. Policy (universal)

- GitHub holds a **read-only mirror**. GitLab is pushed to; GitHub is never
  pushed to directly, has no local `github` remote in any working copy, and
  gets no direct commits, tags, branches, or releases outside what the
  mirror and (for releases) `gh release create` against an already-mirrored
  tag produce.
- The push mirror carries **protected branches and protected tags only**.
  Agent/feature branches never reach GitHub.
- GitHub-side surface area is minimized: Actions disabled, Dependabot off,
  Pages off, Issues/Wiki/Projects off, description and homepage point back
  at GitLab.
- **Repo visibility is a forced decision, not a default.** A private mirror
  undercuts the entire reason for mirroring — Zenodo, FOSSA and
  bestpractices.dev all read from the public GitHub surface. Two repos in
  the rollout (raddr, seor) were mirrored private by default and had to be
  flipped to public by the owner after the fact once this was noticed
  (SEOR-wscogmzh, 2026-09-22 and 2026-09-23 comments). Decide and record
  visibility before the first sync, not after.
- README stays forge-neutral: no GitHub Actions status badges (the badge
  would describe a workflow that never runs).

## 2. Per-repo checklist (universal)

Run in this order. Every correction below was learned the hard way on a real
repo in the rollout and is folded in at the point it applies — follow it top
to bottom and you should not re-hit any of these.

### 2.1 Before touching GitHub: read GitLab main first

Check what `.github/workflows/` looks like on the GitLab default branch
*before* anything else. Most repos in the fleet had none (safe — the first
mirror push simply deletes whatever stale workflow files GitHub already has).
One repo (pagerankr) still carried 8 live workflow files under
`.github/workflows/` on GitLab main; because the first mirror push adds refs
rather than only pruning them, that push would have **published** eight live
workflow files to a repo whose Actions setting doesn't stop anything from
existing, only from running. Delete (or reduce to dispatch-only, see §6) any
workflow files that are still on GitLab main before that repo's first sync,
and drop any GitHub-only artifact paths (e.g. Actions-workflow URLs in a
`codemeta.json`) at the same time. Also check the trigger types on GitHub's
*current* copy of main: punycoder had six workflows on
`push: branches: [main]` plus two live crons — the first mirror push would
otherwise have fired six runs at once, which is exactly the failure mode
this whole effort exists to prevent (SEOR-ggkpweeg, 2026-09-20 11:14 and
2026-09-21 comments).

### 2.2 Disable Actions — before configuring the mirror, no exceptions

```sh
gh api -X PUT repos/OWNER/REPO/actions/permissions -F enabled=false
```

Do this first, always. Three repos in the fleet (rurl, sitemapr, pagerankr)
still had Actions enabled with dormant-but-not-dead schedules; a mirror push
to any of them before this step would both fire the push-triggered workflows
and reactivate the crons (SEOR-ggkpweeg, 2026-09-21 comment). Also turn off
vulnerability alerts / Dependabot security updates. Note: the dynamic
Dependabot-updates entry cannot be disabled via API (`422`) while
`dependabot.yml` still exists on GitHub — it goes away on its own once the
first mirror push deletes that file, so don't spend time fighting the 422
(SEOR-zfpaxrxk, 2026-09-19).

**Staffing note:** this exact API call is refused by the agent permission
classifier as `[Security Weaken]`. Every repo in the rollout stalled here
until the human owner ran it (or until a Bash permission rule was added).
Budget for that hand-off on every repo, not just the first one
(SEOR-ggkpweeg, 2026-09-20 11:14).

### 2.3 Pages off — verify with the API, not the branch list

Delete the `gh-pages` branch (after §2.5's `git cherry` check). Note: a
direct `DELETE /pages` call while `gh-pages` still exists returns `422
Deactivating GitHub pages for this repository is not allowed`; it clears
once `gh-pages` is gone (SEOR-zfpaxrxk, 2026-09-19).

Then check explicitly — do not assume "no `gh-pages` branch" means "no
Pages":

```sh
gh api repos/OWNER/REPO/pages
```

Three repos in the fleet (rurl, pagerankr, sitemapr) had their `gh-pages`
branch deleted, `refs/heads` returning `main` only, and were **still**
serving a built Pages site at `bart-turczynski.github.io/<repo>` with a 200,
because GitHub keeps serving the last build indefinitely once one has
happened. A served static site burns zero Actions minutes, which is exactly
why a run-count check (§4) cannot catch it — check `/pages` per repo,
separately (SEOR-jfoszwzz, 2026-09-22 audit comment; confirmed still true
2026-09-23 for rurl in this session).

### 2.4 Issues, Wiki, Projects off; description and homepage

```sh
gh repo edit OWNER/REPO --enable-issues=false --enable-wiki=false \
  --enable-projects=false \
  --description "Read-only mirror of gitlab.com/OWNER/REPO" \
  --homepage "<GitLab repo or Pages URL>"
```

Point the homepage at the GitLab **Pages** URL only if `pages_access_level`
is enabled there and it actually answers 200 anonymously; otherwise point at
the plain GitLab repo URL — a private-Pages URL 403s anonymously and is a
worse homepage than the repo itself (SEOR-ggkpweeg, 2026-09-20 18:43,
raddr/robotstxtr precedent). `gh repo edit` passes the agent permission
classifier cleanly; this step does not need the owner.

### 2.5 Delete stale branches, after archiving them

```sh
git cherry main <branch>            # anything on GitLab already: safe to drop
git bundle create _backups/<repo>_github-<desc>_<timestamp>.bundle <branch>...
```

Bundle anything not already on GitLab main before deleting it on GitHub, then
delete every branch except `main`. In the pilot, a branch the handover notes
called "a GitLab branch" turned out to already be an ancestor of GitLab main
(no work lost, but don't take the handover's word for it — check with
`git cherry`) (SEOR-zfpaxrxk, 2026-09-19).

### 2.6 Contribution note, on GitLab, not GitHub

GitHub cannot disable pull requests, so add a pinned note instead: a
`.github/pull_request_template.md` (and/or a CONTRIBUTING line) saying
contributions go to GitLab. Commit it to **GitLab** main, not GitHub
directly — GitHub is read-only even for this — and it arrives with the first
mirror push (SEOR-zfpaxrxk, 2026-09-19). Close any pre-existing open GitHub
PRs with a pointer to the GitLab equivalent:

```sh
gh pr close <number> -R OWNER/REPO -c "Superseded by gitlab.com/OWNER/REPO — GitHub is a read-only mirror."
```

**Staffing note:** `gh pr close` is refused by the agent permission
classifier as `[External System Writes]`, on every repo, the same as §2.2.
Hand this off to the owner too (SEOR-ggkpweeg, 2026-09-20 11:14).

### 2.7 The PAT

See §3. By the time a second repo is being mirrored, this step is just
"confirm the repo is in the token's access list" — see §3 for why.

### 2.8 Protected-tag rule, before the first sync

```sh
glab api -X POST projects/OWNER%2FREPO/protected_tags \
  -f name='v*' -f create_access_level=40
```

**This has to exist before the first sync, not after.** With
`only_protected_branches: true`, GitLab mirrors protected branches *and*
protected tags — nothing else. A repo with no `protected_tags` entry mirrors
**zero tags, silently, with no error anywhere** (SEOR-wscogmzh, 2026-09-20
policy addition #1; measured on pslr, SEOR-zfpaxrxk acceptance comment).
Skip this and release tags never reach GitHub, which breaks Zenodo (§5) and
R-hub without any visible failure. Side effect, and a welcome one: a
protected tag cannot be deleted on GitLab at all, so release tags become
immutable at the source once this rule exists.

### 2.9 GH007: the email-privacy block must stay off

GitHub's account setting **"Block command line pushes that expose my
email"** rejects a pushed tag whose tagger email isn't one GitHub is willing
to expose, with `GH007: Your push would publish a private email address`.
This is checked against the **tag's** author email, not the commit author
email — pslr's commits use `b.turczynski@tidio.net` (unaffected) while its
release tags use `bartek@turczynski.pl` (a verified-but-blocked address
until the setting was unticked; old GitHub-era tags carried the
`...@users.noreply.github.com` form instead, which is why this hadn't been
seen before). The address is already public in `DESCRIPTION` and on CRAN, so
unticking it costs nothing here — but if it's ever re-enabled, every future
release-tag push fails the same way (SEOR-zfpaxrxk, 2026-09-19 acceptance
comment; SEOR-wscogmzh policy addition #2).

### 2.10 Create the mirror — and check the stored URL, not just the response

```sh
glab api -X POST projects/OWNER%2FREPO/remote_mirrors \
  -f url="https://<PAT>@github.com/OWNER/REPO.git" \
  -f enabled=true -f only_protected_branches=true -f keep_divergent_refs=false
```

**Known silent, destructive failure mode.** If the shell variable holding
the PAT is empty when this URL is built, the URL still looks plausible
(`https://@github.com/...` collapses to a bare `https://github.com/...` or a
malformed credential) and **GitLab accepts the POST with no error**. The
stored mirror looks configured. It only fails, destructively, at the first
sync, with `could not read Password`. Two confirmed causes: `read -p` is
**bash** syntax — in zsh, `-p` means "read from the coprocess," so the
prompt never appears and the variable silently stays empty (use
`read -rs "PAT?prompt"` in zsh); and mixing a shell-variable step with a
file-based loop. Three sync rounds were lost to this in the rollout. **The
check that catches it:** after creating any mirror, read it back and confirm
the stored `url` contains `:*****@` (both the username and password
placeholders), not just `*****@` (SEOR-ggkpweeg, 2026-09-21 comment) —

```sh
glab api projects/OWNER%2FREPO/remote_mirrors | grep -o 'https://[^"]*@github.com'
```

— **before** forcing a sync, every time.

### 2.11 Force a sync and verify

```sh
glab api -X POST projects/OWNER%2FREPO/remote_mirrors/<mirror_id>/sync
```

Forcing a sync turns each verification into a ~20 second loop instead of
waiting for the schedule; this is safe to run repeatedly (SEOR-ggkpweeg,
2026-09-20 18:08). Then verify, per §4 and the acceptance checks below.

### 2.12 Remove the local `github` remote

```sh
git remote remove github
```

Once the mirror is live, no working copy should have a `github` remote — the
mirror is the only writer, by policy (§1).

### What to expect afterward

Any GitHub App already installed on the account (FOSSA, in the rollout) will
notice the first mirror push and re-scan within minutes — this is normal,
expected, and free (no Actions minutes), but it will resurface findings that
were previously dispositioned only in the old GitHub-era dashboard state
(SEOR-wscogmzh, 2026-09-20 comment).

### Verifying the mirror behaves correctly (acceptance, all measured on the pilot)

- **Main SHA parity**: `git ls-remote` (or `gh`/`glab` API) shows the same
  SHA on both forges after a sync.
- **Tag parity**: `v*` tags have identical object IDs on both forges.
- **Feature branches don't leak.** Safest test: create a throwaway branch on
  GitLab via the API, force a sync, confirm it does *not* appear on GitHub,
  then delete it. GitLab branch create/delete both pass the agent
  permission classifier, unlike the GitHub-side writes above, so this scope
  test is fully agent-runnable (SEOR-ggkpweeg, 2026-09-20 18:08).
- **Deletions never propagate.** The push mirror adds and updates refs; it
  never prunes the remote, `keep_divergent_refs=false` notwithstanding.
  Anything deleted on GitLab (an unprotected tag, a branch) stays on GitHub
  until removed by hand:

  ```sh
  gh api -X DELETE repos/OWNER/REPO/git/refs/tags/NAME
  ```

  This mainly matters for mistakes made *before* a tag is protected —
  protected `v*` tags can't be deleted on GitLab at all, so it's moot for
  real releases (SEOR-zfpaxrxk, 2026-09-19; SEOR-wscogmzh policy addition
  #3).
- **Failure is loud, and needs no extra monitoring.** A broken mirror (bad
  token, GH007 rejection, etc.) produces a GitLab email
  `"<project> | Remote mirror update failed"` from `gitlab@mg.gitlab.com`
  within roughly 2 minutes of the failed sync, quoting the push stderr.
  Confirmed for both a Contents-permission 403 and a GH007 tag rejection
  (SEOR-zfpaxrxk, 2026-09-20 acceptance comment; SEOR-wscogmzh policy
  addition #5).

## 3. The PAT

- **One fine-grained PAT covers every mirrored repo.** Do not mint a
  per-repo token. The pilot started with a PAT scoped to one repo; by the
  second repo in the rollout the owner had extended its **Repository
  access** list to cover all eight, and every later repo just needed adding
  to that list — never a new token (SEOR-ggkpweeg, 2026-09-20 18:08 #1).
- **Permissions: Contents (read/write) *and* Workflows (read/write).**
  GitHub's fine-grained-token creation form does **not** add Contents by
  itself — a token created with only Workflows fails every push with a bare
  `403 Permission denied`, which reads exactly like an access problem.
  Verify on the token's own settings page that it literally says "Read and
  Write access to code" (SEOR-zfpaxrxk, 2026-09-19 21:00; SEOR-wscogmzh
  policy addition #4).
- **Access and permissions are different failure modes — diagnose with a
  control repo.** A `403 Permission denied` on a newly-added repo can mean
  either "the token lacks a permission" or "the token has the permission but
  this repo isn't in its Repository access list." Force a sync on a
  repo that's already working, on the *same* token: if that succeeds, the
  permissions are fine and the problem is always the access list for the new
  repo (SEOR-ggkpweeg, 2026-09-20 18:08 #2).
- **The token value is unrecoverable once stored.** GitHub shows it exactly
  once at creation; GitLab masks it thereafter (`https://*****:*****@...`).
  Write it down when it's created. **After any token change** — new token,
  edited access list, edited permissions — force a sync on an *existing*
  mirror to prove it still authenticates. A stale credential otherwise sits
  silent until the next real release push. Regenerating the token
  invalidates every mirror using it simultaneously, so a regeneration has to
  be followed by re-pasting the new value into every mirror's config, not
  just the one that prompted it (SEOR-ggkpweeg, 2026-09-20 18:08 #3 and
  2026-09-21 comment).
- **Rotation date: none is set.** The pilot's token ("gitlab-mirror") was
  created with expiry **Never**, an explicit owner choice that deviates from
  the original plan's "written-down expiry" rule (SEOR-zfpaxrxk, 2026-09-19
  20:47). Treat that as a recorded, deliberate deviation, not an oversight —
  rotation is manual, on demand (leak, audit, policy change), via
  `github.com/settings/personal-access-tokens`. If this playbook is used to
  set a real rotation date going forward, record it here when that decision
  is made; as of 2026-09-23 there isn't one.
- **Also treat any GitHub-App webhook URL as a live credential.** Zenodo's
  GitHub-integration webhook embeds its `access_token` in the callback URL's
  query string, readable by anyone with repo admin via `gh api
  repos/OWNER/REPO/hooks`. This is separate from the mirror PAT but is the
  same category of "credential nobody thought to protect" (SEOR-bzqbjxxo,
  2026-09-20 10:48 comment).

## 4. Verifying zero runs

Two checks, not one — a run-count check alone misses a live Pages site.

1. **Run count, before vs. after:**

   ```sh
   gh api repos/OWNER/REPO/actions/runs --jq .total_count
   ```

   Record this *before* the first mirror push and compare after. Across the
   full eight-repo rollout, every repo's count was **identical** before and
   after — the whole rollout consumed zero GitHub Actions minutes
   (SEOR-ggkpweeg, closing comment, 2026-09-22; re-confirmed 2026-09-23).
   Also confirm the setting directly:

   ```sh
   gh api repos/OWNER/REPO/actions/permissions --jq .enabled   # expect false
   ```

2. **Pages, explicitly, per §2.3** — `gh api repos/OWNER/REPO/pages` — because
   a served static site costs zero Actions minutes and is therefore
   invisible to check 1. This is the one the "obvious" run-count check
   misses; check it on every repo, not just the ones you remember having
   Pages.

For an ongoing fleet, a longer observation window is the stronger form of
check 1: compare the run count over a week against the number of deliberate
manual dispatches (expected to match exactly, or be zero if nothing was
dispatched). This was still open on the R fleet as of 2026-09-23 — the
window closes around 2026-09-28 — because no dispatchable workflow exists
yet (see §6).

## 5. Zenodo releases through GitHub Releases (universal)

Any repo wanting a Zenodo DOI works the same way once mirrored, independent
of language:

- Zenodo's GitHub integration fires on a **GitHub Release**, not on a
  mirrored tag arriving by itself. A tag reaching GitHub via the mirror does
  nothing on its own.
- Zenodo reads `metadata.version` from `.zenodo.json` (or `CITATION.cff`) in
  the **tagged tarball**, not from the release title — keep that file
  correct at tag time, not after (SEOR-bzqbjxxo, 2026-09-20 10:31 discovery
  comment).
- Handle the **first** release by hand, deliberately, in this order: (1)
  confirm the tag's object ID matches on both forges, (2) run
  `gh release create <tag> --verify-tag` against the **already-mirrored**
  tag — never let GitHub create a new one — (3) confirm the resulting Zenodo
  record before automating anything further.
- A new GitHub Release attaches a **new version under the existing concept
  DOI**; it does not start a new record and does not change any existing DOI
  badge (verified on pslr: concept DOI `10.5281/zenodo.20973660` unchanged,
  version DOI `10.5281/zenodo.22857031` added) (SEOR-bzqbjxxo, 2026-09-20
  10:48).
- **The deposit is not instant.** In the pilot, the release published at
  10:36:31Z and the Zenodo record appeared at 10:42:54Z — about 6.5 minutes
  later. Don't conclude failure from a one-minute poll.
- **The webhook delivery log is misleading; judge by the record.** One
  non-prerelease publish fires three separate `release` webhook deliveries
  (`released`, `published`, `created`), and Zenodo answers them
  inconsistently (`202`, `500`, `409` in the pilot) while still depositing
  correctly. Check the Zenodo record itself, not the delivery log
  (SEOR-bzqbjxxo, 2026-09-20 10:48).
- **Decision: manual, not automated — and why.** Automating "create the
  GitHub Release" from a GitLab tag pipeline would need a *second* GitHub
  credential with Contents write, which directly contradicts §1's "the
  mirror is the only writer" rule. Releases happen a few times a year; that
  second credential is the worse trade. This was decided explicitly during
  the pilot and documented in the affected package's own CONTRIBUTING.md,
  not just here (SEOR-bzqbjxxo, 2026-09-20 10:48).
- A release does **not** wake disabled Actions — confirmed by an unchanged
  run count immediately before and after `gh release create`.

## 6. The `cran-prep` trigger guard — BLOCKED, pending SEOR-fybaobgk

**This section is intentionally a stub.** SEOR-fybaobgk (the manual-dispatch
`cran-prep.yml` workflow and the guard that keeps any future workflow file
from reintroducing `push`/`pull_request`/`schedule` triggers) is `todo` and
untouched as of 2026-09-23 — no guard script exists, no workflow file exists,
nothing has been built. Do not treat the workflow-trigger check in §2.1 as
that guard: §2.1 is a one-time manual read done during rollout, not an
enforced, durable check. Until SEOR-fybaobgk lands, GitHub Actions stays
disabled on every mirrored repo, full stop — there is no repo in the fleet
where it's currently safe to turn Actions on. This section gets filled in
once that ticket produces something proven; nothing generalized beyond it
belongs here yet.

## 7. R-specific extras

These apply only to R packages and have no equivalent for a non-R mirror.

- **R-hub v2** (`rhub::rhub_check()`) dispatches checks as GitHub Actions
  runs in the package's own GitHub repo — it's the reason Actions needs to
  exist on GitHub at all for this fleet, gated behind §6.
- **r-universe**: create the registry repo, install the r-universe GitHub
  App, **then** push `packages.json` — in that order. Installing the app
  against an empty/nonexistent registry does not itself trigger a sync; the
  monorepo's `.registry` pointer only updates in response to a webhook
  event, so if the registry repo already has `packages.json` before the app
  is installed, nothing syncs until an unrelated commit fires the webhook.
  Confirmed the hard way: a bare app install left `.registry` pointing at
  r-universe's own CRAN-fallback source for hours until a trivial README
  commit to the registry repo fired the webhook and the real switchover
  happened within about an hour (SEOR-mqwxeblh, 2026-09-20 07:37 comment).
  Package builds themselves still come from GitLab source URLs — only the
  registry repo needs to live on GitHub.
- **CRAN citation gate side effects, found incidentally during the Zenodo
  pilot, worth checking fleet-wide:** the citation gate checks a package's
  version and URLs, not its DOI identifiers or dates — so a stale DOI in
  `CITATION.cff` or a `NEWS.md` top heading that still names a released
  version number (instead of "(development version)") after a dev-cycle
  bump can sit undetected until the next `cran-prep` run fails on it
  (SEOR-bzqbjxxo, 2026-09-20 10:48).

## Sources

- SEOR-zfpaxrxk — pilot (pslr): the 6-step per-repo procedure and its
  closing acceptance comment (2026-09-20); every GitHub-lockdown trap in
  §2.1–2.9 not otherwise attributed traces to this ticket's 2026-09-19
  comments.
- SEOR-wscogmzh — parent/policy: the five 2026-09-20 policy additions
  (protected tags, GH007, no-prune-on-delete, PAT Contents-by-hand, loud
  failure emails); the visibility-decision and Pages-verification audit
  comment (2026-09-22); the final fleet-state measurement (2026-09-23).
- SEOR-ggkpweeg — rollout (7 more repos): the three procedure corrections in
  the 2026-09-20 18:08 comment (one PAT for all repos; access vs.
  permissions; token unrecoverable/force-sync); the classifier-wall staffing
  note (2026-09-20 11:14); the silent-empty-password mirror-creation failure
  (2026-09-21); the closing measurement (2026-09-22).
- SEOR-bzqbjxxo — Zenodo versioning through GitHub Releases, all of §5.
- SEOR-mqwxeblh — the r-universe registry/app/push ordering gotcha in §7.
- SEOR-fybaobgk — confirms §6 is genuinely untouched (`todo`, 2 comments,
  neither containing implementation work) as of 2026-09-23.
- SEOR-jfoszwzz — this ticket's own 2026-09-22 audit comment, source for the
  Pages-verification-via-API and forced-visibility-decision additions in §1
  and §2.3.

Live-checked against the running system on 2026-09-23 rather than taken on
ticket text alone: `glab api projects/bart-turczynski%2Fseor/remote_mirrors`
(mirror healthy, `only_protected_branches: true`), `gh api
repos/bart-turczynski/seor` (public, Actions disabled, 0 runs, `main` only),
`glab api projects/bart-turczynski%2Fseor/protected_tags` (`v*` rule
present), and `gh api repos/bart-turczynski/rurl/pages` (still serving `200`
from a deleted `gh-pages` branch — the §2.3 gotcha is still live today, not
just in the ticket history).
