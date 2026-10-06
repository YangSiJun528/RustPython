# Native class-method descriptor type (#4690)

[Original issue](https://github.com/RustPython/RustPython/issues/4690). **Resolved in the reported scope.** Both original descriptor queries return classmethod_descriptor. Binding and representative additional native descriptors agree with CPython.

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

Save as `4690-original.py`.

```python
print(type(dict.__dict__["fromkeys"]))
print(type(dict.fromkeys))
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/4690-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/4690-original.py"
```

## Results

**Expected:** Native class methods must use the classmethod_descriptor type.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
<class 'classmethod_descriptor'>
<class 'builtin_function_or_method'>
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`8ff947e83a65`](https://github.com/RustPython/RustPython/commit/8ff947e83a65b74c920edc63aed8a0a5854b8612); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
classmethod
method
```

## Related change and scope

[PR #8780](https://github.com/RustPython/RustPython/pull/8780): native OrderedDict and class-method descriptors.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/4690-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/4690-original-rp.json).
- [Executed source](../../evidence/initial16/agent-a/4690-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/4690/evidence/metadata.json).

AI assistance: OpenAI Codex.
