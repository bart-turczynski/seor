R metapackage, tidyverse-style: `library(seor)` installs and attaches the member packages. No analysis functions of its own.

Gate: local
Verify: .fleet-ci/gate auto

- The merge gate is fleet-ci's local gate, run in the fleet image by the pre-push hook (`pre-commit install`, then `.fleet-ci/pre-push --install`, once per clone; settings in `.fleet-ci.yml`). A docs-only diff against `main` gets T0 (spelling, `pkgdown::check_pkgdown()`); any other gets T1 (T0's checks, then lintr, docs drift, the URL, README and NEWS-heading checks, one `R CMD check --as-cran`; the citation, BugReports and logo-metadata checks run as host gates). The pre-commit pre-push hooks, the fleet tooling's self-tests among them, run after it. One of them, `check-toolchain` (always run), still checks this machine's R library and pandoc, not the gate's image, and can block a push.
- Branch pushes, MRs and pushes to `main` start no pipeline; an empty pipeline list is not a pass. CI runs T2 on the weekly `deep-check` schedule and T3 on a `RELEASE=1` web pipeline and the `v*` tag (ADR 0012). The gate refuses a push when more than one ref targets `main`, or when it adds more than one first-parent merge to `main`.
- `FLEET_INCOMING: "false"` in `.gitlab-ci.yml` is deliberate (ADR 0004, carried forward by ADR 0012).
- Gate red on an untouched tree: keep the evidence (`FLEET_GATE_KEEP=<dir>`); a dependency that moved on CRAN can do it. `Rscript scripts/check-toolchain.R` checks this machine's roxygen2 and pandoc against the pins.
- `man/` and `NAMESPACE` are generated from roxygen in `R/`.
- NEWS.md: one terse line per change a package user notices; never logos, image or repository metadata, CI, gates or housekeeping (AGENTS_LANG.md). Top heading: the `DESCRIPTION` Version or "(development version)".
- `_scratch/`, `tmp/`, `.fp/` stay uncommitted. `docs/` is pkgdown output, never design docs. `.fleet-ci/` is fleet-ci's `bin/vendor` output: re-vendor, never edit.
- Git follows the `agent-workflow` skill. fp tracks issues; status changes stay decoupled from git (the `fp` skill's decoupling reference).

For R style, tests, lints and roxygen, see AGENTS_LANG.md.
For specs, ADRs and the design/ lifecycle, see design/README.md.
For the tiers, the hook and the gaps the fleet-ci migration accepted, see design/ci.md.
For the hooks and the pages keep list, see design/agent-workflow.md.
For the fleet tracker convention, the per-repo drift table and the pipeline schedules, see design/fleet.md.
For members, invariants and CRAN status, see ARCHITECTURE.md.
For setup and the local gate, see CONTRIBUTING.md.
