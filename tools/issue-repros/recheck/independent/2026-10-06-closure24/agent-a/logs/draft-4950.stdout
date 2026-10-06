# Bool numeric format codes (#4950)

[Original issue](https://github.com/RustPython/RustPython/issues/4950). **Resolved in the reported scope.** False and True match CPython for the original codes, the comment's n/d codes and width/precision controls: 34 recorded results.

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


def issue4950():
    import locale

    locale.setlocale(locale.LC_ALL, "C")
    cases = ["f", "x", "X", "e", "E", "c", "g", "o", "%", "o", "n", "d"]
    cases += ["08x", "+08d", ".2f", ".1%", ">5n"]
    results = []
    for value in (False, True):
        for spec in cases:
            actual = ("{:" + spec + "}").format(value)
            assert actual == format(int(value), spec)
            results.append([value, spec, actual])
    print(
        json.dumps(
            {"locale": locale.setlocale(locale.LC_ALL), "results": results},
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
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probes.py" 4950
```

**CPython:**

```sh
"$CP" -B "$CASE/probes.py" 4950
```

## Results

**Expected:** Explicit numeric format codes must format bool through its numeric value.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
locale: C
False 'f'     -> '0.000000'
False 'x'     -> '0'
False 'X'     -> '0'
False 'e'     -> '0.000000e+00'
False 'E'     -> '0.000000E+00'
False 'c'     -> '\x00'
False 'g'     -> '0'
False 'o'     -> '0'
False '%'     -> '0.000000%'
False 'o'     -> '0'
False 'n'     -> '0'
False 'd'     -> '0'
False '08x'   -> '00000000'
False '+08d'  -> '+0000000'
False '.2f'   -> '0.00'
False '.1%'   -> '0.0%'
False '>5n'   -> '    0'
True  'f'     -> '1.000000'
True  'x'     -> '1'
True  'X'     -> '1'
True  'e'     -> '1.000000e+00'
True  'E'     -> '1.000000E+00'
True  'c'     -> '\x01'
True  'g'     -> '1'
True  'o'     -> '1'
True  '%'     -> '100.000000%'
True  'o'     -> '1'
True  'n'     -> '1'
True  'd'     -> '1'
True  '08x'   -> '00000001'
True  '+08d'  -> '+0000001'
True  '.2f'   -> '1.00'
True  '.1%'   -> '100.0%'
True  '>5n'   -> '    1'
```

Recorded JSON rows shown as value, format specifier and result.

**stderr:**

No output.

### Historical failure

Previously recorded at [`fa790558211e`](https://github.com/RustPython/RustPython/commit/fa790558211ec690541299258f44d7453501958a); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
Traceback (most recent call last):
  File "<survey>/repros/4950/issue-4950-case-01/source-01.py", line 1, in <module>
    '{:f}'.format(False)
ValueError: Invalid format specifier
```

## Related change and scope

[PR #5012](https://github.com/RustPython/RustPython/pull/5012): update the parser/format dependency · [Parser PR #91](https://github.com/RustPython/Parser/pull/91).

These numeric format checks used the C locale.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-a/4950-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-a/4950-rustpython.json).
- [Executed source](../../evidence/additional11/agent-a/probes.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
