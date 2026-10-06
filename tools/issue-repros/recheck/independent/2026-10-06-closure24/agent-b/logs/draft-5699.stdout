# Blockers for colored tracebacks (#5699)

[Original issue](https://github.com/RustPython/RustPython/issues/5699). **Resolved in the reported scope.** All four listed blockers execute successfully. Colored traceback APIs and four actual uncaught exception paths match CPython, including builtin and missing-stdlib suggestions.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython: 0.6.1, Python 3.14.0.alpha; x86_64 through Rosetta.
- Comparison: CPython 3.14.6 ARM64.

Use absolute paths for the variables below:

- `RP`: the RustPython executable for this commit.
- `CP`: the CPython 3.14.6 executable.
- `SRC`: the source directory at this commit, including its matching `Lib`.
- `CASE`: the directory containing the files shown below.

Shell variables replace recorded absolute paths. Export them so the Python inputs can use them:

```sh
export RP CP SRC CASE
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP
export PYTHONDONTWRITEBYTECODE=1
```

```sh
export LANG=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8
```

`LC_ALL` was unset in these recorded runs.

```sh
unset LC_ALL
```

## Reproducer

Save as `probe-traceback-blockers.py`.

```python
import sys
import json
import builtins
import traceback
import ast


class Point:
    __match_args__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y


match Point(3, 4):
    case Point(3, y=answer):
        assert answer == 4
    case _:
        raise AssertionError("class pattern did not execute")

assert sys._getframe().f_builtins["len"] is len
custom = {"__builtins__": {"custom_marker": 42}, "frame": sys._getframe}
exec("actual = frame().f_builtins", custom)
assert custom["actual"] is custom["__builtins__"]
assert isinstance(sys.stdlib_module_names, frozenset)
assert {"sys", "io", "_io", "traceback"} <= sys.stdlib_module_names

handled = []
try:
    raise ExceptionGroup("split", [ValueError("v"), TypeError("t")])
except* ValueError as exc:
    handled.append(("value", len(exc.exceptions)))
except* TypeError as exc:
    handled.append(("type", len(exc.exceptions)))
assert handled == [("value", 1), ("type", 1)]

anchors = traceback._extract_caret_anchors_from_line_segment("x + y")
assert anchors is not None, "actual traceback class-pattern branch failed"
records = {
    "class_match": answer,
    "builtins": True,
    "stdlib_module_names": True,
    "except_star": handled,
    "anchors": list(anchors),
}


def zero():
    return 1 / 0


def builtins_typo():
    return ZeroDivisionErrrrr


def stdlib_missing():
    return io.StringIO()


def group():
    raise ExceptionGroup("colored group", [ValueError("v"), TypeError("t")])


for label, function, needle in (
    ("zero", zero, "ZeroDivisionError"),
    ("builtins_typo", builtins_typo, "Did you mean: 'ZeroDivisionError'?"),
    ("stdlib_missing", stdlib_missing, "forget to import 'io'"),
    ("group", group, "ExceptionGroup"),
):
    try:
        function()
    except Exception as exc:
        plain = "".join(traceback.format_exception(exc, colorize=False))
        colored = "".join(traceback.format_exception(exc, colorize=True))
        assert needle in plain, (label, plain)
        assert "\x1b[" in colored, (label, colored)
        assert needle in colored or label == "zero", (label, colored)
        records[label] = {"plain": plain, "colored": colored}
print(json.dumps(records, ensure_ascii=True, indent=2))
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probe-traceback-blockers.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/probe-traceback-blockers.py"
```

## Results

**Expected:** Class-pattern code generation, frame.f_builtins, sys.stdlib_module_names and except* code generation must support traceback rendering.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
class_match: 4
builtins: True
stdlib_module_names: True
except_star: [['value', 1], ['type', 1]]
anchors: [0, 2, 0, 3, '~', '^']
zero: ANSI color sequences present=True
builtins_typo: ANSI color sequences present=True
stdlib_missing: ANSI color sequences present=True
group: ANSI color sequences present=True
```

This summarizes the recorded traceback checks; the code above includes the exact assertions.

**stderr:**

No output.

### Historical failure

Previously recorded at [`a7ad84827023`](https://github.com/RustPython/RustPython/commit/a7ad84827023508684fd57de1f18781082b57060); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-main/issue-5699-case-01.py", line 6, in <module>
    case C(x):
ValueError: not enough values to unpack (expected 1, got 0)
```

## Uncaught-exception check

Save as `probe-traceback-uncaught.py`:

```python
import sys

if sys.argv[1] == "builtin":
    ZeroDivisionErrrrr
elif sys.argv[1] == "stdlib":
    io.StringIO()
elif sys.argv[1] == "zero":
    1 / 0
else:
    raise ExceptionGroup("uncaught group", [ValueError("v"), TypeError("t")])
```

```sh
for case in builtin stdlib zero group; do
  RUSTPYTHONPATH="$SRC/Lib" PYTHON_COLORS=1 FORCE_COLOR=1 \
    "$RP" -B "$CASE/probe-traceback-uncaught.py" "$case"
  PYTHON_COLORS=1 FORCE_COLOR=1 \
    "$CP" -B "$CASE/probe-traceback-uncaught.py" "$case"
done
```

Each of the eight recorded processes exited 1, as expected for uncaught exceptions. All emitted ANSI-colored tracebacks. The builtin typo suggested `ZeroDivisionError`, the missing module suggested importing `io`, division by zero reported `ZeroDivisionError`, and the group displayed both child exceptions.

Historical output excerpt; runner metadata and repeated shutdown warnings are omitted.

## Related change and scope

[PR #6110](https://github.com/RustPython/RustPython/pull/6110): class-pattern code generation; [PR #6568](https://github.com/RustPython/RustPython/pull/6568): provide both frame.f_builtins and sys.stdlib_module_names; [PR #6530](https://github.com/RustPython/RustPython/pull/6530): except* code generation and exception-group handling.

The eight uncaught-exception processes correctly exit 1. The check does not certify every traceback edge case or terminal.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-b/5699-blockers-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-b/5699-blockers-rustpython.json).
- [Executed source](../../evidence/additional11/agent-b/probe-traceback-blockers.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
