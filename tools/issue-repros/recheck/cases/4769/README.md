# Deque subclass pickle state (#4769)

Original issue: [#4769](https://github.com/RustPython/RustPython/issues/4769)

**Verified closure candidate:** The original regression test passes. Protocols 0–5 preserve dict/slots state, type, contents and maxlen in 36 subclass round trips.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Run the shared [probes.py](../../evidence/additional11/agent-a/probes.py.txt) with selector `4769`, as shown in the recorded command. The relevant function is `issue4769`; the full file supplies its imports and dispatcher. The excerpt is formatted for readability.

<details>
<summary>Reproducer function: issue4769</summary>

```python
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
                if cls is DequeWithSlots:
                    assert e.slot == d.slot
                total += 1
    print("pickle protocols:", list(range(pickle.HIGHEST_PROTOCOL + 1)))
    print("subclass roundtrips:", total)
```

</details>

## Expected and observed results

**Expected:** Pickling a deque subclass must preserve its instance state.

**Observed:** The original regression test passes. Protocols 0–5 preserve dict/slots state, type, contents and maxlen in 36 subclass round trips.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
literal original: integer has no __dict__
pickle protocols: [0, 1, 2, 3, 4, 5]
subclass roundtrips: 36
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
literal original: integer has no __dict__
pickle protocols: [0, 1, 2, 3, 4, 5]
subclass roundtrips: 36
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:**

```text
CATALOG_RECORD {"kind": "start", "case_id": "issue-4769-case-02", "selector": "test.test_deque.TestSubclass.test_copy_pickle", "interpreter": "3.11.0alpha (tags/v0.2.0-604-g25ca331dc:25ca331dc, Mar 25 2023, 21:53:53) \n[rustc 1.67.1]", "executable": "<survey>/.build/slot-a/release/rustpython", "cwd": "<survey>/logs/scratch-history-a/25ca331dc8", "selector_derivation": null, "original_selector": null, "derivation": "TODO RustPython skip decorators bypassed in memory; targeted expectedFailure flags cleared"}
CATALOG_RECORD {"kind": "selection", "case_id": "issue-4769-case-02", "selected_ids": ["test.test_deque.TestSubclass.test_copy_pickle"], "loader_errors": [], "module_origin": "<workspace>/pylib/Lib/test/test_deque.py", "module_sha256": "80bf52da28d59465f6fda4002092772c99afce0a30c0594ba6b5234bfdb4962c", "bypassed_decorators": [{"kind": "expectedFailure", "object": "test.test_deque.TestSubclass.test_copy_pickle", "action": "clear selected object metadata; preserve body"}], "note": "Import-time bypass records include unselected tests; only selected_ids are executed"}
CATALOG_RECORD {"kind": "test", "test_id": "test.test_deque.TestSubclass.test_copy_pickle", "outcome": "error", "exception": "AttributeError", "message": "'Deque' object has no attribute 'x'"}
CATALOG_RECORD {"kind": "complete", "case_id": "issue-4769-case-02", "status": "completed", "tests_run": 1, "selected_count": 1, "failures": 0, "errors": 1, "skipped": [], "expected_failures": 0, "unexpected_successes": 0, "passing": false}
```

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
...
======================================================================
ERROR: test_copy_pickle (test.test_deque.TestSubclass.test_copy_pickle)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<workspace>/pylib/Lib/test/test_deque.py", line 839, in test_copy_pickle
    self.assertEqual(e.x, d.x)
AttributeError: 'Deque' object has no attribute 'x'

----------------------------------------------------------------------
Ran 1 test in 0.007s

FAILED (errors=1)
```

Excerpt; complete output is in the linked execution record.

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B '<additional11-audit>/agent-a/probes.py' \
  4769
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<additional11-audit>/agent-a/probes.py' 4769
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

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

- **[4769-cpython](../../evidence/additional11/agent-a/4769-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4769-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4769-cpython.stderr.txt).
- **[4769-rustpython](../../evidence/additional11/agent-a/4769-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4769-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4769-rustpython.stderr.txt).
- **[4769-unittest-rustpython](../../evidence/additional11/agent-a/4769-unittest-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4769-unittest-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4769-unittest-rustpython.stderr.txt).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
