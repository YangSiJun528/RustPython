# Publication validation

This update packages the completed independent audits. No new interpreter result
or historical run is claimed by the publication step.

## Original publication checks

- The catalog contains exactly 27 issues: 24 closure candidates and the partial
  cases #4613, #5181 and #6790. The combined draft has exactly 24 issue bullets.
- Current detailed reports and same-branch reproduction links resolve to included
  files. Preserved historical links resolve to the existing 16-case archive.
- All exported evidence hashes match `export-manifest.json`. Local user paths are
  consistently substituted, with original and exported hashes kept separately.
- JSON data parses. Evidence files retain their recorded formatting; Python source
  evidence is stored as `.py.txt` rather than silently reformatted.
- The current renderer is deterministic and runs no behavior probes.
- The legacy renderer was exercised on a disposable copy of the old report bundle:
  it creates `legacy-report.md` and preserves the current `report.md`.
- Existing case files, logs, inputs, the original manifest and validation record
  remain byte-for-byte unchanged. The former top-level draft is archived before
  replacement. The only existing files intentionally updated are `README.md`,
  `report.md` and the legacy renderer's aggregate-output routing in `run.py`.
- Normal commit hooks are required; they are not bypassed.

The independent audit checks, underlying runtime records and binary/Lib identity
are linked from each case and `ENVIRONMENT.md`. The initial audit has 14 resolved
and 2 partial cases; the additional audit has 10 resolved and 1 partial case.
The latter contains 97 fresh interpreter/control/identity processes, not 97
independent bug fixes. Expected exception exits are not counted as crashes.

No interpreter source, stdlib test or build cache is changed. Cargo build, cargo
test and clippy are not part of this documentation packaging step; creating or
overwriting builds would violate the retained resource and preservation limits.
Only the report branch in the user's fork is authorized for push. No issue,
pull request, comment or issue-state mutation is part of this task.

AI assistance: OpenAI Codex prepared and checked the publication packet.

## Readability validation

The documentation edit changes presentation without rerunning interpreters or
changing closure verdicts.

- All 27 detailed reports use ordinary sections and lists, with no Markdown
  tables or expandable sections. Reproduction inputs, prerequisite versions and
  locales, commands, expected results and recorded results appear inline.
- Shared Python probes include the selected function, imports and dispatcher.
  Companion input files and supplementary regression-test runners are included
  where needed. REPL input remains literal terminal input.
- Displayed Python code is checked against archived source. Differences are
  limited to documented path substitutions and presentation; formatting changes
  preserve the syntax tree. The safe-path fixture uses a shorter directory name.
- Repeated shutdown warnings and runner metadata are omitted from historical
  excerpts. Essential failure messages remain. Reformatted output is identified.
- Current Markdown parses, local evidence links resolve, and the renderer is
  deterministic. The combined draft still contains exactly 24 closure candidates.
- Raw evidence, historical archives, executable caches and interpreter sources
  remain unchanged. This validation runs no behavior probes.


## October 6: independent #6697 review and 25-issue draft

- #6697 was reviewed from its original issue and comments before reading prior
  conclusions, then independently executed at the same interpreter baseline.
  [The new report](independent/2026-10-06-6697/README.md) records its evidence
  and scope limits. This runtime audit is separate from document rendering.
- The current catalog and manifest contain 28 cases: 25 closure candidates and
  the same three partial cases. All previous 27 case documents and judgments
  remain unchanged. The combined draft includes #6697 once.
- Source and export hashes, JSON, evidence links, count consistency and
  deterministic report regeneration were checked. Executed inputs are archived
  as text; original local evidence and prior audit snapshots are preserved.
- The summary explains the issue-tracker cleanup purpose and distinguishes
  extensive AI assistance, the contributor's stated manual spot checks and the
  absence of a complete code-level review of every underlying fix.

Normal pre-commit hooks run for the documentation commit. No interpreter,
stdlib or existing test implementation changes are included.
