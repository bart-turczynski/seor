# seor architecture

The living map of how this project is put together: directories, responsibilities,
seams, and invariants. Unlike a spec, this file must be true *right now* — it
describes the current structure, not a plan or a history.

Keep it coarse. Name directories and what they own; do not cite line numbers or
function signatures, which rot on the first refactor. Update it when the
structure changes, not when code changes.

For *why* a load-bearing choice was made, see the Architecture Decision Records
in [`design/adr/`](design/adr/). For *what* was built and to which requirements,
see [`design/specs/`](design/specs/).

## Overview

<!-- One paragraph: what this project does and the shape of its solution. -->

## Layout

<!--
Name every top-level source directory. `scripts/check-design.py` fails the push
if one is missing here — that check is the only thing standing between this file
and quiet rot.
-->

- `src/` — <!-- responsibility -->

## Invariants

<!-- Rules that must hold across the codebase. Link the ADR that established each. -->
