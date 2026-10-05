# Locale-aware n formatting (#5181)

[Original issue](https://github.com/RustPython/RustPython/issues/5181). **Partially resolved; keep open.** Bare n and the original locale test pass, but en_US format(123456789, "015n") gives 0000123,456,789 instead of CPython's 000,123,456,789.

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

The host must provide `en_US.UTF-8`, `de_DE.UTF-8` and `hi_IN.UTF-8`. A missing locale or a C-locale fallback does not exercise this case.

## Reproducer

Save as `probe-5181-width.py`.

```python
import locale

for name in ["en_US.UTF-8", "de_DE.UTF-8", "hi_IN.UTF-8"]:
    locale.setlocale(locale.LC_ALL, name)
    text = format(123456789, "015n")
    print(name, repr(text), len(text))
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -S "$CASE/probe-5181-width.py"
```

**CPython:**

```sh
"$CP" -B -S "$CASE/probe-5181-width.py"
```

## Results

**Expected:** Locale grouping must also remain correct when n formatting is combined with zero padding.

### RustPython

Exit code: `0`. No timeout.

**stdout:**

```text
en_US.UTF-8 '0000123,456,789' 15
de_DE.UTF-8 '0000123.456.789' 15
hi_IN.UTF-8 '00012,34,56,789' 15
```

**stderr:**

No output.

### CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
en_US.UTF-8 '000,123,456,789' 15
de_DE.UTF-8 '000.123.456.789' 15
hi_IN.UTF-8 '00,12,34,56,789' 15
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`a8ab7dd38814`](https://github.com/RustPython/RustPython/commit/a8ab7dd3881437ad2eef31b3470427db20656a84); exit code `0`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:**

```text
locale en_US.UTF-8
result '123456789'
matches False
```

## Related change and scope

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.

The locale exists and grouping is active. Both outputs have length 15; the defect is grouping, not missing locale setup.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-b/fresh-5181-width-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-b/fresh-5181-width-rp.json).
- [Executed source](../../evidence/initial16/agent-b/probe-5181-width.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/5181/evidence/metadata.json).

AI assistance: OpenAI Codex.
