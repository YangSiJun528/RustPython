# #4856 — Assertion failed: table.sub_tables.is_empty() when decorator class takes a lambda argument.

Original issue: [#4856](https://github.com/RustPython/RustPython/issues/4856)

**Verified closure candidate:** Compiling the original decorated-class source now succeeds without the `table.sub_tables.is_empty()` panic. Decorator scope scanning now matches code-generation order.

**Tested commits:** before `c7faae9b22ce` → after `f39b054b9c8c` (October 4, 2026). Historical selection and full build details are below.

## Reproducer

Canonical input: [repro.py](repro.py). The original source is compiled as a string. This directly exercises the reported compiler panic.

Compile only: the application names in this source need not exist because the source is never executed.

```python
source = """\
import unittest
from unittest import mock

class MockedA(BaseFTests):
    pass

@mock.patch("", lambda: 3)
class MockedB(MockedA):
    def _asserts(self, val):
        pass
"""
compile(source, "repros/4856/issue-4856-case-01/source-01.txt", "exec")
print("compile_success")
```

## Expected and observed results

**Expected:** compile_success (exit 0).

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>CPython 3.14.6</th><th>RustPython before</th><th>RustPython after</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>compile_success</code></pre></td>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>compile_success</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>thread 'main' panicked at 'assertion failed:
table.sub_tables.is_empty()',
compiler/codegen/src/compile.rs:305:9
note: run with `RUST_BACKTRACE=1` environment variable to
display a backtrace</code></pre><p><em>6 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>0</code></td>
<td valign="top"><code>101</code></td>
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

## Run

First complete [BUILD.md](BUILD.md) in the same shell. It creates `rustpython_repro_root`, builds both pinned commits and verifies their versions. Keep both checkouts while running these commands.

Save the code above as `$rustpython_repro_root/repro.py` (or copy the linked `repro.py` there). Both versions execute this one file, each with its matching standard library:

```sh
(
  cd "$rustpython_repro_root" || exit
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE
  for phase in historical current; do
    printf "\n%s\n" "$phase"
    if RUSTPYTHONPATH="$rustpython_repro_root/$phase/Lib" PYTHONDONTWRITEBYTECODE=1 \
      "$rustpython_repro_root/target-$phase/release/rustpython" \
      "$rustpython_repro_root/repro.py"; then
      printf 'exit_code=0\n'
    else
      printf 'exit_code=%s\n' "$?"
    fi
  done
)
```

CPython reference (3.14.6 in the recorded comparison):

```sh
(
  cd "$rustpython_repro_root" || exit
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE RUSTPYTHONPATH
  python3.14 -VV
  if PYTHONDONTWRITEBYTECODE=1 python3.14 "$rustpython_repro_root/repro.py"; then
    printf 'exit_code=0\n'
  else
    printf 'exit_code=%s\n' "$?"
  fi
)
```

To run the comparison and capture all outputs together, use the optional [comparison command](../../README.md#compare-both-revisions-at-once). Direct commands above do not require that runner.

## Analysis and closure rationale

Class decorators are scanned before entering the class scope, matching code-generation order and keeping nested symbol tables aligned. The original source now compiles without the reported `table.sub_tables.is_empty()` panic.

[PR #8138](https://github.com/RustPython/RustPython/pull/8138): correct class-decorator scope scanning order.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Versions and environment

- **Before:** [c7faae9b22ce](https://github.com/RustPython/RustPython/commit/c7faae9b22ce31a3ba1f2cc1cd3ad759b54ce100) (reported v0.2.0 release tag).
- **After:** [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c).
- **Platform:** macOS ARM64.
- **Rust toolchains:** before `rustc 1.67.1 (d5a82bbd2 2023-02-07)`; after `rustc 1.99.0 (b940084d7 2026-09-28)`. Default Cargo features, committed lockfiles.
- **CPython:** `3.14.6 (main, Jun 23 2026, 15:46:31) [Clang 22.1.3 ]`. [Reference provenance](evidence/reference.json).
- **Full reproduction:** [BUILD.md](BUILD.md) contains exact checkout, toolchain, build and executable-version checks. Return to the Run section after setup.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).
- [CPython stdout](evidence/cpython.stdout.txt) / [CPython stderr](evidence/cpython.stderr.txt).

<details>
<summary>Full recorded stderr (including traceback frames)</summary>

**Historical:**

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

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
