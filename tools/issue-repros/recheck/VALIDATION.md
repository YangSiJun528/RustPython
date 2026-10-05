# Publication validation

This update packages the completed independent audits. No new interpreter result
or historical run is claimed by the publication step.

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
