# REPL expressions inside blocks (#2527)

[Original issue](https://github.com/RustPython/RustPython/issues/2527). **Resolved in the reported scope.** The interactive REPL displays expression values inside the original `for` and `with` blocks.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython 0.6.1 / Python 3.14.0.alpha, x86_64 through Rosetta.
- Comparison: CPython 3.14.6 ARM64.

Use absolute paths: set `RP` and `CP` to those executables, `SRC` to the matching source directory, and `CASE` to an existing writable directory for the two new output files.

```sh
export RP CP SRC CASE
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP
export PYTHONDONTWRITEBYTECODE=1
export TERM=xterm LC_ALL=en_US.UTF-8 PYTHON_BASIC_REPL=1
cd "$SRC"
```

## Reproduce in an actual REPL

Start each interpreter in a terminal or PTY:

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -S -q
"$CP" -B -S -q
```

Enter the following input in each session, retaining the blank line after each block. The file path uses `CASE` in place of the recorded absolute directory; the two expression statements are unchanged.

```text
import os, sys
for i in range(10):
    i

name = "repl-created-" + sys.implementation.name + ".txt"
path = os.path.join(os.environ["CASE"], name)
with open(path, "x") as f:
    f.write("hello")

sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
```

The original file-write example used `w`. The recorded check used `x` and a distinct filename per interpreter so existing files were preserved. Use unused filenames for another run. `os._exit(0)` followed explicit flushing and prevented REPL-history writes.

## Results

Both sessions displayed these expression values, exited `0` and reached every expected prompt without a timeout:

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

The first ten lines come from the loop; the final `5` is the return value of `f.write("hello")`. Prompts, echoed input and ANSI cursor-control sequences are omitted here. The PTY captured stdout and stderr together.

### Displayhook and function-scope check

Save this additional input as `probe-2527-single.py`:

```python
import sys

seen = []
sys.displayhook = seen.append
exec(compile("for i in range(10):\n    i\n", "for", "single"))
print("for displayhook", seen)
seen.clear()
exec(
    compile(
        "if True:\n    7\n    None\n    for i in range(2):\n        i + 10\n",
        "nested",
        "single",
    )
)
print("nested displayhook", seen)
seen.clear()
exec(compile("def f():\n    9\n", "function", "single"))
print("function definition hook", seen)
f()
print("function execution hook", seen)
```

Run it with both interpreters:

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -S "$CASE/probe-2527-single.py"
"$CP" -B -S "$CASE/probe-2527-single.py"
```

Both exited `0` with empty stderr and printed:

```text
for displayhook [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
nested displayhook [7, None, 10, 11]
function definition hook []
function execution hook []
```

### Historical failure

The previously recorded Linux PTY run at [`163cd1953377`](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301) returned to the prompt after both blocks without displaying their values. It also exited `0`; missing expression output was the failure. That historical run was not repeated with the current macOS comparison.

## Related change and scope

[PR #7067](https://github.com/RustPython/RustPython/pull/7067) displays interactive expressions in nested blocks. The original REPL examples and the displayhook checks support closure. The current comparison covers macOS/Rosetta; the first fixing commit was not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [RustPython PTY record](../../evidence/initial16/agent-b/fresh-2527-pty-rp.json) and [transcript](../../evidence/initial16/agent-b/fresh-2527-pty-rp.transcript).
- [CPython PTY record](../../evidence/initial16/agent-b/fresh-2527-pty-cp.json) and [transcript](../../evidence/initial16/agent-b/fresh-2527-pty-cp.transcript).
- [RustPython displayhook record](../../evidence/initial16/agent-b/fresh-2527-single-rp.json) and [CPython displayhook record](../../evidence/initial16/agent-b/fresh-2527-single-cp.json).
- [Historical metadata](../../../cases/2527/evidence/metadata.json) and [transcript](../../../cases/2527/evidence/historical.stdout.txt).
- [Scope and execution inventory](assessment.json).

AI assistance: OpenAI Codex.
