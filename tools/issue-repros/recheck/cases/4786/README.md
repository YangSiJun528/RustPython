# Surrogate in a type name (#4786)

[Original issue](https://github.com/RustPython/RustPython/issues/4786). **Resolved in the reported scope.** The original surrogate is retained and type creation raises UnicodeEncodeError, matching CPython. Exit 1 for the uncaught exception is expected.

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

Save as `4786-original.py`.

```python
type("A\udcdcB", (), {})
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/4786-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/4786-original.py"
```

## Results

**Expected:** A surrogate-containing type name must raise UnicodeEncodeError instead of being silently replaced.

### RustPython and CPython 3.14.6

Exit code: `1`. No timeout.

**stdout:**

No output.

**stderr:**

```text
Traceback (most recent call last):
  File "$CASE/4786-original.py", line 1, in <module>
    type("A\udcdcB", (), {})
    ~~~~^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcdc' in position 1: surrogates not allowed
```

### Historical failure

Previously recorded at [`010640ccc8f7`](https://github.com/RustPython/RustPython/commit/010640ccc8f74f56075df09a654352ae3d162d25); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
<class '__main__.A�B'>
```

## Related change and scope

[PR #5629](https://github.com/RustPython/RustPython/pull/5629): retain surrogate literals; [PR #6547](https://github.com/RustPython/RustPython/pull/6547): validate type names as UTF-8.

A separate adjacent-surrogate input is rejected by both, but UnicodeEncodeError.end differs (2 versus 3). Full error-span parity is not claimed.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/4786-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/4786-original-rp.json).
- [Executed source](../../evidence/initial16/agent-a/4786-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/4786/evidence/metadata.json).

AI assistance: OpenAI Codex.
