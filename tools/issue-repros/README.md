# Verification records

Baseline: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c). Checked October 5–6, 2026.

Results: **25 closure recommendations**, **3 partially resolved issues**.

Start with the [closure request](report.md), then follow an issue's detailed report for its reproducer, commands, results and limits.

## Files and directories

| Path | Contents |
| --- | --- |
| [report.md](report.md) | Submission draft covering the 25 closure candidates. |
| [recheck/cases/](recheck/cases/) | Current reports for all 28 issues. Open `<issue>/README.md`. |
| [recheck/not-ready.md](recheck/not-ready.md) | Remaining failures in #4613, #5181 and #6790. |
| [recheck/independent/](recheck/independent/) | Independent rechecks, executed inputs, results and supporting records. |
| [recheck/evidence/](recheck/evidence/) | Earlier audit runs and reused historical failure evidence. |
| [recheck/manifest.json](recheck/manifest.json) | Issue list, verdicts, scope and closure recommendations. |
| [recheck/ENVIRONMENT.md](recheck/ENVIRONMENT.md) | Executable and library identity, environment settings and recorded path aliases. |
| [recheck/VALIDATION.md](recheck/VALIDATION.md) | Checks on report generation, links, exported evidence and preserved files. |

## Execution evidence

Independent recheck reports: [24-issue review](recheck/independent/2026-10-06-closure24/README.md) · [#6697 review](recheck/independent/2026-10-06-6697/README.md).

Follow each report's evidence links for:

- Inputs and commands, including arguments, working directory and environment.
- stdout, stderr, exit code and timeout status.
- Executable, library and dependency identification.
- Original and exported file hashes in `export-manifest.json`.

Historical runs are labeled separately from fresh executions. Archived Python inputs use `.py.txt`; restore the `.py` name before running them. Use the setup and path variables in the relevant report.

## Earlier material and report generation

- [cases/](cases/), [manifest.json](manifest.json) and [VALIDATION.md](VALIDATION.md): the original 16-case report set. Use `recheck/cases/` for current conclusions.
- [recheck/archive/](recheck/archive/): the earlier submission draft and setup guide.
- [recheck/catalog.json](recheck/catalog.json): source text and verdicts used by [render.py](recheck/render.py) to generate the current draft and case reports. Rendering does not execute reproductions.
- [run.py](run.py): the original runner; recorded-output rendering writes `legacy-report.md` while the current catalog is present.

AI assistance: OpenAI Codex.
