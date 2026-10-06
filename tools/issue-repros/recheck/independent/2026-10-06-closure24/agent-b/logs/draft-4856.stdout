# Lambda in a class decorator (#4856)

[Original issue](https://github.com/RustPython/RustPython/issues/4856). **Resolved in the reported scope.** The original source compiles without the Rust compiler panic. Executing that original source raises BaseFTests NameError in both interpreters. Separate valid mock.patch and nested-capture controls execute and restore the patched function.

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

Save as `probe-4856.py`.

First save the originally reported input as `original-4856.py` beside the probe:

```python
import unittest
from unittest import mock


class MockedA(BaseFTests):
    pass


@mock.patch("", lambda: 3)
class MockedB(MockedA):
    def _asserts(self, val):
        pass
```

The following probe checks compilation separately from execution, then runs valid decorator examples:

```python
from pathlib import Path

source = Path(__file__).with_name("original-4856.py").read_text()
code = compile(source, "original-4856.py", "exec")
print("original compile success")
try:
    exec(code, {})
except Exception as e:
    print("original execution", type(e).__name__, str(e))
from unittest import mock


class BaseFTests:
    pass


class MockedA(BaseFTests):
    pass


def target():
    return 1


@mock.patch("__main__.target", lambda: 3)
class MockedB(MockedA):
    def test_value(self):
        return target()


print("valid patch method", MockedB().test_value(), "outside", target())


def factory(value):
    @mock.patch("__main__.target", lambda: value)
    class Nested(MockedA):
        def test_value(self):
            return target()

    return Nested


print("nested capture", factory(7)().test_value(), "outside", target())
```

## Run

```sh
cd "$SRC"
```

**RustPython:**

```sh
RUSTPYTHONPATH="$SRC/Lib" "$RP" -B -S "$CASE/probe-4856.py"
```

**CPython:**

```sh
"$CP" -B -S "$CASE/probe-4856.py"
```

## Results

**Expected:** Compilation must not panic when a class decorator contains a lambda argument.

### RustPython and CPython 3.14.6

Exit code: `0`. No timeout.

**stdout:**

```text
original compile success
original execution NameError name 'BaseFTests' is not defined
valid patch method 3 outside 1
nested capture 7 outside 1
```

**stderr:**

No output.

### Historical failure

Previously recorded at [`c7faae9b22ce`](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100); exit code `101`. This run was not repeated alongside the current results. Historical inputs may differ from the expanded checks above.

**stdout:** No output.

**stderr:**

```text
thread 'main' panicked at 'assertion failed: table.sub_tables.is_empty()', compiler/codegen/src/compile.rs:305:9
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

## Related change and scope

[PR #8138](https://github.com/RustPython/RustPython/pull/8138): visit class decorators before entering their class scope.

The original application is not runnable as written; compile success is not application success. The normalized runtime examples are separate inputs.

First fixing commit: not established.

## Evidence

Recorded executable SHA-256 values:

- RustPython: `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`.
- CPython: `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`.

- [CPython command, environment and output record](../../evidence/initial16/agent-b/fresh-4856-cp.json).
- [RustPython command, environment and output record](../../evidence/initial16/agent-b/fresh-4856-rp.json).
- [Executed source](../../evidence/initial16/agent-b/probe-4856.py.txt).
- [Scope and complete execution inventory](assessment.json).
- [Historical record](../../../cases/4856/evidence/metadata.json).

AI assistance: OpenAI Codex.
