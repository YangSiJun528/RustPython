# #5699 — Blockers for colored tracebacks

Original issue: [#5699](https://github.com/RustPython/RustPython/issues/5699)

**Verified closure candidate:** All four listed blockers execute successfully. Colored traceback APIs and four actual uncaught exception paths match CPython, including builtin and missing-stdlib suggestions.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-traceback-blockers.py](../../evidence/additional11/agent-b/probe-traceback-blockers.py.txt). The export preserves the executed code except for documented local-path substitutions.

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

## Expected and observed results

**Expected:** Class-pattern code generation, frame.f_builtins, sys.stdlib_module_names and except* code generation must support traceback rendering.

**Observed:** All four listed blockers execute successfully. Colored traceback APIs and four actual uncaught exception paths match CPython, including builtin and missing-stdlib suggestions.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>{
  &quot;class_match&quot;: 4,
  &quot;builtins&quot;: true,
  &quot;stdlib_module_names&quot;: true,
...
    &quot;plain&quot;: &quot;Traceback (most recent call last):\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 58, in &lt;module&gt;\n    function()\n    ~~~~~~~~^^\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 43, in builtins_typo\n    return ZeroDivisionErrrrr\n           ^^^^^^^^^^^^^^^^^^\nNameError: name &#x27;ZeroDivisionErrrrr&#x27; is not defined. Did you mean: &#x27;ZeroDivisionError&#x27;?\n&quot;,
    &quot;colored&quot;: &quot;Traceback (most recent call last):\n  File \u001b[35m\&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m&lt;module&gt;\u001b[0m\n    \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n    \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  File \u001b[35m\&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;\u001b[0m, line \u001b[35m43\u001b[0m, in \u001b[35mbuiltins_typo\u001b[0m\n    return \u001b[1;31mZeroDivisionErrrrr\u001b[0m\n           \u001b[1;31m^^^^^^^^^^^^^^^^^^\u001b[0m\n\u001b[1;35mNameError\u001b[0m: \u001b[35mname &#x27;ZeroDivisionErrrrr&#x27; is not defined. Did you mean: &#x27;ZeroDivisionError&#x27;?\u001b[0m\n&quot;
  },
  &quot;stdlib_missing&quot;: {
    &quot;plain&quot;: &quot;Traceback (most recent call last):\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 58, in &lt;module&gt;\n    function()\n    ~~~~~~~~^^\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 46, in stdlib_missing\n    return io.StringIO()\n           ^^\nNameError: name &#x27;io&#x27; is not defined. Did you mean: &#x27;id&#x27;? Or di</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><em>No output</em></td><td valign="top"><pre><code>{
  &quot;class_match&quot;: 4,
  &quot;builtins&quot;: true,
  &quot;stdlib_module_names&quot;: true,
...
    &quot;plain&quot;: &quot;Traceback (most recent call last):\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 58, in &lt;module&gt;\n    function()\n    ~~~~~~~~^^\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 43, in builtins_typo\n    return ZeroDivisionErrrrr\n           ^^^^^^^^^^^^^^^^^^\nNameError: name &#x27;ZeroDivisionErrrrr&#x27; is not defined. Did you mean: &#x27;ZeroDivisionError&#x27;?\n&quot;,
    &quot;colored&quot;: &quot;Traceback (most recent call last):\n  File \u001b[35m\&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m&lt;module&gt;\u001b[0m\n    \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n    \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  File \u001b[35m\&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;\u001b[0m, line \u001b[35m43\u001b[0m, in \u001b[35mbuiltins_typo\u001b[0m\n    return \u001b[1;31mZeroDivisionErrrrr\u001b[0m\n           \u001b[1;31m^^^^^^^^^^^^^^^^^^\u001b[0m\n\u001b[1;35mNameError\u001b[0m: \u001b[35mname &#x27;ZeroDivisionErrrrr&#x27; is not defined. Did you mean: &#x27;ZeroDivisionError&#x27;?\u001b[0m\n&quot;
  },
  &quot;stdlib_missing&quot;: {
    &quot;plain&quot;: &quot;Traceback (most recent call last):\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 58, in &lt;module&gt;\n    function()\n    ~~~~~~~~^^\n  File \&quot;&lt;additional11-audit&gt;/agent-b/probe-traceback-blockers.py\&quot;, line 46, in stdlib_missing\n    return io.StringIO()\n           ^^\nNameError: name &#x27;io&#x27; is not defined. Did you mean: &#x27;id&#x27;? Or di</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
...
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[2026-10-04T09:30:49Z WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
Traceback (most recent call last):
  File &quot;&lt;survey&gt;/verification-tools/derived-main/issue-5699-case-01.py&quot;, line 6, in &lt;module&gt;
    case C(x):
ValueError: not enough values to unpack (expected 1, got 0)</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-b/saved/current-f39-x86/rustpython -B <additional11-audit>/agent-b/probe-traceback-blockers.py
```

CPython reference command:

```sh
<home>/.local/bin/python3 -B <additional11-audit>/agent-b/probe-traceback-blockers.py
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

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

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [5699-blockers-cpython](../../evidence/additional11/agent-b/5699-blockers-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/5699-blockers-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-blockers-cpython.stderr.txt) |
| [5699-blockers-rustpython](../../evidence/additional11/agent-b/5699-blockers-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-b/5699-blockers-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-blockers-rustpython.stderr.txt) |
| [5699-uncaught-builtin-cpython](../../evidence/additional11/agent-b/5699-uncaught-builtin-cpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-builtin-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-builtin-cpython.stderr.txt) |
| [5699-uncaught-builtin-rustpython](../../evidence/additional11/agent-b/5699-uncaught-builtin-rustpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-builtin-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-builtin-rustpython.stderr.txt) |
| [5699-uncaught-group-cpython](../../evidence/additional11/agent-b/5699-uncaught-group-cpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-group-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-group-cpython.stderr.txt) |
| [5699-uncaught-group-rustpython](../../evidence/additional11/agent-b/5699-uncaught-group-rustpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-group-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-group-rustpython.stderr.txt) |
| [5699-uncaught-stdlib-cpython](../../evidence/additional11/agent-b/5699-uncaught-stdlib-cpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-stdlib-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-stdlib-cpython.stderr.txt) |
| [5699-uncaught-stdlib-rustpython](../../evidence/additional11/agent-b/5699-uncaught-stdlib-rustpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-stdlib-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-stdlib-rustpython.stderr.txt) |
| [5699-uncaught-zero-cpython](../../evidence/additional11/agent-b/5699-uncaught-zero-cpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-zero-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-zero-cpython.stderr.txt) |
| [5699-uncaught-zero-rustpython](../../evidence/additional11/agent-b/5699-uncaught-zero-rustpython.json) | 1 | false | [stdout](../../evidence/additional11/agent-b/5699-uncaught-zero-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-b/5699-uncaught-zero-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
{
  "class_match": 4,
  "builtins": true,
  "stdlib_module_names": true,
  "except_star": [
    [
      "value",
      1
    ],
    [
      "type",
      1
    ]
  ],
  "anchors": [
    0,
    2,
    0,
    3,
    "~",
    "^"
  ],
  "zero": {
    "plain": "Traceback (most recent call last):\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n    function()\n    ~~~~~~~~^^\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 40, in zero\n    return 1 / 0\n           ~~^~~\nZeroDivisionError: division by zero\n",
    "colored": "Traceback (most recent call last):\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m<module>\u001b[0m\n    \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n    \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m40\u001b[0m, in \u001b[35mzero\u001b[0m\n    return \u001b[31m1 \u001b[0m\u001b[1;31m/\u001b[0m\u001b[31m 0\u001b[0m\n           \u001b[31m~~\u001b[0m\u001b[1;31m^\u001b[0m\u001b[31m~~\u001b[0m\n\u001b[1;35mZeroDivisionError\u001b[0m: \u001b[35mdivision by zero\u001b[0m\n"
  },
  "builtins_typo": {
    "plain": "Traceback (most recent call last):\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n    function()\n    ~~~~~~~~^^\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 43, in builtins_typo\n    return ZeroDivisionErrrrr\n           ^^^^^^^^^^^^^^^^^^\nNameError: name 'ZeroDivisionErrrrr' is not defined. Did you mean: 'ZeroDivisionError'?\n",
    "colored": "Traceback (most recent call last):\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m<module>\u001b[0m\n    \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n    \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m43\u001b[0m, in \u001b[35mbuiltins_typo\u001b[0m\n    return \u001b[1;31mZeroDivisionErrrrr\u001b[0m\n           \u001b[1;31m^^^^^^^^^^^^^^^^^^\u001b[0m\n\u001b[1;35mNameError\u001b[0m: \u001b[35mname 'ZeroDivisionErrrrr' is not defined. Did you mean: 'ZeroDivisionError'?\u001b[0m\n"
  },
  "stdlib_missing": {
    "plain": "Traceback (most recent call last):\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n    function()\n    ~~~~~~~~^^\n  File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 46, in stdlib_missing\n    return io.StringIO()\n           ^^\nNameError: name 'io' is not defined. Did you mean: 'id'? Or did you forget to import 'io'?\n",
    "colored": "Traceback (most recent call last):\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m<module>\u001b[0m\n    \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n    \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m46\u001b[0m, in \u001b[35mstdlib_missing\u001b[0m\n    return \u001b[1;31mio\u001b[0m.StringIO()\n           \u001b[1;31m^^\u001b[0m\n\u001b[1;35mNameError\u001b[0m: \u001b[35mname 'io' is not defined. Did you mean: 'id'? Or did you forget to import 'io'?\u001b[0m\n"
  },
  "group": {
    "plain": "  + Exception Group Traceback (most recent call last):\n  |   File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 58, in <module>\n  |     function()\n  |     ~~~~~~~~^^\n  |   File \"<additional11-audit>/agent-b/probe-traceback-blockers.py\", line 49, in group\n  |     raise ExceptionGroup('colored group', [ValueError('v'), TypeError('t')])\n  | ExceptionGroup: colored group (2 sub-exceptions)\n  +-+---------------- 1 ----------------\n    | ValueError: v\n    +---------------- 2 ----------------\n    | TypeError: t\n    +------------------------------------\n",
    "colored": "  + Exception Group Traceback (most recent call last):\n  |   File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m58\u001b[0m, in \u001b[35m<module>\u001b[0m\n  |     \u001b[31mfunction\u001b[0m\u001b[1;31m()\u001b[0m\n  |     \u001b[31m~~~~~~~~\u001b[0m\u001b[1;31m^^\u001b[0m\n  |   File \u001b[35m\"<additional11-audit>/agent-b/probe-traceback-blockers.py\"\u001b[0m, line \u001b[35m49\u001b[0m, in \u001b[35mgroup\u001b[0m\n  |     raise ExceptionGroup('colored group', [ValueError('v'), TypeError('t')])\n  | \u001b[1;35mExceptionGroup\u001b[0m: \u001b[35mcolored group (2 sub-exceptions)\u001b[0m\n  +-+---------------- 1 ----------------\n    | \u001b[1;35mValueError\u001b[0m: \u001b[35mv\u001b[0m\n    +---------------- 2 ----------------\n    | \u001b[1;35mTypeError\u001b[0m: \u001b[35mt\u001b[0m\n    +------------------------------------\n"
  }
}

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
