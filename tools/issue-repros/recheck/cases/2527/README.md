# REPL expressions inside blocks (#2527)

## Summary

The behavior reported in [#2527](https://github.com/RustPython/RustPython/issues/2527) is resolved in the tested interactive REPL. Both original compound-statement examples display their expression values, matching CPython.

Verified at [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c) on October 5, 2026.

## Reproducer

Send the following lines to an actual PTY REPL, including the blank line after each block. The same input was sent to RustPython and CPython. This is interactive input, not a script invocation.

```text
import sys
for i in range(10):
    i

with open('<initial16-audit>/agent-b/repl-created-' + sys.implementation.name + '.txt', 'x') as f:
    f.write('hello')

import os; sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
```

The file path is a placeholder for the recorded scratch directory. The original file-write example used mode `w`; this run used `x` and an implementation-specific filename to preserve existing files. `os._exit(0)` avoided writing REPL history. Both changes are recorded in the [execution metadata](../../evidence/initial16/agent-b/fresh-2527-pty-rp.json).

## Expected and observed results

### RustPython and CPython

The loop should display `0` through `9`, and `f.write('hello')` should display `5`. Both PTY sessions produced those values:

```text
0
1
2
3
4
5
6
7
8
9
5
```

This excerpt contains the expression results only. Prompts, echoed input and ANSI terminal-control sequences are omitted for readability; the complete transcripts are linked below.

Both processes exited with code `0`, with no prompt timeouts. PTY stdout and stderr were captured together, so there is no separate stderr result.

- **RustPython:** [command, input and environment](../../evidence/initial16/agent-b/fresh-2527-pty-rp.json) · [complete PTY transcript](../../evidence/initial16/agent-b/fresh-2527-pty-rp.transcript).
- **CPython 3.14.6:** [command, input and environment](../../evidence/initial16/agent-b/fresh-2527-pty-cp.json) · [complete PTY transcript](../../evidence/initial16/agent-b/fresh-2527-pty-cp.transcript).

### Additional displayhook checks

Separate single-mode checks cover the issue comment's displayhook behavior and function scope. Both interpreters produced:

```text
for displayhook [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
nested displayhook [7, None, 10, 11]
function definition hook []
function execution hook []
```

Both checks exited with code `0`, without a timeout or stderr output. These supplement the actual PTY sessions above.

- **RustPython:** [execution record](../../evidence/initial16/agent-b/fresh-2527-single-rp.json) · [stdout](../../evidence/initial16/agent-b/fresh-2527-single-rp.stdout) · [stderr](../../evidence/initial16/agent-b/fresh-2527-single-rp.stderr).
- **CPython:** [execution record](../../evidence/initial16/agent-b/fresh-2527-single-cp.json) · [stdout](../../evidence/initial16/agent-b/fresh-2527-single-cp.stdout) · [stderr](../../evidence/initial16/agent-b/fresh-2527-single-cp.stderr).

### Historical failure

The reused Linux PTY record at [`163cd1953377`](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301) shows both blocks returning to the prompt without displaying their expression values. That process also exited with code `0`; the missing output is the reported failure.

This historical run was not repeated in the independent verification. Its input, platform and file-handling details differ from the new run and are preserved in the [historical metadata](../../../cases/2527/evidence/metadata.json) and [complete transcript](../../../cases/2527/evidence/historical.stdout.txt).

## Commands and environment

These are the recorded PTY launch commands, with local paths represented by placeholders. Substitute the paths described in [environment and path mapping](../../ENVIRONMENT.md), then send the interactive input above.

**RustPython:**

```sh
cd "<slot-b-source>"
env PYTHONDONTWRITEBYTECODE=1 TERM=xterm LC_ALL=en_US.UTF-8 \
    PYTHON_BASIC_REPL=1 RUSTPYTHONPATH="<slot-b-source>/Lib" \
    "<survey>/.build/slot-b/saved/current-f39-x86/rustpython" -B -S -q
```

**CPython:**

```sh
cd "<slot-b-source>"
env PYTHONDONTWRITEBYTECODE=1 TERM=xterm LC_ALL=en_US.UTF-8 \
    PYTHON_BASIC_REPL=1 \
    "<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14" -B -S -q
```

- Host: macOS 26.5.2 ARM64.
- RustPython: x86_64 executable through Rosetta, with the matching baseline standard library.
- CPython: 3.14.6 ARM64.
- Executable SHA-256 values are in each linked execution record; source and standard-library identity are documented in [ENVIRONMENT.md](../../ENVIRONMENT.md).

## Related change and closure rationale

[PR #7067](https://github.com/RustPython/RustPython/pull/7067) adds display of interactive expressions in nested blocks. That change explains the behavior observed in the two original REPL examples and the displayhook checks.

These results support closing #2527 for its reported scope. The new executions cover macOS/Rosetta; Linux evidence is reused, and no new Windows run was performed. The first fixing commit was not established by adjacent-revision execution or bisect.

[Independent assessment and evidence provenance](assessment.json).

AI assistance: verification and drafting with OpenAI Codex.
