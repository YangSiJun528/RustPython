# Classmethod and staticmethod annotations (#8494)

Original issue: [#8494](https://github.com/RustPython/RustPython/issues/8494)

**Verified closure candidate:** Both wrappers support the two annotation attributes, cache values in the wrapper, and isolate writes/deletes from the wrapped function. The original unresolved-name input and regression test pass.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Run the shared [probes.py](../../evidence/additional11/agent-a/probes.py.txt) with selector `8494`, as shown in the recorded command. The relevant function is `issue8494`; the full file supplies its imports and dispatcher. The excerpt is formatted for readability.

<details>
<summary>Reproducer function: issue8494</summary>

```python
def issue8494():
    # This is the literal original, including creating both wrappers before Missing.
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
```

</details>

## Expected and observed results

**Expected:** PEP 749 annotation attributes on classmethod/staticmethod must be writable, cached and independent of the original callable.

**Observed:** Both wrappers support the two annotation attributes, cache values in the wrapper, and isolate writes/deletes from the wrapped function. The original unresolved-name input and regression test pass.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

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

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

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

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

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

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B '<additional11-audit>/agent-a/probes.py' \
  8494
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<additional11-audit>/agent-a/probes.py' 8494
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

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

- **[8494-cpython](../../evidence/additional11/agent-a/8494-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/8494-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/8494-cpython.stderr.txt).
- **[8494-original-cpython](../../evidence/additional11/agent-a/8494-original-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/8494-original-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/8494-original-cpython.stderr.txt).
- **[8494-original-rustpython](../../evidence/additional11/agent-a/8494-original-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/8494-original-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/8494-original-rustpython.stderr.txt).
- **[8494-rustpython](../../evidence/additional11/agent-a/8494-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/8494-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/8494-rustpython.stderr.txt).
- **[8494-unittest-rustpython](../../evidence/additional11/agent-a/8494-unittest-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/8494-unittest-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/8494-unittest-rustpython.stderr.txt).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
