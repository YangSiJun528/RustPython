# #4950 — Bool numeric format codes

Original issue: [#4950](https://github.com/RustPython/RustPython/issues/4950)

**Verified closure candidate:** False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probes.py](../../evidence/additional11/agent-a/probes.py.txt). The export preserves the executed code except for documented local-path substitutions.

```python
"""Fresh independent issue inputs. Same file is executed by both runtimes."""

import sys, json


def issue4769():
    import pickle, copy
    from collections import deque

    global Deque, DequeWithSlots

    class Deque(deque):
        pass

    class DequeWithSlots(deque):
        __slots__ = ("slot", "__dict__")

    # Names must be globally resolvable for pickle.
    Deque.__qualname__ = "Deque"
    DequeWithSlots.__qualname__ = "DequeWithSlots"
    literal = pickle.loads(pickle.dumps(pickle.HIGHEST_PROTOCOL))
    try:
        literal.__dict__
    except AttributeError:
        print("literal original: integer has no __dict__")
    total = 0
    for cls in (Deque, DequeWithSlots):
        for values, maxlen in (
            ([], None),
            (["a", "b", "c"], None),
            (["a", "b", "c"], 2),
        ):
            d = cls(values, maxlen=maxlen)
            d.x = "value"
            d.extra = ["list state"]
            if cls is DequeWithSlots:
                d.slot = ["slot state"]
            for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
                e = pickle.loads(pickle.dumps(d, protocol))
                assert type(e) is cls and e is not d
                assert list(e) == list(d) and e.maxlen == d.maxlen
                assert e.__dict__ == d.__dict__
```

Only the beginning is displayed above; use the linked full input and the case selector in the recorded command.

## Expected and observed results

**Expected:** Explicit numeric format codes must format bool through its numeric value.

**Observed:** False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>{&quot;locale&quot;: &quot;C&quot;, &quot;results&quot;: [[false, &quot;f&quot;, &quot;0.000000&quot;], [false, &quot;x&quot;, &quot;0&quot;], [false, &quot;X&quot;, &quot;0&quot;], [false, &quot;e&quot;, &quot;0.000000e+00&quot;], [false, &quot;E&quot;, &quot;0.000000E+00&quot;], [false, &quot;c&quot;, &quot;\u0000&quot;], [false, &quot;g&quot;, &quot;0&quot;], [false, &quot;o&quot;, &quot;0&quot;], [false, &quot;%&quot;, &quot;0.000000%&quot;], [false, &quot;o&quot;, &quot;0&quot;], [false, &quot;n&quot;, &quot;0&quot;], [false, &quot;d&quot;, &quot;0&quot;], [false, &quot;08x&quot;, &quot;00000000&quot;], [false, &quot;+08d&quot;, &quot;+0000000&quot;], [false, &quot;.2f&quot;, &quot;0.00&quot;], [false, &quot;.1%&quot;, &quot;0.0%&quot;], [false, &quot;&gt;5n&quot;, &quot;    0&quot;], [true, &quot;f&quot;, &quot;1.000000&quot;], [true, &quot;x&quot;, &quot;1&quot;], [true, &quot;X&quot;, &quot;1&quot;], [true, &quot;e&quot;, &quot;1.000000e+00&quot;], [true, &quot;E&quot;, &quot;1.000000E+00&quot;], [true, &quot;c&quot;, &quot;\u0001&quot;], [true, &quot;g&quot;, &quot;1&quot;], [true, &quot;o&quot;, &quot;1&quot;], [true, &quot;%&quot;, &quot;100.000000%&quot;], [true, &quot;o&quot;, &quot;1&quot;], [true, &quot;n&quot;, &quot;1&quot;], [true, &quot;d&quot;, &quot;1&quot;], [true, &quot;08x&quot;, &quot;00000001&quot;], [true, &quot;+08d&quot;, &quot;+0000001&quot;], [true, &quot;.2f&quot;, &quot;1.00&quot;], [true, &quot;.1%&quot;, &quot;100.0%&quot;], [true, &quot;&gt;5n&quot;, &quot;    1&quot;]]}</code></pre></td><td valign="top"><em>No output</em></td><td valign="top"><pre><code>{&quot;locale&quot;: &quot;C&quot;, &quot;results&quot;: [[false, &quot;f&quot;, &quot;0.000000&quot;], [false, &quot;x&quot;, &quot;0&quot;], [false, &quot;X&quot;, &quot;0&quot;], [false, &quot;e&quot;, &quot;0.000000e+00&quot;], [false, &quot;E&quot;, &quot;0.000000E+00&quot;], [false, &quot;c&quot;, &quot;\u0000&quot;], [false, &quot;g&quot;, &quot;0&quot;], [false, &quot;o&quot;, &quot;0&quot;], [false, &quot;%&quot;, &quot;0.000000%&quot;], [false, &quot;o&quot;, &quot;0&quot;], [false, &quot;n&quot;, &quot;0&quot;], [false, &quot;d&quot;, &quot;0&quot;], [false, &quot;08x&quot;, &quot;00000000&quot;], [false, &quot;+08d&quot;, &quot;+0000000&quot;], [false, &quot;.2f&quot;, &quot;0.00&quot;], [false, &quot;.1%&quot;, &quot;0.0%&quot;], [false, &quot;&gt;5n&quot;, &quot;    0&quot;], [true, &quot;f&quot;, &quot;1.000000&quot;], [true, &quot;x&quot;, &quot;1&quot;], [true, &quot;X&quot;, &quot;1&quot;], [true, &quot;e&quot;, &quot;1.000000e+00&quot;], [true, &quot;E&quot;, &quot;1.000000E+00&quot;], [true, &quot;c&quot;, &quot;\u0001&quot;], [true, &quot;g&quot;, &quot;1&quot;], [true, &quot;o&quot;, &quot;1&quot;], [true, &quot;%&quot;, &quot;100.000000%&quot;], [true, &quot;o&quot;, &quot;1&quot;], [true, &quot;n&quot;, &quot;1&quot;], [true, &quot;d&quot;, &quot;1&quot;], [true, &quot;08x&quot;, &quot;00000001&quot;], [true, &quot;+08d&quot;, &quot;+0000001&quot;], [true, &quot;.2f&quot;, &quot;1.00&quot;], [true, &quot;.1%&quot;, &quot;100.0%&quot;], [true, &quot;&gt;5n&quot;, &quot;    1&quot;]]}</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
Traceback (most recent call last):
  File &quot;&lt;survey&gt;/repros/4950/issue-4950-case-01/source-01.py&quot;, line 1, in &lt;module&gt;
    &#x27;{:f}&#x27;.format(False)
ValueError: Invalid format specifier</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <additional11-audit>/agent-a/probes.py 4950
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <additional11-audit>/agent-a/probes.py 4950
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.

[PR #5012](https://github.com/RustPython/RustPython/pull/5012): update the parser/format dependency · [Parser PR #91](https://github.com/RustPython/Parser/pull/91).

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Locale was C for this issue. The broader locale defects in #4613 and #5181 are separate.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`fa790558211e`](https://github.com/RustPython/RustPython/commit/fa790558211ec690541299258f44d7453501958a), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-fa79055821-01-75703bc4-6d760217.stdout](../../evidence/history/logs/issue-4950-case-01/historical-fa79055821-01-75703bc4-6d760217.stdout).
- [Full reused historical-fa79055821-01-75703bc4-6d760217.stderr](../../evidence/history/logs/issue-4950-case-01/historical-fa79055821-01-75703bc4-6d760217.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4950-cpython](../../evidence/additional11/agent-a/4950-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4950-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4950-cpython.stderr.txt) |
| [4950-rustpython](../../evidence/additional11/agent-a/4950-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4950-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4950-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
{"locale": "C", "results": [[false, "f", "0.000000"], [false, "x", "0"], [false, "X", "0"], [false, "e", "0.000000e+00"], [false, "E", "0.000000E+00"], [false, "c", "\u0000"], [false, "g", "0"], [false, "o", "0"], [false, "%", "0.000000%"], [false, "o", "0"], [false, "n", "0"], [false, "d", "0"], [false, "08x", "00000000"], [false, "+08d", "+0000000"], [false, ".2f", "0.00"], [false, ".1%", "0.0%"], [false, ">5n", "    0"], [true, "f", "1.000000"], [true, "x", "1"], [true, "X", "1"], [true, "e", "1.000000e+00"], [true, "E", "1.000000E+00"], [true, "c", "\u0001"], [true, "g", "1"], [true, "o", "1"], [true, "%", "100.000000%"], [true, "o", "1"], [true, "n", "1"], [true, "d", "1"], [true, "08x", "00000001"], [true, "+08d", "+0000001"], [true, ".2f", "1.00"], [true, ".1%", "100.0%"], [true, ">5n", "    1"]]}

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
