# Design docs

Durable, tracked design documentation. Unlike `_scratch/` (gitignored — never on
a fresh clone or in CI), everything here is committed and travels with the code.

Design docs never live in `docs/`. That directory belongs to the toolchain, and
what it means inverts by ecosystem: pkgdown *output* in R, source in
mkdocs/sphinx/docusaurus, handwritten publisher docs in a browser extension.
`design/` is the one name no toolchain claims.

## Layout

- [`adr/`](adr/) — Architecture Decision Records: one file per load-bearing
  decision, capturing the *why* and a status. Start from
  [`adr/0000-template.md`](adr/0000-template.md).
- [`specs/`](specs/) — durable specs: the *what*, as accepted. Point-in-time
  records, frozen once shipped.

See also [`../ARCHITECTURE.md`](../ARCHITECTURE.md) for the structural map.

## Lifecycle

Drafts start in gitignored `_scratch/`. A draft graduates to `specs/` when it
stops being "what if" and becomes what we are building.

On ship, distill the durable facts into `ARCHITECTURE.md` and the load-bearing
choices into an ADR, then set the spec's status to `shipped` and never update it
again. Where a shipped spec and the code disagree, the code and the relevant ADR
win.

## Writing an ADR

1. Copy `adr/0000-template.md` to `adr/NNNN-short-slug.md` (next number).
2. Fill in Context / Decision / Consequences; set `status: accepted`.
3. When a later ADR overturns it, set this one's `status: superseded` and
   `superseded-by:` rather than deleting it — the history is the point.
   Never edit the body of an accepted ADR; `scripts/check-design.py` enforces it.
4. Link the ADR from `ARCHITECTURE.md` where the structure it governs is
   described.
