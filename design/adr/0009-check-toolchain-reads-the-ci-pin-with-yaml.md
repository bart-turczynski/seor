---
status: accepted
date: 2026-10-06
tracking: SEOR-bqroclcz
---

# ADR 0009: check-toolchain.R reads the CI pin with the yaml package

## Context

`scripts/check-toolchain.R` compares the local pandoc with `PANDOC_VERSION`
in `.gitlab-ci.yml`, and it is the fleet's only reader of that pin:
`check-fleet-standard.py` runs its `--pandoc-assignments` and
`--pandoc-unread` rather than reading the pin itself (SEOR-xhyrogfm,
SEOR-mcstkogt; [ADR 0008](0008-fleet-checker-reads-ci-with-pyyaml.md)
left that contract alone). It used only base R, so it read the YAML with
line regexes: a key regex, a scalar decoder, a regex for node properties, a
rule for "the first filled line below the key, deeper than it", and a count
of "settings" per line against values read. Pinned as cases against that
reader on 2026-10-06, none of them in a fleet CI file:

- A block scalar, `PANDOC_VERSION: >-` with `3.10` below it, read as the
  pin `>-`. `!reference [.v, PANDOC_VERSION]` read as that text, `~` and
  `null` as literal pins, and `PANDOC_VERSION=3.10${SUFFIX}` as 3.10.
- `eval PANDOC_VERSION=3.9`, `env -u X PANDOC_VERSION=3.9`,
  `for PANDOC_VERSION in …` and `read PANDOC_VERSION` were not seen at all.
- `echo local PANDOC_VERSION=3.9`, `echo $X, PANDOC_VERSION: 3.9`,
  `echo {PANDOC_VERSION: 3}` and a here-document line
  `{"PANDOC_VERSION": "3.9"}` were refused as settings, and so was a quoted
  or spaced bare key (`"PANDOC_VERSION":`) while `PANDOC_VERSION:` passed.
- `readonly`, `declare -x` and `typeset -x PANDOC_VERSION=3.10` were
  refused, though `check-fleet-standard.py` counts them as assignments.
- A flow mapping, a quoted key, an alias and a merge key were refused
  outright, since the line reader could not read them.

The rule for the value below a key existed twice, and the refusal re-ran
the whole reader on the same text. The script is vendored byte for byte into
the eight member packages. Their pre-push hooks run it (`language: system`,
the R on PATH), and seor's `check-fleet-standard-self-test` hook runs it
through `Rscript --no-save --no-restore --no-init-file`: not `--vanilla`,
which skips `~/.Renviron` and with it a library such as `R_LIBS_USER` set
there. No CI job in any of the nine repositories runs
it (checked on 2026-10-06).

## Decision

1. **The YAML side is the yaml package.** `yaml::yaml.load()` parses
   `.gitlab-ci.yml` with `eval.expr = FALSE` and `merge.precedence =
   "override"`, one call per document (a `---` line starts one). A handler
   marks sequences, so a one-item list is not taken for a scalar, and another
   keeps a `!reference` as an unresolved reference: untagged, the package
   would load `!reference .pin` as the string `.pin`. A warning fails the
   load, since an unknown alias otherwise loads as a placeholder string and
   a `!!int` the package cannot read as NA. The one exception is a number
   out of R's integer or double range (`PROJECT: 12345678901`): it loads as
   NA, which changes nothing read, as a PANDOC_VERSION key with that value
   is refused as unread. A `spec:` header document, the first of two and
   holding only `spec:`, declares an include's inputs and is not read.
   Quoting, comments, flow and block collections, anchors, aliases and merge
   keys are the parser's.
2. **Every PANDOC_VERSION key counts**, in any mapping at any depth, quoted
   or not. A literal value (letters, digits, `.`, `+`, `-`) is a pin.
   Unquoted, `3.10` is the float 3.1, as GitLab's YAML 1.1 reads it. Null
   sets no version, however it is spelled. A mapping with `value:`,
   `description:`, `expand:` or `options:` is GitLab's expanded form, refused
   as before, and `--pandoc-unread` prints its line at any depth:
   `check-fleet-standard.py` finds the form itself only in the global and
   top-level `variables:`, so a deeper one, such as a `rules:` entry's,
   reaches it as that line. Anything else is refused as an unread setting, naming its line:
   a `!reference`, a list, another mapping, a boolean, an empty or computed
   value. So is a number with no plain text after the key on the key's own
   line, because the yaml package types a block scalar the way it types plain
   text: `>-` with `3.10` below it parses as 3.1, where GitLab reads "3.10".
   After an alias, the value's style can no longer be seen.
3. **Lines come from renamed tokens.** The package keeps no line numbers.
   Before the one parse, every `PANDOC_VERSION` token in the text is renamed
   `PANDOC_VERSION__<id>`, numbered in file order, and each id names its
   line. A key or a script item that the parser hands back names its own
   line, however it was spelled, aliased or merged. A token inside an
   anchor's or an alias's name (`&a-PANDOC_VERSION`) keeps its text, so the
   two still match, unless `=` or `+=` follows: that is a shell assignment
   after `&&`. An anchor or an alias starts only a node (a line, or after
   `- `, `: `, `? `, `[`, `{` or `,`); elsewhere `&` and `*` are text, as in
   `?os=linux&v=$PANDOC_VERSION`, and the token is renamed. Renamed apart, two PANDOC_VERSION keys in one mapping no
   longer collide, so a mapping handler records each mapping's own keys and
   refuses the second as the parser's duplicate key, naming its line. A key
   a `<<` merge brings in is the source mapping's, built first, and no
   duplicate. An error the parser raises names the line it reports, and
   its message counts lines from the top of the file, not from the
   document's `---`.
4. **Regexes remain only for shell.** They read script items: strings in a
   YAML sequence at any depth, or the value of `script`, `before_script` or
   `after_script`. They read one token at a time, at a command head: a
   line's start, `;`, `&`, `|`, `(`, a `{` group or a `case` pattern's `)`,
   then any of `if`, `elif`, `while`, `until`, `then`, `do`, `else`, `time`
   and `!`. A comment starts at a `#` that begins a word outside quotes. A
   literal assignment in the current shell or in a command's prefix is a pin,
   plain or through `export`, `readonly`, `declare` or `typeset`. A setting
   under `env` or `local`, a `for`, `select`, `read` or `printf -v` target,
   `+=`, a non-literal value and `${PANDOC_VERSION:=…}` are refused. So is
   any PANDOC_VERSION token under `eval`, quoted or not, but a use
   (`eval "echo $PANDOC_VERSION"`, which sets nothing): eval runs shell this
   does not parse, so `unset` or a `getopts` target there fails closed.
5. **It fails closed.** A file that names PANDOC_VERSION and does not load
   stops the check, with the parser's message. `--pandoc-unread` prints it
   as `unloadable\t<text>\t<line>\t<message>`. `check-fleet-standard.py`
   reports that as a gap. It arises only where PyYAML loads what the yaml
   package refuses, such as a duplicate key. A file that never names
   PANDOC_VERSION is not parsed.
6. **The dependency is checked, not declared.** `scripts/` is in
   `.Rbuildignore`, so no `DESCRIPTION` lists it. A yaml that does not load,
   or one older than 2.2.1, the first whose `yaml.load()` takes
   `merge.precedence` (the package's NEWS), stops the script with one line
   naming the package, the version and its install command, so a machine
   problem is not reported as broken YAML.

## Consequences

- `check-toolchain.R` is no longer base R only. Every fleet machine already
  has yaml: rmarkdown and knitr import it, every member suggests both for its
  vignettes, and check 4 already needs rmarkdown. The self-test runs on every
  invocation, so a machine without yaml stops the pre-push hook in one line
  before any check runs.
- The `--pandoc-assignments` / `--pandoc-unread` contract is unchanged,
  except for the added `unloadable` line kind and the expanded form's
  `unread` line.
- Spellings the line reader refused, such as a flow mapping, a quoted key,
  an alias to a quoted scalar, a merge key or a quoted value below the key,
  are now read as pins. Beside a different global pin they are a second
  value, which is still an error.
- A duplicate mapping key, which GitLab and PyYAML load, stops this check.
  So does `!reference` as the pin's value, which neither reader resolves.
- Standing rule: do not reintroduce a line-based reading of the YAML side.
  A shell rule reads script items from the parsed file, not raw lines.
- Revisit if the yaml package stops typing block scalars, which would let the
  same-line rule for numbers go, or if the fleet starts writing the pin
  through `!reference`.
