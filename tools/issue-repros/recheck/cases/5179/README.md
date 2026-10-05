# #5179 — Builtin buffer methods

Original issue: [#5179](https://github.com/RustPython/RustPython/issues/5179)

**Verified closure candidate:** Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.

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

**Expected:** Builtin buffer providers must expose the Python-facing PEP 688 methods where appropriate.

**Observed:** Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>{&quot;builtins&quot;: [{&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: true, &quot;release&quot;: false, &quot;type&quot;: &quot;bytes&quot;, &quot;writable&quot;: &quot;BufferError&quot;}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;bytearray&quot;, &quot;writable&quot;: true}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;array&quot;, &quot;writable&quot;: true}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: true, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;memoryview&quot;, &quot;writable&quot;: &quot;BufferError&quot;}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: true, &quot;release&quot;: false, &quot;type&quot;: &quot;BytesSubclass&quot;, &quot;writable&quot;: &quot;BufferError&quot;}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;BytearraySubclass&quot;, &quot;writable&quot;: true}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;mmap&quot;, &quot;writable&quot;: true}], &quot;custom_exporter&quot;: [[&quot;get&quot;, 284], [&quot;release&quot;]], &quot;resize_after_release&quot;: true}</code></pre></td><td valign="top"><pre><code>bytes __buffer__ False __release_buffer__ False
bytearray __buffer__ False __release_buffer__ False
array __buffer__ False __release_buffer__ False
memoryview __buffer__ False __release_buffer__ False</code></pre></td><td valign="top"><pre><code>{&quot;builtins&quot;: [{&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: true, &quot;release&quot;: false, &quot;type&quot;: &quot;bytes&quot;, &quot;writable&quot;: &quot;BufferError&quot;}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;bytearray&quot;, &quot;writable&quot;: true}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;array&quot;, &quot;writable&quot;: true}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: true, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;memoryview&quot;, &quot;writable&quot;: &quot;BufferError&quot;}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: true, &quot;release&quot;: false, &quot;type&quot;: &quot;BytesSubclass&quot;, &quot;writable&quot;: &quot;BufferError&quot;}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;BytearraySubclass&quot;, &quot;writable&quot;: true}, {&quot;buffer&quot;: true, &quot;data&quot;: &quot;abc&quot;, &quot;readonly&quot;: false, &quot;release&quot;: true, &quot;released&quot;: true, &quot;type&quot;: &quot;mmap&quot;, &quot;writable&quot;: true}], &quot;custom_exporter&quot;: [[&quot;get&quot;, 284], [&quot;release&quot;]], &quot;resize_after_release&quot;: true}</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <additional11-audit>/agent-a/probes.py 5179
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <additional11-audit>/agent-a/probes.py 5179
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.

[PR #8523](https://github.com/RustPython/RustPython/pull/8523): PEP 688 methods and managed buffer exports.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** __release_buffer__ is optional for types that do not need it. Full C ABI coverage and all lifetime/concurrency combinations were not tested.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`a8ab7dd38814`](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-a8ab7dd388-01-d89ea130-92a69513.stdout](../../evidence/history/logs/issue-5179-case-01/historical-a8ab7dd388-01-d89ea130-92a69513.stdout).
- [Full reused historical-a8ab7dd388-01-d89ea130-92a69513.stderr](../../evidence/history/logs/issue-5179-case-01/historical-a8ab7dd388-01-d89ea130-92a69513.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [5179-cpython](../../evidence/additional11/agent-a/5179-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/5179-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/5179-cpython.stderr.txt) |
| [5179-rustpython](../../evidence/additional11/agent-a/5179-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/5179-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/5179-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
{"builtins": [{"buffer": true, "data": "abc", "readonly": true, "release": false, "type": "bytes", "writable": "BufferError"}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "bytearray", "writable": true}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "array", "writable": true}, {"buffer": true, "data": "abc", "readonly": true, "release": true, "released": true, "type": "memoryview", "writable": "BufferError"}, {"buffer": true, "data": "abc", "readonly": true, "release": false, "type": "BytesSubclass", "writable": "BufferError"}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "BytearraySubclass", "writable": true}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "mmap", "writable": true}], "custom_exporter": [["get", 284], ["release"]], "resize_after_release": true}

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
