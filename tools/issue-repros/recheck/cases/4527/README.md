# Finalization of a global object (#4527)

[Original issue](https://github.com/RustPython/RustPython/issues/4527). **Resolved in the reported scope.** The unchanged original lifetime pattern prints deleted! at interpreter shutdown, with exit 0 and no stderr. An explicit-del control was checked separately.

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

## Reproducer

Save as `4527-original.py`.

```python
class X:
    def __del__(self):
        print("deleted!")


x = X()
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/4527-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/4527-original.py"
```

## Results

**Expected:** The global object destructor must run during ordinary interpreter shutdown.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
deleted!
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`e5735cde67b8`](https://github.com/RustPython/RustPython/commit/e5735cde67b86699bd68c8959167ecf2649a6f2d); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

## Related change and scope

[PR #6934](https://github.com/RustPython/RustPython/pull/6934): module finalization during shutdown.

Process-abort paths and arbitrary shutdown ordering are not promised.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/4527-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/4527-original-rp.json).
- [Executed source](../../evidence/initial16/agent-a/4527-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/4527/evidence/metadata.json).

AI assistance: OpenAI Codex.
