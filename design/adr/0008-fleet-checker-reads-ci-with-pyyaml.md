---
status: accepted
date: 2026-10-05
tracking: SEOR-oznwzhem
---

# ADR 0008: the fleet checker reads CI with PyYAML, not stdlib-only

## Context

`scripts/check-fleet-standard.py` judges each fleet package's `.gitlab-ci.yml`
against `design/fleet-standard.md`. Like the other scripts in seor it was
stdlib-only, so it read the YAML with line-based readers: it split the file
into top-level blocks, and `children()` handed each key's inline value on as
raw text, which five readers (`unquote`, `list_values`, `yaml_scalar`,
`scalar_map`, `parse_rules`) decoded in five different ways. A sixth,
`script_entries()`, rebuilt script items (`- |`, `- >`, flow lists) for the
pandoc install check. Every YAML feature had to be rebuilt by hand, and each
rebuild had its own blind spots. Pinned as failing cases on 2026-10-05
against that reader:

- `extends: .r  # template` lost the template without a word, so the job had
  no image and no script.
- `when: on_success # explicit` read as a job that does not run on push.
- `image: "rocker/r-ver:4.5" # newer` kept its quotes and its comment, so no
  deep-check leg was found.
- `allow_failure: true # soft for now` read as `"true # soft for now"`, which
  is not equal to `"true"`, so a coverage job that cannot fail the pipeline
  passed. That one was a false pass.
- `- &name |` read as a plain scalar, not a literal block, so an anchored
  pandoc install looked like the wrong shape.
- A job's text joined every block it extends, so a parent's `script:` that the
  job replaces still counted. raddr's `.r-job` template runs its verify gate,
  and `coverage`, `readme` and both audit jobs replace that script. The old
  reader still counted `R CMD check --as-cran` in all four.
- The self-test's own fixture `.gitlab-ci.yml` was not valid YAML. Its coverage
  item was a plain scalar holding `Coverage: %`, which GitLab would refuse.
  `- ! cmd`, which a fixture used as a negated check, is YAML's non-specific
  tag, so GitLab runs `cmd`.

Each of these could be patched where it sat, but the same family would come
back with the next construct nobody had rebuilt.

## Decision

1. **The parser is `yaml.safe_load_all` (PyYAML).** YAML 1.1, as GitLab's
   Psych reads it: an unquoted `3.10` is 3.1 and `yes` is true. Quoting,
   comments, block and flow lists, anchors, aliases and `<<` merge keys come
   from YAML itself. The file is one config document, or a header document
   holding only `spec:` and then the config. Hand-written code remains only
   for GitLab's semantics on top of it:
   - `extends` deep-merges mappings and replaces arrays, later parents over
     earlier ones and the job over all;
   - `default:` fills only the keys a job leaves unset. It does not merge into
     a key the job sets;
   - `inherit:`;
   - `rules:if` and `workflow:rules`, a job's rules seeing its own variables
     over the global ones it inherits;
   - `parallel: matrix` image expansion.
2. **The checker fails closed.** A load error marks every CI rule for that
   package as not judged, through `report.skip` with its `incomplete` flag
   set, and the run is incomplete: exit 2 when the run has no gap, under the
   script's existing exit contract. Every failure to load is a load error:
   a YAML error, an unknown tag such as `!reference`, a scalar its tag cannot
   hold (`2026-02-30`, `!!int 'abc'`), a recursive alias, a document shape
   other than the two above, and a top level that is not a mapping. So is an
   `extends` that names no block, loops or nests too deep, and a `rules:if`
   that does not read, an empty one included, since what GitLab makes of an
   empty one is not settled here. The other areas are still judged. `!reference` gets no resolver, and
   `include:` is not followed.
3. **A resolved job is the only input to the CI rules.** It exposes:
   - `Job.config`, the merged mapping;
   - `job.script()`, the `before_script` then `script` items it runs,
     decoded, with nested lists flattened as GitLab flattens them;
   - its variables as typed values, so settings such as
     `_R_CHECK_CRAN_INCOMING_` are checked directly;
   - `job.chunks()`, the one searchable view every text rule reads
     (`--as-cran`, `error_on`, `rcmdcheck`, CRAN incoming, coverage
     thresholds, sanitizer flags, `fossa analyze`, the gates), built once
     per job. It holds the job's effective script items with a `NAME=value`
     line for each variable the job sees, then the repository scripts that
     text names, each a separate text. So a flag or a script path passed
     through a variable counts, and a parent's script the job replaces and
     an anchor it never uses are not in it.

   Raw YAML text is no longer an input to any rule. The one exception is the
   pandoc pin, which `check-toolchain.R --pandoc-assignments` reads from the
   raw file. That contract does not change.
4. **The scope stops at the reader.** `job.script()` replaces
   `script_entries()` as the input to the pandoc install check. The shell
   analysis in `pandoc_install_state` does not change, and neither does the R
   pin reader. The pin-visibility check gets only what it needs to keep its
   meaning: a variable, or an assignment in a setup item that the commands
   after it see (plain, or through `export`, `readonly`, `declare` or
   `typeset`), must supply the pin. The name in a comment, an echoed string
   or a here-document does not count, nor an assignment in a subshell, a
   pipeline stage or a command's prefix. An assignment under `eval`, `sh -c`,
   `$(...)`, backticks or a function's `local` is not judged, and leaves the
   run incomplete.
5. **The dependency is pinned and lives in the hook.** The
   `check-fleet-standard-self-test` pre-commit hook is `language: python` with
   `additional_dependencies: [pyyaml==6.0.3]`, and its entry runs that
   environment's `python`. A manual run without PyYAML exits 2 with an install
   hint.

## Consequences

- `check-fleet-standard.py` is no longer stdlib-only. The scripts vendored
  into other repositories (`check-citation.py`, `check-citation-nonr.py`,
  `bestpractices-url.py`) and `check-design.py` stay stdlib-only. Their reason
  is that they run in any repository's bare CI image. This script runs only
  from seor.
- A package that adopts `!reference` or `include:` has its CI not judged.
  The run reports it rather than guessing.
- The diff run on 2026-10-05 compared the old and new outputs for the nine
  packages (`--local --offline`) and found identical gap tables. A per-job
  comparison of what each reader derives (pipelines run, images, the text
  rules each job's chunks satisfy, coverage keys, the pandoc install state)
  differed only in raddr's overridden template script.
- Standing rules: do not reintroduce a line-based reading of `.gitlab-ci.yml`
  for a rule, and do not match a rule against raw YAML text. A rule that
  needs a setting reads it from `Job.config` or the job's variables. A
  `!reference` resolver or `include:` support needs a new ADR.
- Revisit if GitLab's YAML reading stops matching YAML 1.1 as PyYAML
  implements it, or if the fleet starts depending on `!reference` or
  `include:`.
