# Locale support for FormatSpec n (#4613)

[Original issue](https://github.com/RustPython/RustPython/issues/4613). **Partially resolved; keep open.** Basic n and the original locale tests pass. Across five available locales, 395 formatting results include 102 differences: 84 zero-padding cases and 18 other Unicode-separator width cases.

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
export LANG=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8
```

`LC_ALL` was unset in these recorded runs.

```sh
unset LC_ALL
```

The host must provide `fr_FR.UTF-8` and `en_US.UTF-8`. A missing locale or a C-locale fallback does not exercise this case.

## Reproducer

Save as `probe-locale-unicode-width.py`.

```python
import locale
import json

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
conv = locale.localeconv()
plain = format(1234, "n")
padded = format(1234, ">20n")
print(
    json.dumps(
        {
            "locale": locale.setlocale(locale.LC_ALL),
            "conv": {
                k: conv[k] for k in ("decimal_point", "thousands_sep", "grouping")
            },
            "plain": plain,
            "plain_characters": len(plain),
            "plain_bytes": len(plain.encode()),
            "padded": padded,
            "padded_characters": len(padded),
            "padded_bytes": len(padded.encode()),
        },
        indent=2,
    )
)
assert len(padded) == 20, "Locale separator must count as one character in field width"
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probe-locale-unicode-width.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/probe-locale-unicode-width.py"
```

## Results

**Expected:** Locale-sensitive n formatting must preserve grouping and character-based field width.

### RustPython

Exit code: `1`. No timeout.

**stdout:**

```json
{
  "locale": "fr_FR.UTF-8",
  "conv": {
    "decimal_point": ",",
    "thousands_sep": " ",
    "grouping": [
      3,
      0
    ]
  },
  "plain": "1 234",
  "plain_characters": 5,
  "plain_bytes": 7,
  "padded": "             1 234",
  "padded_characters": 18,
  "padded_bytes": 20
}
```

**stderr:**

```text
Traceback (most recent call last):
  File "$CASE/probe-locale-unicode-width.py", line 12, in <module>
    assert len(padded) == 20, 'Locale separator must count as one character in field width'
           ^^^^^^^^^^^^^^^^^
AssertionError: Locale separator must count as one character in field width
```

### CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```json
{
  "locale": "fr_FR.UTF-8",
  "conv": {
    "decimal_point": ",",
    "thousands_sep": " ",
    "grouping": [
      3,
      0
    ]
  },
  "plain": "1 234",
  "plain_characters": 5,
  "plain_bytes": 7,
  "padded": "               1 234",
  "padded_characters": 20,
  "padded_bytes": 22
}
```

**stderr:**

No output.

### Historical record

Previously recorded at [`a7c985685146`](https://github.com/RustPython/RustPython/commit/a7c985685146ca401011eb0c25c0b2805a767ce7); exit code `1`. This run was not repeated alongside the current results. The old float test reported an expected failure; the expanded checks above expose the remaining width and padding failures directly.

**stderr:**

```text
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... expected failure
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.004s

OK (expected failures=1)
```

## Zero-padding counterexample

Save as `probe-locale-zero-padding.py`:

```python
import locale
import json
import sys
import platform

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
conv = locale.localeconv()
print(
    json.dumps(
        {
            "version": sys.version,
            "machine": platform.machine(),
            "locale": locale.setlocale(locale.LC_ALL),
            "conv": {
                k: conv[k] for k in ("decimal_point", "thousands_sep", "grouping")
            },
            "cases": {
                spec: format(1234, spec)
                for spec in ("n", "20n", "020n", "+020n", "0=20n")
            },
            "float": format(1234.5, "020n"),
        },
        indent=2,
    )
)
```

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probe-locale-zero-padding.py"
"$CP" -B "$CASE/probe-locale-zero-padding.py"
```

Both runs exited `0` with empty stderr. The numeric-result fields from the recorded JSON are shown below; `repr` makes padding spaces visible. The integer input is `1234`; the float input is `1234.5`.

```text
RustPython:
  'n'     -> '1,234'
  '20n'   -> '               1,234'
  '020n'  -> '0000000000000001,234'
  '+020n' -> '+000000000000001,234'
  '0=20n' -> '0000000000000001,234'
  float   -> '00000000000001,234.5'
CPython 3.14.6:
  'n'     -> '1,234'
  '20n'   -> '               1,234'
  '020n'  -> '0,000,000,000,001,234'
  '+020n' -> '+000,000,000,001,234'
  '0=20n' -> '0,000,000,000,001,234'
  float   -> '00,000,000,001,234.5'
```

Both used decimal point `.`, thousands separator `,` and grouping `[3, 0]`. RustPython does not group the zero padding.

Historical output excerpt; runner metadata and repeated shutdown warnings are omitted.

## Related change and scope

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.

The zero-padding defect was rerun on native ARM64 too. The fr_FR U+202F width counterexample was run with Rosetta RustPython; >20n produces 18 characters rather than 20.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-b/4613-unicode-width-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-b/4613-unicode-width-rustpython.json).
- [Zero-padding RustPython record](../../evidence/additional11/agent-b/4613-zero-padding-rustpython.json) and [CPython record](../../evidence/additional11/agent-b/4613-zero-padding-cpython.json).
- [Executed source](../../evidence/additional11/agent-b/probe-locale-unicode-width.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
