# #4907 — Await in an async comprehension

Original issue: [#4907](https://github.com/RustPython/RustPython/issues/4907)

**Verified closure candidate:** The original async function compiles. The comment's actual asyncio event-loop and two awaited sleeps finish with lc done.

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

**Expected:** Await inside an async-function comprehension must not be rejected as outside an async function.

**Observed:** The original async function compiles. The comment's actual asyncio event-loop and two awaited sleeps finish with lc done.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>original compile: success
1
original invocation: TypeError from awaiting print result
lc done
comment execution: two awaited sleeps completed</code></pre></td><td valign="top"><em>No output</em></td><td valign="top"><pre><code>original compile: success
1
original invocation: TypeError from awaiting print result
lc done
comment execution: two awaited sleeps completed</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
SyntaxError: &#x27;await&#x27; outside async function at line 2 column 5
    [await print(i) for i in [1, 2, 3]]
    ^</code></pre></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <additional11-audit>/agent-a/probes.py 4907
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <additional11-audit>/agent-a/probes.py 4907
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The original async function compiles. The comment's actual asyncio event-loop and two awaited sleeps finish with lc done.

[PR #5334](https://github.com/RustPython/RustPython/pull/5334): compile await inside an async comprehension.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** Calling the original await print(...) function correctly raises TypeError because print returns None. Compilation and execution were assessed separately.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`c7faae9b22ce`](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-3794c178be-01-fe88d349-c1d93c6d.stdout](../../evidence/history/logs/issue-4907-case-01/historical-3794c178be-01-fe88d349-c1d93c6d.stdout).
- [Full reused historical-3794c178be-01-fe88d349-c1d93c6d.stderr](../../evidence/history/logs/issue-4907-case-01/historical-3794c178be-01-fe88d349-c1d93c6d.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4907-cpython](../../evidence/additional11/agent-a/4907-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4907-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4907-cpython.stderr.txt) |
| [4907-rustpython](../../evidence/additional11/agent-a/4907-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4907-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4907-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
original compile: success
1
original invocation: TypeError from awaiting print result
lc done
comment execution: two awaited sleeps completed

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
