# Evidence export

This directory preserves the independent #6697 audit from October 6, 2026.
Original and exported SHA-256 values are recorded in [the manifest](export-manifest.json).
The original local audit is unchanged. Local absolute paths use aliases:

- `<6697-audit>`: this audit's original output directory.
- `<prior-6697-audit>`: the separately recorded October 5 check.
- `<closure24-audit>`: the earlier October 6 review of 24 issues.
- `<survey>`: the existing October 4 survey directory and executable caches.
- `<workspace>`: the baseline RustPython source checkout.
- `<report-worktree>`: the report checkout.
- `<home>` and `<reported-home>`: local and original reporter home directories.
- `<system-temp>`: system temporary paths.

Python and shell inputs have `.txt` appended so formatting hooks cannot alter
executed input. Restore their original names before replaying raw commands.
Use the variables and commands in [the report](README.md) to reproduce the
checks in another checkout. Evidence links were adjusted for the archive names.
Historical evidence remains labeled as reused. Report wording and formatting
do not replace the archived executed inputs or original logs.

The commit hook formatted Python blocks in the report. Their syntax trees
match the source audit; [format validation](hook-format-validation.json)
records the comparison. Links are relocated only outside fenced code blocks.
Archived execution inputs and logs are unchanged.
