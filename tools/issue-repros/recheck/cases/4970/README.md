# Locale formatting with LC_ALL unset (#4970)

[Original issue](https://github.com/RustPython/RustPython/issues/4970). **Resolved in the reported scope.** With LC_ALL absent and LANG/LC_NUMERIC=en_US.UTF-8, the unmodified original test_locale and two int/float locale tests pass, with no skip or expectedFailure.

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

The host must provide `en_US.UTF-8`. A missing locale or a C-locale fallback does not exercise this case.

## Reproducer

Save as `probe-original-locale-tests.py`. It imports the unchanged repository test modules while retaining each interpreter's stdlib implementations.

```python
import sys
import os
import json
import locale
import unittest

# CPython imports the identical repository test source, while retaining its own stdlib.
test_parent = os.path.join(os.environ["SRC"], "Lib")
import types

test_package = types.ModuleType("test")
test_package.__path__ = [test_parent + "/test"]
test_package.__file__ = test_parent + "/test/__init__.py"
sys.modules["test"] = test_package
from test import test_format, test_types

effective = locale.setlocale(locale.LC_ALL, "")
conv = locale.localeconv()
print(
    json.dumps(
        {
            "LC_ALL_environment": os.environ.get("LC_ALL"),
            "LANG": os.environ.get("LANG"),
            "LC_NUMERIC": os.environ.get("LC_NUMERIC"),
            "effective": effective,
            "conv": {
                k: conv[k] for k in ("decimal_point", "thousands_sep", "grouping")
            },
            "integer": format(123456789, "n"),
            "float": format(1234.5, "n"),
            "test_files": [test_format.__file__, test_types.__file__],
        },
        indent=2,
    ),
    flush=True,
)
assert conv["grouping"], (
    "A grouping locale must be active to reach the original assertion"
)
suite = unittest.TestSuite(
    [
        test_format.FormatTest("test_locale"),
        test_types.TypesTests("test_int__format__locale"),
        test_types.TypesTests("test_float__format__locale"),
    ]
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
assert result.testsRun == 3
assert (
    not result.skipped
    and not result.expectedFailures
    and not result.unexpectedSuccesses
)
assert result.wasSuccessful()
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B "$CASE/probe-original-locale-tests.py"
```

**CPython:**

```sh
"$CP" -B "$CASE/probe-original-locale-tests.py"
```

## Results

**Expected:** The original test must use locale grouping after setlocale(LC_ALL, "") even when LC_ALL is absent from the environment.

### RustPython

Exit code: `0`. No timeout.

**stdout:**

```json
{
  "LC_ALL_environment": null,
  "LANG": "en_US.UTF-8",
  "LC_NUMERIC": "en_US.UTF-8",
  "effective": "en_US.UTF-8",
  "conv": {
    "decimal_point": ".",
    "thousands_sep": ",",
    "grouping": [
      3,
      0
    ]
  },
  "integer": "123,456,789",
  "float": "1,234.5",
  "test_files": [
    "$SRC/Lib/test/test_format.py",
    "$SRC/Lib/test/test_types.py"
  ]
}
```

**stderr:**

```text
test_locale (test.test_format.FormatTest.test_locale) ... ok
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.005s

OK
```

### CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```json
{
  "LC_ALL_environment": null,
  "LANG": "en_US.UTF-8",
  "LC_NUMERIC": "en_US.UTF-8",
  "effective": "en_US.UTF-8",
  "conv": {
    "decimal_point": ".",
    "thousands_sep": ",",
    "grouping": [
      3,
      0
    ]
  },
  "integer": "123,456,789",
  "float": "1,234.5",
  "test_files": [
    "$SRC/Lib/test/test_format.py",
    "$SRC/Lib/test/test_types.py"
  ]
}
```

**stderr:**

```text
test_locale (test.test_format.FormatTest.test_locale) ... ok
test_int__format__locale (test.test_types.TypesTests.test_int__format__locale) ... ok
test_float__format__locale (test.test_types.TypesTests.test_float__format__locale) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
```

### Historical failure

Previously recorded at [`7a6000d181b7`](https://github.com/RustPython/RustPython/commit/7a6000d181b7611c26f2d1353d0462d7bec26da6); exit code `1`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stderr:**

```text
  File "$SRC/Lib/test/test_format.py", line 446, in test_locale
    locale.setlocale(locale.LC_ALL, oldloc)
  File "$SRC/Lib/test/test_format.py", line 444, in test_locale
    self.assertEqual(text.replace(sep, ''), '1234' + point + '5')
  File "$SRC/Lib/test/test_format.py", line 437, in test_locale
    self.assertIn(sep, text)
AssertionError: ',' not found in '123456789'

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
```

Historical output excerpt; runner metadata and repeated shutdown warnings are omitted.

## Related change and scope

[PR #7350](https://github.com/RustPython/RustPython/pull/7350): use locale grouping, separator and decimal-point data.

The active comma grouping was verified; a C-locale skip is not counted. This narrower bare-n symptom is distinct from the outstanding width/padding issues.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/additional11/agent-b/locale-original-unset-cpython.json).
- [RustPython command, environment and output record](../../evidence/additional11/agent-b/locale-original-unset-rustpython.json).
- [Executed source](../../evidence/additional11/agent-b/probe-original-locale-tests.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](reused-history.json).

AI assistance: OpenAI Codex.
