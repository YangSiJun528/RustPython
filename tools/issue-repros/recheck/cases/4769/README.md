# #4769 — Deque subclass pickle state

Original issue: [#4769](https://github.com/RustPython/RustPython/issues/4769)

**Verified closure candidate:** The original regression test passes. Protocols 0–5 preserve dict/slots state, type, contents and maxlen in 36 subclass round trips.

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

**Expected:** Pickling a deque subclass must preserve its instance state.

**Observed:** The original regression test passes. Protocols 0–5 preserve dict/slots state, type, contents and maxlen in 36 subclass round trips.

Historical and current columns may use different expanded probes. This table compares the reported symptom, not a claim of identical before/after inputs. CPython and the corresponding current probe use the recorded input identified in their metadata.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before (reused)</th><th>Current verification</th></tr></thead>
<tbody>
<tr><th>stdout</th><td valign="top"><pre><code>literal original: integer has no __dict__
pickle protocols: [0, 1, 2, 3, 4, 5]
subclass roundtrips: 36</code></pre></td><td valign="top"><pre><code>CATALOG_RECORD {&quot;kind&quot;: &quot;start&quot;, &quot;case_id&quot;: &quot;issue-4769-case-02&quot;, &quot;selector&quot;: &quot;test.test_deque.TestSubclass.test_copy_pickle&quot;, &quot;interpreter&quot;: &quot;3.11.0alpha (tags/v0.2.0-604-g25ca331dc:25ca331dc, Mar 25 2023, 21:53:53) \n[rustc 1.67.1]&quot;, &quot;executable&quot;: &quot;&lt;survey&gt;/.build/slot-a/release/rustpython&quot;, &quot;cwd&quot;: &quot;&lt;survey&gt;/logs/scratch-history-a/25ca331dc8&quot;, &quot;selector_derivation&quot;: null, &quot;original_selector&quot;: null, &quot;derivation&quot;: &quot;TODO RustPython skip decorators bypassed in memory; targeted expectedFailure flags cleared&quot;}
CATALOG_RECORD {&quot;kind&quot;: &quot;selection&quot;, &quot;case_id&quot;: &quot;issue-4769-case-02&quot;, &quot;selected_ids&quot;: [&quot;test.test_deque.TestSubclass.test_copy_pickle&quot;], &quot;loader_errors&quot;: [], &quot;module_origin&quot;: &quot;&lt;workspace&gt;/pylib/Lib/test/test_deque.py&quot;, &quot;module_sha256&quot;: &quot;80bf52da28d59465f6fda4002092772c99afce0a30c0594ba6b5234bfdb4962c&quot;, &quot;bypassed_decorators&quot;: [{&quot;kind&quot;: &quot;expectedFailure&quot;, &quot;object&quot;: &quot;test.test_deque.TestSubclass.test_copy_pickle&quot;, &quot;action&quot;: &quot;clear selected object metadata; preserve body&quot;}], &quot;note&quot;: &quot;Import-time bypass records include unselected tests; only selected_ids are executed&quot;}
CATALOG_RECORD {&quot;kind&quot;: &quot;test&quot;, &quot;test_id&quot;: &quot;test.test_deque.TestSubclass.test_copy_pickle&quot;, &quot;outcome&quot;: &quot;error&quot;, &quot;exception&quot;: &quot;AttributeError&quot;, &quot;message&quot;: &quot;&#x27;Deque&#x27; object has no attribute &#x27;x&#x27;&quot;}
CATALOG_RECORD {&quot;kind&quot;: &quot;complete&quot;, &quot;case_id&quot;: &quot;issue-4769-case-02&quot;, &quot;status&quot;: &quot;completed&quot;, &quot;tests_run&quot;: 1, &quot;selected_count&quot;: 1, &quot;failures&quot;: 0, &quot;errors&quot;: 1, &quot;skipped&quot;: [], &quot;expected_failures&quot;: 0, &quot;unexpected_successes&quot;: 0, &quot;passing&quot;: false}</code></pre></td><td valign="top"><pre><code>literal original: integer has no __dict__
pickle protocols: [0, 1, 2, 3, 4, 5]
subclass roundtrips: 36</code></pre></td></tr>
<tr><th>stderr</th><td valign="top"><em>No output</em></td><td valign="top"><pre><code>[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
[WARN  rustpython_vm::object::core] couldn&#x27;t run __del__ method for object
...
======================================================================
ERROR: test_copy_pickle (test.test_deque.TestSubclass.test_copy_pickle)
----------------------------------------------------------------------
Traceback (most recent call last):
  File &quot;&lt;workspace&gt;/pylib/Lib/test/test_deque.py&quot;, line 839, in test_copy_pickle
    self.assertEqual(e.x, d.x)
AttributeError: &#x27;Deque&#x27; object has no attribute &#x27;x&#x27;

----------------------------------------------------------------------
Ran 1 test in 0.007s

FAILED (errors=1)</code></pre><p><em>Excerpt; complete output is in the linked execution record.</em></p></td><td valign="top"><em>No output</em></td></tr>
<tr><th>exit</th><td valign="top"><pre><code>0</code></pre></td><td valign="top"><pre><code>1</code></pre></td><td valign="top"><pre><code>0</code></pre></td></tr>
</tbody>
</table>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
<survey>/.build/slot-a/verification/rustpython -B <additional11-audit>/agent-a/probes.py 4769
```

CPython reference command:

```sh
<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14 -B <additional11-audit>/agent-a/probes.py 4769
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below. For PTY checks, replay the interactive input through a PTY; a plain script invocation is not equivalent.

## Analysis and closure rationale

The original regression test passes. Protocols 0–5 preserve dict/slots state, type, contents and maxlen in 36 subclass round trips.

[PR #7699](https://github.com/RustPython/RustPython/pull/7699): include __getstate__ in deque reduction.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The issue snippet accidentally pickles pickle.HIGHEST_PROTOCOL itself. That literal and the corrected intended input are separate. Recursive deque pickle is outside this reported nonrecursive case.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`25ca331dc81e`](https://github.com/RustPython/RustPython/commit/25ca331dc81e617498465ecdb2f848ec81025f71), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-catalog-25ca331dc8-scratch.stdout](../../evidence/history/logs/issue-4769-case-02/historical-catalog-25ca331dc8-scratch.stdout).
- [Full reused historical-catalog-25ca331dc8-scratch.stderr](../../evidence/history/logs/issue-4769-case-02/historical-catalog-25ca331dc8-scratch.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

| Execution record (argv, environment, input) | Exit | Timeout | stdout | stderr |
|---|---|---|---|---|
| [4769-cpython](../../evidence/additional11/agent-a/4769-cpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4769-cpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4769-cpython.stderr.txt) |
| [4769-rustpython](../../evidence/additional11/agent-a/4769-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4769-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4769-rustpython.stderr.txt) |
| [4769-unittest-rustpython](../../evidence/additional11/agent-a/4769-unittest-rustpython.json) | 0 | false | [stdout](../../evidence/additional11/agent-a/4769-unittest-rustpython.stdout.txt) | [stderr](../../evidence/additional11/agent-a/4769-unittest-rustpython.stderr.txt) |

<details>
<summary>Full primary current stdout/stderr</summary>

**stdout:**

```text
literal original: integer has no __dict__
pickle protocols: [0, 1, 2, 3, 4, 5]
subclass roundtrips: 36

```

**stderr:**

```text

```

</details>

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
