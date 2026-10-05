# Disassembly support used by modulefinder (#3846)

[Original issue](https://github.com/RustPython/RustPython/issues/3846). **Resolved in the reported scope.** The three requested dis APIs operate on actual bytecode. A five-module import graph and all 17 original ModuleFinderTest tests pass without skip or expectedFailure.

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


def issue3846():
    import dis, modulefinder, pathlib, tempfile, types

    source = (
        "import first\n"
        "from package import second\n"
        "from package.second import value\n"
        "def nested():\n"
        "    import nested_dependency\n"
    )
    code = compile(source, "<independent-3846>", "exec")
    assert isinstance(dis.opmap["LOAD_CONST"], int)
    assert isinstance(dis.EXTENDED_ARG, int)
    instructions = list(dis._unpack_opargs(code.co_code))
    assert instructions and all(isinstance(x, tuple) for x in instructions)
    print("opmap, EXTENDED_ARG, _unpack_opargs: usable")
    root = pathlib.Path(tempfile.mkdtemp(prefix="modulefinder-"))
    (root / "package").mkdir()
    files = {
        "main.py": source,
        "first.py": "flag=True\n",
        "package/__init__.py": "from . import second\n",
        "package/second.py": "value=42\n",
        "nested_dependency.py": "x=1\n",
    }
    for name, content in files.items():
        with (root / name).open("x") as out:
            out.write(content)
    finder = modulefinder.ModuleFinder(path=[str(root)])
    finder.run_script(str(root / "main.py"))
    expected = ["__main__", "first", "nested_dependency", "package", "package.second"]
    assert sorted(finder.modules) == expected, sorted(finder.modules)
    assert finder.any_missing_maybe() == ([], [])
    print("module graph:", sorted(finder.modules))
    print("missing:", finder.any_missing_maybe())


globals()["issue" + sys.argv[1]]()
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probes.py" 3846
```

**CPython:**

```sh
"$CP" -B "$CASE/probes.py" 3846
```

## Results

**Expected:** The requested dis exports and instruction iteration must support the reported modulefinder path.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
opmap, EXTENDED_ARG, _unpack_opargs: usable
module graph: ['__main__', 'first', 'nested_dependency', 'package', 'package.second']
missing: ([], [])
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`5631d2102bfe`](https://github.com/RustPython/RustPython/commit/5631d2102bfeb8e0ace727ba539258beb6cdbb7e); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
Traceback (most recent call last):
  File "<survey>/verification-tools/derived-a/issue-3846-case-01.py", line 2, in <module>
    print(repr(dis.opmap['LOAD_CONST']))
AttributeError: module 'dis' has no attribute 'opmap'
```

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
  test.test_modulefinder.ModuleFinderTest
```

The recorded RustPython run executed 17 tests: all passed, with no skips, expected failures or unexpected successes. Exit code: `0`; no timeout. Test progress and `OK` were written to stderr.

## Related change and scope

[PR #5377](https://github.com/RustPython/RustPython/pull/5377): provide dis exports and bytecode/import scanning.

Opcode numeric equality is not required. Creating a generator from integer 100 is not evidence of bytecode iteration; valid code bytes were iterated instead.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-a/3846-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-a/3846-rustpython.json).
- [Regression-test record](../../evidence/additional11/agent-a/3846-unittest-rustpython.json).
- [Executed source](../../evidence/additional11/agent-a/probes.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
