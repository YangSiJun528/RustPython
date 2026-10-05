# Py_GIL_DISABLED configuration value (#6429)

[Original issue](https://github.com/RustPython/RustPython/issues/6429). **Resolved in the reported scope.** sysconfig.get_config_var("Py_GIL_DISABLED") is defined as 1 in the verified POSIX RustPython build.

## Environment

- Source and standard library: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Verified October 5, 2026 on macOS 26.5.2 ARM64.
- RustPython: 0.6.1, Python 3.14.0.alpha; x86_64 through Rosetta.
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
export LC_ALL=en_US.UTF-8
```

## Reproducer

Save as `probe-6429.py`.

```python
import sys, sysconfig

value = sysconfig.get_config_var("Py_GIL_DISABLED")
print(value)
print("type", type(value).__name__)
print("implementation", sys.implementation.name)
print("platform", sys.platform)
print("gil_enabled", getattr(sys, "_is_gil_enabled", lambda: "unavailable")())
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -S "$CASE/probe-6429.py"
```

**CPython:**

```sh
"$CP" -B -S "$CASE/probe-6429.py"
```

## Results

**Expected:** The tested RustPython build must expose its build-time Py_GIL_DISABLED setting instead of None.

### RustPython

Exit code: `0`. No timeout.

**stdout:**

```text
1
type int
implementation rustpython
platform darwin
gil_enabled False
```

**stderr:**

No output.

### CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
0
type int
implementation cpython
platform darwin
gil_enabled True
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`e227956a58f0`](https://github.com/RustPython/RustPython/commit/e227956a58f0f072f8be177264e0fdc1b9280e8a); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
None
```

Historical output excerpt; runner metadata and repeated shutdown warnings are omitted.

## Related change and scope

[PR #6428](https://github.com/RustPython/RustPython/pull/6428): expose the build-time Py_GIL_DISABLED value.

CPython can legitimately return a different value. This is not proof of full free-threading or C-extension compatibility.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-b/fresh-6429-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-b/fresh-6429-rp.json).
- [Executed source](../../evidence/initial16/agent-b/probe-6429.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/6429/evidence/metadata.json).

AI assistance: OpenAI Codex.
