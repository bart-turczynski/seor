R metapackage, tidyverse-style: `library(seor)` installs and attaches the member packages. No analysis functions of its own.

- Verify gate: the pre-push `verify` hook, the chain CI runs. `_R_CHECK_CRAN_INCOMING_=false` in it is deliberate (ADR 0004).
- Branch pushes and MRs start no pipeline. The pre-push hook is the only branch gate; an empty pipeline list is not a pass.
- Gate red on an untouched tree: check toolchain drift first, `Rscript scripts/check-toolchain.R`.
- `man/` and `NAMESPACE` are generated from roxygen in `R/`.
- Each user-facing change: one NEWS.md bullet. Top heading matches `DESCRIPTION` Version.
- `_scratch/`, `tmp/`, `.fp/` stay uncommitted. `docs/` is pkgdown output, never design docs.
- Git follows the `agent-workflow` skill. fp tracks issues; status changes stay decoupled from git (the `fp` skill's `references/decoupling.md`).

For R style, tests, lints and roxygen, see AGENTS_LANG.md.
For specs, ADRs and the design/ lifecycle, see design/README.md.
For hooks and the pages KEEP list, see design/agent-workflow.md.
For the fleet tracker convention and the per-repo drift table, see design/fleet.md.
For members, invariants and CRAN status, see ARCHITECTURE.md.
For setup and the verify command, see CONTRIBUTING.md.
