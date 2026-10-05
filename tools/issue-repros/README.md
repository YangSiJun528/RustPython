# RustPython resolved-issue reproducers

The October 5, 2026 review recommends **24 issues for closure** and identifies
**3 partially resolved issues** at
[`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).

- [Combined issue draft](report.md): the 24 closure recommendations.
- [Detailed reports](recheck/cases/): all 27 cases, with complete reproduction
  inputs, commands, environment, expected results and recorded results inline.
- [Partially resolved issues](recheck/not-ready.md): #4613, #5181 and #6790.
- [Case manifest](recheck/manifest.json).
- [Environment and evidence mapping](recheck/ENVIRONMENT.md).
- [Validation record](recheck/VALIDATION.md).

## Reading and reproducing a case

Each detailed report can be read from top to bottom without expanding sections
or opening supporting files. Raw evidence links provide the original execution
records and full logs in addition to the relevant results shown inline.

Use the interpreter versions, matching source and standard library, dependency
versions and locale settings specified in the case. Commands use named path
variables in place of machine-specific paths. Archived inputs use a `.py.txt`
suffix to preserve the executed source independently of document formatting.

Current results were executed on October 5; historical results are labeled
separately. Related changes explain the observed behavior without claiming an
unverified first fixing commit.

Regenerate the current documents without running interpreters:

```sh
python3 tools/issue-repros/recheck/render.py
```

## Historical archive

The original [16-case manifest](manifest.json), [case files](cases/),
[validation record](VALIDATION.md), [combined draft](recheck/archive/report-before-independent-review.md)
and [setup guide](recheck/archive/README-before-independent-review.md) are
preserved for comparison. Current closure recommendations are in `report.md`.

The [legacy runner](run.py) writes its aggregate output to `legacy-report.md`
when the current recheck catalog is present:

```sh
python3 tools/issue-repros/run.py --render-recorded
```

AI assistance: OpenAI Codex.
