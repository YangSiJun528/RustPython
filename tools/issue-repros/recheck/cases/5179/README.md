# Builtin buffer methods (#5179)

Original issue: [#5179](https://github.com/RustPython/RustPython/issues/5179)

**Verified closure candidate:** Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Run the shared [probes.py](../../evidence/additional11/agent-a/probes.py.txt) with selector `5179`, as shown in the recorded command. The relevant function is `issue5179`; the full file supplies its imports and dispatcher. The excerpt is formatted for readability.

<details>
<summary>Reproducer function: issue5179</summary>

```python
def issue5179():
    import array, mmap, inspect

    class BytesSubclass(bytes):
        pass

    class BytearraySubclass(bytearray):
        pass

    objects = [
        bytes(b"abc"),
        bytearray(b"abc"),
        array.array("B", b"abc"),
        memoryview(b"abc"),
        BytesSubclass(b"abc"),
        BytearraySubclass(b"abc"),
    ]
    mapping = mmap.mmap(-1, 3)
    mapping[:] = b"abc"
    objects.append(mapping)
    rows = []
    for obj in objects:
        row = {
            "type": type(obj).__name__,
            "buffer": hasattr(obj, "__buffer__"),
            "release": hasattr(obj, "__release_buffer__"),
        }
        view = obj.__buffer__(0)
        assert isinstance(view, memoryview)
        row["data"] = view.tobytes().decode("ascii")
        row["readonly"] = view.readonly
        assert row["data"] == "abc"
        if hasattr(obj, "__release_buffer__"):
            obj.__release_buffer__(view)
            try:
                view.tobytes()
            except ValueError:
                row["released"] = True
            else:
                row["released"] = False
        else:
            view.release()
        try:
            writable = obj.__buffer__(inspect.BufferFlags.WRITABLE)
        except Exception as e:
            row["writable"] = type(e).__name__
        else:
            row["writable"] = not writable.readonly
            if hasattr(obj, "__release_buffer__"):
                obj.__release_buffer__(writable)
            else:
                writable.release()
        rows.append(row)
    objects[3].release()
    mapping.close()
    ba = bytearray(b"abc")
    view = ba.__buffer__(0)
    try:
        ba.append(100)
    except BufferError:
        pass
    else:
        raise AssertionError("resize while exported should be blocked")
    ba.__release_buffer__(view)
    ba.append(100)
    assert ba == b"abcd"
    events = []

    class Exporter:
        def __buffer__(self, flags):
            events.append(["get", flags])
            self.view = memoryview(bytearray(b"xyz"))
            return self.view

        def __release_buffer__(self, view):
            assert view is self.view
            events.append(["release"])
            view.release()

    obj = Exporter()
    with memoryview(obj) as view:
        assert view.tobytes() == b"xyz"
        view[0] = 65
        assert view.tobytes() == b"Ayz"
    assert events[-1] == ["release"]
    print(
        json.dumps(
            {"builtins": rows, "resize_after_release": True, "custom_exporter": events},
            sort_keys=True,
        )
    )
```

</details>

## Expected and observed results

**Expected:** Builtin buffer providers must expose the Python-facing PEP 688 methods where appropriate.

**Observed:** Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```json
{
  "builtins": [
    {
      "buffer": true,
      "data": "abc",
      "readonly": true,
      "release": false,
      "type": "bytes",
      "writable": "BufferError"
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "bytearray",
      "writable": true
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "array",
      "writable": true
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": true,
      "release": true,
      "released": true,
      "type": "memoryview",
      "writable": "BufferError"
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": true,
      "release": false,
      "type": "BytesSubclass",
      "writable": "BufferError"
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "BytearraySubclass",
      "writable": true
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "mmap",
      "writable": true
    }
  ],
  "custom_exporter": [
    [
      "get",
      284
    ],
    [
      "release"
    ]
  ],
  "resize_after_release": true
}
```

JSON whitespace is expanded for readability.

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```json
{
  "builtins": [
    {
      "buffer": true,
      "data": "abc",
      "readonly": true,
      "release": false,
      "type": "bytes",
      "writable": "BufferError"
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "bytearray",
      "writable": true
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "array",
      "writable": true
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": true,
      "release": true,
      "released": true,
      "type": "memoryview",
      "writable": "BufferError"
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": true,
      "release": false,
      "type": "BytesSubclass",
      "writable": "BufferError"
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "BytearraySubclass",
      "writable": true
    },
    {
      "buffer": true,
      "data": "abc",
      "readonly": false,
      "release": true,
      "released": true,
      "type": "mmap",
      "writable": true
    }
  ],
  "custom_exporter": [
    [
      "get",
      284
    ],
    [
      "release"
    ]
  ],
  "resize_after_release": true
}
```

JSON whitespace is expanded for readability.

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 0</summary>

**stdout:**

```text
bytes __buffer__ False __release_buffer__ False
bytearray __buffer__ False __release_buffer__ False
array __buffer__ False __release_buffer__ False
memoryview __buffer__ False __release_buffer__ False
```

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-a/verification/rustpython' -B '<additional11-audit>/agent-a/probes.py' \
  5179
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B \
  '<additional11-audit>/agent-a/probes.py' 5179
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.

[PR #8523](https://github.com/RustPython/RustPython/pull/8523): PEP 688 methods and managed buffer exports.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** __release_buffer__ is optional for types that do not need it. Full C ABI coverage and all lifetime/concurrency combinations were not tested.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot A/native ARM64.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](reused-history.json).
- Historical baseline: [`a8ab7dd38814`](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical-a8ab7dd388-01-d89ea130-92a69513.stdout](../../evidence/history/logs/issue-5179-case-01/historical-a8ab7dd388-01-d89ea130-92a69513.stdout).
- [Full reused historical-a8ab7dd388-01-d89ea130-92a69513.stderr](../../evidence/history/logs/issue-5179-case-01/historical-a8ab7dd388-01-d89ea130-92a69513.stderr).
- [Independent assessment, original scope and limitations](assessment.json).

- **[5179-cpython](../../evidence/additional11/agent-a/5179-cpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/5179-cpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/5179-cpython.stderr.txt).
- **[5179-rustpython](../../evidence/additional11/agent-a/5179-rustpython.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/additional11/agent-a/5179-rustpython.stdout.txt); stderr: [stderr](../../evidence/additional11/agent-a/5179-rustpython.stderr.txt).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
