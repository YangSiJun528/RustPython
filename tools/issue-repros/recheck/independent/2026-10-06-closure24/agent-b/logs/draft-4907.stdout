# Await in an async comprehension (#4907)

[Original issue](https://github.com/RustPython/RustPython/issues/4907). **Resolved in the reported scope.** The original async function compiles. The comment's actual asyncio event-loop and two awaited sleeps finish with lc done.

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


def issue4907():
    import asyncio, time

    source = "async def bar():\n    [await print(i) for i in [1, 2, 3]]\n"
    namespace = {}
    exec(compile(source, "<original-4907>", "exec"), namespace)
    print("original compile: success")
    original = namespace["bar"]()
    try:
        original.send(None)
    except TypeError:
        print("original invocation: TypeError from awaiting print result")
    else:
        raise AssertionError("expected TypeError")

    async def lc():
        [await asyncio.sleep(1) for _ in range(2)]
        print("lc done")

    start = time.monotonic()
    loop = asyncio.new_event_loop()
    tasks = [loop.create_task(lc())]
    done, pending = loop.run_until_complete(asyncio.wait(tasks))
    assert not pending
    for task in done:
        assert task.result() is None
    loop.close()
    assert time.monotonic() - start >= 1.9
    print("comment execution: two awaited sleeps completed")


globals()["issue" + sys.argv[1]]()
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probes.py" 4907
```

**CPython:**

```sh
"$CP" -B "$CASE/probes.py" 4907
```

## Results

**Expected:** Await inside an async-function comprehension must not be rejected as outside an async function.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
original compile: success
1
original invocation: TypeError from awaiting print result
lc done
comment execution: two awaited sleeps completed
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`c7faae9b22ce`](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
SyntaxError: 'await' outside async function at line 2 column 5
    [await print(i) for i in [1, 2, 3]]
    ^
```

## Related change and scope

[PR #5334](https://github.com/RustPython/RustPython/pull/5334): compile await inside an async comprehension.

Calling the original await print(...) function correctly raises TypeError because print returns None. Compilation and execution were assessed separately.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-a/4907-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-a/4907-rustpython.json).
- [Executed source](../../evidence/additional11/agent-a/probes.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
