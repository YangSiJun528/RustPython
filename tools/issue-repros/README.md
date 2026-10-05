# RustPython resolved-issue reproducers

The October 5, 2026 independent review recommends **24 issues for closure** and
keeps **3 partially resolved issues open**. The interpreter baseline remains
[`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).

- [Combined issue submission draft](report.md): the 24 closure candidates, using
  the existing issue-summary, related-change and reproduction-link format.
- [Current detailed reports](recheck/cases/): executed input, expected and observed
  output, commands, rationale, environment and linked evidence for all 27 issues.
- [Not ready for closure](recheck/not-ready.md): #4613, #5181 and #6790, including
  the counterexamples that changed the previous recommendations.
- [Current case manifest](recheck/manifest.json).
- [Executable and standard-library identity](recheck/ENVIRONMENT.md).
- [Publication validation](recheck/VALIDATION.md).

This branch contains a draft only. No GitHub issue, PR or comment was submitted.
#6697 and #5361 are outside these independent reviews and are not included.

## Read and reproduce the current evidence

Each current case presents the reproducer, expected and observed results,
commands, analysis, versions and linked evidence. Output is grouped vertically
by execution, with long code and logs in expandable sections. Historical results
are explicitly marked as reused evidence. The October 5 current results
were independently executed; publication itself does not claim new executions.

The [environment guide](recheck/ENVIRONMENT.md) explains the two existing execution
slots, exact binary hashes, actual imported `Lib` locations, CPython version and
local-path placeholders. Archived Python inputs retain a `.py.txt` suffix so
formatting tools cannot silently alter the executed evidence. They are readable
Python source, not a new build environment or automatically portable setup.

The independent review used new agents without inherited conclusions. They read
the original issue requirements before reading the previous report. The current
verdicts are based on fresh behavior and source inspection, with historical logs
clearly separated. Related PRs are not asserted to be the first fixing commits.

Regenerate the current draft and detailed reports without running interpreters:

```sh
python3 tools/issue-repros/recheck/render.py
```

## Preserved October 4 material

The original [16-case catalog](manifest.json), [case files](cases/), [runner](run.py)
and [validation record](VALIDATION.md) are retained. Their passing narrow oracles
do not override the independent verdicts: in particular, the bare locale example
and forced-skip check do not establish closure of #5181 or #6790.

The former [combined draft](recheck/archive/report-before-independent-review.md)
and [setup/runner guide](recheck/archive/README-before-independent-review.md) are
archived. Those documents describe the earlier scope and are not the current
closure recommendation. Existing `BUILD.md` recipes are historical instructions;
no clone, checkout, new target directory or rebuild was used for this update.

The legacy renderer still regenerates its 16 case documents. Once this recheck
catalog is present, its aggregate output goes to `legacy-report.md`, preserving
the current 24-case `report.md`:

```sh
python3 tools/issue-repros/run.py --render-recorded
```

AI assistance: OpenAI Codex assisted with independent verification, evidence
selection, packaging and drafting.
