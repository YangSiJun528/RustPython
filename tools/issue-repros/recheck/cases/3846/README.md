# #3846 — Disassembly support used by modulefinder

Original issue: [#3846](https://github.com/RustPython/RustPython/issues/3846)

**Verified closure candidate:** The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.

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

**Expected:** The requested dis exports and instruction iteration must support the reported modulefinder path.

**Observed:** The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>opmap, EXTENDED_ARG, _unpack_opargs: usable
module graph: [&#x27;__main__&#x27;, &#x27;first&#x27;, &#x27;nested_dependency&#x27;, &#x27;package&#x27;, &#x27;package.second&#x27;]
missing: ([], [])</code></pre></td><td valign="top"><em>No output</em></td><td valign="top"><pre><code>opmap, EXTENDED_ARG, _unpack_opargs: usable
module graph: [&#x27;__main__&#x27;, &#x27;first&#x27;, &#x27;nested_dependency&#x27;, &#x27;package&#x27;, &#x27;package.second&#x27;]
missing: ([], [])</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
Traceback (most recent call last):
  File &quot;&lt;survey&gt;/verification-tools/derived-a/issue-3846-case-01.py&quot;, line 2, in &lt;module&gt;
    print(repr(dis.opmap[&#x27;LOAD_CONST&#x27;]))
AttributeError: module &#x27;dis&#x27; has no attribute &#x27;opmap&#x27;</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <additional11-audit>/agent-a/probes.py 3846
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <additional11-audit>/agent-a/probes.py 3846
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.

[PR #5377](https://github.com/RustPython/RustPython/pull/5377): provide dis exports and bytecode/import scanning.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Opcode numeric equality is not required. Creating a generator from integer 100 is not evidence of bytecode iteration; valid code bytes were iterated instead.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`5631d2102bfe`](https://github.com/RustPython/RustPython/commit/5631d2102bfeb8e0ace727ba539258beb6cdbb7e), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-5631d2102b-01-7f102daa-1ca15133.stdout](../../evidence/history/logs/issue-3846-case-01/historical-5631d2102b-01-7f102daa-1ca15133.stdout).
- [Full reused historical-5631d2102b-01-7f102daa-1ca15133.stderr](../../evidence/history/logs/issue-3846-case-01/historical-5631d2102b-01-7f102daa-1ca15133.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [3846-cpython](../../evidence/additional11/agent-a/3846-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/3846-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/3846-cpython.stderr.txt) |
| [3846-rustpython](../../evidence/additional11/agent-a/3846-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/3846-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/3846-rustpython.stderr.txt) |
| [3846-unittest-rustpython](../../evidence/additional11/agent-a/3846-unittest-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/3846-unittest-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/3846-unittest-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
opmap, EXTENDED_ARG, _unpack_opargs: usable
module graph: ['__main__', 'first', 'nested_dependency', 'package', 'package.second']
missing: ([], [])

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
