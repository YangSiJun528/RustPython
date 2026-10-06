# Classmethod and staticmethod annotations (#8494)

[Original issue](https://github.com/RustPython/RustPython/issues/8494). **Resolved in the reported scope.** Both wrappers support the two annotation attributes, cache values in the wrapper, and isolate writes/deletes from the wrapped function. The module-level original, a separate function-local variant and the regression test pass.

Independently rechecked on October 6, 2026 (KST): [fresh inputs, results and scope](../../independent/2026-10-06-closure24/cases/8494/README.md).

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

The function-local input below is a variant of the original module-level example. Both forms were separately executed in the independent review; they must not be described as identical source.

## Reproducer

Save as `probes.py`. This contains the selected function plus the original imports and dispatcher; unrelated issue functions are omitted.

```python
import sys, json


def issue8494():
    # Function-local variant; the module-level original is tested separately.
    def f() -> Missing:
        pass

    for wrapper in (classmethod(f), staticmethod(f)):
        Missing = int
        print(type(wrapper).__name__, wrapper.__annotations__)
        print("__annotations__" in wrapper.__dict__)
        wrapper.__annotations__ = {"x": str}
        print("wrapper:", wrapper.__annotations__)
        print("wrapped:", f.__annotations__)
    for decorator in (classmethod, staticmethod):

        def annotated(x: int) -> str:
            pass

        def unannotated(x):
            pass

        for function in (annotated, unannotated):
            wrapper = decorator(function)
            for name, replacement in [
                ("__annotations__", {"new": bytes}),
                ("__annotate__", lambda format: {"new": bytes}),
            ]:
                assert name not in wrapper.__dict__
                original = getattr(function, name)
                assert getattr(wrapper, name) is original
                assert wrapper.__dict__[name] is original
                setattr(wrapper, name, replacement)
                assert getattr(wrapper, name) is replacement
                assert getattr(function, name) is original
                delattr(wrapper, name)
                assert name not in wrapper.__dict__
                assert getattr(wrapper, name) is original
            print(
                decorator.__name__,
                function.__name__,
                "both attributes cache/write/delete isolation passed",
            )


globals()["issue" + sys.argv[1]]()
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probes.py" 8494
```

**CPython:**

```sh
"$CP" -B "$CASE/probes.py" 8494
```

## Results

**Expected:** PEP 749 annotation attributes on classmethod/staticmethod must be writable, cached and independent of the original callable.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

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

No output.

### Historical failure

Previously recorded at [`b304919a6301`](https://github.com/RustPython/RustPython/commit/b304919a63010f78daa65bc5db14fd487829aeb9); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
classmethod {'return': <class 'int'>}
False
wrapper: {'x': <class 'str'>}
wrapped: {'x': <class 'str'>}
staticmethod {'x': <class 'str'>}
False
wrapper: {'x': <class 'str'>}
wrapped: {'x': <class 'str'>}
```

**stderr:** No output.

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
  test.test_descr.ClassPropertiesAndMethods.test_classmethod_staticmethod_annotations
```

The recorded RustPython run executed 1 test: all passed, with no skips, expected failures or unexpected successes. Exit code: `0`; no timeout. Test progress and `OK` were written to stderr.

## Related change and scope

[PR #8701](https://github.com/RustPython/RustPython/pull/8701): cache and assign annotation attributes on the wrapper.

CPython 3.14.6 is the reference; this is not compared to older eager-annotation semantics.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-a/8494-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-a/8494-rustpython.json).
- [Regression-test record](../../evidence/additional11/agent-a/8494-unittest-rustpython.json).
- [Executed source](../../evidence/additional11/agent-a/probes.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
