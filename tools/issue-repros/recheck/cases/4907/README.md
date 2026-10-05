# Await in an async comprehension (#4907)

Original issue: [#4907](https://github.com/RustPython/RustPython/issues/4907)

**Verified closure candidate:** The original async function compiles. The comment's actual asyncio event-loop and two awaited sleeps finish with lc done.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Run the shared [probes.py](../../evidence/additional11/agent-a/probes.py.txt) with selector `4907`, as shown in the recorded command. The relevant function is `issue4907`; the full file supplies its imports and dispatcher. The excerpt is formatted for readability.

<details>
<summary>Reproducer function: issue4907</summary>

```python
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
```

</details>

## Expected and observed results

**Expected:** Await inside an async-function comprehension must not be rejected as outside an async function.

**Observed:** The original async function compiles. The comment's actual asyncio event-loop and two awaited sleeps finish with lc done.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
original compile: success
1
original invocation: TypeError from awaiting print result
lc done
comment execution: two awaited sleeps completed
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
original compile: success
1
original invocation: TypeError from awaiting print result
lc done
comment execution: two awaited sleeps completed
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 1</summary>

**stdout:** No output.

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
SyntaxError: 'await' outside async function at line 2 column 5
    [await print(i) for i in [1, 2, 3]]
    ^
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B '<additional11-audit>/agent-a/probes.py' \
  4907
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<additional11-audit>/agent-a/probes.py' 4907
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

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

- **[4907-cpython](../../evidence/additional11/agent-a/4907-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4907-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4907-cpython.stderr.txt).
- **[4907-rustpython](../../evidence/additional11/agent-a/4907-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/4907-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/4907-rustpython.stderr.txt).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
