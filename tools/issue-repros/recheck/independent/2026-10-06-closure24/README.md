# Independent closure review — October 6, 2026

This is the independently collected review of the 24 closure candidates at
interpreter commit `f39b054b9c8cbbf884f53123eef028131789990c`, reviewing the draft at
`ad600eb347fd7de31a453dd56cd377d6ae948c10`.

All 24 original issue scopes were confirmed resolved. The review retained
22 draft entries unchanged and required wording corrections for #4690 and
#8494. The submission draft and its two detail reports now incorporate those
corrections. This snapshot records the assessment before those wording edits.

- [Full review and scope limits](SUMMARY.md).
- [24 case reports](cases/), including inputs, commands and key output.
- [Machine-readable judgments](results.json) and [execution records](executions.jsonl).
- [Preservation comparison](parent/preservation-comparison.json).
- [Export mapping and original/export SHA-256 values](export-manifest.json).

The source verification directory remains unchanged. This export anonymizes
machine-local paths consistently with the existing evidence archives. Logical
path markers are `<closure24-audit>` (this verification output), `<workspace>`
(slot A source), `<slot-b-source>`, `<report-worktree>`, `<survey>` (retained
build/dependency/history artifacts), `<home>`, `<reported-home>` (paths quoted in upstream issue/source text) and `<system-temp>`. Substitute
your equivalent absolute locations when reconstructing an input or command.

Executed Python and shell inputs use `.py.txt` / `.sh.txt` archive suffixes;
HTML captures use `.html.txt`. Save the text using the recorded original name
before running it. The text suffix prevents formatting hooks from rewriting
executed evidence. Markdown links point to the archived names; paths inside
execution records retain their original logical names, resolved through the
export manifest. No interpreter input was reexecuted for this export.

Large Git status captures and NUL-delimited status records are gzip-compressed.
Decompression recovers the anonymized capture. Original hashes describe the
unmodified local originals; export hashes describe the committed representation.
These are different whenever path anonymization or compression was applied.
Only generated controller bytecode and xcrun lookup caches are omitted, as listed in the manifest.

Historical build/run evidence is explicitly distinguished from fresh runs.
The existing successful-build records, embedded version banners and matching
artifact hashes corroborate the target binaries; no fresh rebuild or earliest
fixing-commit claim is made. Slot B actually imports slot A's matching Lib tree.

AI assistance: OpenAI Codex.

The repository commit hook formatted Python blocks in 19 exported case reports.
All 47 affected Python blocks have equivalent ASTs before and after formatting.
The archived execution inputs and logs were unchanged; updated report hashes
and formatting transformations are recorded in the export manifest. See the
[format verification](export-format-validation.json).
