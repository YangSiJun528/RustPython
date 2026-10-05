# Lambda in a class decorator (#4856)

Original issue: [#4856](https://github.com/RustPython/RustPython/issues/4856)

**Verified closure candidate:** The original source compiles without the Rust compiler panic. Executing that original source raises BaseFTests NameError in both interpreters. Separate valid mock.patch and nested-capture controls execute and restore the patched function.

**Current verification:** `f39b054b9c8cbbf884f53123eef028131789990c` (October 5, 2026). Historical observations are reused and are explicitly separated below.

## Reproducer

Executed input: [probe-4856.py](../../evidence/initial16/agent-b/probe-4856.py.txt). The export preserves the executed code except for documented local-path substitutions.

<details>
<summary>Reproducer code</summary>

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

</details>

## Expected and observed results

**Expected:** Compilation must not panic when a class decorator contains a lambda argument.

**Observed:** The original source compiles without the Rust compiler panic. Executing that original source raises BaseFTests NameError in both interpreters. Separate valid mock.patch and nested-capture controls execute and restore the patched function.

Output is grouped by execution below. Historical and current runs may use different expanded probes; they compare the reported symptom rather than identical before/after inputs. The paired CPython and current inputs are identified in their execution records.

<details>
<summary>Current verification — exit 0</summary>

**stdout:**

```text
original compile success
original execution NameError name 'BaseFTests' is not defined
valid patch method 3 outside 1
nested capture 7 outside 1
```

**stderr:** No output.

</details>

<details>
<summary>CPython 3.14.6 — exit 0</summary>

**stdout:**

```text
original compile success
original execution NameError name 'BaseFTests' is not defined
valid patch method 3 outside 1
nested capture 7 outside 1
```

**stderr:** No output.

</details>

<details>
<summary>RustPython before (reused) — exit 101</summary>

**stdout:** No output.

**stderr:**

```text
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
[WARN  rustpython_vm::object::core] couldn't run __del__ method for object
thread 'main' panicked at 'assertion failed: table.sub_tables.is_empty()', compiler/codegen/src/compile.rs:305:9
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

</details>

## Run

Use existing verified executables and a matching baseline Lib; see [environment and path mapping](../../ENVIRONMENT.md). No new build or environment was created for this publication. The command below is the archived argv with local paths replaced by placeholders, not a new execution. Restore those paths to your existing setup before running it.

```sh
'<survey>/.build/slot-b/saved/current-f39-x86/rustpython' -B -S \
  '<initial16-audit>/agent-b/probe-4856.py'
```

CPython reference command:

```sh
'<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14' -B -S \
  '<initial16-audit>/agent-b/probe-4856.py'
```

All environment overrides, cwd, input and executable identity are preserved in the execution records below.

## Analysis and closure rationale

The original source compiles without the Rust compiler panic. Executing that original source raises BaseFTests NameError in both interpreters. Separate valid mock.patch and nested-capture controls execute and restore the patched function.

[PR #8138](https://github.com/RustPython/RustPython/pull/8138): visit class decorators before entering their class scope.

The changes explain the observed behavior. No adjacent parent/commit execution or bisect established the first fixing commit.

**Scope and limitations:** The original application is not runnable as written; compile success is not application success. The normalized runtime examples are separate inputs.

## Versions and environment

- Baseline source: [`f39b054b9c8c`](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- Host: macOS 26.5.2 ARM64. Slot A uses native ARM64 RustPython; slot B uses x86_64 RustPython through Rosetta. CPython is 3.14.6 ARM64.
- This primary record is from slot B/Rosetta.
- [Binary hashes, actual imported Lib, and resource constraints](../../ENVIRONMENT.md).
- Historical runs were not replayed during the independent recheck or this publication. Approximate historical baselines remain marked in their metadata.

## Recorded evidence

- [Reused historical metadata and evidence](../../../cases/4856/evidence/metadata.json).
- Historical baseline: [`c7faae9b22ce`](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100), reused only. Exact/release/approximate selection is recorded in the historical metadata.
- [Full reused historical.stdout.txt](../../../cases/4856/evidence/historical.stdout.txt).
- [Full reused historical.stderr.txt](../../../cases/4856/evidence/historical.stderr.txt).
- [Independent assessment, original scope and limitations](assessment.json).

- **[fresh-4856-cp](../../evidence/initial16/agent-b/fresh-4856-cp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-4856-cp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-4856-cp.stderr).
- **[fresh-4856-rp](../../evidence/initial16/agent-b/fresh-4856-rp.json)** — exit `0`; timeout `false`.
  stdout: [stdout](../../evidence/initial16/agent-b/fresh-4856-rp.stdout); stderr: [stderr](../../evidence/initial16/agent-b/fresh-4856-rp.stderr).

AI assistance: OpenAI Codex assisted with independent verification, evidence packaging and drafting.
