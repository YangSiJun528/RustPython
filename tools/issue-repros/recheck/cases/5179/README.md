# Builtin buffer methods (#5179)

[Original issue](https://github.com/RustPython/RustPython/issues/5179). **Resolved in the reported scope.** Seven builtin/subclass types expose the expected buffer behavior. Writable flags, release, blocked resize during export and successful resize after release agree with CPython.

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


globals()["issue" + sys.argv[1]]()
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probes.py" 5179
```

**CPython:**

```sh
"$CP" -B "$CASE/probes.py" 5179
```

## Results

**Expected:** Builtin buffer providers must expose the Python-facing PEP 688 methods where appropriate.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
bytes:
  buffer=True
  data='abc'
  readonly=True
  release=False
  writable='BufferError'
bytearray:
  buffer=True
  data='abc'
  readonly=False
  release=True
  released=True
  writable=True
array:
  buffer=True
  data='abc'
  readonly=False
  release=True
  released=True
  writable=True
memoryview:
  buffer=True
  data='abc'
  readonly=True
  release=True
  released=True
  writable='BufferError'
BytesSubclass:
  buffer=True
  data='abc'
  readonly=True
  release=False
  writable='BufferError'
BytearraySubclass:
  buffer=True
  data='abc'
  readonly=False
  release=True
  released=True
  writable=True
mmap:
  buffer=True
  data='abc'
  readonly=False
  release=True
  released=True
  writable=True
resize_after_release=True
custom_exporter=[['get', 284], ['release']]
```

All fields from the recorded JSON are shown above.

**stderr:**

No output.

### Historical failure

Previously recorded at [`a8ab7dd38814`](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
bytes __buffer__ False __release_buffer__ False
bytearray __buffer__ False __release_buffer__ False
array __buffer__ False __release_buffer__ False
memoryview __buffer__ False __release_buffer__ False
```

## Related change and scope

[PR #8523](https://github.com/RustPython/RustPython/pull/8523): PEP 688 methods and managed buffer exports.

__release_buffer__ is optional for types that do not need it. Full C ABI coverage and all lifetime/concurrency combinations were not tested.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-a/5179-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-a/5179-rustpython.json).
- [Executed source](../../evidence/additional11/agent-a/probes.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
