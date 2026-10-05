# RustPython resolved-issue reproducers

Run the 16 closure candidates from the October 4, 2026 verification locally.
This directory contains 14 script checks, one interactive check covering two
REPL examples, and one documentation URL check. The interpreter baseline is
[`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).

- [Combined issue submission draft](report-before-independent-review.md): a closure request with each issue's
  before/after behavior, related changes and link to its detailed report.
- [Detailed reports](../../cases/): the reproducer, expected behavior and inline
  CPython/before/after results come first, followed by direct execution commands,
  closure rationale and related PRs. Each runtime case's `BUILD.md` contains the
  exact checkouts, pinned toolchains and executable-version checks.
  Full logs remain linked and stderr is expandable in the report.
- [Case definitions and expected results](../../manifest.json)
- [Local validation record](../../VALIDATION.md)
- Individual inputs, commands and recorded evidence are under `cases/<issue>/`.

## Optional local batch runner

Use a POSIX host (Linux or macOS) with Python 3.12 or newer. From the repository root, build RustPython and launch the host-side runner:

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

## Compare both revisions at once

For one script case, complete its `BUILD.md` first in the same shell, then run
this from the report branch's repository root (example: #4762):

```sh
python3 tools/issue-repros/run.py --compare --issue 4762 \
  --reference "$(command -v python3.14)" \
  --before "$rustpython_repro_root/target-historical/release/rustpython" \
  --before-stdlib "$rustpython_repro_root/historical/Lib" \
  --after "$rustpython_repro_root/target-current/release/rustpython" \
  --after-stdlib "$rustpython_repro_root/current/Lib"
```

`--reference` is optional; it must name an installed CPython executable. The
runner executes the case's one canonical input in each interpreter and prints
stdout, stderr, exit code and the current-behavior oracle side by side. It saves
full outputs, versions, executable hashes and input hashes in a new ignored
`runs/` directory (`--output` can select another new directory).

The comparison checks each RustPython executable's embedded commit, the supplied
checkout's `Lib` tree against that commit, local changes under `Lib`, and the
actual `os`/`json` import paths. A mismatch is an `ERROR` before the reproducer
runs. The source Git objects for the recorded commit must remain available;
`BUILD.md` prepares them. These checks detect common pairing errors, but are not
an attestation of how an arbitrary supplied executable was built.

`PASS` / `FAIL` means matching / missing the **current expected behavior** in
that column. An old build normally shows `FAIL`; compare its diagnostic with
the report to establish that it is the original failure. A timeout, failed
startup or mismatched environment is `ERROR`, never evidence of the old bug.
The comparison exits nonzero for an error, a failed After oracle or a failed
CPython oracle. Before passing is displayed as such and does not by itself make
the command fail. Outputs are not required to be byte-identical: diagnostic
wording, file paths and warnings can differ between interpreters.

- **#6429:** CPython's build setting may be `0` or `1`. Its column reports
  `CONFIG`; the RustPython POSIX oracle is `1`.
- **#6790:** omit `--reference`. The case checks the removal of a forced skip in
  RustPython's own `test.support`, with lzma available, not complete XZ support.
- **#2527:** use the case's direct Docker/TTY commands for the recorded setup.
  `--compare` can also run already-built Linux executables on a Linux host with
  Python 3, Git and PTY support, using each retained checkout's `Lib`.
- **#4784:** use the direct URL check; interpreter comparisons do not apply.

Changing a working directory or `RUSTPYTHONPATH` does not select an interpreter
version. Select the separately built executable and its matching standard
library. Keep the source checkout used to build it: historical binaries may
retain that checkout's standard-library path, which `RUSTPYTHONPATH` does not
necessarily replace. Each runtime case's `BUILD.md` preserves complete setup
instructions; its README also has direct commands that do not need this runner.

For an arbitrary revision outside the pinned comparison, the single-interpreter
runner above remains available. It records the supplied version and checks the
current expectation, but does not verify the pinned commit/Lib pairing.

## Recorded evidence and documents

The selected logs were imported from the completed October 4 verification.
`original-*.txt` preserves the extracted issue inputs, and `recorded-input.txt`
preserves the exact previously executed script where one exists. The runnable
`repro.py` may differ in formatting; transcript extraction and instrumentation
are explained in each case document. The displayed code is generated from the
canonical input, including both #4690 descriptor queries. #4856 compiles its
original source without executing the application.

Exported logs replace machine-specific user and checkout paths with placeholders.
Their metadata retains both original and exported SHA-256 hashes. Build-command
paths in that metadata describe the original environment; use the portable
commands above for a new run. Existing evidence is preserved. `evidence/reference.json` records the recovered
CPython 3.14.6 version and input equivalence for 13 archived script comparisons.
#2527 adds a separately dated macOS CPython PTY reference; both archived
RustPython REPL runs used Linux. Only the selected successful comparisons are
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
