# Negative dynamic format width (#4762)

[Original issue](https://github.com/RustPython/RustPython/issues/4762). **Resolved in the reported scope.** The original assertion preserves the two trailing spaces in `'abc  '`. Positive, zero and additional negative-width controls also agree with CPython.

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

Save as `4762-original.py`.

```python
assert "%*s" % (-5, "abc") == "abc  "
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/4762-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/4762-original.py"
```

## Results

**Expected:** A negative dynamic width selects left alignment.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

No output.

**stderr:**

No output.

### Historical failure

Previously recorded at [`c36e3612e7dd`](https://github.com/RustPython/RustPython/commit/c36e3612e7dd1c7abd9fc7b76b912372bd26afbf); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
Traceback (most recent call last):
  File "<survey>/repros/4762/issue-4762-case-01/source-01.py", line 1, in <module>
    assert('%*s' % (-5, 'abc') == 'abc  ')
AssertionError
```

## Related change and scope

[PR #4766](https://github.com/RustPython/RustPython/pull/4766): left alignment for negative dynamic widths.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/4762-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/4762-original-rp.json).
- [Executed source](../../evidence/initial16/agent-a/4762-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/4762/evidence/metadata.json).

AI assistance: OpenAI Codex.
