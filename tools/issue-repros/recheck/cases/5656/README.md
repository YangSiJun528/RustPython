# Invalid escape warning in a bytes literal (#5656)

[Original issue](https://github.com/RustPython/RustPython/issues/5656). **Resolved in the reported scope.** The bytes value is preserved and compilation emits the required SyntaxWarning for the invalid escape. Warning presence and warning-as-error behavior were checked.

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

Save as `5656-original.py`.

```python
assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/5656-original.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/5656-original.py"
```

## Results

**Expected:** Compilation of the original bytes literal must report the invalid escape while preserving its value.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

No output.

**stderr:**

```text
$CASE/5656-original.py:1: SyntaxWarning: "\X" is an invalid escape sequence. Such
sequences will not work in the future. Did you mean "\\X"? A raw string is also an
option.
  assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])
```

The warning text is wrapped for readability.

### Historical failure

Previously recorded at [`c3ed002b1204`](https://github.com/RustPython/RustPython/commit/c3ed002b1204d9ff156b5192b634a4056101b255); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

The bytes assertion passed, but stderr contained only interpreter shutdown warnings and no invalid-escape warning.

## Warning-filter and valid-literal controls

Save as `5656-boundaries.py`:

```python
import warnings

for literal in [
    r'b"omkmok\Xaa"',
    r'"omkmok\Xaa"',
    r'b"omkmok\\Xaa"',
    r'rb"omkmok\Xaa"',
    r'b"\xff"',
]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        code = compile(literal, "<invalid-escape-probe>", "eval")
        print(
            "always",
            literal,
            repr(eval(code)),
            [
                (warning.category.__name__, str(warning.message), warning.lineno)
                for warning in caught
            ],
        )
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("error")
        try:
            compile(literal, "<invalid-escape-probe>", "eval")
        except Exception as error:
            print("error", literal, type(error).__name__)
        else:
            print("error", literal, "accepted")
```

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/5656-boundaries.py"
"$CP" -B "$CASE/5656-boundaries.py"
```

Both recorded runs exited `0` with empty stderr. Under `always`, the invalid bytes and string escapes emitted `SyntaxWarning`; under `error`, compilation raised `SyntaxError`. Escaped backslashes, raw bytes and valid hexadecimal escapes emitted no warning.

## Related change and scope

[PR #7164](https://github.com/RustPython/RustPython/pull/7164): warn about invalid string and bytes escapes.

Success requires the warning as well as the unchanged bytes value; exit code 0 alone is insufficient.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-a/5656-original-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-a/5656-original-rp.json).
- [Warning-filter RustPython record](../../evidence/initial16/agent-a/5656-boundaries-rp.json) and [CPython record](../../evidence/initial16/agent-a/5656-boundaries-cp.json).
- [Executed source](../../evidence/initial16/agent-a/5656-original.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/5656/evidence/metadata.json).

AI assistance: OpenAI Codex.
