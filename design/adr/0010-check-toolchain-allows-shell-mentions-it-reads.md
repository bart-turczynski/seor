---
status: accepted
date: 2026-10-06
tracking: SEOR-eeswpcpq
---

# ADR 0010: check-toolchain.R allows only the shell mentions it reads

## Context

[ADR 0009](0009-check-toolchain-reads-the-ci-pin-with-yaml.md), decision 4,
read script items with a denylist. A token at a command head was a pin, and
a list of other spellings was refused: `env`, `local`, `eval`, `for`,
`select`, `read`, `printf -v`, `+=` and `${PANDOC_VERSION:=…}`. Any other
token passed as text. Each review of that reader found more ways sh sets the
variable that the list did not name. Every one was checked on 2026-10-06
with `--pandoc-assignments --pandoc-unread`, and none is in a fleet CI file:

- SEOR-qakbchzg: a quoted declaration argument, `export "PANDOC_VERSION=3.9"`,
  and `let PANDOC_VERSION=3`.
- SEOR-eeswpcpq: a `\` continuation (`export \` with the argument on the next
  line), a wrapper (`command export`, `builtin export`, `nohup env`), a
  spaced arithmetic command (`(( PANDOC_VERSION = 3 ))`), and a name split by
  a quote, a backslash or an escape (`PANDOC_"VERSION"`,
  `$'PANDOC_\x56ERSION=3.9'`, a YAML `\n` before the name).
- Seen while fixing those: `declare -n r=PANDOC_VERSION`, `mapfile`,
  `unset`, a bare `local` and `trap 'PANDOC_VERSION=3.9' EXIT`.

Text the denylist passed can set the value as well: an echoed
`PANDOC_VERSION=3.9` written to a file and sourced does. The nine fleet CI
files name PANDOC_VERSION in a script only as the pin, as
`${PANDOC_VERSION}` and as `Sys.getenv("PANDOC_VERSION")` (checked on
2026-10-06).

## Decision

This replaces ADR 0009's decision 4. Its other decisions stand.

1. **A script item names PANDOC_VERSION only in forms this reads.** A token
   is allowed when it is:
   - a pin: a literal assignment at a command head, plain or through
     `export`, `readonly`, `declare` or `typeset`, after other assignments
     or as a command's prefix (ADR 0009's heads, except that `((` starts no
     command);
   - a use: `$PANDOC_VERSION`, or `${PANDOC_VERSION…}` with no `=`, `:=` or
     subscript, or R's `Sys.getenv("PANDOC_VERSION")`;
   - a bare name that `export` or `readonly` hands on unchanged; or
   - in a comment.

   Any other token is refused as unread, naming its line, quoted or not and
   whatever the command: echoed text, a here-document, arithmetic, `let`,
   `eval`, a wrapper and a builtin no list names. A string in a list under a
   key GitLab never runs as shell (`paths`, `needs`, `tags`, `extends`,
   `include` and the like) is text, not a script item.
2. **A script item's lines are joined as sh reads them.** A line that ends
   in a `\` outside single quotes and comments is joined to the next, and so
   is a line that ends inside a quote or a substitution, so a `#` that
   starts the next line is the quote's, not a comment. Each token keeps its
   id, so it still names its own line.
3. **A disguised name is refused by line.** It may be split by a quote or a
   backslash, written with an escape that YAML or `$'...'` decodes, or
   broken across an escaped YAML line break. The token pattern cannot see
   such a name, so a line is refused when more names appear in its text
   after decoding, up to three layers deep, than before. This runs on every
   text, including one with no plain PANDOC_VERSION in it. A comment whose
   escapes decode to the name is refused too: telling a YAML comment from a
   line of a quoted scalar that starts with `#` takes a YAML reader.

## Consequences

- A new way to set a variable needs no new rule. It is refused because it is
  not one of the allowed forms.
- Echoed or printed text, a here-document, or arithmetic that names the
  variable without setting it is now refused, as is a bare `local`. The fix
  is to drop the name from the text or to write it as a use, for example
  `echo "pandoc ${PANDOC_VERSION}"`. `check-fleet-standard.py` reports the
  same lines as a gap.
- The reader got smaller: the `eval`, declaration-argument, `let` and
  arithmetic patterns and the stray-`)` patterns are gone.
- A here-document whose text holds an unpaired quote joins the lines after
  it into that quote, and a pin there is then refused, not read. A pin
  written as the fleet writes it, outside here-documents, is unaffected.
- Out of reach: a name computed at run time (`${P}_VERSION`), a file that is
  sourced, and the CI/CD settings. A static reader cannot see these.
- Standing rule: do not add a shell spelling to a list of refusals. Widen the
  allowed forms only for a spelling the fleet needs, with a self-test case.
