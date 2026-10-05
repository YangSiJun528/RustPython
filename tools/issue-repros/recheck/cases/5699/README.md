# Blockers for colored tracebacks (#5699)

Original issue: [#5699](https://github.com/RustPython/RustPython/issues/5699)

**Verified closure candidate:** All four listed blockers execute successfully. Colored traceback APIs and four actual uncaught exception paths match CPython, including builtin and missing-stdlib suggestions.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-traceback-blockers.py](../../evidence/additional11/agent-b/probe-traceback-blockers.py.txt). The export preserves the executed code except for documented local-path substitutions.

<details>
<summary>Reproducer code</summary>

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

</details>

## Expected and observed results

**Expected:** Class-pattern code generation, frame.f_builtins, sys.stdlib_module_names and except* code generation must support traceback rendering.

**Observed:** All four listed blockers execute successfully. Colored traceback APIs and four actual uncaught exception paths match CPython, including builtin and missing-stdlib suggestions.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
{
  "class_match": 4,
  "builtins": true,
  "stdlib_module_names": true,
...
    "plain": "Traceback (most recent call last):\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n    function()\n    ~~~~~~~~^^\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 43, in builtins_typo\n    return ZeroDivisionErrrrr\n           ^^^^^^^^^^^^^^^^^^\nNameError: name 'ZeroDivisionErrrrr' is not defined. Did you mean: 'ZeroDivisionError'?\n",
    "colored": "Traceback (most recent call last):\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m<module>\u001b[0m\n    \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n    \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m43\u001b[0m, in \u001b[35mbuiltins_typo\u001b[0m\n    return \u001b[1;31mZeroDivisionErrrrr\u001b[0m\n           \u001b[1;31m^^^^^^^^^^^^^^^^^^\u001b[0m\n\u001b[1;35mNameError\u001b[0m: \u001b[35mname 'ZeroDivisionErrrrr' is not defined. Did you mean: 'ZeroDivisionError'?\u001b[0m\n"
  },
  "stdlib_missing": {
    "plain": "Traceback (most recent call last):\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n    function()\n    ~~~~~~~~^^\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 46, in stdlib_missing\n    return io.StringIO()\n           ^^\nNameError: name 'io' is not defined. Did you mean: 'id'? Or di
```

Excerpt; complete output is in the linked execution record.

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
{
  "class_match": 4,
  "builtins": true,
  "stdlib_module_names": true,
...
    "plain": "Traceback (most recent call last):\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n    function()\n    ~~~~~~~~^^\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 43, in builtins_typo\n    return ZeroDivisionErrrrr\n           ^^^^^^^^^^^^^^^^^^\nNameError: name 'ZeroDivisionErrrrr' is not defined. Did you mean: 'ZeroDivisionError'?\n",
    "colored": "Traceback (most recent call last):\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m<module>\u001b[0m\n    \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n    \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m43\u001b[0m, in \u001b[35mbuiltins_typo\u001b[0m\n    return \u001b[1;31mZeroDivisionErrrrr\u001b[0m\n           \u001b[1;31m^^^^^^^^^^^^^^^^^^\u001b[0m\n\u001b[1;35mNameError\u001b[0m: \u001b[35mname 'ZeroDivisionErrrrr' is not defined. Did you mean: 'ZeroDivisionError'?\u001b[0m\n"
  },
  "stdlib_missing": {
    "plain": "Traceback (most recent call last):\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n    function()\n    ~~~~~~~~^^\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 46, in stdlib_missing\n    return io.StringIO()\n           ^^\nNameError: name 'io' is not defined. Did you mean: 'id'? Or di
```

Excerpt; complete output is in the linked execution record.

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
...
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn't run __del__ method for object
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-main/issue-5699-case-01.py", line 6, in <module>
    case C(x):
ValueError: not enough values to unpack (expected 1, got 0)
```

Excerpt; complete output is in the linked execution record.

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-b/saved/current-f39-x86/rustpython' -B \
  '<additional11-audit>/agent-b/probe-traceback-blockers.py'
```

CPython reference command:

```sh
'<home>/.local/bin/python3' -B '<additional11-audit>/agent-b/probe-traceback-blockers.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

All four listed blockers execute successfully. Colored traceback APIs and four actual uncaught exception paths match CPython, including builtin and missing-stdlib suggestions.

[PR #6110](https://github.com/RustPython/RustPython/pull/6110): class-pattern code generation; [PR #6568](https://github.com/RustPython/RustPython/pull/6568): provide both frame.f_builtins and sys.stdlib_module_names; [PR #6530](https://github.com/RustPython/RustPython/pull/6530): except* code generation and exception-group handling.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The eight uncaught-exception processes correctly exit 1. The check does not certify every traceback edge case or terminal.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`a7ad84827023`](https://github.com/RustPython/RustPython/commit/a7ad84827023508684fd57de1f18781082b57060), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-a7ad848270-01.stdout](../../evidence/history/logs/issue-5699-case-01/historical-a7ad848270-01.stdout).
- [Full reused historical-a7ad848270-01.stderr](../../evidence/history/logs/issue-5699-case-01/historical-a7ad848270-01.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

<details>
<summary>Execution records (10 runs)</summary>

- **[5699-blockers-cpython](../../evidence/additional11/agent-b/5699-blockers-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-blockers-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-blockers-cpython.stderr.txt).
- **[5699-blockers-rustpython](../../evidence/additional11/agent-b/5699-blockers-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-blockers-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-blockers-rustpython.stderr.txt).
- **[5699-uncaught-builtin-cpython](../../evidence/additional11/agent-b/5699-uncaught-builtin-cpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-builtin-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-builtin-cpython.stderr.txt).
- **[5699-uncaught-builtin-rustpython](../../evidence/additional11/agent-b/5699-uncaught-builtin-rustpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-builtin-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-builtin-rustpython.stderr.txt).
- **[5699-uncaught-group-cpython](../../evidence/additional11/agent-b/5699-uncaught-group-cpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-group-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-group-cpython.stderr.txt).
- **[5699-uncaught-group-rustpython](../../evidence/additional11/agent-b/5699-uncaught-group-rustpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-group-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-group-rustpython.stderr.txt).
- **[5699-uncaught-stdlib-cpython](../../evidence/additional11/agent-b/5699-uncaught-stdlib-cpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-stdlib-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-stdlib-cpython.stderr.txt).
- **[5699-uncaught-stdlib-rustpython](../../evidence/additional11/agent-b/5699-uncaught-stdlib-rustpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-stdlib-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-stdlib-rustpython.stderr.txt).
- **[5699-uncaught-zero-cpython](../../evidence/additional11/agent-b/5699-uncaught-zero-cpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-zero-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-zero-cpython.stderr.txt).
- **[5699-uncaught-zero-rustpython](../../evidence/additional11/agent-b/5699-uncaught-zero-rustpython.json)** — exit `1`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-b/5699-uncaught-zero-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-b/5699-uncaught-zero-rustpython.stderr.txt).

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
