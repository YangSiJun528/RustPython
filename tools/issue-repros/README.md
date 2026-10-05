# RustPython resolved-issue reproducers

Run the 16 closure candidates from the October 4, 2026 verification locally.
This directory contains 14 script checks, one interactive check covering two
REPL examples, and one documentation URL check. The interpreter baseline is
[`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).

- [Combined issue submission draft](report.md): a closure request with each issue's
  before/after behavior, related changes and link to its detailed report.
- [Detailed reports](cases/): exact historical/current checkout commands, pinned
  build toolchains, executable version checks, identical reproduction inputs,
  inline output comparisons, analysis and relevant PRs for each issue.
  Full logs remain linked; display-only omissions are labeled in the comparison.
- [Case definitions and expected results](manifest.json)
- [Local validation record](VALIDATION.md)
- Individual inputs, commands and recorded evidence are under `cases/<issue>/`.

## Optional local batch runner

Use a POSIX host (Linux or macOS) with Python 3. From the repository root, build RustPython and launch the host-side runner:

```sh
cargo build --release --locked
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib"
```

`python3` runs the orchestration code only. Every Python reproducer runs in the
explicitly supplied RustPython executable. The runner uses only Python's standard
library and starts each case in a fresh temporary working directory.

Select one issue, or repeat `--issue` to select several:

```sh
python3 tools/issue-repros/run.py \
  --rustpython "$PWD/target/release/rustpython" \
  --stdlib "$PWD/Lib" \
  --issue 4762 --issue 8052 \
  --output /tmp/rustpython-selected-results
```

The output directory must not already exist. Without `--output`, results go to
a new timestamped directory under `tools/issue-repros/runs/`, which Git ignores.
Each issue produces `report.md`, `result.json`, `stdout.txt` and `stderr.txt`;
the top-level `README.md` and `summary.json` link the results. Manual or skipped
checks have a report explaining their prerequisites instead of execution logs.

A `PASS` means the recorded current-behavior oracle matched. In particular,
#4786 must raise `UnicodeEncodeError`, and #5656 must emit `SyntaxWarning`;
successful process exit alone is insufficient. `FAIL` or `ERROR` makes the
runner exit nonzero. `SKIP` and `MANUAL` are explicitly reported and never count
as passes. A timeout is a failed check, not evidence of an interpreter crash.

### Special setup

- **#2527:** run on Linux with PTY support. The runner uses `TERM=xterm`, sends
  one line after each prompt, and checks both block outputs. It stores history
  and the output file in the temporary directory. On other systems it reports
  `SKIP`. A script or piped stdin does not exercise the reported REPL behavior.
- **#5181:** install or enable the `en_US.UTF-8` system locale first (`locale -a`).
- **#6790:** use the matching RustPython standard library with `test.support`
  and an available lzma module.
- **#4784:** the runner reports `MANUAL`; the read-only URL check is:

  ```sh
  sh tools/issue-repros/cases/4784/check.sh
  ```

## Compare another revision

Supply an already-built historical executable and its matching standard library
with the same `--issue` option. Run from this branch so the input stays the same:

```sh
python3 tools/issue-repros/run.py \
  --rustpython /path/to/historical/target/release/rustpython \
  --stdlib /path/to/historical/Lib \
  --issue 4762
```

For the recorded comparisons, follow the complete checkout/build/run procedure
in the individual case document. It creates separate source and target directories
for the two exact commits, pins the recorded Rust toolchains, verifies each
binary's embedded commit, then executes the same input with that version's `Lib`.
All selected revisions have a top-level `Lib` directory. #2527 uses the recorded
Linux ARM64 Docker images and starts each REPL separately in a real terminal.
The other runtime reports describe the recorded macOS ARM64 builds.

The local runner above consumes already-built interpreters. Changing a working
directory or `RUSTPYTHONPATH` does not select a different interpreter version;
select the separately built executable as well as its matching standard library.
Keep the source checkout used to build it: historical binaries may retain that
checkout's standard-library path, which `RUSTPYTHONPATH` does not necessarily replace.

The runner always checks the **current expected behavior**. An old build that
reproduces the original failure should therefore report `FAIL`; inspect its
captured output against the historical observation. The actual interpreter
version and binary hash are saved with each fresh result. A new run never changes
the recorded historical evidence.

## Recorded evidence and documents

The selected logs were imported from the completed October 4 verification.
`original-*.txt` preserves the extracted issue inputs, and `recorded-input.txt`
preserves the exact previously executed script where one exists. The runnable
`repro.py` may differ in formatting; transcript extraction and instrumentation
are explained in each case document.

Exported logs replace machine-specific user and checkout paths with placeholders.
Their metadata retains both original and exported SHA-256 hashes. Build-command
paths in that metadata describe the original environment; use the portable
commands above for a new run. Only the selected successful comparisons are
included here; the full survey remains in the original local workspace.

Regenerate the committed individual documents and combined bullet draft from
the imported manifest, without executing interpreters:

```sh
python3 tools/issue-repros/run.py --render-recorded
```

The linked PRs contain source changes matching the observed behavior. These
comparisons establish the reported old/current behavior, not the first fixing
commit. Approximate historical baselines are labeled in the case documents.

The layout was informed by the executable examples and case catalog linked in
[RustPython #8325](https://github.com/RustPython/RustPython/issues/8325#issuecomment-5017169153).

AI assistance: OpenAI Codex assisted with verification, evidence selection,
executable packaging and drafting.
