# #8494 — Classmethod and staticmethod annotations

Original issue: [#8494](https://github.com/RustPython/RustPython/issues/8494)

**Verified closure candidate:** Both wrappers support the two annotation attributes, cache values in the wrapper, and isolate writes/deletes from the wrapped function. The original unresolved-name input and regression test pass.

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

**Expected:** PEP 749 annotation attributes on classmethod/staticmethod must be writable, cached and independent of the original callable.

**Observed:** Both wrappers support the two annotation attributes, cache values in the wrapper, and isolate writes/deletes from the wrapped function. The original unresolved-name input and regression test pass.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>classmethod {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
True
wrapper: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
wrapped: {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
staticmethod {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
True
wrapper: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
wrapped: {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
classmethod annotated both attributes cache/write/delete isolation passed
classmethod unannotated both attributes cache/write/delete isolation passed
staticmethod annotated both attributes cache/write/delete isolation passed
staticmethod unannotated both attributes cache/write/delete isolation passed</code></pre></td><td valign="top"><pre><code>classmethod {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
False
wrapper: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
wrapped: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
staticmethod {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
False
wrapper: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
wrapped: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}</code></pre></td><td valign="top"><pre><code>classmethod {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
True
wrapper: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
wrapped: {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
staticmethod {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
True
wrapper: {&#x27;x&#x27;: &lt;class &#x27;str&#x27;&gt;}
wrapped: {&#x27;return&#x27;: &lt;class &#x27;int&#x27;&gt;}
classmethod annotated both attributes cache/write/delete isolation passed
classmethod unannotated both attributes cache/write/delete isolation passed
staticmethod annotated both attributes cache/write/delete isolation passed
staticmethod unannotated both attributes cache/write/delete isolation passed</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <additional11-audit>/agent-a/probes.py 8494
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <additional11-audit>/agent-a/probes.py 8494
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

Both wrappers support the two annotation attributes, cache values in the wrapper, and isolate writes/deletes from the wrapped function. The original unresolved-name input and regression test pass.

[PR #8701](https://github.com/RustPython/RustPython/pull/8701): cache and assign annotation attributes on the wrapper.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** CPython 3.14.6 is the reference; this is not compared to older eager-annotation semantics.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`b304919a6301`](https://github.com/RustPython/RustPython/commit/b304919a63010f78daa65bc5db14fd487829aeb9), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-b304919a63-01.stdout](../../evidence/history/logs/issue-8494-case-01/historical-b304919a63-01.stdout).
- [Full reused historical-b304919a63-01.stderr](../../evidence/history/logs/issue-8494-case-01/historical-b304919a63-01.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [8494-cpython](../../evidence/additional11/agent-a/8494-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/8494-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/8494-cpython.stderr.txt) |
| [8494-original-cpython](../../evidence/additional11/agent-a/8494-original-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/8494-original-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/8494-original-cpython.stderr.txt) |
| [8494-original-rustpython](../../evidence/additional11/agent-a/8494-original-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/8494-original-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/8494-original-rustpython.stderr.txt) |
| [8494-rustpython](../../evidence/additional11/agent-a/8494-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/8494-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/8494-rustpython.stderr.txt) |
| [8494-unittest-rustpython](../../evidence/additional11/agent-a/8494-unittest-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/8494-unittest-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/8494-unittest-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
classmethod {'return': <class 'int'>}
True
wrapper: {'x': <class 'str'>}
wrapped: {'return': <class 'int'>}
staticmethod {'return': <class 'int'>}
True
wrapper: {'x': <class 'str'>}
wrapped: {'return': <class 'int'>}
classmethod annotated both attributes cache/write/delete isolation passed
classmethod unannotated both attributes cache/write/delete isolation passed
staticmethod annotated both attributes cache/write/delete isolation passed
staticmethod unannotated both attributes cache/write/delete isolation passed

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
