# Deque subclass pickle state (#4769)

[Original issue](https://github.com/RustPython/RustPython/issues/4769). **Resolved in the reported scope.** The original regression test passes. Protocols 0–5 preserve dict/slots state, type, contents and maxlen in 36 subclass round trips.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython: 0.6.1, Python 3.14.0.alpha; native ARM64.
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
export LANG=C LC_ALL=C NO_COLOR=1 TERM=dumb
```

## Reproducer

Save as `probes.py`. This contains the selected function plus the original imports and dispatcher; unrelated issue functions are omitted.

```python
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
                if cls is DequeWithSlots:
                    assert e.slot == d.slot
                total += 1
    print("pickle protocols:", list(range(pickle.HIGHEST_PROTOCOL + 1)))
    print("subclass roundtrips:", total)


globals()["issue" + sys.argv[1]]()
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probes.py" 4769
```

**CPython:**

```sh
"$CP" -B "$CASE/probes.py" 4769
```

## Results

**Expected:** Pickling a deque subclass must preserve its instance state.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
literal original: integer has no __dict__
pickle protocols: [0, 1, 2, 3, 4, 5]
subclass roundtrips: 36
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`25ca331dc81e`](https://github.com/RustPython/RustPython/commit/25ca331dc81e617498465ecdb2f848ec81025f71); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stderr:**

```text
======================================================================
ERROR: test_copy_pickle (test.test_deque.TestSubclass.test_copy_pickle)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "$SRC/pylib/Lib/test/test_deque.py", line 839, in test_copy_pickle
    self.assertEqual(e.x, d.x)
AttributeError: 'Deque' object has no attribute 'x'

----------------------------------------------------------------------
Ran 1 test in 0.007s

FAILED (errors=1)
```

Historical output excerpt; runner metadata and repeated shutdown warnings are omitted.

## Existing regression tests

Save the following runner as `unittest-probe.py`. It reports skip and expected-failure markers and runs the repository tests unchanged.

```python
import unittest, json, sys

suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:])


def flatten(item):
    if isinstance(item, unittest.TestSuite):
        return [t for child in item for t in flatten(child)]
    return [item]


tests = flatten(suite)
print(
    json.dumps(
        {
            "tests": [
                {
                    "id": t.id(),
                    "skip": bool(
                        getattr(t, "__unittest_skip__", False)
                        or getattr(
                            getattr(t, t._testMethodName), "__unittest_skip__", False
                        )
                    ),
                    "expected_failure": bool(
                        getattr(
                            getattr(t, t._testMethodName),
                            "__unittest_expecting_failure__",
                            False,
                        )
                    ),
                }
                for t in tests
            ]
        },
        sort_keys=True,
    ),
    flush=True,
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(
    json.dumps(
        {
            "run": result.testsRun,
            "skips": [(t.id(), reason) for t, reason in result.skipped],
            "expected_failures": [
                (t.id(), trace) for t, trace in result.expectedFailures
            ],
            "unexpected_successes": [t.id() for t in result.unexpectedSuccesses],
            "success": result.wasSuccessful(),
        },
        sort_keys=True,
    )
)
sys.exit(0 if result.wasSuccessful() else 1)
```

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/unittest-probe.py" \
  test.test_deque.TestSubclass.test_copy_pickle
```

The recorded RustPython run executed 1 test: all passed, with no skips, expected failures or unexpected successes. Exit code: `0`; no timeout. Test progress and `OK` were written to stderr.

## Related change and scope

[PR #7699](https://github.com/RustPython/RustPython/pull/7699): include __getstate__ in deque reduction.

The issue snippet accidentally pickles pickle.HIGHEST_PROTOCOL itself. That literal and the corrected intended input are separate. Recursive deque pickle is outside this reported nonrecursive case.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-a/4769-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-a/4769-rustpython.json).
- [Regression-test record](../../evidence/additional11/agent-a/4769-unittest-rustpython.json).
- [Executed source](../../evidence/additional11/agent-a/probes.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
